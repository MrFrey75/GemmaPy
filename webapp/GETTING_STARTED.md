# Getting Started with GemmaPy WebApp

This guide will help you get the GemmaPy WebApp up and running.

## Prerequisites

- Node.js 16+ and npm
- GemmaPy API running on `http://localhost:5000`
- Ollama service running (for model inference)

## Installation

### 1. Clone the Repository

```bash
cd /path/to/GemmaPy
cd webapp/frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Create a `.env.local` file based on `.env.example`:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration:

```
VITE_API_URL=http://localhost:5000
VITE_API_TIMEOUT=30000
VITE_LOG_LEVEL=info
VITE_ENABLE_RAG=true
VITE_ENABLE_COMPARISON=true
VITE_ENABLE_METRICS=true
```

### 4. Start Development Server

```bash
npm run dev
```

The application will open at `http://localhost:3000`

## First Steps

### Default Login Credentials

The GemmaPy API comes with a default admin account:

- **Username**: `admin`
- **Password**: `pass123`

Use these to log in initially.

### Verify API Connection

After logging in, you should see the home dashboard. If you encounter connection errors:

1. Check that the API is running: `curl http://localhost:5000/api/health`
2. Verify environment variables are set correctly
3. Check browser console for errors (F12)
4. Check network tab to see API requests

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── Header.jsx
│   │   ├── ProtectedRoute.jsx
│   │   └── NotificationContainer.jsx
│   │
│   ├── pages/              # Page components
│   │   ├── LoginPage.jsx
│   │   └── HomePage.jsx
│   │
│   ├── services/           # API integration
│   │   ├── api.js          # Base axios client
│   │   ├── auth.js         # Authentication
│   │   ├── conversation.js # Conversations
│   │   ├── ollama.js       # LLM operations
│   │   ├── rag.js          # RAG operations
│   │   ├── comparison.js   # Model comparison
│   │   ├── metrics.js      # Metrics/analytics
│   │   ├── profile.js      # User profile
│   │   └── admin.js        # Admin operations
│   │
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.js
│   │   ├── useApi.js
│   │   ├── useNotification.js
│   │   └── useLocalStorage.js
│   │
│   ├── context/            # React Context providers
│   │   ├── AuthContext.jsx
│   │   └── NotificationContext.jsx
│   │
│   ├── styles/             # Styling
│   │   └── globals.css
│   │
│   ├── App.jsx             # Main app component
│   └── index.jsx           # Entry point
│
├── public/
│   └── index.html
│
├── vite.config.js          # Vite configuration
├── tailwind.config.js      # Tailwind CSS config
├── postcss.config.js       # PostCSS config
├── package.json
└── .env.example            # Environment template
```

## Building Features

### Authentication

The app uses JWT tokens stored in `localStorage`. The `useAuth` hook provides:

```javascript
const { user, token, isAuthenticated, isAdmin, login, logout } = useAuth();
```

### API Calls

Use the service layer for all API calls:

```javascript
import { conversationService } from '../services/conversation';

const conversations = await conversationService.list();
```

### Loading States

Use the `useApi` hook for handling API calls with loading/error states:

```javascript
const { data, loading, error, execute } = useApi(myApiFunction);

const result = await execute(args);
```

### Notifications

Use the `useNotification` hook:

```javascript
const { success, error, warning, info } = useNotification();

success('Operation completed!');
error('Something went wrong');
```

### Protected Routes

Wrap pages with `ProtectedRoute`:

```jsx
<Route
  path="/protected"
  element={
    <ProtectedRoute>
      <MyPage />
    </ProtectedRoute>
  }
/>
```

## Adding New Pages

1. Create a new component in `src/pages/`
2. Add the route in `src/App.jsx`
3. Add navigation link in `src/components/Header.jsx`

Example:

```jsx
// src/pages/MyNewPage.jsx
import React from 'react';

export const MyNewPage = () => {
  return <div>My New Page</div>;
};
```

```jsx
// src/App.jsx - Add to Routes
<Route
  path="/my-page"
  element={
    <ProtectedRoute>
      <>
        <Header />
        <MyNewPage />
      </>
    </ProtectedRoute>
  }
/>
```

## Common Tasks

### Getting User Data

```javascript
import { useAuth } from './hooks/useAuth';

function MyComponent() {
  const { user, isAdmin } = useAuth();
  
  return (
    <div>
      <p>Hello, {user?.username}</p>
      {isAdmin && <p>You are an admin</p>}
    </div>
  );
}
```

### Making API Calls

```javascript
import { useApi } from './hooks/useApi';
import { conversationService } from './services/conversation';

function MyComponent() {
  const { data, loading, error, execute } = useApi(
    conversationService.list
  );

  return (
    <button onClick={() => execute()}>
      {loading ? 'Loading...' : 'Load Conversations'}
    </button>
  );
}
```

### Showing Notifications

```javascript
import { useNotification } from './hooks/useNotification';

function MyComponent() {
  const { success, error } = useNotification();

  const handleAction = async () => {
    try {
      await doSomething();
      success('Success!');
    } catch (err) {
      error('Failed: ' + err.message);
    }
  };

  return <button onClick={handleAction}>Do Action</button>;
}
```

## Building for Production

```bash
npm run build
```

Output files will be in `dist/` directory.

### Deploy to Vercel

1. Push your code to GitHub
2. Connect GitHub repo to Vercel
3. Set environment variables
4. Deploy

### Deploy to Traditional Server

```bash
npm run build
npm install -g serve
serve -s dist -l 3000
```

## Troubleshooting

### "Cannot find module" errors

```bash
rm -rf node_modules
npm install
```

### API Connection Errors

1. Check API URL in `.env.local`
2. Verify API is running: `curl http://localhost:5000/api/health`
3. Check for CORS issues in browser console
4. Ensure `Authorization` header is being sent

### Authentication Issues

1. Clear browser localStorage: Open DevTools → Application → Local Storage → Clear
2. Log in again
3. Check network requests to verify token is being sent

### Styling Issues

```bash
npm run dev
```

And refresh the page. Tailwind CSS watches for file changes.

## Next Steps

1. **Create Chat Page**: Implement the chat interface using `ollamaService`
2. **Implement Conversations**: Build conversation management using `conversationService`
3. **Add RAG Support**: Implement document upload and search
4. **Model Comparison**: Create comparison interface
5. **Metrics Dashboard**: Display usage metrics
6. **Admin Panel**: Implement admin features

## Resources

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [React Router Documentation](https://reactrouter.com)
- [Axios Documentation](https://axios-http.com)

## Support

For issues or questions:

1. Check existing GitHub issues
2. Review the API documentation in `API_DOCS.md`
3. Check browser console for error messages
4. Contact the GemmaPy team

---

**Last Updated**: October 29, 2025
