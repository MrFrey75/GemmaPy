# GemmaPy

**Production-ready Python REST API with advanced LLM integration**

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](VERSION)
[![Tests](https://img.shields.io/badge/tests-218%20passing-success)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Version 1.0.0** - Released October 29, 2025

A comprehensive REST API featuring JWT authentication, role-based access control, and extensive Ollama/LLM integration with caching, retry logic, RAG, metrics tracking, and multi-model comparison.

## ✨ Features

### 🔐 Core API
- JWT authentication with bcrypt password hashing
- Role-based access control (User/Admin)
- User profile management
- SQLite database with auto-initialization
- RESTful endpoints (GET/POST/PUT/DELETE)
- CORS support

### 🤖 LLM Integration (4 Phases Complete)

**Phase 1 - Foundation:**
- ⚡ Response caching with TTL
- 🔁 Auto-retry with model fallbacks
- 📚 RAG (Retrieval Augmented Generation)

**Phase 2 - Analytics:**
- 📊 Performance metrics tracking
- 💰 Cost tracking per user/model
- 📈 Analytics dashboard
- ⭐ User ratings

**Phase 3 - User Features:**
- 💬 Conversation persistence
- 📝 Prompt template library (10+ templates)

**Phase 4 - Advanced:**
- 🔄 Multi-model comparison
- 📊 Model rankings & benchmarking
- 📉 Performance analytics

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python src/init_db.py

# 3. Start server
python src/app.py

# 4. Test API
curl http://localhost:5000/api/health
```

**Default Admin:** `admin` / `pass123` ⚠️ *Change in production!*

**Full setup guide:** [QUICKSTART.md](QUICKSTART.md) | [SETUP.md](SETUP.md)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [**Quick Start**](QUICKSTART.md) | Get started in 2 minutes |
| [**API Docs**](API_DOCS.md) | Complete API reference |
| [**Setup Guide**](SETUP.md) | Detailed installation |
| [**Developer Guide**](DEVELOPER_GUIDE.md) | Contributing & development |
| [**Testing Guide**](TESTING.md) | Running and writing tests |
| [**Ollama Guide**](OLLAMA_GUIDE.md) | LLM integration guide |
| [**Multi-Model Comparison**](MULTI_MODEL_COMPARISON.md) | Model comparison feature |

---

## 📡 API Overview

### Core Endpoints
- `POST /api/login` - Authentication
- `GET/PUT /api/profile` - Profile management
- `GET/POST /api/data` - Data operations

### LLM Features
- `POST /api/ollama/generate` - Text generation with caching
- `POST /api/ollama/chat` - Chat completions
- `POST /api/rag/generate` - RAG-powered generation
- `POST /api/compare/models` - Multi-model comparison

### Analytics
- `GET /api/metrics/dashboard` - Performance metrics
- `GET /api/costs/summary` - Cost tracking
- `GET /api/compare/rankings` - Model rankings

**Full API reference:** [API_DOCS.md](API_DOCS.md)

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

- ✅ 218 tests passing
- 📊 93%+ code coverage
- ⚡ ~75 seconds runtime

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│      Flask Application          │
├─────────────────────────────────┤
│  Auth │ Ollama │ Cache │ RAG   │
├─────────────────────────────────┤
│      SQLite Database            │
└─────────────────────────────────┘
```

**Key Components:**
- `app.py` - Main application & routes
- `auth.py` - JWT authentication
- `ollama_manager.py` - LLM integration
- `llm_cache.py` - Response caching
- `rag_manager.py` - RAG system
- `multi_model_comparator.py` - Model comparison

---

## 📦 Dependencies

```
Flask==3.0.0              # Web framework
PyJWT==2.8.0              # JWT tokens
bcrypt==4.1.2             # Password hashing
scikit-learn==1.3.2       # RAG similarity
pytest==7.4.3             # Testing
```

---

## 🚢 Deployment

### Production
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.app:app
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python src/init_db.py
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.app:app"]
```

---

## 🤝 Contributing

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for:
- Development setup
- Code structure
- Adding features
- Testing guidelines

Quick start:
```bash
git checkout -b feature/amazing-feature
# Make changes, add tests
pytest tests/ -v
git commit -m "Add amazing feature"
git push origin feature/amazing-feature
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🙏 Acknowledgments

Built with [Flask](https://flask.palletsprojects.com/), [Ollama](https://ollama.ai/), [bcrypt](https://github.com/pyca/bcrypt/), and [PyJWT](https://pyjwt.readthedocs.io/)

---

**⭐ Star this repo if you find it helpful!**

**Built with ❤️ using Python and Flask**

---

## 📋 Version Information

- **Current Version:** 1.0.0
- **Release Date:** October 29, 2025
- **Status:** Production Ready
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Release Notes:** [RELEASE.md](RELEASE.md)

