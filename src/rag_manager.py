import numpy as np
from datetime import datetime
from database import get_db_connection

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class RAGManager:
    def __init__(self, ollama_manager, chunk_size=500):
        self.ollama = ollama_manager
        self.chunk_size = chunk_size
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create RAG tables if they don't exist"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB,
                    tokens INTEGER,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_doc_user 
                ON documents(user_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_chunk_doc 
                ON document_chunks(document_id)
            ''')
            conn.commit()
    
    def add_document(self, user_id, title, content, source=None, metadata=None):
        """Add document and generate embeddings"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for RAG. Install with: pip install scikit-learn")
        
        chunks = self.split_into_chunks(content)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO documents (user_id, title, content, source, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, title, content, source, metadata))
            doc_id = cursor.lastrowid
            
            for i, chunk in enumerate(chunks):
                try:
                    embedding_response = self.ollama.embeddings('llama2', chunk)
                    embedding = embedding_response.get('embedding', [])
                    
                    if embedding:
                        embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
                    else:
                        embedding_bytes = None
                    
                    cursor.execute('''
                        INSERT INTO document_chunks
                        (document_id, chunk_index, content, embedding, tokens)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (doc_id, i, chunk, embedding_bytes, len(chunk.split())))
                except Exception as e:
                    print(f"Warning: Failed to generate embedding for chunk {i}: {e}")
                    cursor.execute('''
                        INSERT INTO document_chunks
                        (document_id, chunk_index, content, tokens)
                        VALUES (?, ?, ?, ?)
                    ''', (doc_id, i, chunk, len(chunk.split())))
            
            conn.commit()
            return doc_id
    
    def search(self, query, user_id=None, top_k=3):
        """Search for relevant chunks"""
        if not SKLEARN_AVAILABLE:
            return self._fallback_search(query, user_id, top_k)
        
        try:
            query_embedding_response = self.ollama.embeddings('llama2', query)
            query_embedding = query_embedding_response.get('embedding', [])
            
            if not query_embedding:
                return self._fallback_search(query, user_id, top_k)
            
            query_vec = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        except Exception as e:
            print(f"Warning: Failed to generate query embedding: {e}")
            return self._fallback_search(query, user_id, top_k)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT dc.id, dc.document_id, dc.content, dc.embedding, d.title, d.source
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE d.user_id = ? AND dc.embedding IS NOT NULL
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT dc.id, dc.document_id, dc.content, dc.embedding, d.title, d.source
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE dc.embedding IS NOT NULL
                ''')
            
            results = []
            for row in cursor.fetchall():
                try:
                    chunk_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                    chunk_vec = chunk_embedding.reshape(1, -1)
                    
                    similarity = cosine_similarity(query_vec, chunk_vec)[0][0]
                    
                    results.append({
                        'chunk_id': row['id'],
                        'document_id': row['document_id'],
                        'title': row['title'],
                        'content': row['content'],
                        'source': row['source'],
                        'similarity': float(similarity)
                    })
                except Exception as e:
                    print(f"Warning: Failed to calculate similarity for chunk {row['id']}: {e}")
                    continue
            
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
    
    def _fallback_search(self, query, user_id, top_k):
        """Fallback keyword-based search"""
        query_lower = query.lower()
        keywords = query_lower.split()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT dc.id, dc.document_id, dc.content, d.title, d.source
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE d.user_id = ?
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT dc.id, dc.document_id, dc.content, d.title, d.source
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                ''')
            
            results = []
            for row in cursor.fetchall():
                content_lower = row['content'].lower()
                score = sum(1 for keyword in keywords if keyword in content_lower)
                
                if score > 0:
                    results.append({
                        'chunk_id': row['id'],
                        'document_id': row['document_id'],
                        'title': row['title'],
                        'content': row['content'],
                        'source': row['source'],
                        'similarity': score / len(keywords)
                    })
            
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
    
    def generate_with_context(self, query, user_id=None, model='llama2', top_k=3):
        """Generate response with RAG"""
        relevant_chunks = self.search(query, user_id, top_k)
        
        if not relevant_chunks:
            return {
                'response': 'No relevant documents found. Please ask a question based on uploaded documents.',
                'sources': []
            }
        
        context = "\n\n".join([
            f"Source {i+1} ({chunk['title']}):\n{chunk['content']}"
            for i, chunk in enumerate(relevant_chunks)
        ])
        
        prompt = f"""Answer the question based on the following context.

Context:
{context}

Question: {query}

Answer:"""
        
        response = self.ollama.generate(model, prompt)
        
        return {
            'response': response['response'],
            'sources': relevant_chunks
        }
    
    def split_into_chunks(self, text):
        """Split text into chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size):
            chunk = ' '.join(words[i:i + self.chunk_size])
            chunks.append(chunk)
        
        return chunks if chunks else [text]
    
    def delete_document(self, document_id, user_id):
        """Delete a document and its chunks"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM documents 
                WHERE id = ? AND user_id = ?
            ''', (document_id, user_id))
            deleted = cursor.rowcount
            conn.commit()
            return deleted > 0
    
    def list_documents(self, user_id):
        """List all documents for a user"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT d.id, d.title, d.source, d.created_at,
                       COUNT(dc.id) as chunk_count
                FROM documents d
                LEFT JOIN document_chunks dc ON d.id = dc.document_id
                WHERE d.user_id = ?
                GROUP BY d.id
                ORDER BY d.created_at DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self):
        """Get RAG statistics"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT d.id) as total_documents,
                    COUNT(dc.id) as total_chunks,
                    SUM(dc.tokens) as total_tokens,
                    COUNT(CASE WHEN dc.embedding IS NOT NULL THEN 1 END) as embedded_chunks
                FROM documents d
                LEFT JOIN document_chunks dc ON d.id = dc.document_id
            ''')
            return dict(cursor.fetchone())
