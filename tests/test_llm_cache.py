import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from llm_cache import LLMCache
from database import get_database_path
import sqlite3
from datetime import datetime, timedelta

@pytest.fixture
def cache():
    """Create a fresh cache instance for testing"""
    import tempfile
    # Create a temporary database file for each test
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    os.environ['DATABASE_PATH'] = temp_db.name
    
    cache = LLMCache(default_ttl=3600)
    yield cache
    
    # Cleanup
    try:
        os.unlink(temp_db.name)
    except:
        pass

def test_cache_initialization(cache):
    """Test cache table creation"""
    assert cache is not None
    assert cache.default_ttl == 3600

def test_generate_cache_key(cache):
    """Test cache key generation"""
    key1 = cache.generate_cache_key('llama2', 'Hello world', None, 0.7, None)
    key2 = cache.generate_cache_key('llama2', 'Hello world', None, 0.7, None)
    key3 = cache.generate_cache_key('llama2', 'Different prompt', None, 0.7, None)
    
    # Same inputs should generate same key
    assert key1 == key2
    # Different inputs should generate different keys
    assert key1 != key3
    # Keys should be SHA256 hashes (64 chars)
    assert len(key1) == 64

def test_cache_set_and_get(cache):
    """Test setting and retrieving cached values"""
    cache_key = cache.generate_cache_key('llama2', 'Test prompt', None, 0.7, None)
    test_response = 'This is a test response'
    
    # Set cache
    cache.set(cache_key, 'llama2', 'Test prompt', test_response)
    
    # Get cache
    retrieved = cache.get(cache_key)
    assert retrieved == test_response

def test_cache_miss(cache):
    """Test cache miss returns None"""
    cache_key = 'nonexistent_key_12345'
    retrieved = cache.get(cache_key)
    assert retrieved is None

def test_cache_expiration(cache):
    """Test cache expiration"""
    cache_short_ttl = LLMCache(default_ttl=1)  # 1 second TTL
    cache_key = cache_short_ttl.generate_cache_key('llama2', 'Test', None, 0.7, None)
    
    cache_short_ttl.set(cache_key, 'llama2', 'Test', 'Response', ttl=1)
    
    # Should be available immediately
    assert cache_short_ttl.get(cache_key) == 'Response'
    
    # Wait for expiration
    import time
    time.sleep(2)
    
    # Should be expired
    assert cache_short_ttl.get(cache_key) is None

def test_cache_hit_count(cache):
    """Test hit count tracking"""
    cache_key = cache.generate_cache_key('llama2', 'Hit test', None, 0.7, None)
    cache.set(cache_key, 'llama2', 'Hit test', 'Response')
    
    # Access multiple times
    cache.get(cache_key)
    cache.get(cache_key)
    cache.get(cache_key)
    
    # Check hit count in database
    from database import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT hit_count FROM llm_cache WHERE cache_key = ?', (cache_key,))
        result = cursor.fetchone()
        assert result['hit_count'] == 3

def test_cache_clear_expired(cache):
    """Test clearing expired entries"""
    # Add expired entry
    cache_key1 = cache.generate_cache_key('llama2', 'Expired', None, 0.7, None)
    cache.set(cache_key1, 'llama2', 'Expired', 'Response', ttl=1)
    
    # Add valid entry
    cache_key2 = cache.generate_cache_key('llama2', 'Valid', None, 0.7, None)
    cache.set(cache_key2, 'llama2', 'Valid', 'Response', ttl=3600)
    
    import time
    time.sleep(2)
    
    deleted = cache.clear_expired()
    assert deleted == 1
    
    # Valid entry should still exist
    assert cache.get(cache_key2) == 'Response'

def test_cache_invalidate_all(cache):
    """Test invalidating all cache"""
    cache.set(cache.generate_cache_key('llama2', 'Test1', None, 0.7, None),
              'llama2', 'Test1', 'Response1')
    cache.set(cache.generate_cache_key('llama2', 'Test2', None, 0.7, None),
              'llama2', 'Test2', 'Response2')
    
    deleted = cache.invalidate()
    assert deleted == 2

def test_cache_invalidate_pattern(cache):
    """Test pattern-based cache invalidation"""
    cache.set(cache.generate_cache_key('llama2', 'Python code', None, 0.7, None),
              'llama2', 'Python code', 'Response1')
    cache.set(cache.generate_cache_key('llama2', 'JavaScript code', None, 0.7, None),
              'llama2', 'JavaScript code', 'Response2')
    cache.set(cache.generate_cache_key('llama2', 'General question', None, 0.7, None),
              'llama2', 'General question', 'Response3')
    
    deleted = cache.invalidate('code')
    assert deleted == 2

def test_cache_stats(cache):
    """Test cache statistics"""
    cache.set(cache.generate_cache_key('llama2', 'Test1', None, 0.7, None),
              'llama2', 'Test1', 'Response1')
    cache.set(cache.generate_cache_key('llama2', 'Test2', None, 0.7, None),
              'llama2', 'Test2', 'Response2')
    
    # Access first entry
    key1 = cache.generate_cache_key('llama2', 'Test1', None, 0.7, None)
    cache.get(key1)
    cache.get(key1)
    
    stats = cache.get_stats()
    assert stats['total_entries'] == 2
    assert stats['total_hits'] == 2

def test_cache_temperature_sensitivity(cache):
    """Test that different temperatures create different cache keys"""
    key1 = cache.generate_cache_key('llama2', 'Test', None, 0.7, None)
    key2 = cache.generate_cache_key('llama2', 'Test', None, 0.8, None)
    
    assert key1 != key2

def test_cache_model_sensitivity(cache):
    """Test that different models create different cache keys"""
    key1 = cache.generate_cache_key('llama2', 'Test', None, 0.7, None)
    key2 = cache.generate_cache_key('llama3', 'Test', None, 0.7, None)
    
    assert key1 != key2

def test_cache_system_prompt_sensitivity(cache):
    """Test that system prompts affect cache keys"""
    key1 = cache.generate_cache_key('llama2', 'Test', 'You are helpful', 0.7, None)
    key2 = cache.generate_cache_key('llama2', 'Test', 'You are concise', 0.7, None)
    key3 = cache.generate_cache_key('llama2', 'Test', None, 0.7, None)
    
    assert key1 != key2
    assert key1 != key3
    assert key2 != key3
