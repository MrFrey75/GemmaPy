# GemmaPy Ollama Enhancement Roadmap

Comprehensive plan for future enhancements to the Ollama/LLM integration in GemmaPy.

**Last Updated:** October 29, 2025  
**Version:** 1.3.0  
**Status:** Planning Phase

---

## Table of Contents

1. [Response Caching](#1-response-caching)
2. [Conversation Persistence](#2-conversation-persistence)
3. [Multi-Model Comparison](#3-multi-model-comparison)
4. [Fine-Tuning Support](#4-fine-tuning-support)
5. [RAG (Retrieval Augmented Generation)](#5-rag-retrieval-augmented-generation)
6. [Model Performance Metrics](#6-model-performance-metrics)
7. [Cost Tracking](#7-cost-tracking)
8. [A/B Testing Framework](#8-ab-testing-framework)
9. [Prompt Templates Library](#9-prompt-templates-library)
10. [Auto-Retry with Fallbacks](#10-auto-retry-with-fallbacks)

---

## 1. Response Caching

### Overview
Implement intelligent caching to avoid redundant LLM calls for identical or similar prompts.

### Priority
🔥 **HIGH** - Significant performance and resource savings

### Benefits
- Faster response times (instant for cached results)
- Reduced computational load
- Lower resource consumption
- Better user experience

### Technical Approach

#### Database Schema
```sql
CREATE TABLE llm_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    system_prompt TEXT,
    response TEXT NOT NULL,
    temperature REAL,
    max_tokens INTEGER,
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_cache_key ON llm_cache(cache_key);
CREATE INDEX idx_expires ON llm_cache(expires_at);
```

#### Implementation
```python
import hashlib
import json
from datetime import datetime, timedelta

class LLMCache:
    def __init__(self, default_ttl=3600):
        self.default_ttl = default_ttl  # 1 hour default
    
    def generate_cache_key(self, model, prompt, system=None, 
                          temperature=0.7, max_tokens=None):
        """Generate unique cache key from parameters"""
        cache_data = {
            'model': model,
            'prompt': prompt.strip(),
            'system': system,
            'temperature': round(temperature, 2),
            'max_tokens': max_tokens
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    def get(self, cache_key):
        """Retrieve cached response if valid"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT response, expires_at 
                FROM llm_cache 
                WHERE cache_key = ? AND 
                      (expires_at IS NULL OR expires_at > ?)
            ''', (cache_key, datetime.now()))
            
            result = cursor.fetchone()
            if result:
                # Update statistics
                cursor.execute('''
                    UPDATE llm_cache 
                    SET hit_count = hit_count + 1,
                        last_accessed = ?
                    WHERE cache_key = ?
                ''', (datetime.now(), cache_key))
                conn.commit()
                return result['response']
        return None
    
    def set(self, cache_key, response, ttl=None):
        """Store response in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO llm_cache 
                (cache_key, response, expires_at)
                VALUES (?, ?, ?)
            ''', (cache_key, response, expires_at))
            conn.commit()
    
    def clear_expired(self):
        """Remove expired cache entries"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM llm_cache 
                WHERE expires_at IS NOT NULL 
                  AND expires_at < ?
            ''', (datetime.now(),))
            conn.commit()
    
    def invalidate(self, pattern=None):
        """Invalidate cache entries"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if pattern:
                cursor.execute('''
                    DELETE FROM llm_cache 
                    WHERE prompt LIKE ?
                ''', (f'%{pattern}%',))
            else:
                cursor.execute('DELETE FROM llm_cache')
            conn.commit()
```

#### API Enhancement
```python
@app.route('/api/ollama/generate', methods=['POST'])
@require_auth
def ollama_generate():
    data = request.get_json()
    use_cache = data.get('use_cache', True)
    
    cache = LLMCache()
    cache_key = cache.generate_cache_key(
        data.get('model', 'llama2'),
        data.get('prompt'),
        data.get('system'),
        data.get('temperature', 0.7),
        data.get('max_tokens')
    )
    
    # Check cache
    if use_cache:
        cached_response = cache.get(cache_key)
        if cached_response:
            return jsonify({
                'response': cached_response,
                'cached': True,
                'cache_key': cache_key
            }), 200
    
    # Generate new response
    response = ollama.generate(...)
    
    # Cache the response
    if use_cache:
        cache.set(cache_key, response['response'])
    
    return jsonify({**response, 'cached': False}), 200
```

### Configuration Options
```python
CACHE_CONFIG = {
    'enabled': True,
    'default_ttl': 3600,  # 1 hour
    'max_size': 10000,    # Maximum cache entries
    'strategies': {
        'exact': True,      # Exact prompt matching
        'semantic': False,  # Semantic similarity (future)
    }
}
```

### Estimated Effort
- Development: **2-3 days**
- Testing: **1 day**
- Documentation: **0.5 days**

### Dependencies
- SQLite (already available)
- hashlib (built-in)

---

## 2. Conversation Persistence

### Overview
Store and retrieve conversation histories for multi-session continuity.

### Priority
🟡 **MEDIUM** - Improves user experience

### Benefits
- Resume conversations across sessions
- Conversation history tracking
- User context preservation
- Analytics on conversation patterns

### Database Schema
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE conversation_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_conv_user ON conversations(user_id);
CREATE INDEX idx_msg_conv ON conversation_messages(conversation_id);
```

### API Endpoints

#### Create Conversation
```http
POST /api/conversations
{
  "title": "Python Learning",
  "model": "llama2",
  "system_prompt": "You are a helpful Python tutor"
}
```

#### List Conversations
```http
GET /api/conversations
```

#### Get Conversation
```http
GET /api/conversations/<id>
```

#### Add Message
```http
POST /api/conversations/<id>/messages
{
  "role": "user",
  "content": "How do I use list comprehensions?"
}
```

#### Generate Response
```http
POST /api/conversations/<id>/generate
{
  "temperature": 0.7,
  "stream": false
}
```

#### Delete Conversation
```http
DELETE /api/conversations/<id>
```

### Implementation
```python
class ConversationManager:
    def create(self, user_id, title, model, system_prompt=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (user_id, title, model)
                VALUES (?, ?, ?)
            ''', (user_id, title, model))
            conversation_id = cursor.lastrowid
            
            # Add system message if provided
            if system_prompt:
                cursor.execute('''
                    INSERT INTO conversation_messages 
                    (conversation_id, role, content)
                    VALUES (?, 'system', ?)
                ''', (conversation_id, system_prompt))
            
            conn.commit()
            return conversation_id
    
    def get_messages(self, conversation_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content, created_at
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY id ASC
            ''', (conversation_id,))
            return cursor.fetchall()
    
    def add_message(self, conversation_id, role, content):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversation_messages
                (conversation_id, role, content)
                VALUES (?, ?, ?)
            ''', (conversation_id, role, content))
            
            # Update conversation
            cursor.execute('''
                UPDATE conversations
                SET message_count = message_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (conversation_id,))
            conn.commit()
    
    def generate_title(self, messages):
        """Auto-generate conversation title from first message"""
        if messages:
            first_user_msg = next(
                (m for m in messages if m['role'] == 'user'), 
                None
            )
            if first_user_msg:
                content = first_user_msg['content']
                return content[:50] + ('...' if len(content) > 50 else '')
        return "New Conversation"
```

### Estimated Effort
- Development: **3-4 days**
- Testing: **1-2 days**
- Documentation: **1 day**

---

## 3. Multi-Model Comparison

### Overview
Run the same prompt across multiple models simultaneously and compare results.

### Priority
🟡 **MEDIUM** - Valuable for quality assessment

### Benefits
- Compare model outputs side-by-side
- Choose best model for specific tasks
- Quality benchmarking
- A/B testing support

### Implementation
```python
class ModelComparator:
    def compare(self, prompt, models=['llama2', 'llama3', 'mistral'],
                system=None, temperature=0.7):
        results = []
        
        for model in models:
            start_time = time.time()
            try:
                response = ollama.generate(
                    model=model,
                    prompt=prompt,
                    system=system,
                    temperature=temperature
                )
                duration = time.time() - start_time
                
                results.append({
                    'model': model,
                    'response': response['response'],
                    'duration': duration,
                    'success': True,
                    'eval_count': response.get('eval_count', 0),
                    'tokens_per_second': response.get('eval_count', 0) / duration
                })
            except Exception as e:
                results.append({
                    'model': model,
                    'error': str(e),
                    'success': False
                })
        
        return results
    
    def evaluate_responses(self, results, criteria):
        """Evaluate responses based on criteria"""
        scores = []
        
        for result in results:
            if not result['success']:
                continue
            
            score = {
                'model': result['model'],
                'speed_score': self._score_speed(result['duration']),
                'length_score': self._score_length(result['response']),
                'quality_score': 0  # Would need LLM-based evaluation
            }
            scores.append(score)
        
        return scores
```

### API Endpoint
```python
@app.route('/api/ollama/compare', methods=['POST'])
@require_auth
def ollama_compare():
    data = request.get_json()
    
    comparator = ModelComparator()
    results = comparator.compare(
        prompt=data.get('prompt'),
        models=data.get('models', ['llama2', 'llama3']),
        system=data.get('system'),
        temperature=data.get('temperature', 0.7)
    )
    
    return jsonify({
        'prompt': data.get('prompt'),
        'results': results,
        'comparison_id': str(uuid.uuid4())
    }), 200
```

### UI Considerations
```
┌─────────────────────────────────────────────────────────┐
│ Prompt: "Explain quantum computing"                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ LLaMA 2           │ LLaMA 3           │ Mistral         │
│ ────────────────  │ ────────────────  │ ──────────────  │
│ Response...       │ Response...       │ Response...     │
│                   │                   │                 │
│ ⏱ 2.3s           │ ⏱ 1.8s           │ ⏱ 2.1s         │
│ 📊 150 tokens    │ 📊 175 tokens    │ 📊 160 tokens  │
│                   │                   │                 │
│ [👍 Like]        │ [👍 Like]        │ [👍 Like]      │
└─────────────────────────────────────────────────────────┘
```

### Estimated Effort
- Development: **2-3 days**
- Testing: **1 day**
- Documentation: **1 day**

---

## 4. Fine-Tuning Support

### Overview
Enable fine-tuning of models with custom datasets for specialized tasks.

### Priority
🔵 **LOW** - Advanced feature, complex implementation

### Benefits
- Specialized models for specific domains
- Improved accuracy on custom tasks
- Domain-specific language understanding

### Technical Approach

#### Dataset Management
```sql
CREATE TABLE training_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    format TEXT CHECK(format IN ('jsonl', 'csv', 'txt')),
    file_path TEXT NOT NULL,
    size_bytes INTEGER,
    sample_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE fine_tuning_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    base_model TEXT NOT NULL,
    dataset_id INTEGER NOT NULL,
    output_model TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    progress REAL DEFAULT 0,
    epochs INTEGER DEFAULT 3,
    learning_rate REAL DEFAULT 0.0001,
    batch_size INTEGER DEFAULT 4,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (dataset_id) REFERENCES training_datasets(id)
);
```

#### Implementation
```python
class FineTuningManager:
    def create_modelfile(self, base_model, dataset_path, 
                        output_name, params):
        """Generate Ollama Modelfile for fine-tuning"""
        modelfile = f"""FROM {base_model}
ADAPTER {dataset_path}
PARAMETER temperature {params.get('temperature', 0.7)}
PARAMETER num_ctx {params.get('context_length', 2048)}
"""
        return modelfile
    
    def start_fine_tuning(self, job_id):
        """Start fine-tuning job"""
        job = self.get_job(job_id)
        
        # Create modelfile
        modelfile = self.create_modelfile(
            job['base_model'],
            job['dataset_path'],
            job['output_model'],
            job['params']
        )
        
        # Save modelfile
        modelfile_path = f"/tmp/modelfile_{job_id}"
        with open(modelfile_path, 'w') as f:
            f.write(modelfile)
        
        # Create model via Ollama
        subprocess.run([
            'ollama', 'create', 
            job['output_model'],
            '-f', modelfile_path
        ])
        
        # Update job status
        self.update_job_status(job_id, 'completed')
```

### Ollama Integration
```bash
# Create fine-tuned model
ollama create my-custom-model -f Modelfile

# Modelfile example
FROM llama2
ADAPTER ./my-training-data.jsonl
PARAMETER temperature 0.8
PARAMETER num_ctx 4096
```

### Estimated Effort
- Research: **2-3 days**
- Development: **5-7 days**
- Testing: **2-3 days**
- Documentation: **2 days**

---

## 5. RAG (Retrieval Augmented Generation)

### Overview
Implement Retrieval Augmented Generation to enhance responses with external knowledge.

### Priority
🔥 **HIGH** - Very valuable feature

### Benefits
- Access to external knowledge bases
- More accurate and up-to-date responses
- Source attribution
- Reduced hallucinations

### Architecture

```
User Query
    ↓
[Embed Query] → Vector Search → [Find Relevant Docs]
    ↓                                    ↓
[Combine: Query + Context] → [LLM Generate] → Response
```

### Database Schema
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB,  -- Store as binary
    tokens INTEGER,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_doc_user ON documents(user_id);
CREATE INDEX idx_chunk_doc ON document_chunks(document_id);
```

### Implementation
```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class RAGManager:
    def __init__(self, ollama_manager, chunk_size=500):
        self.ollama = ollama_manager
        self.chunk_size = chunk_size
    
    def add_document(self, user_id, title, content, source=None):
        """Add document and generate embeddings"""
        # Split into chunks
        chunks = self.split_into_chunks(content)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert document
            cursor.execute('''
                INSERT INTO documents (user_id, title, content, source)
                VALUES (?, ?, ?, ?)
            ''', (user_id, title, content, source))
            doc_id = cursor.lastrowid
            
            # Generate and store embeddings
            for i, chunk in enumerate(chunks):
                embedding = self.ollama.embeddings('llama2', chunk)
                embedding_bytes = np.array(embedding).tobytes()
                
                cursor.execute('''
                    INSERT INTO document_chunks
                    (document_id, chunk_index, content, embedding, tokens)
                    VALUES (?, ?, ?, ?, ?)
                ''', (doc_id, i, chunk, embedding_bytes, len(chunk.split())))
            
            conn.commit()
            return doc_id
    
    def search(self, query, top_k=3):
        """Search for relevant chunks"""
        # Generate query embedding
        query_embedding = self.ollama.embeddings('llama2', query)
        query_vec = np.array(query_embedding).reshape(1, -1)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, document_id, content, embedding
                FROM document_chunks
            ''')
            
            results = []
            for row in cursor.fetchall():
                chunk_embedding = np.frombuffer(row['embedding'])
                chunk_vec = chunk_embedding.reshape(1, -1)
                
                similarity = cosine_similarity(query_vec, chunk_vec)[0][0]
                
                results.append({
                    'chunk_id': row['id'],
                    'document_id': row['document_id'],
                    'content': row['content'],
                    'similarity': float(similarity)
                })
            
            # Sort by similarity
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
    
    def generate_with_context(self, query, model='llama2'):
        """Generate response with RAG"""
        # Find relevant context
        relevant_chunks = self.search(query)
        
        # Build context
        context = "\n\n".join([
            f"Source {i+1}:\n{chunk['content']}"
            for i, chunk in enumerate(relevant_chunks)
        ])
        
        # Generate with context
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
        
        return chunks
```

### API Endpoints
```python
@app.route('/api/rag/documents', methods=['POST'])
@require_auth
def rag_add_document():
    data = request.get_json()
    rag = RAGManager(ollama)
    
    doc_id = rag.add_document(
        user_id=request.user['user_id'],
        title=data['title'],
        content=data['content'],
        source=data.get('source')
    )
    
    return jsonify({'document_id': doc_id}), 201

@app.route('/api/rag/generate', methods=['POST'])
@require_auth
def rag_generate():
    data = request.get_json()
    rag = RAGManager(ollama)
    
    result = rag.generate_with_context(
        query=data['query'],
        model=data.get('model', 'llama2')
    )
    
    return jsonify(result), 200
```

### Dependencies
- numpy
- scikit-learn

### Estimated Effort
- Development: **5-7 days**
- Testing: **2-3 days**
- Documentation: **2 days**

---

## 6. Model Performance Metrics

### Overview
Track and analyze model performance across various dimensions.

### Priority
🟡 **MEDIUM** - Important for optimization

### Metrics to Track
- Response time
- Tokens per second
- Token count (prompt + response)
- Cache hit rate
- Error rate
- User satisfaction (thumbs up/down)
- Model usage distribution

### Database Schema
```sql
CREATE TABLE llm_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    model TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    prompt_tokens INTEGER,
    response_tokens INTEGER,
    total_tokens INTEGER,
    duration_ms INTEGER,
    tokens_per_second REAL,
    cached BOOLEAN DEFAULT 0,
    error BOOLEAN DEFAULT 0,
    error_message TEXT,
    user_rating INTEGER CHECK(user_rating IN (-1, 0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_metrics_model ON llm_metrics(model);
CREATE INDEX idx_metrics_created ON llm_metrics(created_at);
CREATE INDEX idx_metrics_user ON llm_metrics(user_id);
```

### Implementation
```python
class MetricsCollector:
    def record(self, user_id, model, endpoint, prompt, response, 
               duration, error=None, cached=False):
        metrics = {
            'user_id': user_id,
            'model': model,
            'endpoint': endpoint,
            'prompt_tokens': len(prompt.split()),
            'response_tokens': len(response.split()) if response else 0,
            'duration_ms': int(duration * 1000),
            'cached': cached,
            'error': error is not None,
            'error_message': str(error) if error else None
        }
        
        metrics['total_tokens'] = (
            metrics['prompt_tokens'] + metrics['response_tokens']
        )
        metrics['tokens_per_second'] = (
            metrics['total_tokens'] / duration if duration > 0 else 0
        )
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO llm_metrics 
                (user_id, model, endpoint, prompt_tokens, response_tokens,
                 total_tokens, duration_ms, tokens_per_second, cached,
                 error, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', tuple(metrics.values()))
            conn.commit()
    
    def get_dashboard_stats(self, days=7):
        """Get metrics for dashboard"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Overall stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN error = 1 THEN 1 ELSE 0 END) as errors,
                    AVG(duration_ms) as avg_duration,
                    AVG(tokens_per_second) as avg_tokens_per_sec,
                    SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cache_hits
                FROM llm_metrics
                WHERE created_at >= datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            stats = dict(cursor.fetchone())
            
            # Per-model stats
            cursor.execute('''
                SELECT 
                    model,
                    COUNT(*) as requests,
                    AVG(duration_ms) as avg_duration,
                    AVG(tokens_per_second) as avg_tps
                FROM llm_metrics
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY model
            ''', (days,))
            
            stats['by_model'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
```

### Dashboard API
```python
@app.route('/api/metrics/dashboard', methods=['GET'])
@require_admin
def metrics_dashboard():
    days = request.args.get('days', 7, type=int)
    collector = MetricsCollector()
    stats = collector.get_dashboard_stats(days)
    return jsonify(stats), 200
```

### Estimated Effort
- Development: **3-4 days**
- Testing: **1-2 days**
- Documentation: **1 day**

---

## 7. Cost Tracking

### Overview
Track computational costs for LLM operations.

### Priority
🟡 **MEDIUM** - Important for resource management

### Cost Factors
- Token count (input + output)
- Model size/complexity
- Processing time
- GPU/CPU usage
- Electricity estimates

### Implementation
```python
class CostCalculator:
    # Cost per 1K tokens (example pricing)
    COSTS = {
        'llama2': {
            'input': 0.0001,   # $0.0001 per 1K tokens
            'output': 0.0002,
        },
        'llama2:13b': {
            'input': 0.0002,
            'output': 0.0004,
        },
        'llama2:70b': {
            'input': 0.0005,
            'output': 0.001,
        }
    }
    
    def calculate_cost(self, model, prompt_tokens, response_tokens):
        """Calculate cost for a request"""
        if model not in self.COSTS:
            model = 'llama2'  # Default
        
        pricing = self.COSTS[model]
        
        prompt_cost = (prompt_tokens / 1000) * pricing['input']
        response_cost = (response_tokens / 1000) * pricing['output']
        
        return {
            'prompt_cost': prompt_cost,
            'response_cost': response_cost,
            'total_cost': prompt_cost + response_cost,
            'currency': 'USD'
        }
    
    def get_user_costs(self, user_id, period='month'):
        """Get cost summary for user"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            period_map = {
                'day': 1,
                'week': 7,
                'month': 30
            }
            
            cursor.execute('''
                SELECT 
                    model,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(response_tokens) as total_response_tokens
                FROM llm_metrics
                WHERE user_id = ?
                  AND created_at >= datetime('now', '-' || ? || ' days')
                GROUP BY model
            ''', (user_id, period_map.get(period, 30)))
            
            total_cost = 0
            breakdown = []
            
            for row in cursor.fetchall():
                cost = self.calculate_cost(
                    row['model'],
                    row['total_prompt_tokens'],
                    row['total_response_tokens']
                )
                breakdown.append({
                    'model': row['model'],
                    **cost
                })
                total_cost += cost['total_cost']
            
            return {
                'period': period,
                'total_cost': total_cost,
                'breakdown': breakdown
            }
```

### API Endpoint
```python
@app.route('/api/costs/summary', methods=['GET'])
@require_auth
def cost_summary():
    period = request.args.get('period', 'month')
    calculator = CostCalculator()
    costs = calculator.get_user_costs(
        request.user['user_id'],
        period
    )
    return jsonify(costs), 200
```

### Estimated Effort
- Development: **2-3 days**
- Testing: **1 day**
- Documentation: **0.5 days**

---

## 8. A/B Testing Framework

### Overview
Framework for testing different prompts, models, or parameters.

### Priority
🔵 **LOW** - Advanced optimization feature

### Implementation
```python
class ABTestManager:
    def create_test(self, name, variants):
        """Create A/B test"""
        test_id = uuid.uuid4()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ab_tests (id, name, variants, status)
                VALUES (?, ?, ?, 'active')
            ''', (test_id, name, json.dumps(variants)))
            conn.commit()
        
        return test_id
    
    def assign_variant(self, test_id, user_id):
        """Assign user to variant"""
        # Simple random assignment
        test = self.get_test(test_id)
        variants = json.loads(test['variants'])
        variant = random.choice(variants)
        
        # Record assignment
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ab_assignments
                (test_id, user_id, variant)
                VALUES (?, ?, ?)
            ''', (test_id, user_id, variant))
            conn.commit()
        
        return variant
    
    def record_result(self, test_id, user_id, variant, 
                     metric_name, metric_value):
        """Record test result"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ab_results
                (test_id, user_id, variant, metric_name, metric_value)
                VALUES (?, ?, ?, ?, ?)
            ''', (test_id, user_id, variant, metric_name, metric_value))
            conn.commit()
    
    def get_results(self, test_id):
        """Get test results"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    variant,
                    metric_name,
                    AVG(metric_value) as avg_value,
                    COUNT(*) as sample_size
                FROM ab_results
                WHERE test_id = ?
                GROUP BY variant, metric_name
            ''', (test_id,))
            
            return cursor.fetchall()
```

### Estimated Effort
- Development: **4-5 days**
- Testing: **2 days**
- Documentation: **1 day**

---

## 9. Prompt Templates Library

### Overview
Reusable prompt templates for common tasks.

### Priority
🟡 **MEDIUM** - Improves developer experience

### Database Schema
```sql
CREATE TABLE prompt_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    template TEXT NOT NULL,
    variables TEXT,  -- JSON array
    model TEXT,
    temperature REAL,
    is_public BOOLEAN DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Implementation
```python
class PromptTemplateManager:
    # Built-in templates
    TEMPLATES = {
        'summarize': {
            'name': 'Summarize Text',
            'template': 'Summarize the following text in {length} sentences:\n\n{text}',
            'variables': ['text', 'length'],
            'category': 'content'
        },
        'translate': {
            'name': 'Translate',
            'template': 'Translate the following text to {language}:\n\n{text}',
            'variables': ['text', 'language'],
            'category': 'language'
        },
        'code_review': {
            'name': 'Code Review',
            'template': '''Review the following {language} code and provide feedback:

```{language}
{code}
```

Focus on:
- Code quality
- Potential bugs
- Best practices
- Suggestions for improvement''',
            'variables': ['code', 'language'],
            'category': 'code'
        },
        'explain_eli5': {
            'name': 'Explain Like I\'m 5',
            'template': 'Explain {concept} in simple terms that a 5-year-old would understand.',
            'variables': ['concept'],
            'category': 'education'
        }
    }
    
    def render(self, template_name, variables):
        """Render template with variables"""
        template = self.TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        prompt = template['template']
        for var, value in variables.items():
            prompt = prompt.replace(f'{{{var}}}', str(value))
        
        return prompt
    
    def create_custom(self, user_id, name, template, 
                     variables, category=None):
        """Create custom template"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO prompt_templates
                (user_id, name, template, variables, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, template, 
                  json.dumps(variables), category))
            conn.commit()
            return cursor.lastrowid
```

### API Endpoints
```python
@app.route('/api/templates', methods=['GET'])
@require_auth
def list_templates():
    manager = PromptTemplateManager()
    return jsonify({
        'built_in': list(manager.TEMPLATES.keys()),
        'templates': manager.TEMPLATES
    }), 200

@app.route('/api/templates/render', methods=['POST'])
@require_auth
def render_template():
    data = request.get_json()
    manager = PromptTemplateManager()
    
    prompt = manager.render(
        data['template_name'],
        data['variables']
    )
    
    # Optionally generate immediately
    if data.get('generate', False):
        response = ollama.generate(
            data.get('model', 'llama2'),
            prompt
        )
        return jsonify({
            'prompt': prompt,
            'response': response['response']
        }), 200
    
    return jsonify({'prompt': prompt}), 200
```

### Example Usage
```bash
curl -X POST http://localhost:5000/api/templates/render \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "summarize",
    "variables": {
      "text": "Long article text...",
      "length": "3"
    },
    "generate": true
  }'
```

### Estimated Effort
- Development: **2-3 days**
- Testing: **1 day**
- Documentation: **1 day**

---

## 10. Auto-Retry with Fallbacks

### Overview
Automatic retry logic with model fallbacks for reliability.

### Priority
🔥 **HIGH** - Critical for production reliability

### Implementation
```python
class RetryManager:
    def __init__(self, max_retries=3, fallback_models=None):
        self.max_retries = max_retries
        self.fallback_models = fallback_models or ['llama2', 'llama3', 'mistral']
    
    def generate_with_retry(self, model, prompt, **kwargs):
        """Generate with automatic retry and fallback"""
        errors = []
        models_to_try = [model] + [
            m for m in self.fallback_models if m != model
        ]
        
        for attempt_model in models_to_try:
            for attempt in range(self.max_retries):
                try:
                    response = ollama.generate(
                        model=attempt_model,
                        prompt=prompt,
                        **kwargs
                    )
                    
                    # Success
                    return {
                        **response,
                        'model_used': attempt_model,
                        'attempts': attempt + 1,
                        'fallback_used': attempt_model != model
                    }
                    
                except Exception as e:
                    error_info = {
                        'model': attempt_model,
                        'attempt': attempt + 1,
                        'error': str(e)
                    }
                    errors.append(error_info)
                    
                    # Wait before retry (exponential backoff)
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                    
                    continue
        
        # All attempts failed
        raise Exception(f"All retry attempts failed: {errors}")
    
    def chat_with_retry(self, model, messages, **kwargs):
        """Chat with automatic retry and fallback"""
        errors = []
        models_to_try = [model] + [
            m for m in self.fallback_models if m != model
        ]
        
        for attempt_model in models_to_try:
            for attempt in range(self.max_retries):
                try:
                    response = ollama.chat(
                        model=attempt_model,
                        messages=messages,
                        **kwargs
                    )
                    
                    return {
                        **response,
                        'model_used': attempt_model,
                        'attempts': attempt + 1,
                        'fallback_used': attempt_model != model
                    }
                    
                except Exception as e:
                    errors.append({
                        'model': attempt_model,
                        'attempt': attempt + 1,
                        'error': str(e)
                    })
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                    
                    continue
        
        raise Exception(f"All retry attempts failed: {errors}")
```

### Configuration
```python
RETRY_CONFIG = {
    'enabled': True,
    'max_retries': 3,
    'fallback_models': ['llama2', 'llama3', 'mistral'],
    'exponential_backoff': True,
    'initial_delay': 1,  # seconds
    'max_delay': 60,
    'retry_on_errors': [
        'connection_error',
        'timeout',
        'model_not_loaded',
        'out_of_memory'
    ]
}
```

### API Integration
```python
@app.route('/api/ollama/generate', methods=['POST'])
@require_auth
def ollama_generate():
    data = request.get_json()
    use_retry = data.get('use_retry', True)
    
    if use_retry:
        retry_manager = RetryManager()
        response = retry_manager.generate_with_retry(
            model=data.get('model', 'llama2'),
            prompt=data.get('prompt'),
            system=data.get('system'),
            temperature=data.get('temperature', 0.7)
        )
    else:
        response = ollama.generate(...)
    
    return jsonify(response), 200
```

### Monitoring
```python
class RetryMonitor:
    def log_retry_event(self, request_id, model, attempt, 
                       success, error=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO retry_logs
                (request_id, model, attempt, success, error)
                VALUES (?, ?, ?, ?, ?)
            ''', (request_id, model, attempt, success, str(error)))
            conn.commit()
    
    def get_failure_rate(self, hours=24):
        """Calculate failure rate"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures
                FROM retry_logs
                WHERE created_at >= datetime('now', '-' || ? || ' hours')
            ''', (hours,))
            
            result = cursor.fetchone()
            if result['total'] > 0:
                return result['failures'] / result['total']
            return 0
```

### Estimated Effort
- Development: **2-3 days**
- Testing: **1-2 days**
- Documentation: **1 day**

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)
**Priority:** 🔥 HIGH
- [x] Auto-Retry with Fallbacks (Week 1) - **COMPLETED**
- [x] Response Caching (Week 2) - **COMPLETED**
- [x] RAG Implementation (Week 3) - **COMPLETED**

**Phase 1 Status:** ✅ **COMPLETED** on October 29, 2025
- All 39 Phase 1 tests passing
- 13 LLM Cache tests
- 12 Retry Manager tests
- 14 RAG Manager tests

### Phase 2: Analytics (Weeks 4-5)
**Priority:** 🟡 MEDIUM
- [x] Model Performance Metrics (Week 4) - **COMPLETED**
- [x] Cost Tracking (Week 5) - **COMPLETED**

**Phase 2 Status:** ✅ **COMPLETED** on October 29, 2025
- All 25 Phase 2 tests passing
- 13 MetricsCollector tests
- 12 CostCalculator tests
- Integrated into all Ollama endpoints
- Full API endpoints for metrics and cost tracking

### Phase 3: User Features (Weeks 6-7)
**Priority:** 🟡 MEDIUM
- [x] Conversation Persistence (Week 6) - **COMPLETED**
- [x] Prompt Templates Library (Week 7) - **COMPLETED**

**Phase 3 Status:** ✅ **COMPLETED** on October 29, 2025
- All Phase 3 tests passing
- ConversationManager fully implemented
- PromptTemplateManager with 10+ built-in templates
- Full API endpoints for conversations and templates
- Custom template creation and management

### Phase 4: Advanced (Weeks 8-10)
**Priority:** 🔵 LOW
- [x] Multi-Model Comparison (Week 8) - **COMPLETED**
- [ ] A/B Testing Framework (Week 9) - **DEFERRED**
- [ ] Fine-Tuning Support (Week 10) - **DEFERRED**

**Phase 4 Status:** ✅ **COMPLETED (Partial)** on October 29, 2025
- Multi-Model Comparison fully implemented
- All 25 Phase 4 tests passing
- 7 new API endpoints for model comparison
- Full documentation and usage guides
- Model ranking and rating system
- Performance analytics and statistics
- A/B Testing and Fine-Tuning deferred to future releases

---

## Resource Requirements

### Team
- 1-2 Backend Developers
- 1 QA Engineer
- 1 Technical Writer

### Infrastructure
- Development environment
- Test database
- CI/CD pipeline
- Documentation platform

### Third-Party Dependencies
- numpy
- scikit-learn
- Additional Python packages as needed

---

## Success Metrics

### Phase 1
- Cache hit rate > 30%
- Retry success rate > 95%
- RAG retrieval accuracy > 80%

### Phase 2
- Metrics dashboard live
- Cost tracking per user
- Performance baseline established

### Phase 3
- 50+ prompt templates
- Conversation retention rate > 70%

### Phase 4
- A/B tests running
- Fine-tuning pipeline operational
- Multi-model comparison used

---

## Risk Assessment

### Technical Risks
- **Vector search performance** - May need specialized database (Pinecone, Weaviate)
- **Embedding storage** - Large storage requirements for RAG
- **Fine-tuning complexity** - Requires significant compute resources

### Mitigation Strategies
- Start with simple implementations
- Iterative development with user feedback
- Performance testing at each phase
- Scalability planning from start

---

## Conclusion

This enhancement roadmap provides a clear path to significantly expand GemmaPy's Ollama integration capabilities. Prioritizing high-impact features like caching, retry logic, and RAG will provide immediate value, while advanced features can be implemented as the platform matures.

**Estimated Total Timeline:** 10-12 weeks  
**Estimated Total Effort:** 250-300 developer hours

---

**Document Version:** 1.0  
**Last Updated:** October 29, 2025  
**Next Review:** December 2025
