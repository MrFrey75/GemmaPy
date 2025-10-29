# GemmaPy WebApp - Documentation Index

Welcome to the GemmaPy WebApp documentation. Start here to understand the structure and get up and running.

## 📋 Documentation Files

### Getting Started (Read First!)
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Installation, setup, and first steps
  - Prerequisites and dependencies
  - Step-by-step installation
  - Default credentials
  - Verifying API connection

### Main Documentation  
- **[README.md](README.md)** - Project overview and features
  - Feature list
  - Project structure
  - Technology stack
  - Quick start guide

### Technical Documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture and patterns
  - Architecture layers
  - Data flow diagrams
  - Communication patterns
  - Security considerations
  - Design patterns used

### Deployment Guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment options
  - Vercel deployment
  - Docker deployment
  - Docker Compose
  - Traditional server
  - Performance optimization
  - Monitoring & logging

### Reference Materials
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference guide
  - Common tasks and commands
  - Code snippets
  - API patterns
  - Debugging tips
  - Troubleshooting

### Implementation Details
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Detailed implementation
  - Project structure breakdown
  - Files created
  - Features implemented
  - API endpoints covered
  - Technology choices

### This File
- **[INDEX.md](INDEX.md)** - Documentation index (you are here)

---

## 🚀 Quick Navigation

### I want to...

**Get started developing**
→ Read [GETTING_STARTED.md](GETTING_STARTED.md)

**Understand the architecture**
→ Read [ARCHITECTURE.md](ARCHITECTURE.md)

**Look up common tasks**
→ Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Deploy to production**
→ Read [DEPLOYMENT.md](DEPLOYMENT.md)

**See what was created**
→ Read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

**Find API endpoint examples**
→ See `api.js` in `src/services/`

---

## 📁 Project Structure Overview

```
webapp/
├── frontend/                    # React application
│   ├── src/
│   │   ├── services/           # API integration (9 files)
│   │   ├── hooks/              # Custom React hooks (4 files)
│   │   ├── context/            # State management (2 files)
│   │   ├── components/         # UI components (3 files)
│   │   ├── pages/              # Page components (2 files)
│   │   └── styles/             # CSS styles
│   │
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   └── tsconfig.json
│
├── backend/                     # Optional proxy server
├── Dockerfile                   # Container image
├── docker-compose.yml           # Full stack
└── Documentation/               # You are here
```

---

## 🎯 Key Files Explained

### Services (`src/services/`)
These handle all API communication:
- **api.js** - Base Axios client with interceptors
- **auth.js** - Authentication operations
- **conversation.js** - Conversation management
- **ollama.js** - LLM model operations
- **rag.js** - Document RAG
- **comparison.js** - Model comparison
- **metrics.js** - Analytics
- **profile.js** - User profiles
- **admin.js** - Admin operations

### Hooks (`src/hooks/`)
Reusable logic:
- **useAuth** - Access authentication state
- **useApi** - Make API calls with loading/error handling
- **useNotification** - Show toast notifications
- **useLocalStorage** - Persist data locally

### Context (`src/context/`)
Global state:
- **AuthContext** - User authentication state
- **NotificationContext** - Toast notifications

### Components (`src/components/`)
Reusable UI:
- **Header** - Navigation and user menu
- **ProtectedRoute** - Route protection wrapper
- **NotificationContainer** - Toast display

### Pages (`src/pages/`)
Full pages:
- **LoginPage** - Authentication
- **HomePage** - Dashboard

---

## 💻 Development Workflow

### 1. Install & Start
```bash
cd frontend
npm install
npm run dev
```

### 2. Access Application
```
http://localhost:3000
```

### 3. Default Login
```
Username: admin
Password: pass123
```

### 4. Start Building
- Create new pages in `src/pages/`
- Add routes in `src/App.jsx`
- Use services for API calls
- Use hooks for state management

---

## 🔌 API Integration Examples

### Making an API Call
```javascript
import { conversationService } from '../services/conversation';

const conversations = await conversationService.list();
```

### With Loading State
```javascript
import { useApi } from '../hooks/useApi';

const { data, loading, error, execute } = useApi(
  conversationService.list
);

await execute();
```

### With Error Handling
```javascript
import { useNotification } from '../hooks/useNotification';

const { success, error } = useNotification();

try {
  await conversationService.create('My Chat');
  success('Created!');
} catch (err) {
  error('Failed: ' + err.message);
}
```

---

## 🚢 Deployment

### Local Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
# Creates optimized dist/ folder
```

### Docker
```bash
docker build -f Dockerfile -t gemmapp-web .
docker run -p 3000:3000 -e VITE_API_URL=http://api:5000 gemmapp-web
```

### Docker Compose (Full Stack)
```bash
docker-compose up -d
```

### Vercel (Recommended)
1. Push to GitHub
2. Connect to Vercel
3. Set environment variables
4. Deploy

See [DEPLOYMENT.md](DEPLOYMENT.md) for more options.

---

## 📚 Learning Path

1. **Start Here**
   - Read [GETTING_STARTED.md](GETTING_STARTED.md)
   - Get development environment running
   - Log in and explore dashboard

2. **Understand Architecture**
   - Read [ARCHITECTURE.md](ARCHITECTURE.md)
   - Review `src/services/api.js`
   - Understand hooks and context

3. **Build Your First Feature**
   - Create a new page in `src/pages/`
   - Import and use a service
   - Use hooks for state management
   - Add to routes in `App.jsx`

4. **Common Tasks**
   - Reference [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
   - Copy code snippets
   - Apply patterns

5. **Deploy**
   - Read [DEPLOYMENT.md](DEPLOYMENT.md)
   - Choose deployment option
   - Deploy to production

---

## 🔍 Troubleshooting

### API Connection Issues
→ Check `VITE_API_URL` in `.env.local`
→ Verify API is running: `curl http://localhost:5000/api/health`

### Module Not Found
→ Run `npm install`
→ Check import paths

### Port Already in Use
→ Change port in `vite.config.js`
→ Or kill process using port 3000

### Styling Issues
→ Refresh page
→ Verify Tailwind classes are correct

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for more troubleshooting.

---

## 🆘 Getting Help

1. **Check Documentation**
   - Read the relevant documentation file
   - Search for your topic

2. **Check Quick Reference**
   - Common tasks are documented
   - Code snippets provided

3. **Check API Docs**
   - See `API_DOCS.md` in project root
   - View available endpoints

4. **Check Code Examples**
   - Review existing services
   - Look at component examples

---

## 🎓 Topics by Experience Level

### Beginner
- Read GETTING_STARTED.md
- Run `npm run dev`
- Explore existing pages
- Use QUICK_REFERENCE.md for common tasks

### Intermediate
- Read ARCHITECTURE.md
- Create a new page
- Use services for API calls
- Implement error handling

### Advanced
- Add new services
- Implement complex state management
- Optimize performance
- Deploy to production

---

## 📞 Support Resources

- **API Documentation**: See `API_DOCS.md` in project root
- **React Docs**: https://react.dev
- **Vite Docs**: https://vitejs.dev
- **Tailwind CSS**: https://tailwindcss.com
- **Axios**: https://axios-http.com

---

## ✅ Checklist

- [ ] Read GETTING_STARTED.md
- [ ] Install dependencies: `npm install`
- [ ] Create .env.local from template
- [ ] Start dev server: `npm run dev`
- [ ] Open http://localhost:3000
- [ ] Log in with admin/pass123
- [ ] Explore the app
- [ ] Read ARCHITECTURE.md
- [ ] Create your first page
- [ ] Deploy when ready

---

## 📝 File Summary

| File | Purpose |
|------|---------|
| README.md | Project overview |
| GETTING_STARTED.md | Installation & setup |
| ARCHITECTURE.md | Technical design |
| DEPLOYMENT.md | Production deployment |
| QUICK_REFERENCE.md | Common tasks |
| IMPLEMENTATION_SUMMARY.md | What was created |
| INDEX.md | This file |

---

## 🔗 Related Resources

- **Backend API**: See parent directory's `src/app.py`
- **API Documentation**: See parent directory's `API_DOCS.md`
- **Database Schema**: See parent directory's `src/database.py`
- **Ollama Integration**: See parent directory's `src/ollama_manager.py`

---

**Last Updated**: October 29, 2025
**Version**: 1.0.0
**Status**: ✅ Ready for Development

---

**Need help?** Start with [GETTING_STARTED.md](GETTING_STARTED.md)
