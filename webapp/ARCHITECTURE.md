# Frontend Architecture

## Overview

The GemmaPy WebApp frontend is built with React and follows a modular, service-oriented architecture to ensure scalability and maintainability.

## Architecture Layers

### 1. Presentation Layer (UI Components)

Located in `src/components/` and `src/pages/`

- **Components**: Reusable UI elements
  - `Header.jsx` - Navigation and user menu
  - `ProtectedRoute.jsx` - Route protection wrapper
  - `NotificationContainer.jsx` - Toast notifications
  
- **Pages**: Full-page components
  - `LoginPage.jsx` - Authentication
  - `HomePage.jsx` - Dashboard
  - Add more pages as needed

### 2. State Management Layer

Located in `src/context/` and `src/hooks/`

**Context Providers:**
- `AuthContext` - User authentication and session
- `NotificationContext` - Toast notifications

**Custom Hooks:**
- `useAuth()` - Access authentication state
- `useApi()` - API calls with loading/error handling
- `useNotification()` - Show notifications
- `useLocalStorage()` - Persist data locally

### 3. Service Layer (API Integration)

Located in `src/services/`

Each service handles specific API domain:

- `api.js` - Base axios client with interceptors
- `auth.js` - Authentication operations
- `conversation.js` - Conversation management
- `ollama.js` - LLM/model operations
- `rag.js` - RAG document management
- `comparison.js` - Model comparison
- `metrics.js` - Analytics and metrics
- `profile.js` - User profile management
- `admin.js` - Admin operations

## Data Flow

```
User Interaction
       ↓
Component (e.g., LoginPage.jsx)
       ↓
Custom Hook (e.g., useAuth)
       ↓
Service Layer (e.g., authService.login())
       ↓
API Client (Axios)
       ↓
Backend API
       ↓
Response
       ↓
State Update (Context)
       ↓
Re-render Component
```

## Communication Patterns

### 1. Direct API Call

```javascript
import { conversationService } from '../services/conversation';

const conversations = await conversationService.list();
```

### 2. Using useApi Hook

```javascript
const { data, loading, error, execute } = useApi(
  conversationService.list
);

const handleClick = async () => {
  try {
    await execute();
  } catch (err) {
    console.error(err);
  }
};
```

### 3. Using Context

```javascript
const { user, token } = useAuth();
const { success, error } = useNotification();
```

## Error Handling

### API Errors

All API calls are wrapped with error handling:

```javascript
try {
  const result = await apiService.method();
} catch (error) {
  const message = error.response?.data?.error || error.message;
  // Handle error
}
```

### 401 Unauthorized

Automatically clears token and redirects to login:

```javascript
// In api.js interceptor
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## Authentication Flow

1. User enters credentials on `LoginPage`
2. `useAuth().login()` calls `authService.login()`
3. API returns token and user info
4. Token stored in `localStorage`
5. Token added to all subsequent requests via axios interceptor
6. User redirected to home page
7. On logout, token cleared and user redirected to login

## Component Structure

### Functional Components Only

All components are functional and use hooks:

```javascript
// ✅ Good
export const MyComponent = () => {
  const [state, setState] = useState(null);
  const { user } = useAuth();
  
  return <div>{user?.username}</div>;
};

// ❌ Bad - Class components
class MyComponent extends React.Component {
  render() {
    return <div>...</div>;
  }
}
```

### Props Drilling Prevention

Use Context API to avoid prop drilling:

```javascript
// ✅ Good - Using Context
const { user } = useAuth();

// ❌ Bad - Prop drilling
<Component1 user={user}>
  <Component2 user={user}>
    <Component3 user={user} />
  </Component2>
</Component1>
```

## Styling Architecture

### Tailwind CSS First

Use Tailwind classes for styling:

```jsx
<div className="flex items-center justify-center min-h-screen bg-gray-50">
  <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
    Click Me
  </button>
</div>
```

### CSS Modules (Optional)

For component-specific styles:

```css
/* MyComponent.module.css */
.container {
  display: flex;
  align-items: center;
}
```

```javascript
import styles from './MyComponent.module.css';

export const MyComponent = () => (
  <div className={styles.container}>...</div>
);
```

### Global Styles

In `src/styles/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

## Performance Optimization

### Code Splitting

```javascript
import { lazy, Suspense } from 'react';

const ChatPage = lazy(() => import('./pages/ChatPage'));

<Suspense fallback={<Loading />}>
  <ChatPage />
</Suspense>
```

### Memoization

```javascript
import { memo } from 'react';

export const MessageItem = memo(({ message }) => {
  return <div>{message.content}</div>;
});
```

### Virtual Scrolling

For long lists:

```javascript
// Use react-window for large lists
import { FixedSizeList } from 'react-window';
```

## API Request Optimization

### Request Debouncing

```javascript
import { useState, useEffect } from 'react';

const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};
```

### Response Caching

The API service handles caching via Ollama's built-in cache.

### Request Cancellation

```javascript
const cancelToken = axios.CancelToken.source();

try {
  await apiClient.get('/endpoint', { cancelToken: cancelToken.token });
} catch (error) {
  if (axios.isCancel(error)) {
    console.log('Request cancelled');
  }
}
```

## Testing Strategy

### Unit Tests

Test individual functions:

```javascript
// services/auth.test.js
describe('authService', () => {
  it('should parse login response', () => {
    const response = { token: 'abc', user: { id: 1 } };
    expect(response.token).toBe('abc');
  });
});
```

### Component Tests

Test component behavior:

```javascript
// components/Button.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('should call onClick when clicked', () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(onClick).toHaveBeenCalled();
  });
});
```

### E2E Tests

Test user flows:

```javascript
// e2e/login.spec.js
describe('Login Flow', () => {
  it('should login and redirect to home', () => {
    cy.visit('/login');
    cy.get('[name=username]').type('admin');
    cy.get('[name=password]').type('pass123');
    cy.get('button').click();
    cy.url().should('eq', '/');
  });
});
```

## Deployment Architecture

### Development
```
npm run dev → Vite dev server → localhost:3000
```

### Production
```
npm run build → dist/ folder → Serve static files
```

### Environment Separation

```
Development: .env.local
Production: .env.production
```

## Security Considerations

1. **Token Storage**: Stored in localStorage (vulnerable to XSS)
   - Better: httpOnly cookies
   - Current: Accept this limitation for now

2. **CORS**: API should only allow frontend domain
   - Configure CORS on backend

3. **Input Validation**: Validate all user inputs
   - Use libraries like `zod` or `yup`

4. **Sensitive Data**: Never log passwords or tokens

5. **HTTPS**: Always use HTTPS in production

## Monitoring & Analytics

### Error Logging

```javascript
const logError = (error, context) => {
  console.error(`[${context}]`, error);
  // Send to error tracking service (e.g., Sentry)
};
```

### Performance Monitoring

```javascript
const startTime = performance.now();
// Do work
const duration = performance.now() - startTime;
console.log(`Operation took ${duration}ms`);
```

## Future Enhancements

1. **State Management**: Consider Redux for complex state
2. **Real-time Updates**: Implement WebSocket for live updates
3. **Offline Support**: Add Service Workers for offline functionality
4. **PWA Features**: Make it a Progressive Web App
5. **Mobile App**: Use React Native for mobile
6. **Testing**: Increase test coverage
7. **Accessibility**: Improve WCAG compliance
8. **Analytics**: Add user analytics tracking

---

**Last Updated**: October 29, 2025
