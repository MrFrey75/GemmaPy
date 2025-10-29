# GemmaPy API Documentation

Complete API reference for GemmaPy REST API v1.0

## Table of Contents
- [Authentication](#authentication)
- [Public Endpoints](#public-endpoints)
- [Protected Endpoints](#protected-endpoints)
- [Admin Endpoints](#admin-endpoints)
- [Error Responses](#error-responses)
- [Examples](#examples)

## Base URL
```
http://localhost:5000
```

## Authentication

GemmaPy uses JWT (JSON Web Tokens) for authentication. After logging in, include the token in the `Authorization` header for all protected endpoints.

**Header Format:**
```
Authorization: Bearer <your-jwt-token>
```

**Token Properties:**
- Expiration: 24 hours
- Algorithm: HS256
- Contains: user_id, username, is_admin, exp

---

## Public Endpoints

### Health Check

Check if the API server is running.

**Endpoint:** `GET /api/health`

**Authentication:** None required

**Response (200):**
```json
{
  "status": "healthy"
}
```

**Example:**
```bash
curl http://localhost:5000/api/health
```

---

### User Login

Authenticate and receive a JWT token.

**Endpoint:** `POST /api/login`

**Authentication:** None required

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Success Response (200):**
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

**Error Responses:**
- `400` - Missing username or password
- `401` - Invalid credentials

**Example:**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123"}'
```

---

## Protected Endpoints

These endpoints require a valid JWT token in the Authorization header.

### Get User Data

Retrieve all data entries created by the authenticated user.

**Endpoint:** `GET /api/data`

**Authentication:** Required (any authenticated user)

**Request Headers:**
```
Authorization: Bearer <token>
```

**Success Response (200):**
```json
{
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "username": "admin",
      "content": "Sample data content",
      "created_at": "2025-10-29 14:30:00"
    }
  ]
}
```

**Error Responses:**
- `401` - No token provided or invalid token

**Example:**
```bash
curl http://localhost:5000/api/data \
  -H "Authorization: Bearer <your-token>"
```

---

### Create Data Entry

Create a new data entry for the authenticated user.

**Endpoint:** `POST /api/data`

**Authentication:** Required (any authenticated user)

**Request Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "string (required) - Data content to store"
}
```

**Success Response (201):**
```json
{
  "message": "Data created successfully",
  "id": 1
}
```

**Error Responses:**
- `400` - Missing content field
- `401` - No token provided or invalid token

**Example:**
```bash
curl -X POST http://localhost:5000/api/data \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"content":"My data entry"}'
```

---

## Admin Endpoints

These endpoints require admin privileges (is_admin = true).

### List All Users

Retrieve a list of all users in the system.

**Endpoint:** `GET /api/admin/users`

**Authentication:** Required (admin only)

**Request Headers:**
```
Authorization: Bearer <admin-token>
```

**Success Response (200):**
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
      "username": "testuser",
      "is_admin": 0,
      "created_at": "2025-10-29 14:00:00"
    }
  ]
}
```

**Error Responses:**
- `401` - No token provided or invalid token
- `403` - Admin privileges required

**Example:**
```bash
curl http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer <admin-token>"
```

---

### Create User

Create a new user account (admin only).

**Endpoint:** `POST /api/admin/users`

**Authentication:** Required (admin only)

**Request Headers:**
```
Authorization: Bearer <admin-token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "string (required) - Unique username",
  "password": "string (required) - User password",
  "is_admin": "boolean (optional, default: false) - Admin status"
}
```

**Success Response (201):**
```json
{
  "message": "User created successfully",
  "id": 3,
  "username": "newuser"
}
```

**Error Responses:**
- `400` - Missing required fields or username already exists
- `401` - No token provided or invalid token
- `403` - Admin privileges required

**Example:**
```bash
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"securepass","is_admin":false}'
```

---

## Error Responses

### Standard Error Format

All errors return a JSON object with an `error` field:

```json
{
  "error": "Error message description"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Missing or invalid parameters |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

### Common Error Messages

**Authentication Errors (401):**
```json
{"error": "No token provided"}
{"error": "Invalid or expired token"}
{"error": "Invalid credentials"}
{"error": "Username and password required"}
```

**Authorization Errors (403):**
```json
{"error": "Admin privileges required"}
```

**Validation Errors (400):**
```json
{"error": "Content is required"}
{"error": "Username and password required"}
{"error": "Username already exists"}
```

---

## Examples

### Complete Workflow Example

#### 1. Login and Get Token
```bash
# Login with default admin
TOKEN=$(curl -s -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123"}' \
  | jq -r '.token')

echo "Token: $TOKEN"
```

#### 2. Create a Data Entry
```bash
curl -X POST http://localhost:5000/api/data \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"My first entry"}'
```

#### 3. Retrieve Data
```bash
curl http://localhost:5000/api/data \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. Create a New User (Admin Only)
```bash
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"securepass123","is_admin":false}'
```

#### 5. List All Users (Admin Only)
```bash
curl http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN"
```

### Python Example

```python
import requests

BASE_URL = "http://localhost:5000"

# Login
response = requests.post(f"{BASE_URL}/api/login", json={
    "username": "admin",
    "password": "pass123"
})
token = response.json()["token"]

# Create data
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{BASE_URL}/api/data",
    headers=headers,
    json={"content": "Sample data"}
)
print(response.json())

# Get data
response = requests.get(f"{BASE_URL}/api/data", headers=headers)
print(response.json())
```

### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:5000';

// Login
const login = async () => {
  const response = await fetch(`${BASE_URL}/api/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'admin',
      password: 'pass123'
    })
  });
  const data = await response.json();
  return data.token;
};

// Create data
const createData = async (token, content) => {
  const response = await fetch(`${BASE_URL}/api/data`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ content })
  });
  return await response.json();
};

// Usage
(async () => {
  const token = await login();
  const result = await createData(token, 'My data');
  console.log(result);
})();
```

---

## Profile Management Endpoints

These endpoints allow authenticated users to manage their own profile information.

### Get Profile

Retrieve the authenticated user's profile information.

**Endpoint:** `GET /api/profile`

**Authentication:** Required (any authenticated user)

**Request Headers:**
```
Authorization: Bearer <token>
```

**Success Response (200):**
```json
{
  "profile": {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "full_name": "John Doe",
    "bio": "Software developer and tech enthusiast",
    "phone": "+1-555-0123",
    "address": "123 Main Street",
    "city": "San Francisco",
    "country": "USA",
    "date_of_birth": "1990-05-15",
    "website": "https://johndoe.com",
    "company": "Tech Corp",
    "job_title": "Senior Developer",
    "created_at": "2025-10-29 10:00:00",
    "updated_at": "2025-10-29 15:30:00"
  }
}
```

**Error Responses:**
- `401` - No token provided or invalid token
- `404` - User not found

**Example:**
```bash
curl http://localhost:5000/api/profile \
  -H "Authorization: Bearer <your-token>"
```

---

### Update Profile

Update the authenticated user's profile information. All fields are optional.

**Endpoint:** `PUT /api/profile`

**Authentication:** Required (any authenticated user)

**Request Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "string (optional) - User email address",
  "full_name": "string (optional) - User's full name",
  "bio": "string (optional) - User biography/description",
  "phone": "string (optional) - Phone number",
  "address": "string (optional) - Street address",
  "city": "string (optional) - City",
  "country": "string (optional) - Country",
  "date_of_birth": "string (optional) - Date of birth (YYYY-MM-DD)",
  "website": "string (optional) - Website URL",
  "company": "string (optional) - Company name",
  "job_title": "string (optional) - Job title"
}
```

**Success Response (200):**
```json
{
  "message": "Profile updated successfully",
  "profile": {
    "id": 1,
    "username": "john",
    "email": "newemail@example.com",
    "full_name": "John Doe",
    "bio": "Updated bio",
    "created_at": "2025-10-29 10:00:00",
    "updated_at": "2025-10-29 15:45:00"
  }
}
```

**Error Responses:**
- `400` - No fields to update
- `401` - No token provided or invalid token

**Example:**
```bash
curl -X PUT http://localhost:5000/api/profile \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "bio": "Full-stack developer passionate about Python"
  }'
```

---

### Change Password

Change the authenticated user's password.

**Endpoint:** `PUT /api/profile/password`

**Authentication:** Required (any authenticated user)

**Request Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "current_password": "string (required) - Current password",
  "new_password": "string (required) - New password (min 6 characters)"
}
```

**Success Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses:**
- `400` - Missing required fields or password too short
- `401` - Current password is incorrect or no token provided
- `404` - User not found

**Example:**
```bash
curl -X PUT http://localhost:5000/api/profile/password \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "oldpass123",
    "new_password": "newpass456"
  }'
```

---

### Delete Account

Delete the authenticated user's account and all associated data permanently.

**Endpoint:** `DELETE /api/profile`

**Authentication:** Required (any authenticated user)

**Request Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "password": "string (required) - User password for confirmation"
}
```

**Success Response (200):**
```json
{
  "message": "Account deleted successfully"
}
```

**Error Responses:**
- `400` - Password required
- `401` - Invalid password or no token provided
- `403` - Cannot delete admin account
- `404` - User not found

**Security Notes:**
- Admin accounts cannot be deleted via this endpoint
- All user data is permanently deleted
- This action cannot be undone

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/profile \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"password": "mypassword"}'
```

---

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider implementing rate limiting using Flask-Limiter.

## Versioning

Current API Version: **1.0**

Future versions will be indicated in the URL path (e.g., `/api/v2/...`)

## Support

For API issues or questions:
- Open an issue on the GitHub repository
- Check the [README.md](README.md) for setup instructions
- Review [SETUP.md](SETUP.md) for detailed configuration

---

**Last Updated:** October 29, 2025
