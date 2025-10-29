# Backend Proxy Server (Optional)

This directory contains an optional backend proxy server that can be used to:

1. Add middleware for additional security
2. Handle CORS more elegantly
3. Cache responses
4. Rate limiting
5. Request/response transformation

## When to Use

Use this proxy if you need:

- ✅ Additional middleware between frontend and API
- ✅ Request/response logging
- ✅ Rate limiting
- ✅ Request transformation
- ✅ Custom error handling

Don't use this if:

- ❌ Frontend can directly communicate with API
- ❌ API already has proper CORS headers
- ❌ No need for intermediate processing

## Setup

### 1. Create Python Virtual Environment

```bash
cd webapp/backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env`:

```
FLASK_ENV=development
FLASK_DEBUG=1
API_URL=http://localhost:5000
PROXY_PORT=5001
```

### 4. Run Server

```bash
python server.py
```

Server will run on `http://localhost:5001`

### 5. Update Frontend API URL

In frontend `.env.local`:

```
VITE_API_URL=http://localhost:5001
```

## Features

- Request/response logging
- CORS handling
- Rate limiting
- Request transformation
- Error handling
- Health checks

## File Structure

```
backend/
├── server.py           # Main proxy server
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── middleware/
    ├── auth.py        # Authentication middleware
    ├── logging.py     # Logging middleware
    └── ratelimit.py   # Rate limiting
```

## Development

To implement this later, refer to examples:
- Flask documentation
- Requests library
- Flask-CORS

---

**Status**: Optional - Can be implemented as needed
