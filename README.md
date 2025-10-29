# GemmaPy

A secure Python REST API with JWT authentication, role-based access control, and SQLite database integration.

## Features

### Core Features
- 🔐 JWT-based authentication with bcrypt password hashing
- 👥 Role-based access control (User/Admin)
- 📊 RESTful API with GET and POST endpoints
- 💾 SQLite database with automatic initialization
- 🔧 Preseeded admin account for immediate use
- ✅ Comprehensive test suite (161 tests, 92% coverage)
- 🚀 Production-ready with CORS support

### User Management
- User profile management with personal details
- Admin controls for user management
- Secure password hashing and token-based auth

### Ollama/LLM Integration
- 🤖 Local Ollama integration for LLM operations
- 💬 Text generation and chat completions
- 🔄 Model management (list, pull, delete, info)
- 📝 Embeddings generation

#### Phase 1 Features (Completed)
- ⚡ **Response Caching** - Intelligent LLM response caching with TTL
- 🔁 **Auto-Retry with Fallbacks** - Automatic retry logic with model fallbacks
- 📚 **RAG (Retrieval Augmented Generation)** - Document-based context augmentation

#### Phase 2 Features (Completed)
- 📊 **Model Performance Metrics** - Track response times, token usage, and performance
- 💰 **Cost Tracking** - Monitor computational costs per user and model
- 📈 **Analytics Dashboard** - Comprehensive metrics visualization
- ⭐ **User Ratings** - Rate LLM responses for quality tracking

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd GemmaPy
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Initialize the database:**
```bash
python src/init_db.py
```

This creates a SQLite database with a default admin account:
- **Username:** `admin`
- **Password:** `pass123`

⚠️ **SECURITY:** Change the default admin password in production!

4. **Start the server:**
```bash
python src/app.py
```

The API will be available at `http://localhost:5000`

## Default Credentials

For initial setup and testing:

| Username | Password | Role  |
|----------|----------|-------|
| admin    | pass123  | Admin |

**First Steps:**
1. Login with admin credentials to get a JWT token
2. Use the admin account to create additional users
3. Change the admin password immediately

## API Endpoints

### Public Endpoints

#### Health Check
```http
GET /api/health
```
Returns server status.

#### User Login
```http
POST /api/login
Content-Type: application/json

{
  "username": "admin",
  "password": "pass123"
}
```
Returns JWT token for authentication.

### Protected Endpoints (Require Authentication)

Add JWT token to requests:
```
Authorization: Bearer <your-jwt-token>
```

#### Get User Data
```http
GET /api/data
```
Returns all data entries for the authenticated user.

#### Create Data Entry
```http
POST /api/data
Content-Type: application/json

{
  "content": "Your data content"
}
```
Creates a new data entry for the authenticated user.

### Admin Endpoints (Require Admin Role)

#### List All Users
```http
GET /api/admin/users
```
Returns all users in the system.

#### Create New User
```http
POST /api/admin/users
Content-Type: application/json

{
  "username": "newuser",
  "password": "securepassword",
  "is_admin": false
}
```
Creates a new user account.

### Profile Management Endpoints (User)

#### Get Profile
```http
GET /api/profile
```
Returns the authenticated user's profile information.

#### Update Profile
```http
PUT /api/profile
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "bio": "Software developer"
}
```
Updates the authenticated user's profile. All fields are optional.

#### Change Password
```http
PUT /api/profile/password
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```
Changes the authenticated user's password.

#### Delete Account
```http
DELETE /api/profile
Content-Type: application/json

{
  "password": "userpassword"
}
```
Deletes the authenticated user's account and all associated data.

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=src --cov-report=html
```

### Test Statistics
- **Total Tests:** 97
- **Code Coverage:** 93%+
- **Test Suites:**
  - Authentication tests (5)
  - API endpoint tests (6)
  - Admin functionality tests (7)
  - Database tests (3)
  - Preseeded admin tests (4)
  - Profile management tests (27)
  - Ollama manager tests (17)
  - Ollama API tests (20)
  - Utility tests (7)
  - Health check test (1)

## Project Structure

```
GemmaPy/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── app.py               # Main Flask application
│   ├── auth.py              # Authentication & authorization
│   ├── database.py          # Database connection & setup
│   └── init_db.py           # Database initialization script
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_admin.py        # Admin endpoint tests
│   ├── test_api.py          # API endpoint tests
│   ├── test_auth.py         # Authentication tests
│   ├── test_database.py     # Database tests
│   ├── test_health.py       # Health check tests
│   ├── test_preseeded_admin.py  # Default admin tests
│   └── test_utils.py        # Utility function tests
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── API_DOCS.md             # Detailed API documentation
├── CONTRIBUTING.md         # Contribution guidelines
├── LICENSE                 # MIT License
├── pytest.ini              # Pytest configuration
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── SETUP.md                # Detailed setup instructions
└── TESTING.md              # Testing guide
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Available variables:

| Variable | Default | Description |
|----------|---------|-------------|
| SECRET_KEY | dev-secret-key-change-in-production | JWT signing key |
| DATABASE_PATH | gemmapy.db | SQLite database file path |
| FLASK_ENV | development | Flask environment |
| FLASK_DEBUG | 1 | Enable debug mode |

## Security Features

- ✅ Password hashing with bcrypt (salt rounds: 12)
- ✅ JWT tokens with 24-hour expiration
- ✅ Role-based access control (@require_auth, @require_admin)
- ✅ SQL injection prevention (parameterized queries)
- ✅ CORS enabled for cross-origin requests

## Development

### Adding New Endpoints

1. Define route in `src/app.py`
2. Add authentication decorator if needed
3. Implement business logic
4. Write tests in `tests/`

### Running in Development Mode

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python src/app.py
```

## Documentation

- **[API Documentation](API_DOCS.md)** - Complete API reference
- **[Setup Guide](SETUP.md)** - Detailed installation instructions
- **[Testing Guide](TESTING.md)** - Comprehensive testing documentation
- **[Contributing](CONTRIBUTING.md)** - How to contribute

## Dependencies

- **Flask 3.0.0** - Web framework
- **Flask-CORS 4.0.0** - Cross-origin resource sharing
- **PyJWT 2.8.0** - JSON Web Tokens
- **bcrypt 4.1.2** - Password hashing
- **pytest 7.4.3** - Testing framework
- **pytest-cov 4.1.0** - Coverage reporting

## Troubleshooting

### Database locked error
```bash
rm gemmapy.db  # Remove the database
python src/init_db.py  # Reinitialize
```

### Import errors
```bash
pip install -r requirements.txt --upgrade
```

### Test failures
```bash
# Clean test artifacts
rm -rf .pytest_cache
rm -rf htmlcov
pytest tests/ -v
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.

---

**Built with ❤️ using Python and Flask**
