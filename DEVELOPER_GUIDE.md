# GemmaPy Developer Guide

Complete developer guide for contributing to and extending GemmaPy.

**Version:** 1.0.0  
**Last Updated:** October 29, 2025

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [Development Setup](#development-setup)
4. [Code Structure](#code-structure)
5. [Adding Features](#adding-features)
6. [Testing Guidelines](#testing-guidelines)
7. [API Development](#api-development)
8. [Database Management](#database-management)
9. [Best Practices](#best-practices)
10. [Deployment](#deployment)

---

## Getting Started

### Prerequisites

- Python 3.8+
- pip or pip3
- SQLite3
- Git
- (Optional) Ollama for LLM features

### Quick Setup

```bash
# Clone repository
git clone https://github.com/MrFrey75/GemmaPy.git
cd GemmaPy

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/init_db.py

# Run tests
pytest tests/ -v

# Start development server
python src/app.py
```

---

## Architecture Overview

### System Design

```
┌─────────────────────────────────────────────┐
│            Flask Application                 │
├─────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Auth   │  │  Ollama  │  │  Cache   │  │
│  │  Layer   │  │ Manager  │  │  Layer   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────┤
│            Database Layer (SQLite)           │
└─────────────────────────────────────────────┘
```

### Key Components

**Core Modules:**
- `app.py` - Flask application and route handlers
- `auth.py` - JWT authentication and decorators
- `database.py` - Database connection and initialization

**LLM Integration:**
- `ollama_manager.py` - Ollama API wrapper
- `llm_cache.py` - Response caching system
- `retry_manager.py` - Auto-retry with fallbacks
- `rag_manager.py` - RAG document system

**Analytics & Management:**
- `metrics_collector.py` - Performance metrics
- `cost_calculator.py` - Cost tracking
- `conversation_manager.py` - Conversation persistence
- `prompt_templates.py` - Template management
- `multi_model_comparator.py` - Model comparison

---

## Development Setup

### Environment Configuration

Create `.env` file:

```bash
# Required
SECRET_KEY=your-secure-secret-key-min-32-chars

# Optional
DATABASE_PATH=gemmapy.db
FLASK_ENV=development
FLASK_DEBUG=1
```

### Database Schema

The database is automatically created on first run. To manually recreate:

```bash
rm gemmapy.db
python src/init_db.py
```

### Development Server

```bash
# With debug mode
export FLASK_DEBUG=1
python src/app.py

# With auto-reload
flask --app src.app run --reload
```

---

## Code Structure

### Project Layout

```
GemmaPy/
├── src/                          # Source code
│   ├── __init__.py              # Package init
│   ├── app.py                   # Main application (1600+ lines)
│   ├── auth.py                  # Authentication (71 lines)
│   ├── database.py              # Database layer (169 lines)
│   ├── init_db.py               # DB initialization (6 lines)
│   └── [managers]               # Feature modules
├── tests/                        # Test suite
│   ├── conftest.py              # Test fixtures
│   └── test_*.py                # Test modules
├── docs/                         # Documentation (organized)
└── requirements.txt              # Dependencies
```

### Module Organization

**Each manager module follows this pattern:**

```python
class FeatureManager:
    def __init__(self, dependencies):
        """Initialize with dependencies"""
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create database tables if needed"""
        pass
    
    def create(self, ...):
        """Create new resource"""
        pass
    
    def get(self, id):
        """Retrieve resource"""
        pass
    
    def update(self, id, ...):
        """Update resource"""
        pass
    
    def delete(self, id):
        """Delete resource"""
        pass
```

---

## Adding Features

### 1. Create Manager Module

```python
# src/my_feature_manager.py
from database import get_db_connection

class MyFeatureManager:
    def __init__(self):
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create tables if they don't exist"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS my_feature (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            conn.commit()
    
    def create(self, user_id, data):
        """Create new feature entry"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO my_feature (user_id, data)
                VALUES (?, ?)
            ''', (user_id, data))
            conn.commit()
            return cursor.lastrowid
```

### 2. Add API Endpoints

```python
# In src/app.py
from my_feature_manager import MyFeatureManager

my_feature = MyFeatureManager()

@app.route('/api/my-feature', methods=['POST'])
@require_auth
def create_my_feature():
    """Create new feature"""
    data = request.get_json()
    
    # Validate input
    if not data.get('content'):
        return jsonify({'error': 'Content required'}), 400
    
    # Create resource
    feature_id = my_feature.create(
        user_id=request.user['user_id'],
        data=data['content']
    )
    
    return jsonify({
        'message': 'Feature created',
        'id': feature_id
    }), 201

@app.route('/api/my-feature/<int:feature_id>', methods=['GET'])
@require_auth
def get_my_feature(feature_id):
    """Get feature by ID"""
    feature = my_feature.get(feature_id, request.user['user_id'])
    
    if not feature:
        return jsonify({'error': 'Not found'}), 404
    
    return jsonify({'feature': feature}), 200
```

### 3. Write Tests

```python
# tests/test_my_feature.py
import pytest

class TestMyFeature:
    def test_create_feature(self, client, auth_token):
        """Test feature creation"""
        response = client.post('/api/my-feature',
            json={'content': 'test data'},
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
    
    def test_get_feature(self, client, auth_token):
        """Test feature retrieval"""
        # Create feature first
        create_response = client.post('/api/my-feature',
            json={'content': 'test data'},
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        feature_id = create_response.get_json()['id']
        
        # Get feature
        response = client.get(f'/api/my-feature/{feature_id}',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 200
```

---

## Testing Guidelines

### Test Structure

```python
# Standard test pattern
def test_feature_name(client, auth_token):
    """Test description"""
    # Arrange - Set up test data
    data = {'key': 'value'}
    
    # Act - Perform action
    response = client.post('/api/endpoint',
        json=data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # Assert - Check results
    assert response.status_code == 200
    assert response.get_json()['key'] == 'expected'
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_my_feature.py -v

# Specific test
pytest tests/test_my_feature.py::test_create_feature -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Fast fail
pytest tests/ -x

# Show print statements
pytest tests/ -v -s
```

### Test Fixtures

Available fixtures in `conftest.py`:

```python
@pytest.fixture
def client():
    """Flask test client with initialized database"""
    # Returns test client

@pytest.fixture
def auth_token(client):
    """JWT token for regular user (testuser)"""
    # Returns valid JWT token

@pytest.fixture
def admin_token(client):
    """JWT token for admin user"""
    # Returns admin JWT token
```

---

## API Development

### Authentication Decorators

```python
from auth import require_auth, require_admin

@app.route('/api/protected', methods=['GET'])
@require_auth
def protected_route():
    """Route accessible by any authenticated user"""
    user_id = request.user['user_id']
    username = request.user['username']
    is_admin = request.user['is_admin']
    return jsonify({'user': username})

@app.route('/api/admin-only', methods=['GET'])
@require_admin
def admin_route():
    """Route accessible only by admins"""
    return jsonify({'message': 'Admin access granted'})
```

### Request Validation

```python
@app.route('/api/resource', methods=['POST'])
@require_auth
def create_resource():
    data = request.get_json()
    
    # Check required fields
    if not data.get('name'):
        return jsonify({'error': 'Name required'}), 400
    
    # Validate types
    if not isinstance(data.get('count'), int):
        return jsonify({'error': 'Count must be integer'}), 400
    
    # Validate values
    if data['count'] < 1:
        return jsonify({'error': 'Count must be positive'}), 400
    
    # Process request...
```

### Error Handling

```python
@app.route('/api/resource', methods=['POST'])
@require_auth
def create_resource():
    try:
        # Your logic here
        result = do_something()
        return jsonify({'result': result}), 200
    
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    
    except PermissionError as e:
        return jsonify({'error': 'Access denied'}), 403
    
    except Exception as e:
        # Log error for debugging
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
```

---

## Database Management

### Database Queries

```python
# SELECT
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()  # Returns dict or None

# INSERT
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO table (col1, col2) VALUES (?, ?)
    ''', (val1, val2))
    conn.commit()
    new_id = cursor.lastrowid

# UPDATE
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE table SET col1 = ? WHERE id = ?
    ''', (new_value, record_id))
    conn.commit()

# DELETE
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('DELETE FROM table WHERE id = ?', (record_id,))
    rows_deleted = cursor.rowcount
    conn.commit()
```

### Adding Tables

```python
def _ensure_tables(self):
    """Create tables if they don't exist"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS my_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_my_table_user 
            ON my_table(user_id)
        ''')
        
        conn.commit()
```

---

## Best Practices

### Code Style

```python
# Use type hints
def process_data(user_id: int, data: str) -> Dict:
    """Process user data and return result"""
    pass

# Use docstrings
def complex_function(param1, param2):
    """
    Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
    """
    pass

# Use context managers
with get_db_connection() as conn:
    # Database operations
    pass  # Connection automatically closed
```

### Security

```python
# ✅ GOOD: Parameterized queries
cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))

# ❌ BAD: String formatting (SQL injection risk)
cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')

# ✅ GOOD: Validate input
if rating not in [-1, 0, 1]:
    raise ValueError("Invalid rating")

# ✅ GOOD: Check permissions
if resource.user_id != request.user['user_id']:
    return jsonify({'error': 'Access denied'}), 403
```

### Performance

```python
# Use indexes for frequently queried columns
cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_created_at 
    ON table(created_at)
''')

# Batch operations when possible
cursor.executemany('''
    INSERT INTO table (col1, col2) VALUES (?, ?)
''', data_list)

# Cache expensive operations
from llm_cache import LLMCache
cache = LLMCache()
result = cache.get(key) or compute_expensive_result()
```

---

## Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` to secure random value
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=0`
- [ ] Change default admin password
- [ ] Enable HTTPS
- [ ] Configure firewall
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring

### Using Gunicorn

```bash
# Install
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 src.app:app

# With logging
gunicorn -w 4 -b 0.0.0.0:5000 \
    --access-logfile access.log \
    --error-logfile error.log \
    src.app:app
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY . .

RUN python src/init_db.py

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.app:app"]
```

---

## Contributing

### Workflow

1. Fork repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Write tests
5. Run test suite: `pytest tests/ -v`
6. Commit: `git commit -m "Add my feature"`
7. Push: `git push origin feature/my-feature`
8. Create Pull Request

### Commit Messages

```
feat: Add multi-model comparison feature
fix: Resolve cache invalidation bug
docs: Update API documentation
test: Add tests for RAG manager
refactor: Simplify authentication logic
```

---

## Resources

### Documentation
- [API Documentation](API_DOCS.md)
- [Quick Start Guide](QUICKSTART.md)
- [Testing Guide](TESTING.md)
- [Ollama Integration](OLLAMA_GUIDE.md)

### External Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Happy Coding! 🚀**

*For questions or issues, open an issue on GitHub or consult the documentation.*
