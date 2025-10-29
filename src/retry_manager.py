import time
import uuid
from datetime import datetime
from database import get_db_connection

class RetryManager:
    def __init__(self, max_retries=3, fallback_models=None):
        self.max_retries = max_retries
        self.fallback_models = fallback_models or ['llama2', 'mistral', 'llama3']
        self._ensure_table()
    
    def _ensure_table(self):
        """Create retry logs table if it doesn't exist"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retry_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    attempt INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    error TEXT,
                    duration_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_retry_request 
                ON retry_logs(request_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_retry_created 
                ON retry_logs(created_at)
            ''')
            conn.commit()
    
    def generate_with_retry(self, ollama_manager, model, prompt, **kwargs):
        """Generate with automatic retry and fallback"""
        request_id = str(uuid.uuid4())
        errors = []
        models_to_try = [model] + [
            m for m in self.fallback_models if m != model
        ]
        
        for attempt_model in models_to_try:
            for attempt in range(self.max_retries):
                start_time = time.time()
                try:
                    response = ollama_manager.generate(
                        model=attempt_model,
                        prompt=prompt,
                        **kwargs
                    )
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    self._log_retry_event(
                        request_id, attempt_model, attempt + 1,
                        True, None, duration_ms
                    )
                    
                    return {
                        **response,
                        'model_used': attempt_model,
                        'attempts': attempt + 1,
                        'fallback_used': attempt_model != model,
                        'request_id': request_id
                    }
                    
                except Exception as e:
                    duration_ms = int((time.time() - start_time) * 1000)
                    error_info = {
                        'model': attempt_model,
                        'attempt': attempt + 1,
                        'error': str(e)
                    }
                    errors.append(error_info)
                    
                    self._log_retry_event(
                        request_id, attempt_model, attempt + 1,
                        False, str(e), duration_ms
                    )
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                    
                    continue
        
        raise Exception(f"All retry attempts failed: {errors}")
    
    def chat_with_retry(self, ollama_manager, model, messages, **kwargs):
        """Chat with automatic retry and fallback"""
        request_id = str(uuid.uuid4())
        errors = []
        models_to_try = [model] + [
            m for m in self.fallback_models if m != model
        ]
        
        for attempt_model in models_to_try:
            for attempt in range(self.max_retries):
                start_time = time.time()
                try:
                    response = ollama_manager.chat(
                        model=attempt_model,
                        messages=messages,
                        **kwargs
                    )
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    self._log_retry_event(
                        request_id, attempt_model, attempt + 1,
                        True, None, duration_ms
                    )
                    
                    return {
                        **response,
                        'model_used': attempt_model,
                        'attempts': attempt + 1,
                        'fallback_used': attempt_model != model,
                        'request_id': request_id
                    }
                    
                except Exception as e:
                    duration_ms = int((time.time() - start_time) * 1000)
                    errors.append({
                        'model': attempt_model,
                        'attempt': attempt + 1,
                        'error': str(e)
                    })
                    
                    self._log_retry_event(
                        request_id, attempt_model, attempt + 1,
                        False, str(e), duration_ms
                    )
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                    
                    continue
        
        raise Exception(f"All retry attempts failed: {errors}")
    
    def _log_retry_event(self, request_id, model, attempt, 
                        success, error, duration_ms):
        """Log retry event"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO retry_logs
                (request_id, model, attempt, success, error, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (request_id, model, attempt, success, error, duration_ms))
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
    
    def get_stats(self):
        """Get retry statistics"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT request_id) as total_requests,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_attempts,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_attempts,
                    AVG(duration_ms) as avg_duration_ms,
                    COUNT(CASE WHEN attempt > 1 THEN 1 END) as retry_count
                FROM retry_logs
                WHERE created_at >= datetime('now', '-24 hours')
            ''')
            return dict(cursor.fetchone())
