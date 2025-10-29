import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from retry_manager import RetryManager
from database import get_database_path

class MockOllamaManager:
    """Mock Ollama manager for testing"""
    def __init__(self, fail_count=0):
        self.fail_count = fail_count
        self.call_count = 0
    
    def generate(self, model, prompt, **kwargs):
        self.call_count += 1
        if self.call_count <= self.fail_count:
            raise Exception(f"Mock failure {self.call_count}")
        return {
            'response': f'Generated response for: {prompt}',
            'model': model
        }
    
    def chat(self, model, messages, **kwargs):
        self.call_count += 1
        if self.call_count <= self.fail_count:
            raise Exception(f"Mock failure {self.call_count}")
        return {
            'message': {'content': f'Chat response'},
            'model': model
        }

@pytest.fixture
def retry_manager():
    """Create retry manager with temporary database"""
    import tempfile
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    os.environ['DATABASE_PATH'] = temp_db.name
    
    manager = RetryManager(max_retries=3, fallback_models=['llama2', 'mistral'])
    yield manager
    
    # Cleanup
    try:
        os.unlink(temp_db.name)
    except:
        pass

def test_retry_manager_initialization(retry_manager):
    """Test retry manager initialization"""
    assert retry_manager.max_retries == 3
    assert 'llama2' in retry_manager.fallback_models
    assert 'mistral' in retry_manager.fallback_models

def test_successful_first_attempt(retry_manager):
    """Test successful generation on first attempt"""
    mock_ollama = MockOllamaManager(fail_count=0)
    
    response = retry_manager.generate_with_retry(
        mock_ollama, 'llama2', 'Test prompt'
    )
    
    assert response['response'] == 'Generated response for: Test prompt'
    assert response['model_used'] == 'llama2'
    assert response['attempts'] == 1
    assert response['fallback_used'] == False
    assert mock_ollama.call_count == 1

def test_retry_after_failure(retry_manager):
    """Test retry after initial failure"""
    mock_ollama = MockOllamaManager(fail_count=1)
    
    response = retry_manager.generate_with_retry(
        mock_ollama, 'llama2', 'Test prompt'
    )
    
    assert response['response'] == 'Generated response for: Test prompt'
    assert response['attempts'] == 2
    assert mock_ollama.call_count == 2

def test_fallback_to_different_model(retry_manager):
    """Test fallback to different model after max retries"""
    mock_ollama = MockOllamaManager(fail_count=3)
    
    response = retry_manager.generate_with_retry(
        mock_ollama, 'llama2', 'Test prompt'
    )
    
    assert response['model_used'] == 'mistral'
    assert response['fallback_used'] == True
    assert mock_ollama.call_count == 4

def test_all_attempts_fail(retry_manager):
    """Test when all retry attempts fail"""
    mock_ollama = MockOllamaManager(fail_count=10)
    
    with pytest.raises(Exception) as exc_info:
        retry_manager.generate_with_retry(
            mock_ollama, 'llama2', 'Test prompt'
        )
    
    assert 'All retry attempts failed' in str(exc_info.value)

def test_chat_with_retry(retry_manager):
    """Test chat with retry functionality"""
    mock_ollama = MockOllamaManager(fail_count=1)
    
    messages = [{'role': 'user', 'content': 'Hello'}]
    response = retry_manager.chat_with_retry(
        mock_ollama, 'llama2', messages
    )
    
    assert response['message']['content'] == 'Chat response'
    assert response['attempts'] == 2

def test_retry_logging(retry_manager):
    """Test that retry attempts are logged"""
    mock_ollama = MockOllamaManager(fail_count=2)
    
    response = retry_manager.generate_with_retry(
        mock_ollama, 'llama2', 'Test prompt'
    )
    
    request_id = response['request_id']
    
    # Check logs in database
    from database import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) as count FROM retry_logs WHERE request_id = ?',
            (request_id,)
        )
        result = cursor.fetchone()
        assert result['count'] == 3  # 2 failures + 1 success

def test_failure_rate_calculation(retry_manager):
    """Test failure rate calculation"""
    mock_ollama = MockOllamaManager(fail_count=0)
    
    # Successful attempts
    retry_manager.generate_with_retry(mock_ollama, 'llama2', 'Test 1')
    
    mock_ollama2 = MockOllamaManager(fail_count=1)
    retry_manager.generate_with_retry(mock_ollama2, 'llama2', 'Test 2')
    
    stats = retry_manager.get_stats()
    assert stats['total_requests'] == 2
    assert stats['successful_attempts'] == 2
    assert stats['failed_attempts'] == 1

def test_exponential_backoff():
    """Test exponential backoff timing (mock time.sleep)"""
    import time
    import unittest.mock
    
    retry_manager = RetryManager(max_retries=3)
    mock_ollama = MockOllamaManager(fail_count=2)
    
    with unittest.mock.patch('time.sleep') as mock_sleep:
        retry_manager.generate_with_retry(mock_ollama, 'llama2', 'Test')
        
        # Check sleep was called with exponential backoff
        assert mock_sleep.call_count == 2
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert calls[0] == 1  # 2^0
        assert calls[1] == 2  # 2^1

def test_retry_stats(retry_manager):
    """Test retry statistics"""
    mock_ollama1 = MockOllamaManager(fail_count=0)
    mock_ollama2 = MockOllamaManager(fail_count=1)
    
    retry_manager.generate_with_retry(mock_ollama1, 'llama2', 'Test 1')
    retry_manager.generate_with_retry(mock_ollama2, 'llama2', 'Test 2')
    
    stats = retry_manager.get_stats()
    assert stats['total_requests'] == 2
    assert stats['retry_count'] >= 1  # At least one retry occurred

def test_request_id_uniqueness(retry_manager):
    """Test that each request gets a unique ID"""
    mock_ollama = MockOllamaManager(fail_count=0)
    
    response1 = retry_manager.generate_with_retry(mock_ollama, 'llama2', 'Test 1')
    response2 = retry_manager.generate_with_retry(mock_ollama, 'llama2', 'Test 2')
    
    assert response1['request_id'] != response2['request_id']

def test_custom_fallback_models():
    """Test custom fallback model configuration"""
    custom_retry = RetryManager(
        max_retries=2,
        fallback_models=['custom1', 'custom2']
    )
    assert custom_retry.fallback_models == ['custom1', 'custom2']
