# GemmaPy Setup Guide

Complete installation and configuration guide for GemmaPy.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.8 or higher**
  ```bash
  python --version  # or python3 --version
  ```

- **pip** (Python package installer)
  ```bash
  pip --version  # or pip3 --version
  ```

- **Git** (for cloning the repository)
  ```bash
  git --version
  ```

### System Requirements

- **OS:** Linux, macOS, or Windows
- **RAM:** 256MB minimum
- **Disk Space:** 100MB minimum
- **Network:** Internet connection for initial setup

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd GemmaPy
```

Or download and extract the ZIP file.

### Step 2: Create Virtual Environment (Recommended)

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**
- Flask 3.0.0 - Web framework
- Flask-CORS 4.0.0 - CORS support
- PyJWT 2.8.0 - JWT authentication
- bcrypt 4.1.2 - Password hashing
- pytest 7.4.3 - Testing framework
- pytest-cov 4.1.0 - Code coverage

**Verify installation:**
```bash
pip list | grep -E "Flask|bcrypt|PyJWT|pytest"
```

## Configuration

### Step 4: Environment Variables

Create environment configuration file:

```bash
cp .env.example .env
```

Edit `.env` file with your settings:

```bash
# Secret key for JWT tokens (CHANGE THIS!)
SECRET_KEY=your-very-secure-secret-key-here-use-at-least-32-characters

# Database file path
DATABASE_PATH=gemmapy.db

# Flask environment
FLASK_ENV=development
FLASK_DEBUG=1
```

**Generate a secure secret key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | dev-secret-key-change-in-production | JWT signing key (MUST change for production) |
| `DATABASE_PATH` | gemmapy.db | SQLite database file location |
| `FLASK_ENV` | development | Flask environment (development/production) |
| `FLASK_DEBUG` | 1 | Enable debug mode (0=off, 1=on) |

## Database Setup

### Step 5: Initialize Database

```bash
python src/init_db.py
```

**Expected output:**
```
Default admin user created (username: admin, password: pass123)
Database initialized successfully
```

This creates:
- SQLite database file (`gemmapy.db`)
- `users` table
- `data` table
- Default admin account

### Default Admin Account

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `pass123` |
| Role | Administrator |

⚠️ **SECURITY WARNING:** Change this password immediately after first login!

### Database Schema

**Users Table:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Data Table:**
```sql
CREATE TABLE data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## Running the Application

### Step 6: Start the Server

**Development Mode:**
```bash
python src/app.py
```

**Expected output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

**Custom Host/Port:**
```bash
# Bind to all interfaces on port 8080
python -c "from src.app import app; app.run(host='0.0.0.0', port=8080)"
```

### Step 7: Verify Installation

**Test health endpoint:**
```bash
curl http://localhost:5000/api/health
```

**Expected response:**
```json
{"status":"healthy"}
```

**Test login:**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pass123"}'
```

**Expected response:**
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

## Testing

### Run Test Suite

**All tests:**
```bash
pytest tests/ -v
```

**With coverage report:**
```bash
pytest tests/ --cov=src --cov-report=html
```

**Specific test file:**
```bash
pytest tests/test_auth.py -v
```

**Expected results:**
- 33 tests should pass
- Code coverage: ~92%

### View Coverage Report

```bash
# Generate HTML report
pytest tests/ --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Change default admin password
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=0`
- [ ] Use HTTPS/TLS encryption
- [ ] Configure firewall rules
- [ ] Set up regular database backups
- [ ] Implement rate limiting
- [ ] Use a production WSGI server (Gunicorn, uWSGI)

### Using Gunicorn (Production Server)

**Install Gunicorn:**
```bash
pip install gunicorn
```

**Run with Gunicorn:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 src.app:app
```

**Options:**
- `-w 4` - 4 worker processes
- `-b 0.0.0.0:5000` - Bind to all interfaces on port 5000
- `--timeout 120` - 120 second timeout
- `--access-logfile access.log` - Log access requests

### Using systemd (Linux)

Create `/etc/systemd/system/gemmapy.service`:

```ini
[Unit]
Description=GemmaPy API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/GemmaPy
Environment="PATH=/path/to/GemmaPy/venv/bin"
ExecStart=/path/to/GemmaPy/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 src.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable gemmapy
sudo systemctl start gemmapy
sudo systemctl status gemmapy
```

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/gemmapy`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/gemmapy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Troubleshooting

### Common Issues

#### 1. Module Not Found Error

**Error:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. Database Locked

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Stop all running instances
pkill -f "python.*app.py"

# Remove database and reinitialize
rm gemmapy.db
python src/init_db.py
```

#### 3. Port Already in Use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Kill the process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Or use a different port
python -c "from src.app import app; app.run(port=8080)"
```

#### 4. Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'gemmapy.db'
```

**Solution:**
```bash
# Fix file permissions
chmod 644 gemmapy.db
chmod 755 .

# Or run with sudo (not recommended)
sudo python src/app.py
```

#### 5. Import Errors in Tests

**Error:**
```
ImportError: cannot import name 'app' from 'app'
```

**Solution:**
```bash
# Ensure you're in the project root
cd /path/to/GemmaPy

# Run tests from project root
pytest tests/ -v
```

### Getting Help

1. **Check logs:**
   ```bash
   # View recent logs
   tail -f /var/log/gemmapy.log
   ```

2. **Enable debug mode:**
   ```python
   # In src/app.py
   app.run(debug=True)
   ```

3. **Run with verbose output:**
   ```bash
   python -v src/app.py
   ```

4. **Open an issue:**
   - Check existing issues on GitHub
   - Provide error messages and system info
   - Include steps to reproduce

### System Information

**Check your setup:**
```bash
python --version
pip --version
pip list | grep -E "Flask|bcrypt|PyJWT"
ls -la gemmapy.db
```

## Next Steps

After successful installation:

1. **Read the API documentation:** [API_DOCS.md](API_DOCS.md)
2. **Change default admin password**
3. **Create additional user accounts**
4. **Explore the API endpoints**
5. **Run the test suite**

## Additional Resources

- [README.md](README.md) - Project overview
- [API_DOCS.md](API_DOCS.md) - Complete API reference
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [LICENSE](LICENSE) - MIT License

---

**Setup Complete! 🎉**

Your GemmaPy API is now ready to use at http://localhost:5000
