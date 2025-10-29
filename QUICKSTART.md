# 🚀 Quick Start Guide for GemmaPy

Get up and running with GemmaPy in under 2 minutes!

## Prerequisites

- Python 3.8+
- pip

## Installation (30 seconds)

```bash
# 1. Navigate to project
cd GemmaPy

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python src/init_db.py
```

Expected output:
```
Default admin user created (username: admin, password: pass123)
Database initialized successfully
```

## Start the Server (5 seconds)

```bash
python src/app.py
```

Server starts at: **http://localhost:5000**

## Test the API (30 seconds)

### 1. Health Check
```bash
curl http://localhost:5000/api/health
```

Response: `{"status":"healthy"}`

### 2. Login (Get Token)
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123"}'
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "is_admin": true
  }
}
```

### 3. Save Your Token
```bash
# Linux/Mac
export TOKEN="<paste-your-token-here>"

# Windows PowerShell
$TOKEN = "<paste-your-token-here>"
```

### 4. Create Data
```bash
curl -X POST http://localhost:5000/api/data \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"My first entry!"}'
```

Response:
```json
{
  "message": "Data created successfully",
  "id": 1
}
```

### 5. Get Data
```bash
curl http://localhost:5000/api/data \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "username": "admin",
      "content": "My first entry!",
      "created_at": "2025-10-29 10:30:00"
    }
  ]
}
```

### 6. Create a User (Admin Only)
```bash
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"secure123","is_admin":false}'
```

Response:
```json
{
  "message": "User created successfully",
  "id": 2,
  "username": "john"
}
```

### 7. List All Users (Admin Only)
```bash
curl http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "is_admin": 1,
      "created_at": "2025-10-29 10:00:00"
    },
    {
      "id": 2,
      "username": "john",
      "is_admin": 0,
      "created_at": "2025-10-29 10:35:00"
    }
  ]
}
```

## Run Tests (30 seconds)

```bash
pytest tests/ -v
```

Expected: **33 tests pass** with **92% coverage**

---

## Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin    | pass123  | Admin |

⚠️ **Change this password in production!**

## Available Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /api/health | None | Health check |
| POST | /api/login | None | User login |
| GET | /api/data | User | Get user's data |
| POST | /api/data | User | Create data entry |
| GET | /api/profile | User | Get user profile |
| PUT | /api/profile | User | Update profile |
| PUT | /api/profile/password | User | Change password |
| DELETE | /api/profile | User | Delete account |
| GET | /api/admin/users | Admin | List all users |
| POST | /api/admin/users | Admin | Create new user |

## Next Steps

1. ✅ **Read the docs:**
   - [README.md](README.md) - Overview
   - [API_DOCS.md](API_DOCS.md) - API reference
   - [SETUP.md](SETUP.md) - Detailed setup

2. ✅ **Change admin password:**
   - Login with new user
   - Use admin to create users
   - Change admin password

3. ✅ **Explore the code:**
   - `src/app.py` - Main application
   - `src/auth.py` - Authentication
   - `src/database.py` - Database

4. ✅ **Run tests:**
   - `pytest tests/ -v`
   - `pytest tests/ --cov=src --cov-report=html`

5. ✅ **Configure for production:**
   - Update `.env` file
   - Change SECRET_KEY
   - Set FLASK_ENV=production

## Troubleshooting

**Port already in use?**
```bash
# Use different port
python -c "from src.app import app; app.run(port=8080)"
```

**Database locked?**
```bash
rm gemmapy.db
python src/init_db.py
```

**Import errors?**
```bash
pip install -r requirements.txt --upgrade
```

## Help & Documentation

- 📖 [Full README](README.md)
- 🔧 [Setup Guide](SETUP.md)
- 📡 [API Documentation](API_DOCS.md)
- 🧪 [Testing Guide](TESTING.md)
- 📊 [Project Summary](PROJECT_SUMMARY.md)

---

## Copy-Paste Script for Full Test

```bash
#!/bin/bash

# Quick test script for GemmaPy

echo "1. Health Check..."
curl -s http://localhost:5000/api/health | jq

echo -e "\n2. Login..."
TOKEN=$(curl -s -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123"}' | jq -r '.token')

echo "Token: ${TOKEN:0:20}..."

echo -e "\n3. Create Data..."
curl -s -X POST http://localhost:5000/api/data \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Test entry"}' | jq

echo -e "\n4. Get Data..."
curl -s http://localhost:5000/api/data \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n5. Create User..."
curl -s -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}' | jq

echo -e "\n6. List Users..."
curl -s http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n7. Get Profile..."
curl -s http://localhost:5000/api/profile \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n8. Update Profile..."
curl -s -X PUT http://localhost:5000/api/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","full_name":"Admin User"}' | jq

echo -e "\n✅ All tests complete!"
```

Save as `test_api.sh`, make executable, and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

**You're all set! 🎉**

Happy coding with GemmaPy!
