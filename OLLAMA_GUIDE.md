# Ollama Integration Guide

Complete guide for using Ollama and LLaMA 2 with GemmaPy.

## Overview

GemmaPy includes full integration with Ollama, allowing you to run large language models locally. The integration supports:
- Text generation with LLaMA 2 and other models
- Chat conversations with context
- Streaming responses
- Model management
- Text embeddings

## Prerequisites

### Install Ollama

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com

# Verify installation
ollama --version
```

### Pull LLaMA 2

```bash
# Pull LLaMA 2 (3.8GB)
ollama pull llama2

# Or specific version
ollama pull llama2:13b
ollama pull llama2:70b

# List available models
ollama list
```

## API Endpoints

### Check Ollama Status

**Endpoint:** `GET /api/ollama/status`

**Authentication:** Required

```bash
curl http://localhost:5000/api/ollama/status \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "running": true,
  "message": "Ollama is running"
}
```

---

### List Models

**Endpoint:** `GET /api/ollama/models`

**Authentication:** Required

```bash
curl http://localhost:5000/api/ollama/models \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "models": [
    {
      "name": "llama2:latest",
      "size": 3826793677,
      "modified_at": "2025-10-29T10:00:00Z"
    }
  ],
  "count": 1
}
```

---

### Get Model Info

**Endpoint:** `GET /api/ollama/models/<model_name>`

**Authentication:** Required

```bash
curl http://localhost:5000/api/ollama/models/llama2 \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "modelfile": "FROM llama2\nPARAMETER temperature 0.7",
  "parameters": "temperature 0.7\nnum_predict 128",
  "template": "...",
  "details": {...}
}
```

---

### Generate Text

**Endpoint:** `POST /api/ollama/generate`

**Authentication:** Required

**Request Body:**
```json
{
  "model": "llama2",
  "prompt": "Explain quantum computing in simple terms",
  "system": "You are a helpful assistant",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "model": "llama2",
  "created_at": "2025-10-29T15:00:00Z",
  "response": "Quantum computing is...",
  "done": true,
  "total_duration": 5000000000,
  "load_duration": 1000000000,
  "prompt_eval_count": 20,
  "eval_count": 150
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/ollama/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Write a Python function to calculate fibonacci numbers",
    "temperature": 0.5
  }'
```

---

### Generate Text (Streaming)

**Endpoint:** `POST /api/ollama/generate/stream`

**Authentication:** Required

**Response:** Server-Sent Events (SSE) stream

```bash
curl -X POST http://localhost:5000/api/ollama/generate/stream \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Tell me a story"
  }'
```

**Stream Format:**
```
data: {"chunk": "Once"}
data: {"chunk": " upon"}
data: {"chunk": " a"}
data: {"chunk": " time"}
...
data: {"done": true}
```

---

### Chat Completion

**Endpoint:** `POST /api/ollama/chat`

**Authentication:** Required

**Request Body:**
```json
{
  "model": "llama2",
  "messages": [
    {"role": "system", "content": "You are a helpful coding assistant"},
    {"role": "user", "content": "How do I reverse a list in Python?"},
    {"role": "assistant", "content": "You can use the reverse() method..."},
    {"role": "user", "content": "Can you show me an example?"}
  ],
  "temperature": 0.7
}
```

**Response:**
```json
{
  "model": "llama2",
  "created_at": "2025-10-29T15:00:00Z",
  "message": {
    "role": "assistant",
    "content": "Certainly! Here's an example:\n\nmy_list = [1, 2, 3, 4, 5]\nmy_list.reverse()\nprint(my_list)  # Output: [5, 4, 3, 2, 1]"
  },
  "done": true
}
```

---

### Chat Completion (Streaming)

**Endpoint:** `POST /api/ollama/chat/stream`

**Authentication:** Required

Streams chat responses in real-time using Server-Sent Events.

---

### Generate Embeddings

**Endpoint:** `POST /api/ollama/embeddings`

**Authentication:** Required

**Request Body:**
```json
{
  "model": "llama2",
  "text": "The quick brown fox jumps over the lazy dog"
}
```

**Response:**
```json
{
  "embeddings": [0.123, -0.456, 0.789, ...],
  "dimensions": 4096
}
```

---

### Pull Model

**Endpoint:** `POST /api/ollama/models/pull`

**Authentication:** Required

```bash
curl -X POST http://localhost:5000/api/ollama/models/pull \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama2:13b"}'
```

---

### Delete Model

**Endpoint:** `DELETE /api/ollama/models/<model_name>`

**Authentication:** Admin only

```bash
curl -X DELETE http://localhost:5000/api/ollama/models/llama2:13b \
  -H "Authorization: Bearer <admin-token>"
```

## Python Usage

### Using the OllamaManager Class

```python
from ollama_manager import OllamaManager

# Initialize
ollama = OllamaManager()

# Check if running
if ollama.is_running():
    print("Ollama is ready!")

# List models
models = ollama.list_models()
for model in models:
    print(f"Model: {model['name']}, Size: {model['size']}")

# Generate text
response = ollama.generate(
    model='llama2',
    prompt='Explain neural networks',
    temperature=0.7
)
print(response['response'])

# Chat
messages = [
    {'role': 'user', 'content': 'Hello!'}
]
response = ollama.chat('llama2', messages)
print(response['message']['content'])

# Streaming generation
for chunk in ollama.generate_stream('llama2', 'Tell me a joke'):
    print(chunk, end='', flush=True)
print()

# Generate embeddings
embeddings = ollama.embeddings('llama2', 'Sample text')
print(f"Generated {len(embeddings)} dimensional embeddings")
```

### Quick Functions

```python
from ollama_manager import generate_text, chat_with_llama

# Quick text generation
text = generate_text("What is machine learning?", model="llama2")
print(text)

# Quick chat
messages = [
    {'role': 'user', 'content': 'Hello'}
]
response = chat_with_llama(messages, model="llama2")
print(response)
```

## JavaScript Usage

### Generate Text

```javascript
const generateText = async (prompt) => {
  const response = await fetch('http://localhost:5000/api/ollama/generate', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'llama2',
      prompt: prompt,
      temperature: 0.7
    })
  });
  
  const data = await response.json();
  return data.response;
};

// Usage
const result = await generateText('Explain photosynthesis');
console.log(result);
```

### Streaming Generation

```javascript
const generateTextStream = async (prompt) => {
  const response = await fetch('http://localhost:5000/api/ollama/generate/stream', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'llama2',
      prompt: prompt
    })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.chunk) {
          process.stdout.write(data.chunk);
        }
        if (data.done) {
          console.log('\nDone!');
          return;
        }
      }
    }
  }
};
```

### Chat Completion

```javascript
const chat = async (messages) => {
  const response = await fetch('http://localhost:5000/api/ollama/chat', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'llama2',
      messages: messages,
      temperature: 0.7
    })
  });
  
  const data = await response.json();
  return data.message.content;
};

// Usage
const messages = [
  { role: 'user', content: 'What is React?' }
];
const response = await chat(messages);
console.log(response);
```

## Advanced Usage

### Multi-turn Conversation

```python
from ollama_manager import OllamaManager

ollama = OllamaManager()

# Maintain conversation history
conversation = [
    {'role': 'system', 'content': 'You are a helpful Python tutor'}
]

def chat_turn(user_message):
    conversation.append({'role': 'user', 'content': user_message})
    
    response = ollama.chat('llama2', conversation)
    assistant_message = response['message']['content']
    
    conversation.append({'role': 'assistant', 'content': assistant_message})
    return assistant_message

# Have a conversation
print(chat_turn("How do I create a list in Python?"))
print(chat_turn("Can you show me how to add items to it?"))
print(chat_turn("What about removing items?"))
```

### Batch Processing

```python
prompts = [
    "Summarize: Machine learning is...",
    "Translate to Spanish: Hello, how are you?",
    "Code review: def add(a,b): return a+b"
]

results = []
for prompt in prompts:
    response = ollama.generate('llama2', prompt)
    results.append(response['response'])

for i, result in enumerate(results):
    print(f"\nPrompt {i+1}:\n{result}")
```

### Custom System Prompts

```python
# Specific personality/role
response = ollama.generate(
    model='llama2',
    prompt='Explain recursion',
    system='You are a patient teacher explaining concepts to beginners using simple analogies'
)

# Code generation
response = ollama.generate(
    model='llama2',
    prompt='Create a REST API endpoint for user registration',
    system='You are an expert Python/Flask developer. Provide clean, well-commented code'
)

# Creative writing
response = ollama.generate(
    model='llama2',
    prompt='Start a science fiction story',
    system='You are a creative sci-fi author with a focus on hard science fiction'
)
```

## Available Models

### LLaMA 2 Variants

- `llama2` (7B) - Best balance of speed and quality
- `llama2:13b` - Better quality, slower
- `llama2:70b` - Highest quality, requires significant RAM

### Other Models

```bash
# Pull other popular models
ollama pull llama3
ollama pull mistral
ollama pull codellama
ollama pull phi3
ollama pull gemma
```

## Configuration

### Temperature Settings

- `0.0-0.3` - Focused, deterministic (code, facts)
- `0.4-0.7` - Balanced (general use)
- `0.8-1.0` - Creative, diverse (stories, brainstorming)

### Token Limits

```python
# Limit response length
response = ollama.generate(
    model='llama2',
    prompt='Write a short poem',
    max_tokens=50  # Maximum 50 tokens
)
```

## Performance Tips

### 1. Model Selection
- Use `llama2` (7B) for speed
- Use `llama2:13b` for better quality
- Use specialized models (codellama for code)

### 2. Prompt Engineering
```python
# Good: Specific and clear
prompt = "Write a Python function that takes a list of numbers and returns the sum. Include error handling."

# Better: With examples
prompt = """Write a Python function that sums numbers.

Example:
Input: [1, 2, 3]
Output: 6

Requirements:
- Handle empty lists
- Validate input types
- Include docstring
"""
```

### 3. Context Management
- Keep conversation history reasonable (<10-15 messages)
- Summarize long conversations
- Clear context when topic changes

### 4. Caching
```python
# Cache frequent prompts
cache = {}

def generate_cached(prompt):
    if prompt in cache:
        return cache[prompt]
    
    response = ollama.generate('llama2', prompt)
    cache[prompt] = response['response']
    return response['response']
```

## Troubleshooting

### Ollama Not Running

```bash
# Start Ollama service
ollama serve

# Or as background process
nohup ollama serve > ollama.log 2>&1 &
```

### Model Not Found

```bash
# Pull the model first
ollama pull llama2

# List available models
ollama list
```

### Out of Memory

```bash
# Use smaller model
ollama pull llama2  # Instead of llama2:70b

# Or reduce context
# Limit max_tokens in requests
```

### Slow Responses

- Use CPU offloading: Set `OLLAMA_NUM_GPU=0`
- Use smaller model
- Reduce max_tokens
- Enable GPU acceleration if available

## Security Considerations

- Authentication required for all endpoints
- Admin-only model deletion
- Rate limiting recommended for production
- Monitor resource usage
- Sanitize user inputs
- Log generations for auditing

## Future Enhancements

Potential improvements:

- [ ] Response caching
- [ ] Conversation persistence
- [ ] Multi-model comparison
- [ ] Fine-tuning support
- [ ] RAG (Retrieval Augmented Generation)
- [ ] Model performance metrics
- [ ] Cost tracking
- [ ] A/B testing framework
- [ ] Prompt templates library
- [ ] Auto-retry with fallbacks

---

**Last Updated:** October 29, 2025

For more information:
- [Ollama Documentation](https://github.com/ollama/ollama)
- [LLaMA 2 Paper](https://ai.meta.com/llama/)
- [GemmaPy API Docs](API_DOCS.md)
