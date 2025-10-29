import requests
import json
from typing import Optional, Dict, List, Generator

class OllamaManager:
    """
    Manager class for interacting with locally running Ollama instance.
    Provides methods to generate text, manage models, and stream responses.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama manager.
        
        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def is_running(self) -> bool:
        """
        Check if Ollama service is running.
        
        Returns:
            bool: True if Ollama is running, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def list_models(self) -> List[Dict]:
        """
        List all available models.
        
        Returns:
            List of model dictionaries with name, size, and modified date
        """
        try:
            response = requests.get(f"{self.api_url}/tags")
            response.raise_for_status()
            data = response.json()
            return data.get('models', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list models: {str(e)}")
    
    def pull_model(self, model_name: str) -> Dict:
        """
        Pull/download a model from Ollama library.
        
        Args:
            model_name: Name of the model to pull (e.g., 'llama2', 'llama2:13b')
        
        Returns:
            Dict with status information
        """
        try:
            response = requests.post(
                f"{self.api_url}/pull",
                json={"name": model_name},
                stream=True
            )
            response.raise_for_status()
            
            # Get final status
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if data.get('status') == 'success':
                        return {"status": "success", "message": f"Model {model_name} pulled successfully"}
            
            return {"status": "success", "message": f"Model {model_name} pulled"}
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to pull model: {str(e)}")
    
    def delete_model(self, model_name: str) -> Dict:
        """
        Delete a model from local storage.
        
        Args:
            model_name: Name of the model to delete
        
        Returns:
            Dict with status information
        """
        try:
            response = requests.delete(
                f"{self.api_url}/delete",
                json={"name": model_name}
            )
            response.raise_for_status()
            return {"status": "success", "message": f"Model {model_name} deleted"}
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to delete model: {str(e)}")
    
    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict:
        """
        Generate text completion from a prompt.
        
        Args:
            model: Model name (e.g., 'llama2')
            prompt: The prompt text
            system: Optional system message
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
        
        Returns:
            Dict with generated text and metadata
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate: {str(e)}")
    
    def generate_stream(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Generate text completion with streaming.
        
        Args:
            model: Model name
            prompt: The prompt text
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Yields:
            Generated text chunks
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        yield data['response']
                    
                    if data.get('done', False):
                        break
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate stream: {str(e)}")
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict:
        """
        Chat completion with conversation history.
        
        Args:
            model: Model name
            messages: List of message dicts with 'role' and 'content'
                     e.g., [{"role": "user", "content": "Hello"}]
            temperature: Sampling temperature
            stream: Whether to stream the response
        
        Returns:
            Dict with generated response and metadata
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/chat",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to chat: {str(e)}")
    
    def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        Chat completion with streaming.
        
        Args:
            model: Model name
            messages: List of message dicts
            temperature: Sampling temperature
        
        Yields:
            Generated text chunks
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/chat",
                json=payload,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'message' in data and 'content' in data['message']:
                        yield data['message']['content']
                    
                    if data.get('done', False):
                        break
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to chat stream: {str(e)}")
    
    def embeddings(self, model: str, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            model: Model name
            text: Text to generate embeddings for
        
        Returns:
            List of embedding values
        """
        payload = {
            "model": model,
            "prompt": text
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/embeddings",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get('embedding', [])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate embeddings: {str(e)}")
    
    def show_model_info(self, model_name: str) -> Dict:
        """
        Get detailed information about a model.
        
        Args:
            model_name: Name of the model
        
        Returns:
            Dict with model information
        """
        try:
            response = requests.post(
                f"{self.api_url}/show",
                json={"name": model_name}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get model info: {str(e)}")
    
    def copy_model(self, source: str, destination: str) -> Dict:
        """
        Copy a model to a new name.
        
        Args:
            source: Source model name
            destination: Destination model name
        
        Returns:
            Dict with status information
        """
        try:
            response = requests.post(
                f"{self.api_url}/copy",
                json={"source": source, "destination": destination}
            )
            response.raise_for_status()
            return {"status": "success", "message": f"Model copied from {source} to {destination}"}
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to copy model: {str(e)}")


# Convenience functions for direct usage
def generate_text(prompt: str, model: str = "llama2", system: Optional[str] = None) -> str:
    """
    Quick text generation function.
    
    Args:
        prompt: The prompt text
        model: Model to use (default: llama2)
        system: Optional system message
    
    Returns:
        Generated text
    """
    manager = OllamaManager()
    response = manager.generate(model, prompt, system=system)
    return response.get('response', '')


def chat_with_llama(messages: List[Dict[str, str]], model: str = "llama2") -> str:
    """
    Quick chat function.
    
    Args:
        messages: List of message dicts
        model: Model to use (default: llama2)
    
    Returns:
        Generated response
    """
    manager = OllamaManager()
    response = manager.chat(model, messages)
    return response.get('message', {}).get('content', '')
