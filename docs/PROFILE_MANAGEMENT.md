# Profile Management Guide

Complete guide for managing user profiles in GemmaPy.

## Overview

GemmaPy provides comprehensive profile management features allowing users to:
- View their profile information
- Update email, full name, and bio
- Change their password
- Delete their account

## Profile Fields

| Field | Type | Description | Editable |
|-------|------|-------------|----------|
| id | Integer | Unique user identifier | No |
| username | String | User's login name | No |
| email | String | User's email address | Yes |
| full_name | String | User's full name | Yes |
| bio | Text | User biography/description | Yes |
| phone | String | Phone number | Yes |
| address | String | Street address | Yes |
| city | String | City of residence | Yes |
| country | String | Country of residence | Yes |
| date_of_birth | String | Date of birth (YYYY-MM-DD) | Yes |
| website | String | Personal or professional website | Yes |
| company | String | Current company/employer | Yes |
| job_title | String | Current job title | Yes |
| created_at | Timestamp | Account creation date | No |
| updated_at | Timestamp | Last update date | Auto |

## API Endpoints

### 1. Get Profile

Retrieve your profile information.

**Endpoint:** `GET /api/profile`

**Authentication:** Required

**Example:**
```bash
curl http://localhost:5000/api/profile \
  -H "Authorization: Bearer <your-token>"
```

**Response:**
```json
{
  "profile": {
    "id": 2,
    "username": "john",
    "email": "john@example.com",
    "full_name": "John Doe",
    "bio": "Software developer",
    "created_at": "2025-10-29 10:00:00",
    "updated_at": "2025-10-29 15:30:00"
  }
}
```

### 2. Update Profile

Update one or more profile fields.

**Endpoint:** `PUT /api/profile`

**Authentication:** Required

**Fields (all optional):**
- `email` - Email address
- `full_name` - Full name
- `bio` - Biography/description
- `phone` - Phone number
- `address` - Street address
- `city` - City
- `country` - Country
- `date_of_birth` - Date of birth (YYYY-MM-DD format)
- `website` - Website URL
- `company` - Company name
- `job_title` - Job title

**Example - Update Email:**
```bash
curl -X PUT http://localhost:5000/api/profile \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com"}'
```

**Example - Update Multiple Fields:**
```bash
curl -X PUT http://localhost:5000/api/profile \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "bio": "Full-stack developer passionate about Python and Flask",
    "phone": "+1-555-0199",
    "city": "San Francisco",
    "country": "USA",
    "website": "https://johndoe.com",
    "company": "Tech Corp",
    "job_title": "Senior Developer"
  }'
```

**Response:**
```json
{
  "message": "Profile updated successfully",
  "profile": {
    "id": 2,
    "username": "john",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "bio": "Full-stack developer passionate about Python and Flask",
    "created_at": "2025-10-29 10:00:00",
    "updated_at": "2025-10-29 15:45:00"
  }
}
```

### 3. Change Password

Change your account password.

**Endpoint:** `PUT /api/profile/password`

**Authentication:** Required

**Requirements:**
- Current password must be correct
- New password must be at least 6 characters

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

**Response:**
```json
{
  "message": "Password changed successfully"
}
```

**Security Notes:**
- You must provide your current password
- Passwords are hashed with bcrypt
- No password history is kept
- You'll need to login again with the new password

### 4. Delete Account

Permanently delete your account and all associated data.

**Endpoint:** `DELETE /api/profile`

**Authentication:** Required

**Requirements:**
- Must provide password for confirmation
- Admin accounts cannot be deleted via API

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/profile \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"password": "mypassword"}'
```

**Response:**
```json
{
  "message": "Account deleted successfully"
}
```

**⚠️ Warning:**
- This action is **permanent and cannot be undone**
- All your data entries will be deleted
- You cannot delete admin accounts this way
- You'll need to create a new account to use the service again

## Python Examples

### Complete Profile Management Workflow

```python
import requests

BASE_URL = "http://localhost:5000"

# Login
response = requests.post(f"{BASE_URL}/api/login", json={
    "username": "john",
    "password": "mypassword"
})
token = response.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. Get current profile
response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
profile = response.json()["profile"]
print(f"Current profile: {profile}")

# 2. Update profile
response = requests.put(
    f"{BASE_URL}/api/profile",
    headers=headers,
    json={
        "email": "john.doe@example.com",
        "full_name": "John Doe",
        "bio": "Python developer"
    }
)
updated_profile = response.json()["profile"]
print(f"Updated profile: {updated_profile}")

# 3. Change password
response = requests.put(
    f"{BASE_URL}/api/profile/password",
    headers=headers,
    json={
        "current_password": "mypassword",
        "new_password": "newsecurepass123"
    }
)
print(response.json()["message"])

# 4. Get profile again to verify changes
response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
print(f"Final profile: {response.json()['profile']}")
```

### Update Only Specific Fields

```python
import requests

BASE_URL = "http://localhost:5000"
token = "your-jwt-token"
headers = {"Authorization": f"Bearer {token}"}

# Update only email
requests.put(
    f"{BASE_URL}/api/profile",
    headers=headers,
    json={"email": "newemail@example.com"}
)

# Update only bio
requests.put(
    f"{BASE_URL}/api/profile",
    headers=headers,
    json={"bio": "Updated my bio"}
)

# Update only full name
requests.put(
    f"{BASE_URL}/api/profile",
    headers=headers,
    json={"full_name": "Jane Smith"}
)
```

## JavaScript Examples

### Using Fetch API

```javascript
const BASE_URL = 'http://localhost:5000';
const token = 'your-jwt-token';

// Get profile
const getProfile = async () => {
  const response = await fetch(`${BASE_URL}/api/profile`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  console.log('Profile:', data.profile);
};

// Update profile
const updateProfile = async () => {
  const response = await fetch(`${BASE_URL}/api/profile`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      email: 'user@example.com',
      full_name: 'John Doe',
      bio: 'JavaScript developer'
    })
  });
  const data = await response.json();
  console.log('Updated:', data.profile);
};

// Change password
const changePassword = async () => {
  const response = await fetch(`${BASE_URL}/api/profile/password`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      current_password: 'oldpass',
      new_password: 'newpass123'
    })
  });
  const data = await response.json();
  console.log(data.message);
};

// Delete account
const deleteAccount = async () => {
  if (!confirm('Are you sure? This cannot be undone!')) return;
  
  const response = await fetch(`${BASE_URL}/api/profile`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      password: 'mypassword'
    })
  });
  const data = await response.json();
  console.log(data.message);
};
```

## Error Handling

### Common Errors

**401 Unauthorized**
```json
{"error": "No token provided"}
{"error": "Invalid or expired token"}
{"error": "Current password is incorrect"}
{"error": "Invalid password"}
```

**400 Bad Request**
```json
{"error": "No fields to update"}
{"error": "Current password and new password required"}
{"error": "New password must be at least 6 characters"}
{"error": "Password required to delete account"}
```

**403 Forbidden**
```json
{"error": "Cannot delete admin account"}
```

**404 Not Found**
```json
{"error": "User not found"}
```

### Error Handling Example (Python)

```python
import requests

def update_profile_safe(token, updates):
    try:
        response = requests.put(
            "http://localhost:5000/api/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=updates
        )
        
        if response.status_code == 200:
            return response.json()["profile"]
        elif response.status_code == 401:
            print("Authentication failed. Please login again.")
        elif response.status_code == 400:
            print(f"Invalid request: {response.json()['error']}")
        else:
            print(f"Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
    
    return None
```

## Best Practices

### Security

1. **Password Changes:**
   - Always require current password
   - Enforce minimum password length
   - Consider adding password strength validation
   - Login again after password change

2. **Account Deletion:**
   - Always require password confirmation
   - Warn users about data loss
   - Consider soft-delete with recovery period
   - Protect admin accounts

3. **Profile Updates:**
   - Validate email format
   - Sanitize input data
   - Limit bio length
   - Rate limit updates

### User Experience

1. **Feedback:**
   - Show success messages
   - Display validation errors clearly
   - Confirm destructive actions
   - Update UI immediately

2. **Data:**
   - Load profile on login
   - Cache profile data
   - Auto-save drafts
   - Validate before submit

3. **Navigation:**
   - Easy access to profile
   - Clear edit mode
   - Cancel without saving
   - Breadcrumb navigation

## Testing

### Test Profile Management

```bash
# Run profile tests
pytest tests/test_profile.py -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/test_profile.py --cov=src --cov-report=html
```

### Manual Testing Checklist

- [ ] Can retrieve profile information
- [ ] Can update email
- [ ] Can update full name
- [ ] Can update bio
- [ ] Can update multiple fields at once
- [ ] Cannot update with no fields
- [ ] Can change password with correct current password
- [ ] Cannot change password with wrong current password
- [ ] Cannot use password shorter than 6 characters
- [ ] Can delete account with correct password
- [ ] Cannot delete account with wrong password
- [ ] Cannot delete admin account
- [ ] Profile updates persist after logout
- [ ] Updated_at timestamp updates correctly

## Database Schema

The users table includes these profile-related fields:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    full_name TEXT,
    bio TEXT,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Future Enhancements

Potential profile management improvements:

- [ ] Profile picture upload
- [ ] Email verification
- [ ] Password reset via email
- [ ] Two-factor authentication
- [ ] Account activity log
- [ ] Privacy settings
- [ ] Social media links
- [ ] User preferences
- [ ] Profile visibility settings
- [ ] Account export
- [ ] Soft delete with recovery
- [ ] Username change
- [ ] Account suspension

---

**Updated:** October 29, 2025

For more information, see:
- [API Documentation](API_DOCS.md)
- [README](README.md)
- [Testing Guide](TESTING.md)
