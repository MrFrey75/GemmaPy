# Quick Reference Guide

## File Organization

```
🗂️ webapp/
├── 📖 README.md                          - Main documentation
├── 🚀 GETTING_STARTED.md                 - Quick start guide
├── 🏗️ ARCHITECTURE.md                    - Technical architecture
├── 🚢 DEPLOYMENT.md                      - Production deployment
├── 📋 IMPLEMENTATION_SUMMARY.md          - This implementation summary
│
├── 🎨 frontend/                          - React application
│   ├── 📦 package.json                   - Dependencies
│   ├── ⚙️ vite.config.js                 - Build config
│   ├── 🎯 tailwind.config.js             - Tailwind config
│   ├── 📬 postcss.config.js              - PostCSS config
│   ├── 📝 tsconfig.json                  - TypeScript config
│   ├── 🔐 .env.example                   - Environment template
│   │
│   ├── 📂 src/
│   │   ├── 🔌 services/                  - API Integration
│   │   │   ├── api.js                    ← API client
│   │   │   ├── auth.js
│   │   │   ├── conversation.js
│   │   │   ├── ollama.js
│   │   │   ├── rag.js
│   │   │   ├── comparison.js
│   │   │   ├── metrics.js
│   │   │   ├── profile.js
│   │   │   └── admin.js
│   │   │
│   │   ├── ⚓ context/                   - React State
│   │   │   ├── AuthContext.jsx
│   │   │   └── NotificationContext.jsx
│   │   │
│   │   ├── 🪝 hooks/                    - Custom Hooks
│   │   │   ├── useAuth.js               ← User authentication
│   │   │   ├── useApi.js                ← API calls
│   │   │   ├── useNotification.js       ← Toasts
│   │   │   └── useLocalStorage.js       ← Persistence
│   │   │
│   │   ├── 📄 components/               - UI Components
│   │   │   ├── Header.jsx               ← Navigation
│   │   │   ├── ProtectedRoute.jsx       ← Route protection
│   │   │   └── NotificationContainer.jsx ← Toast display
│   │   │
│   │   ├── 📖 pages/                    - Pages
│   │   │   ├── LoginPage.jsx            ← Login screen
│   │   │   └── HomePage.jsx             ← Dashboard
│   │   │
│   │   ├── 🎨 styles/
│   │   │   └── globals.css              ← Global styles
│   │   │
│   │   ├── App.jsx                      ← Main component
│   │   └── index.jsx                    ← Entry point
│   │
│   └── 📂 public/
│       └── index.html                   ← HTML template
│
├── 🐍 backend/                          - Optional proxy
│   ├── server.py
│   ├── requirements.txt
│   └── README.md
│
├── 🐳 Dockerfile                        - Frontend container
├── 🐳 docker-compose.yml                - Full stack container
└── .gitignore
```

## Common Tasks

### Starting Development

```bash
cd webapp/frontend
npm install
npm run dev
# → http://localhost:3000
```

### Environment Setup

```bash
cp .env.example .env.local
# Edit VITE_API_URL=http://localhost:5000
```

### Building for Production

```bash
npm run build
# → Creates optimized dist/ folder
```

### Testing Locally

```bash
# Terminal 1: API
cd .. && python src/app.py

# Terminal 2: Frontend
npm run dev

# Terminal 3: Ollama
ollama serve
```

### Using Services

```javascript
// Import service
import { conversationService } from '../services/conversation';

// Call method
const conversations = await conversationService.list();

// With error handling
try {
  const result = await conversationService.create('My Chat');
  success('Created!');
} catch (error) {
  error('Failed: ' + error.message);
}
```

### Using Hooks

```javascript
// Authentication
const { user, isAdmin, login, logout } = useAuth();

// API calls with loading state
const { data, loading, error, execute } = useApi(apiFunction);
await execute(args);

// Notifications
const { success, error, warning, info } = useNotification();
success('Done!');

// Local storage
const [value, setValue, remove] = useLocalStorage('key', defaultValue);
```

### Adding a New Page

1. Create file: `src/pages/MyPage.jsx`
2. Export component:
   ```jsx
   export const MyPage = () => <div>Content</div>;
   ```
3. Add to `App.jsx`:
   ```jsx
   <Route path="/mypage" element={<ProtectedRoute><Header /><MyPage /></ProtectedRoute>} />
   ```
4. Add link in `Header.jsx`:
   ```jsx
   <Link to="/mypage">My Page</Link>
   ```

## API Patterns

### List Endpoint

```javascript
// Service
async list(limit = 50) {
  const response = await apiClient.get('/api/endpoint', { 
    params: { limit } 
  });
  return response.data.items;
}

// Component
const { data: items, execute } = useApi(service.list);
const results = await execute(20);
```

### Create Endpoint

```javascript
// Service
async create(data) {
  const response = await apiClient.post('/api/endpoint', data);
  return response.data;
}

// Component
const { execute } = useApi(service.create);
const result = await execute({ name: 'value' });
```

### Update Endpoint

```javascript
// Service
async update(id, data) {
  const response = await apiClient.put(`/api/endpoint/${id}`, data);
  return response.data;
}

// Component
const result = await execute(1, { name: 'new value' });
```

### Delete Endpoint

```javascript
// Service
async delete(id) {
  const response = await apiClient.delete(`/api/endpoint/${id}`);
  return response.data;
}

// Component
const result = await execute(1);
```

## Error Handling

### API Errors

```javascript
try {
  await apiCall();
} catch (error) {
  const message = error.response?.data?.error || error.message;
  error(message);
}
```

### 401 Errors

Automatically handled by interceptor - redirects to login.

### Network Errors

```javascript
if (error.code === 'ECONNABORTED') {
  error('Request timeout');
} else if (!error.response) {
  error('Network error');
}
```

## Styling Guide

### Using Tailwind

```jsx
<div className="flex items-center justify-center min-h-screen bg-gray-50">
  <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
    Click
  </button>
</div>
```

### Common Classes

```
Flexbox:       flex, items-center, justify-center, gap-4
Spacing:       p-4, m-4, mt-2, px-6, py-2
Colors:        bg-blue-600, text-white, border-gray-300
Sizing:        w-full, h-auto, min-h-screen
Positioning:   fixed, absolute, relative, sticky
Display:       block, inline, grid, hidden
Responsive:    md:, lg:, sm:
Transitions:   hover:, transition, duration-200
```

## Deployment Options

### Local Development

```bash
npm run dev
```

### Build for Production

```bash
npm run build
# dist/ ready to deploy
```

### Docker

```bash
docker build -f Dockerfile -t gemmapp-web .
docker run -p 3000:3000 -e VITE_API_URL=http://api:5000 gemmapp-web
```

### Docker Compose (Full Stack)

```bash
docker-compose up -d
# Starts: Frontend (3000), API (5000), Ollama (11434)
```

### Vercel

1. Push to GitHub
2. Connect to Vercel
3. Set `VITE_API_URL` environment variable
4. Deploy

## Debugging Tips

### Check Console

```
F12 → Console tab
Look for error messages
```

### Network Tab

```
F12 → Network tab
Check API requests
View response status and data
```

### DevTools Application

```
F12 → Application tab
Check localStorage (token, user)
Check cookies
```

### React DevTools

```
Install React DevTools browser extension
Inspect component props and state
```

### API Testing

```bash
# Test API connection
curl http://localhost:5000/api/health

# Test with authentication
curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/profile
```

## Performance Tips

1. **Lazy Load Components**
   ```javascript
   const ChatPage = lazy(() => import('./pages/ChatPage'));
   ```

2. **Memoize Components**
   ```javascript
   export const Item = memo(({ data }) => <div>{data}</div>);
   ```

3. **Debounce Search**
   ```javascript
   const debouncedSearch = useDebounce(searchTerm, 300);
   ```

4. **Virtual Scrolling**
   ```javascript
   // For long lists use react-window
   ```

5. **Image Optimization**
   ```javascript
   // Lazy load images
   <img loading="lazy" src="..." />
   ```

## Security Best Practices

1. ✅ Never commit `.env.local`
2. ✅ Don't log sensitive data
3. ✅ Validate all inputs
4. ✅ Use HTTPS in production
5. ✅ Keep dependencies updated
6. ✅ Use httpOnly cookies (future)
7. ✅ Implement CSRF protection
8. ✅ Set secure headers

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API Connection Error | Check VITE_API_URL, ensure API is running |
| 401 Errors | Clear localStorage, login again |
| CORS Issues | Check API CORS configuration |
| Build Fails | Run `npm ci`, check Node version |
| Styling Not Applied | Refresh page, check class names |
| Module Not Found | Run `npm install`, check imports |

## Useful Commands

```bash
# Install dependencies
npm install

# Start development
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Check for updates
npm outdated

# Update dependencies
npm update

# Clear cache
rm -rf node_modules package-lock.json
npm install
```

## File Size Limits

- **Bundle**: < 100KB gzipped (target)
- **Image**: < 100KB each (optimize before upload)
- **API Timeout**: 30 seconds (configurable)
- **Local Storage**: ~5-10MB limit

## Browser Support

| Browser | Version |
|---------|---------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |
| Mobile Chrome | Latest |
| Mobile Safari | 14+ |

## Resources

- [React Docs](https://react.dev)
- [Vite Docs](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [React Router](https://reactrouter.com)
- [Axios](https://axios-http.com)
- [GemmaPy API Docs](../API_DOCS.md)

---

**Quick Links**
- 🚀 Start: `npm run dev`
- 📚 Docs: Read GETTING_STARTED.md
- 🐳 Deploy: See DEPLOYMENT.md
- 🏗️ Architecture: See ARCHITECTURE.md

**Last Updated**: October 29, 2025
