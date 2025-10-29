# Multi-Model Comparison Guide

Complete guide for using the Multi-Model Comparison feature in GemmaPy.

## Overview

The Multi-Model Comparison system allows you to compare responses from multiple LLM models simultaneously. This helps you:
- Evaluate different models for your use case
- Compare response quality, speed, and accuracy
- Track which models work best for specific tasks
- Make data-driven decisions about model selection

## Features

- ✅ Compare 2+ models simultaneously
- ✅ Track response times and token counts
- ✅ Rate and rank model responses
- ✅ Model performance analytics
- ✅ Success/failure tracking
- ✅ User-specific and admin-level statistics

## API Endpoints

### 1. Compare Models

**Endpoint:** `POST /api/compare/models`

**Authentication:** Required

**Request Body:**
```json
{
  "prompt": "Explain quantum computing",
  "models": ["llama2", "mistral", "llama3"],
  "system": "You are a helpful AI assistant",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "comparison_id": 1,
  "prompt": "Explain quantum computing",
  "models": ["llama2", "mistral", "llama3"],
  "responses": [
    {
      "response_id": 1,
      "model": "llama2",
      "response": "Quantum computing is...",
      "duration_ms": 2500,
      "tokens": 150,
      "error": null,
      "success": true
    },
    {
      "response_id": 2,
      "model": "mistral",
      "response": "Quantum computing uses...",
      "duration_ms": 1800,
      "tokens": 145,
      "error": null,
      "success": true
    }
  ],
  "created_at": "2025-10-29T17:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/compare/models \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to calculate fibonacci",
    "models": ["llama2", "mistral", "codellama"]
  }'
```

---

### 2. List Comparisons

**Endpoint:** `GET /api/compare/comparisons`

**Authentication:** Required

**Query Parameters:**
- `limit` (optional) - Maximum number of results (default: 50)

**Response:**
```json
{
  "comparisons": [
    {
      "id": 1,
      "prompt": "Explain quantum computing",
      "created_at": "2025-10-29T17:00:00Z",
      "model_count": 3,
      "models": "llama2,mistral,llama3"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/api/compare/comparisons?limit=20 \
  -H "Authorization: Bearer <token>"
```

---

### 3. Get Comparison Details

**Endpoint:** `GET /api/compare/comparisons/<comparison_id>`

**Authentication:** Required

**Response:**
```json
{
  "comparison": {
    "id": 1,
    "user_id": 1,
    "prompt": "Explain quantum computing",
    "system_prompt": null,
    "temperature": 0.7,
    "created_at": "2025-10-29T17:00:00Z",
    "responses": [
      {
        "id": 1,
        "model": "llama2",
        "response": "...",
        "duration_ms": 2500,
        "tokens": 150,
        "error": null,
        "user_rating": 1,
        "created_at": "2025-10-29T17:00:00Z"
      }
    ]
  }
}
```

**Example:**
```bash
curl http://localhost:5000/api/compare/comparisons/1 \
  -H "Authorization: Bearer <token>"
```

---

### 4. Rate a Response

**Endpoint:** `POST /api/compare/responses/<response_id>/rate`

**Authentication:** Required

**Request Body:**
```json
{
  "rating": 1
}
```

**Rating Values:**
- `1` - Positive (good response)
- `0` - Neutral
- `-1` - Negative (bad response)

**Response:**
```json
{
  "message": "Rating recorded"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/compare/responses/1/rate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"rating": 1}'
```

---

### 5. Delete Comparison

**Endpoint:** `DELETE /api/compare/comparisons/<comparison_id>`

**Authentication:** Required

**Response:**
```json
{
  "message": "Comparison deleted"
}
```

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/compare/comparisons/1 \
  -H "Authorization: Bearer <token>"
```

---

### 6. Get Model Rankings

**Endpoint:** `GET /api/compare/rankings`

**Authentication:** Required

**Query Parameters:**
- `days` (optional) - Number of days to consider (default: 30)

**Response:**
```json
{
  "rankings": [
    {
      "model": "llama2",
      "total_responses": 50,
      "avg_duration_ms": 2300,
      "avg_tokens": 145,
      "positive_ratings": 35,
      "negative_ratings": 5,
      "total_ratings": 40,
      "successful_responses": 48,
      "failed_responses": 2,
      "satisfaction_rate": 0.875,
      "success_rate": 0.96
    },
    {
      "model": "mistral",
      "total_responses": 45,
      "avg_duration_ms": 1900,
      "avg_tokens": 140,
      "positive_ratings": 30,
      "negative_ratings": 8,
      "total_ratings": 38,
      "successful_responses": 44,
      "failed_responses": 1,
      "satisfaction_rate": 0.789,
      "success_rate": 0.978
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/api/compare/rankings?days=7 \
  -H "Authorization: Bearer <token>"
```

---

### 7. Get Statistics

**Endpoint:** `GET /api/compare/statistics`

**Authentication:** Required

**Response:**
```json
{
  "statistics": {
    "total_comparisons": 25,
    "unique_models_compared": 5,
    "most_compared_models": [
      {"model": "llama2", "count": 20},
      {"model": "mistral", "count": 18},
      {"model": "llama3", "count": 15}
    ]
  }
}
```

**Example:**
```bash
curl http://localhost:5000/api/compare/statistics \
  -H "Authorization: Bearer <token>"
```

---

## Usage Examples

### Python

```python
import requests

BASE_URL = "http://localhost:5000"
token = "<your-jwt-token>"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Compare models
comparison = requests.post(
    f"{BASE_URL}/api/compare/models",
    headers=headers,
    json={
        "prompt": "Explain machine learning in simple terms",
        "models": ["llama2", "mistral", "llama3"],
        "temperature": 0.7
    }
).json()

print(f"Comparison ID: {comparison['comparison_id']}")

# Review responses
for response in comparison['responses']:
    print(f"\nModel: {response['model']}")
    print(f"Duration: {response['duration_ms']}ms")
    print(f"Response: {response['response'][:100]}...")
    
    # Rate the response
    if response['success']:
        rating = 1  # or -1, 0 based on quality
        requests.post(
            f"{BASE_URL}/api/compare/responses/{response['response_id']}/rate",
            headers=headers,
            json={"rating": rating}
        )

# Get rankings
rankings = requests.get(
    f"{BASE_URL}/api/compare/rankings?days=30",
    headers=headers
).json()

print("\nModel Rankings:")
for rank in rankings['rankings']:
    print(f"{rank['model']}: {rank['satisfaction_rate']:.2%} satisfaction")
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:5000';
const token = '<your-jwt-token>';
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Compare models
async function compareModels() {
  const response = await fetch(`${BASE_URL}/api/compare/models`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      prompt: 'Explain machine learning in simple terms',
      models: ['llama2', 'mistral', 'llama3'],
      temperature: 0.7
    })
  });
  
  const comparison = await response.json();
  console.log('Comparison ID:', comparison.comparison_id);
  
  // Rate responses
  for (const resp of comparison.responses) {
    console.log(`\nModel: ${resp.model}`);
    console.log(`Duration: ${resp.duration_ms}ms`);
    
    if (resp.success) {
      await fetch(`${BASE_URL}/api/compare/responses/${resp.response_id}/rate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ rating: 1 })
      });
    }
  }
  
  return comparison;
}

// Get rankings
async function getRankings() {
  const response = await fetch(`${BASE_URL}/api/compare/rankings?days=30`, {
    headers
  });
  
  const data = await response.json();
  console.log('\nModel Rankings:');
  data.rankings.forEach(rank => {
    console.log(`${rank.model}: ${(rank.satisfaction_rate * 100).toFixed(1)}% satisfaction`);
  });
}

compareModels().then(getRankings);
```

---

## Use Cases

### 1. Model Selection

Compare models to find the best one for your specific use case:

```python
# Compare models for code generation
comparison = compare_models(
    prompt="Write a Python function to validate email addresses",
    models=["llama2", "codellama", "mistral"]
)

# Review and rate based on code quality
```

### 2. Quality Assurance

Verify consistency across models:

```python
# Compare models for customer support
comparison = compare_models(
    prompt="How do I reset my password?",
    models=["llama2", "mistral", "llama3"],
    system="You are a helpful customer support agent"
)
```

### 3. Performance Benchmarking

Track model performance over time:

```python
# Run daily benchmarks
for prompt in test_prompts:
    compare_models(prompt, models=["llama2", "mistral", "llama3"])

# Analyze rankings
rankings = get_rankings(days=7)
```

### 4. Cost Optimization

Compare models based on speed and quality:

```python
rankings = get_rankings(days=30)

# Find fastest model with good satisfaction
best_model = min(
    [r for r in rankings if r['satisfaction_rate'] > 0.8],
    key=lambda x: x['avg_duration_ms']
)

print(f"Best model: {best_model['model']}")
```

---

## Best Practices

### 1. Rating Responses

- Rate responses consistently
- Use clear criteria (accuracy, relevance, completeness)
- Rate enough responses for meaningful statistics

### 2. Model Selection

- Compare at least 2-3 models
- Test with representative prompts
- Consider both speed and quality

### 3. Temperature Settings

- Use consistent temperature for fair comparison
- Lower temperature (0.3-0.5) for factual tasks
- Higher temperature (0.7-0.9) for creative tasks

### 4. Prompt Engineering

- Use clear, specific prompts
- Include system prompts when relevant
- Test edge cases

---

## Admin Features

Admins can view rankings and statistics across all users:

```python
# Admin: View all model rankings
rankings = get_rankings(days=30)  # Shows all users' data

# Admin: View global statistics
stats = get_statistics()  # Shows all users' data
```

---

## Troubleshooting

### Issue: Comparison returns empty responses

**Solution:** Verify Ollama is running and models are available:
```bash
curl http://localhost:5000/api/ollama/status
curl http://localhost:5000/api/ollama/models
```

### Issue: Rating fails

**Solution:** Ensure you own the comparison:
- You can only rate responses from your own comparisons
- Check comparison_id and response_id are correct

### Issue: Slow comparisons

**Solution:**
- Models run sequentially, so comparing many models takes time
- Consider reducing max_tokens
- Use faster models for comparisons

---

## Metrics Explained

### Satisfaction Rate
Percentage of positive ratings vs total ratings:
```
satisfaction_rate = positive_ratings / total_ratings
```

### Success Rate
Percentage of successful responses (no errors):
```
success_rate = successful_responses / total_responses
```

### Average Duration
Mean response time in milliseconds across all comparisons.

### Average Tokens
Mean token count across all responses.

---

## Future Enhancements

Planned improvements:
- [ ] Parallel model execution for faster comparisons
- [ ] Side-by-side UI for response comparison
- [ ] Export comparison results to CSV/JSON
- [ ] Scheduled automated comparisons
- [ ] Model recommendation engine
- [ ] Cost comparison integration

---

**Last Updated:** October 29, 2025  
**Version:** 1.0.0  
**Status:** Production Ready
