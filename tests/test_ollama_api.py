import pytest
from unittest.mock import patch, Mock

def test_ollama_status_requires_auth(client):
    """Test that Ollama status requires authentication"""
    response = client.get('/api/ollama/status')
    assert response.status_code == 401

@patch('app.ollama.is_running')
def test_ollama_status_running(mock_is_running, client, auth_token):
    """Test Ollama status when running"""
    mock_is_running.return_value = True
    
    response = client.get('/api/ollama/status', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['running'] == True

@patch('app.ollama.list_models')
def test_ollama_list_models(mock_list_models, client, auth_token):
    """Test listing Ollama models"""
    mock_list_models.return_value = [
        {'name': 'llama2', 'size': 1000000},
        {'name': 'llama3', 'size': 2000000}
    ]
    
    response = client.get('/api/ollama/models', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 2
    assert len(data['models']) == 2

@patch('app.ollama.show_model_info')
def test_ollama_model_info(mock_show_info, client, auth_token):
    """Test getting model info"""
    mock_show_info.return_value = {
        'modelfile': 'FROM llama2',
        'parameters': 'temperature 0.7'
    }
    
    response = client.get('/api/ollama/models/llama2', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'modelfile' in data

@patch('app.retry_manager.generate_with_retry')
def test_ollama_generate(mock_generate, client, auth_token):
    """Test text generation"""
    mock_generate.return_value = {
        'response': 'Generated text from llama2',
        'model': 'llama2',
        'attempts': 1,
        'fallback_used': False
    }
    
    response = client.post('/api/ollama/generate',
        json={
            'prompt': 'Hello, how are you?',
            'model': 'llama2',
            'use_cache': False  # Disable cache for testing
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['response'] == 'Generated text from llama2'

def test_ollama_generate_missing_prompt(client, auth_token):
    """Test generation without prompt"""
    response = client.post('/api/ollama/generate',
        json={'model': 'llama2'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'Prompt is required' in data['error']

@patch('app.retry_manager.generate_with_retry')
def test_ollama_generate_with_options(mock_generate, client, auth_token):
    """Test generation with custom options"""
    mock_generate.return_value = {
        'response': 'Test',
        'attempts': 1,
        'fallback_used': False
    }
    
    response = client.post('/api/ollama/generate',
        json={
            'prompt': 'Test',
            'model': 'llama2',
            'system': 'You are helpful',
            'temperature': 0.5,
            'max_tokens': 100,
            'use_cache': False  # Disable cache for testing
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    mock_generate.assert_called_once()
    # Check that the retry manager was called with correct arguments
    call_args = mock_generate.call_args
    assert call_args is not None

@patch('app.ollama.chat')
def test_ollama_chat(mock_chat, client, auth_token):
    """Test chat completion"""
    mock_chat.return_value = {
        'message': {
            'role': 'assistant',
            'content': 'Hello! How can I help you?'
        }
    }
    
    response = client.post('/api/ollama/chat',
        json={
            'messages': [
                {'role': 'user', 'content': 'Hello'}
            ],
            'model': 'llama2'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['message']['content'] == 'Hello! How can I help you?'

def test_ollama_chat_missing_messages(client, auth_token):
    """Test chat without messages"""
    response = client.post('/api/ollama/chat',
        json={'model': 'llama2'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'Messages array is required' in data['error']

def test_ollama_chat_invalid_messages(client, auth_token):
    """Test chat with invalid messages format"""
    response = client.post('/api/ollama/chat',
        json={
            'messages': 'invalid',
            'model': 'llama2'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 400

@patch('app.ollama.embeddings')
def test_ollama_embeddings(mock_embeddings, client, auth_token):
    """Test embeddings generation"""
    mock_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    response = client.post('/api/ollama/embeddings',
        json={
            'text': 'Test text for embeddings',
            'model': 'llama2'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['embeddings']) == 5
    assert data['dimensions'] == 5

def test_ollama_embeddings_missing_text(client, auth_token):
    """Test embeddings without text"""
    response = client.post('/api/ollama/embeddings',
        json={'model': 'llama2'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 400

@patch('app.ollama.pull_model')
def test_ollama_pull_model(mock_pull, client, auth_token):
    """Test pulling a model"""
    mock_pull.return_value = {
        'status': 'success',
        'message': 'Model pulled successfully'
    }
    
    response = client.post('/api/ollama/models/pull',
        json={'model': 'llama2:13b'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'

def test_ollama_pull_model_missing_name(client, auth_token):
    """Test pulling without model name"""
    response = client.post('/api/ollama/models/pull',
        json={},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 400

@patch('app.ollama.delete_model')
def test_ollama_delete_model_admin(mock_delete, client, admin_token):
    """Test deleting a model as admin"""
    mock_delete.return_value = {
        'status': 'success',
        'message': 'Model deleted'
    }
    
    response = client.delete('/api/ollama/models/test-model',
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200

def test_ollama_delete_model_requires_admin(client, auth_token):
    """Test that deleting models requires admin"""
    response = client.delete('/api/ollama/models/test-model',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 403

@patch('app.retry_manager.generate_with_retry')
def test_ollama_generate_stores_in_database(mock_generate, client, auth_token):
    """Test that generations are stored in database"""
    mock_generate.return_value = {
        'response': 'Test response',
        'attempts': 1,
        'fallback_used': False
    }
    
    response = client.post('/api/ollama/generate',
        json={'prompt': 'Test prompt', 'model': 'llama2', 'use_cache': False},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    
    # Check data was stored
    from database import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM data WHERE user_id = 2 ORDER BY id DESC LIMIT 1')
        data_entry = cursor.fetchone()
        assert data_entry is not None
        assert 'Ollama:' in data_entry['content']

@patch('app.ollama.chat')
def test_ollama_chat_stores_in_database(mock_chat, client, auth_token):
    """Test that chats are stored in database"""
    mock_chat.return_value = {
        'message': {'content': 'Response'}
    }
    
    response = client.post('/api/ollama/chat',
        json={
            'messages': [{'role': 'user', 'content': 'Hello'}],
            'model': 'llama2'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 200
    
    # Check data was stored
    from database import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM data WHERE user_id = 2 ORDER BY id DESC LIMIT 1')
        data_entry = cursor.fetchone()
        assert data_entry is not None
        assert 'Chat:' in data_entry['content']

@patch('app.ollama.generate')
def test_ollama_generate_error_handling(mock_generate, client, auth_token):
    """Test error handling in generation"""
    mock_generate.side_effect = Exception("Model not found")
    
    response = client.post('/api/ollama/generate',
        json={'prompt': 'Test', 'model': 'invalid'},
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 500
    data = response.get_json()
    assert 'error' in data

@patch('app.ollama.list_models')
def test_ollama_list_models_error(mock_list, client, auth_token):
    """Test error handling in list models"""
    mock_list.side_effect = Exception("API error")
    
    response = client.get('/api/ollama/models',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    assert response.status_code == 500
