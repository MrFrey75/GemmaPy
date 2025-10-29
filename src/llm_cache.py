import hashlib
import json
from datetime import datetime, timedelta
from database import get_db_connection

class LLMCache:
    def __init__(self, default_ttl=3600):
        self.default_ttl = default_ttl
        self._ensure_table()
    
    def _ensure_table(self):
        """Create cache table if it doesn't exist"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS llm_cache (
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
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_cache_key 
                ON llm_cache(cache_key)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_expires 
                ON llm_cache(expires_at)
            ''')
            conn.commit()
    
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
            ''', (cache_key, datetime.now().isoformat()))
            
            result = cursor.fetchone()
            if result:
                cursor.execute('''
                    UPDATE llm_cache 
                    SET hit_count = hit_count + 1,
                        last_accessed = ?
                    WHERE cache_key = ?
                ''', (datetime.now().isoformat(), cache_key))
                conn.commit()
                return result['response']
        return None
    
    def set(self, cache_key, model, prompt, response, system=None,
            temperature=0.7, max_tokens=None, ttl=None):
        """Store response in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO llm_cache 
                (cache_key, model, prompt, system_prompt, response, 
                 temperature, max_tokens, expires_at, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cache_key, model, prompt, system, response, 
                  temperature, max_tokens, expires_at, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
    
    def clear_expired(self):
        """Remove expired cache entries"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM llm_cache 
                WHERE expires_at IS NOT NULL 
                  AND expires_at < ?
            ''', (datetime.now().isoformat(),))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
    
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
            deleted = cursor.rowcount
            conn.commit()
            return deleted
    
    def get_stats(self):
        """Get cache statistics"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(hit_count) as total_hits,
                    AVG(hit_count) as avg_hits,
                    COUNT(CASE WHEN expires_at < ? THEN 1 END) as expired_entries
                FROM llm_cache
            ''', (datetime.now().isoformat(),))
            return dict(cursor.fetchone())
