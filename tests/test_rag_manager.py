import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from rag_manager import RAGManager
from database import get_database_path
import numpy as np

class MockOllamaManager:
    """Mock Ollama manager for testing"""
    def __init__(self):
        self.embedding_size = 4096
    
    def embeddings(self, model, text):
        """Return mock embeddings"""
        # Generate deterministic embeddings based on text
        np.random.seed(len(text))
        embedding = np.random.random(self.embedding_size).tolist()
        return {'embedding': embedding}
    
    def generate(self, model, prompt, **kwargs):
        """Return mock generation"""
        return {
            'response': f'Mock response for prompt containing: {prompt[:50]}...',
            'model': model
        }

@pytest.fixture
def rag_manager():
    """Create RAG manager with temporary database"""
    import tempfile
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    os.environ['DATABASE_PATH'] = temp_db.name
    
    # Initialize database with users table (required for foreign key)
    from database import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Add test users
        cursor.execute("INSERT INTO users (id, username, password) VALUES (1, 'user1', 'pass1')")
        cursor.execute("INSERT INTO users (id, username, password) VALUES (2, 'user2', 'pass2')")
        conn.commit()
    
    mock_ollama = MockOllamaManager()
    manager = RAGManager(mock_ollama, chunk_size=100)
    yield manager
    
    # Cleanup
    try:
        os.unlink(temp_db.name)
    except:
        pass

def test_rag_manager_initialization(rag_manager):
    """Test RAG manager initialization"""
    assert rag_manager is not None
    assert rag_manager.chunk_size == 100

def test_add_document(rag_manager):
    """Test adding a document"""
    doc_id = rag_manager.add_document(
        user_id=1,
        title='Test Document',
        content='This is a test document with some content.',
        source='test.txt'
    )
    
    assert doc_id > 0

def test_split_into_chunks(rag_manager):
    """Test text chunking"""
    text = ' '.join(['word'] * 250)  # 250 words
    chunks = rag_manager.split_into_chunks(text)
    
    assert len(chunks) == 3  # 250 words / 100 words per chunk = 3 chunks
    
    # Test small text
    small_text = 'Short text'
    small_chunks = rag_manager.split_into_chunks(small_text)
    assert len(small_chunks) == 1

def test_list_documents(rag_manager):
    """Test listing documents"""
    # Add multiple documents
    rag_manager.add_document(1, 'Doc 1', 'Content 1', 'source1.txt')
    rag_manager.add_document(1, 'Doc 2', 'Content 2', 'source2.txt')
    rag_manager.add_document(2, 'Doc 3', 'Content 3', 'source3.txt')
    
    # List for user 1
    docs = rag_manager.list_documents(1)
    assert len(docs) == 2
    assert docs[0]['title'] in ['Doc 1', 'Doc 2']
    
    # List for user 2
    docs = rag_manager.list_documents(2)
    assert len(docs) == 1
    assert docs[0]['title'] == 'Doc 3'

def test_delete_document(rag_manager):
    """Test deleting a document"""
    doc_id = rag_manager.add_document(1, 'Test', 'Content', 'source.txt')
    
    # Delete should succeed for correct user
    success = rag_manager.delete_document(doc_id, 1)
    assert success == True
    
    # Document should be gone
    docs = rag_manager.list_documents(1)
    assert len(docs) == 0
    
    # Delete non-existent document
    success = rag_manager.delete_document(999, 1)
    assert success == False

def test_search_documents(rag_manager):
    """Test searching documents"""
    # Add documents
    rag_manager.add_document(
        1, 'Python Guide',
        'Python is a high-level programming language. It is easy to learn and powerful.',
        'python.txt'
    )
    rag_manager.add_document(
        1, 'JavaScript Guide',
        'JavaScript is a scripting language for web browsers. It is very popular.',
        'javascript.txt'
    )
    
    # Search for Python-related content
    results = rag_manager.search('Python programming', user_id=1, top_k=2)
    
    assert len(results) > 0
    # Results should contain similarity scores
    assert 'similarity' in results[0]
    assert 'content' in results[0]
    assert 'title' in results[0]

def test_generate_with_context(rag_manager):
    """Test RAG generation"""
    # Add document
    rag_manager.add_document(
        1, 'Python Basics',
        'Python uses indentation for code blocks. Variables are dynamically typed.',
        'python.txt'
    )
    
    # Generate with RAG
    result = rag_manager.generate_with_context(
        'What is Python?',
        user_id=1,
        model='llama2'
    )
    
    assert 'response' in result
    assert 'sources' in result
    assert len(result['sources']) > 0

def test_generate_without_documents(rag_manager):
    """Test RAG generation with no relevant documents"""
    result = rag_manager.generate_with_context(
        'What is quantum computing?',
        user_id=1,
        model='llama2'
    )
    
    assert 'No relevant documents found' in result['response']
    assert len(result['sources']) == 0

def test_rag_stats(rag_manager):
    """Test RAG statistics"""
    # Add documents
    rag_manager.add_document(1, 'Doc 1', ' '.join(['word'] * 200), 'source1.txt')
    rag_manager.add_document(1, 'Doc 2', ' '.join(['word'] * 150), 'source2.txt')
    
    stats = rag_manager.get_stats()
    
    assert stats['total_documents'] == 2
    assert stats['total_chunks'] > 2  # Should have multiple chunks
    assert stats['total_tokens'] > 0

def test_chunk_embeddings(rag_manager):
    """Test that chunks get embeddings"""
    doc_id = rag_manager.add_document(
        1, 'Test',
        'This is a test document with enough content to create embeddings.',
        'test.txt'
    )
    
    # Check in database that embeddings were created
    from database import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count, 
                   SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as embedded_count
            FROM document_chunks
            WHERE document_id = ?
        ''', (doc_id,))
        result = cursor.fetchone()
        
        assert result['count'] > 0
        # Most chunks should have embeddings (may fail gracefully for some)
        assert result['embedded_count'] > 0

def test_user_isolation(rag_manager):
    """Test that users can only see their own documents"""
    # Add documents for different users
    doc1 = rag_manager.add_document(1, 'User1 Doc', 'Content 1', 'source1.txt')
    doc2 = rag_manager.add_document(2, 'User2 Doc', 'Content 2', 'source2.txt')
    
    # User 1 should only see their documents
    results1 = rag_manager.search('Content', user_id=1, top_k=10)
    assert all(r['title'] == 'User1 Doc' for r in results1)
    
    # User 2 should only see their documents
    results2 = rag_manager.search('Content', user_id=2, top_k=10)
    assert all(r['title'] == 'User2 Doc' for r in results2)

def test_top_k_limit(rag_manager):
    """Test that top_k limits results"""
    # Add multiple documents
    for i in range(5):
        rag_manager.add_document(1, f'Doc {i}', f'Content {i}', f'source{i}.txt')
    
    # Search with different top_k values
    results_3 = rag_manager.search('Content', user_id=1, top_k=3)
    results_5 = rag_manager.search('Content', user_id=1, top_k=5)
    
    assert len(results_3) <= 3
    assert len(results_5) <= 5

def test_fallback_keyword_search(rag_manager):
    """Test fallback to keyword search when sklearn is unavailable"""
    # Add documents
    rag_manager.add_document(
        1, 'Python Tutorial',
        'Python is great for beginners. Python has simple syntax.',
        'python.txt'
    )
    rag_manager.add_document(
        1, 'Java Tutorial',
        'Java is used for enterprise applications.',
        'java.txt'
    )
    
    # Force fallback search by using the _fallback_search method
    results = rag_manager._fallback_search('Python syntax', user_id=1, top_k=2)
    
    assert len(results) > 0
    # Python document should rank higher
    assert 'Python' in results[0]['title']

def test_empty_document(rag_manager):
    """Test handling of empty/whitespace content"""
    doc_id = rag_manager.add_document(
        1, 'Empty Doc', '   ', 'empty.txt'
    )
    
    assert doc_id > 0
    
    # Should still be searchable
    docs = rag_manager.list_documents(1)
    assert len(docs) == 1
