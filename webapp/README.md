# GemmaPy Web Application

A comprehensive web application for consuming the GemmaPy API. This webapp provides a user-friendly interface for interacting with local language models (Ollama), managing conversations, comparing models, and tracking usage metrics.

## Project Structure

```
webapp/
├── frontend/                 # React/Next.js frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API service layer
│   │   ├── hooks/           # Custom React hooks
│   │   ├── context/         # React context providers
│   │   ├── styles/          # Global styles and CSS modules
│   │   ├── App.jsx          # Main application component
│   │   └── index.jsx        # Application entry point
│   ├── public/              # Static assets
│   ├── package.json         # Frontend dependencies
│   └── .env.example         # Environment variables template
│
├── backend/                 # Optional backend proxy/extensions
│   ├── server.py            # Express-like middleware (optional)
│   └── requirements.txt      # Python dependencies
│
└── README.md                # This file
```

## Features

### Core Features
- **User Authentication**: JWT-based login/logout with token management
- **Profile Management**: View and edit user profiles
- **Conversation Management**: Create, manage, and search conversations
- **LLM Generation**: Generate text using Ollama models
- **Streaming Responses**: Real-time streaming for long-running tasks
- **Chat Interface**: Chat-based interaction with models

### Advanced Features
- **Model Comparison**: Compare responses from multiple models
- **RAG Integration**: Retrieve Augmented Generation for document-based Q&A
- **Prompt Templates**: Built-in and custom prompt templates
- **Metrics Dashboard**: Track API usage and performance
- **Cost Calculator**: Monitor and project API costs
- **LLM Caching**: Automatic response caching for efficiency
- **Admin Panel**: User management and system monitoring

## Quick Start

### Frontend Setup

```bash
cd webapp/frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local with your API configuration
# REACT_APP_API_URL=http://localhost:5000
# REACT_APP_API_TIMEOUT=30000

# Start development server
npm start
```

The frontend will be available at `http://localhost:3000`

### Backend Setup (Optional)

```bash
cd webapp/backend

# Create Python virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the proxy server
python server.py
```

## Environment Variables

### Frontend (.env.local)
```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_API_TIMEOUT=30000
REACT_APP_LOG_LEVEL=info
```

## API Integration

The webapp integrates with the GemmaPy API with the following endpoints:

### Authentication
- `POST /api/login` - User login
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update user profile
- `PUT /api/profile/password` - Change password
- `DELETE /api/profile` - Delete account

### Conversations
- `GET /api/conversations` - List conversations
- `POST /api/conversations` - Create conversation
- `GET /api/conversations/{id}` - Get conversation
- `POST /api/conversations/{id}/messages` - Add message
- `POST /api/conversations/{id}/generate` - Generate response

### Ollama/LLM
- `GET /api/ollama/models` - List available models
- `POST /api/ollama/generate` - Generate text
- `POST /api/ollama/generate/stream` - Stream generation
- `POST /api/ollama/chat` - Chat completion
- `POST /api/ollama/chat/stream` - Stream chat

### Model Comparison
- `POST /api/compare/models` - Compare multiple models
- `GET /api/compare/comparisons` - List comparisons
- `GET /api/compare/rankings` - Get model rankings

### RAG (Retrieval Augmented Generation)
- `POST /api/rag/documents` - Add document
- `GET /api/rag/documents` - List documents
- `POST /api/rag/search` - Search documents
- `POST /api/rag/generate` - Generate with RAG context

### Metrics & Costs
- `GET /api/metrics/dashboard` - Get metrics dashboard
- `GET /api/costs/summary` - Get cost summary

### Admin
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create user

## Frontend Technology Stack

- **React 18+** - UI library
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Context API** - State management
- **React Query** - Server state management (optional)
- **React Hook Form** - Form management (optional)

## Key Components

### Authentication
- `LoginPage` - User login form
- `ProfilePage` - User profile management
- `ProtectedRoute` - Route protection wrapper

### Chat & Conversation
- `ConversationList` - List of user conversations
- `ChatInterface` - Main chat component
- `MessageList` - Display conversation messages
- `MessageInput` - User message input form

### Model Management
- `ModelSelector` - Select LLM model
- `ModelComparison` - Compare multiple models
- `ModelInfo` - Display model information

### RAG & Documents
- `DocumentUpload` - Upload documents
- `DocumentList` - List user documents
- `RAGSearch` - Search documents

### Metrics & Admin
- `MetricsDashboard` - Display usage metrics
- `AdminPanel` - Admin user management
- `CostTracker` - Display cost information

## Service Layer

All API calls are abstracted through services:

```
services/
├── api.js              # Base API client
├── auth.js             # Authentication service
├── conversation.js     # Conversation service
├── ollama.js           # Ollama/LLM service
├── comparison.js       # Model comparison service
├── rag.js              # RAG service
├── metrics.js          # Metrics service
└── profile.js          # Profile service
```

## Custom Hooks

- `useAuth()` - Authentication state and methods
- `useApi()` - API calls with loading/error handling
- `useConversation()` - Conversation state management
- `useLocalStorage()` - Local storage persistence

## State Management

Using React Context API with providers:

- `AuthContext` - User authentication state
- `UIContext` - UI/theme state
- `NotificationContext` - Toast notifications

## Styling

- Global styles in `styles/globals.css`
- Component-scoped styles using CSS modules
- Tailwind CSS for utility-first styling
- Responsive design for mobile/tablet/desktop

## Development

### Running Tests
```bash
npm test
```

### Building for Production
```bash
npm run build
```

### Linting
```bash
npm run lint
```

## Deployment

### Docker
```bash
docker build -f Dockerfile -t gemmapp-web .
docker run -p 3000:3000 -e REACT_APP_API_URL=http://api:5000 gemmapp-web
```

### Vercel / Netlify
- Connect GitHub repository
- Set environment variables
- Deploy automatically on push

### Traditional Server
```bash
npm run build
npm install -g serve
serve -s build -l 3000
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Optimization

- Code splitting with React.lazy()
- Image optimization
- Virtual scrolling for long lists
- Response caching
- API request debouncing/throttling

## Security

- JWT token management
- Secure credential storage
- XSS protection
- CSRF token handling
- Input validation and sanitization
- Environment variable protection

## Troubleshooting

### CORS Issues
Ensure the backend API has CORS enabled and the frontend API URL is correct.

### Authentication Failures
Check that the JWT token is being stored and sent correctly in the Authorization header.

### Streaming Not Working
Verify that your backend supports Server-Sent Events (SSE) and CORS headers for streaming.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

Same as GemmaPy project - See LICENSE file

## Support

For issues or questions:
- Check existing GitHub issues
- Open a new issue with details
- Contact the GemmaPy team

---

**Last Updated:** October 29, 2025
**Frontend Version:** 1.0.0
