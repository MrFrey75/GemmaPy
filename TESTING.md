# GemmaPy Testing Guide

Comprehensive guide for testing the GemmaPy API.

## Table of Contents
- [Test Overview](#test-overview)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Coverage Reports](#coverage-reports)
- [Continuous Integration](#continuous-integration)

## Test Overview

GemmaPy includes a comprehensive test suite with:

- **33 total tests**
- **92% code coverage**
- **7 test modules**
- **Automated fixtures**
- **Isolated test databases**

### Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| Authentication | 5 | Login, credentials, validation |
| API Endpoints | 6 | GET/POST data operations |
| Admin Functions | 7 | User management, permissions |
| Database | 3 | Schema, initialization, seeding |
| Preseeded Admin | 4 | Default admin account |
| Utilities | 7 | Password hashing, JWT tokens |
| Health Check | 1 | Server status |

## Running Tests

### Basic Test Commands

**Run all tests:**
```bash
pytest tests/
```

**Run with verbose output:**
```bash
pytest tests/ -v
```

**Run specific test file:**
```bash
pytest tests/test_auth.py -v
```

**Run specific test function:**
```bash
pytest tests/test_auth.py::test_login_success -v
```

**Run tests matching a pattern:**
```bash
pytest tests/ -k "admin" -v
```

### Coverage Reports

**Generate coverage report:**
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

**HTML coverage report:**
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

**XML coverage (for CI):**
```bash
pytest tests/ --cov=src --cov-report=xml
```

### Test Output Options

**Show print statements:**
```bash
pytest tests/ -v -s
```

**Stop on first failure:**
```bash
pytest tests/ -x
```

**Run failed tests only:**
```bash
pytest tests/ --lf
```

**Show slowest tests:**
```bash
pytest tests/ --durations=10
```

## Test Structure

### Directory Layout

```
tests/
├── __init__.py                 # Test package
├── conftest.py                 # Shared fixtures
├── test_admin.py               # Admin endpoint tests
├── test_api.py                 # API endpoint tests
├── test_auth.py                # Authentication tests
├── test_database.py            # Database tests
├── test_health.py              # Health check tests
├── test_preseeded_admin.py     # Default admin tests
└── test_utils.py               # Utility function tests
```

### Test Fixtures (conftest.py)

**client** - Flask test client with initialized database
```python
@pytest.fixture
def client():
    # Creates unique database for each test
    # Seeds with admin and testuser
    # Returns Flask test client
    ...
```

**auth_token** - JWT token for regular user
```python
@pytest.fixture
def auth_token(client):
    # Returns JWT token for 'testuser'
    ...
```

**admin_token** - JWT token for admin user
```python
@pytest.fixture
def admin_token(client):
    # Returns JWT token for 'admin'
    ...
```

## Test Details

### Authentication Tests (test_auth.py)

Tests login functionality and credential validation.

**test_login_success**
- ✅ Valid credentials return token
- ✅ User information included

**test_login_invalid_credentials**
- ✅ Wrong password rejected
- ✅ Returns 401 status

**test_login_missing_username**
- ✅ Validates required fields
- ✅ Returns 400 status

**test_login_missing_password**
- ✅ Validates required fields
- ✅ Returns 400 status

**test_login_nonexistent_user**
- ✅ Non-existent user rejected
- ✅ Returns 401 status

### API Endpoint Tests (test_api.py)

Tests data GET/POST operations.

**test_get_data_requires_auth**
- ✅ Unauthenticated request rejected

**test_get_data_with_auth**
- ✅ Returns user's data
- ✅ Proper data structure

**test_post_data_requires_auth**
- ✅ Unauthenticated request rejected

**test_post_data_with_auth**
- ✅ Creates data entry
- ✅ Returns created ID

**test_post_data_missing_content**
- ✅ Validates required fields

**test_get_data_after_post**
- ✅ Created data is retrievable
- ✅ Data persistence

### Admin Tests (test_admin.py)

Tests admin-only functionality.

**test_get_users_requires_admin**
- ✅ Regular users blocked
- ✅ Returns 403 status

**test_get_users_with_admin**
- ✅ Admin can list users
- ✅ Returns all users

**test_create_user_requires_admin**
- ✅ Regular users blocked

**test_create_user_with_admin**
- ✅ Admin can create users
- ✅ Returns user info

**test_create_user_duplicate**
- ✅ Duplicate usernames rejected

**test_create_admin_user**
- ✅ Can create admin users

**test_create_user_missing_fields**
- ✅ Validates required fields

### Database Tests (test_database.py)

Tests database initialization and schema.

**test_init_db_creates_tables**
- ✅ Users table created
- ✅ Data table created

**test_init_db_creates_default_admin**
- ✅ Admin user seeded
- ✅ Correct credentials
- ✅ Admin privileges set

**test_init_db_does_not_duplicate_admin**
- ✅ Idempotent initialization
- ✅ No duplicate admin

### Preseeded Admin Tests (test_preseeded_admin.py)

Tests default admin account.

**test_default_admin_login**
- ✅ Can login with default credentials
- ✅ Returns valid token

**test_default_admin_has_privileges**
- ✅ Has admin access
- ✅ Can access admin endpoints

**test_default_admin_can_create_users**
- ✅ Can create new users

**test_wrong_default_admin_password**
- ✅ Wrong password rejected

### Utility Tests (test_utils.py)

Tests authentication utilities.

**test_hash_password**
- ✅ Hashes passwords
- ✅ Different from plaintext

**test_verify_password_success**
- ✅ Verifies correct password

**test_verify_password_failure**
- ✅ Rejects wrong password

**test_generate_token**
- ✅ Generates JWT token

**test_decode_token**
- ✅ Decodes valid token
- ✅ Contains correct payload

**test_decode_invalid_token**
- ✅ Rejects invalid tokens

**test_admin_token**
- ✅ Admin flag in token

## Writing Tests

### Test Template

```python
def test_my_feature(client, auth_token):
    """Test description"""
    # Arrange
    data = {"field": "value"}
    
    # Act
    response = client.post('/api/endpoint',
        json=data,
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.get_json()['key'] == 'expected'
```

### Best Practices

1. **One assertion per test (when possible)**
2. **Use descriptive test names**
3. **Follow Arrange-Act-Assert pattern**
4. **Clean up resources**
5. **Test edge cases**
6. **Use fixtures for common setup**

### Adding New Tests

1. **Create test file:**
```bash
touch tests/test_my_feature.py
```

2. **Import dependencies:**
```python
import pytest
```

3. **Write test functions:**
```python
def test_my_feature(client):
    # Your test code
    pass
```

4. **Run tests:**
```bash
pytest tests/test_my_feature.py -v
```

## Coverage Reports

### Current Coverage

```
Name              Stmts   Miss  Cover   Missing
-----------------------------------------------
src/__init__.py       3      3     0%   5-7
src/app.py           80      1    99%   130
src/auth.py          51      4    92%   29, 45, 56, 63
src/database.py      28      1    96%   62
src/init_db.py        4      4     0%   1-5
-----------------------------------------------
TOTAL               166     13    92%
```

### Coverage Goals

- ✅ **Current:** 92%
- 🎯 **Target:** 95%
- 📊 **Critical paths:** 100%

### Improving Coverage

**Identify uncovered lines:**
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

**View HTML report:**
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        files: ./coverage.xml
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest tests/ --tb=short
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Troubleshooting Tests

### Common Issues

**Import errors:**
```bash
# Run from project root
cd /path/to/GemmaPy
pytest tests/
```

**Database conflicts:**
```bash
# Clean test artifacts
rm -rf .pytest_cache
rm /tmp/test_*.db
```

**Slow tests:**
```bash
# Identify slow tests
pytest tests/ --durations=10
```

### Debug Mode

**Run with debugger:**
```bash
pytest tests/ --pdb
```

**Print test output:**
```bash
pytest tests/ -v -s
```

**Verbose failures:**
```bash
pytest tests/ -vv
```

## Test Maintenance

### Regular Tasks

- [ ] Run full test suite before commits
- [ ] Update tests when adding features
- [ ] Maintain >90% coverage
- [ ] Review and remove obsolete tests
- [ ] Update test documentation

### Performance Benchmarks

- Total test time: ~15 seconds
- Average per test: ~0.45 seconds
- Database setup: ~0.1 seconds per test

---

**Happy Testing! 🧪**
