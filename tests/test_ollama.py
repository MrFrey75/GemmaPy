import pytest
from unittest.mock import Mock, patch, MagicMock
from ollama_manager import OllamaManager, generate_text, chat_with_llama

@pytest.fixture
def ollama_manager():
    return OllamaManager()

@pytest.fixture
def mock_response():
    """Create a mock response object"""
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = {'response': 'Test response'}
    return mock

# OllamaManager Tests

def test_ollama_manager_initialization():
    """Test OllamaManager initialization"""
    manager = OllamaManager()
    assert manager.base_url == "http://localhost:11434"
    assert manager.api_url == "http://localhost:11434/api"
    
    custom_manager = OllamaManager("http://custom:8000")
    assert custom_manager.base_url == "http://custom:8000"

@patch('ollama_manager.requests.get')
def test_is_running_true(mock_get, ollama_manager):
    """Test checking if Ollama is running"""
    mock_get.return_value.status_code = 200
    assert ollama_manager.is_running() == True

@patch('ollama_manager.requests.get')
def test_is_running_false(mock_get, ollama_manager):
    """Test checking if Ollama is not running"""
    import requests
    mock_get.side_effect = requests.exceptions.RequestException("Connection refused")
    assert ollama_manager.is_running() == False

@patch('ollama_manager.requests.get')
def test_list_models(mock_get, ollama_manager):
    """Test listing models"""
    mock_get.return_value.json.return_value = {
        'models': [
            {'name': 'llama2', 'size': 1000000},
            {'name': 'llama3', 'size': 2000000}
        ]
    }
    mock_get.return_value.raise_for_status = Mock()
    
    models = ollama_manager.list_models()
    assert len(models) == 2
    assert models[0]['name'] == 'llama2'

@patch('ollama_manager.requests.post')
def test_generate(mock_post, ollama_manager):
    """Test text generation"""
    mock_post.return_value.json.return_value = {
        'response': 'Generated text',
        'model': 'llama2'
    }
    mock_post.return_value.raise_for_status = Mock()
    
    result = ollama_manager.generate(
        model='llama2',
        prompt='Test prompt'
    )
    
    assert result['response'] == 'Generated text'
    assert mock_post.called

@patch('ollama_manager.requests.post')
def test_generate_with_options(mock_post, ollama_manager):
    """Test generation with custom options"""
    mock_post.return_value.json.return_value = {'response': 'Test'}
    mock_post.return_value.raise_for_status = Mock()
    
    ollama_manager.generate(
        model='llama2',
        prompt='Test',
        system='You are helpful',
        temperature=0.5,
        max_tokens=100
    )
    
    call_args = mock_post.call_args[1]['json']
    assert call_args['system'] == 'You are helpful'
    assert call_args['options']['temperature'] == 0.5
    assert call_args['options']['num_predict'] == 100

@patch('ollama_manager.requests.post')
def test_chat(mock_post, ollama_manager):
    """Test chat completion"""
    mock_post.return_value.json.return_value = {
        'message': {'role': 'assistant', 'content': 'Hello!'}
    }
    mock_post.return_value.raise_for_status = Mock()
    
    messages = [
        {'role': 'user', 'content': 'Hello'}
    ]
    
    result = ollama_manager.chat(
        model='llama2',
        messages=messages
    )
    
    assert result['message']['content'] == 'Hello!'

@patch('ollama_manager.requests.post')
def test_embeddings(mock_post, ollama_manager):
    """Test embeddings generation"""
    mock_post.return_value.json.return_value = {
        'embedding': [0.1, 0.2, 0.3, 0.4, 0.5]
    }
    mock_post.return_value.raise_for_status = Mock()
    
    embeddings = ollama_manager.embeddings('llama2', 'Test text')
    
    assert len(embeddings) == 5
    assert embeddings[0] == 0.1

@patch('ollama_manager.requests.post')
def test_show_model_info(mock_post, ollama_manager):
    """Test getting model info"""
    mock_post.return_value.json.return_value = {
        'modelfile': 'FROM llama2',
        'parameters': 'temperature 0.7'
    }
    mock_post.return_value.raise_for_status = Mock()
    
    info = ollama_manager.show_model_info('llama2')
    
    assert 'modelfile' in info
    assert 'parameters' in info

@patch('ollama_manager.requests.delete')
def test_delete_model(mock_delete, ollama_manager):
    """Test model deletion"""
    mock_delete.return_value.raise_for_status = Mock()
    
    result = ollama_manager.delete_model('test-model')
    
    assert result['status'] == 'success'
    assert 'deleted' in result['message']

@patch('ollama_manager.requests.post')
def test_copy_model(mock_post, ollama_manager):
    """Test model copying"""
    mock_post.return_value.raise_for_status = Mock()
    
    result = ollama_manager.copy_model('llama2', 'llama2-custom')
    
    assert result['status'] == 'success'
    assert 'copied' in result['message']

# Convenience Functions Tests

@patch('ollama_manager.OllamaManager.generate')
def test_generate_text_function(mock_generate):
    """Test generate_text convenience function"""
    mock_generate.return_value = {'response': 'Generated'}
    
    result = generate_text('Test prompt')
    
    assert result == 'Generated'
    mock_generate.assert_called_once()

@patch('ollama_manager.OllamaManager.chat')
def test_chat_with_llama_function(mock_chat):
    """Test chat_with_llama convenience function"""
    mock_chat.return_value = {
        'message': {'content': 'Response'}
    }
    
    messages = [{'role': 'user', 'content': 'Hi'}]
    result = chat_with_llama(messages)
    
    assert result == 'Response'
    mock_chat.assert_called_once()

# Error Handling Tests

@patch('ollama_manager.requests.post')
def test_generate_error_handling(mock_post, ollama_manager):
    """Test error handling in generation"""
    import requests
    mock_post.side_effect = requests.exceptions.RequestException("Connection error")
    
    with pytest.raises(Exception) as exc_info:
        ollama_manager.generate('llama2', 'Test')
    
    assert 'Failed to generate' in str(exc_info.value)

@patch('ollama_manager.requests.get')
def test_list_models_error(mock_get, ollama_manager):
    """Test error handling in list models"""
    import requests
    mock_get.side_effect = requests.exceptions.RequestException("API error")
    
    with pytest.raises(Exception) as exc_info:
        ollama_manager.list_models()
    
    assert 'Failed to list models' in str(exc_info.value)

# Stream Tests (using mocks)

@patch('ollama_manager.requests.post')
def test_generate_stream(mock_post, ollama_manager):
    """Test streaming generation"""
    mock_response = Mock()
    mock_response.iter_lines.return_value = [
        b'{"response": "Hello", "done": false}',
        b'{"response": " world", "done": true}'
    ]
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    chunks = list(ollama_manager.generate_stream('llama2', 'Test'))
    
    assert len(chunks) == 2
    assert chunks[0] == 'Hello'
    assert chunks[1] == ' world'

@patch('ollama_manager.requests.post')
def test_chat_stream(mock_post, ollama_manager):
    """Test streaming chat"""
    mock_response = Mock()
    mock_response.iter_lines.return_value = [
        b'{"message": {"content": "Hi"}, "done": false}',
        b'{"message": {"content": " there"}, "done": true}'
    ]
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    messages = [{'role': 'user', 'content': 'Hello'}]
    chunks = list(ollama_manager.chat_stream('llama2', messages))
    
    assert len(chunks) == 2
    assert chunks[0] == 'Hi'
    assert chunks[1] == ' there'
