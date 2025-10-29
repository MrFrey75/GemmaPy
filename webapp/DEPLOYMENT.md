# Deployment Guide

This guide covers deploying the GemmaPy WebApp to production.

## Deployment Options

### 1. Vercel (Recommended for Frontend)

Vercel is perfect for deploying the React frontend.

#### Setup

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your repository
4. Configure project:
   - **Root Directory**: `webapp/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

5. Set Environment Variables:
   ```
   VITE_API_URL=https://your-api.com
   VITE_API_TIMEOUT=30000
   ```

6. Deploy

#### Benefits

- Zero-config deployments
- Automatic HTTPS
- CDN integration
- Automatic deployments on push
- Serverless functions support

### 2. Netlify

Alternative to Vercel with similar features.

#### Setup

1. Connect GitHub repository
2. Configure:
   - **Base Directory**: `webapp/frontend`
   - **Build Command**: `npm run build`
   - **Publish Directory**: `dist`

3. Set environment variables in Netlify UI
4. Deploy

### 3. Docker Deployment

For self-hosted deployments.

#### Dockerfile

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app/frontend
COPY webapp/frontend/package*.json ./
RUN npm ci

COPY webapp/frontend . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve
RUN npm install -g serve

# Copy built application
COPY --from=builder /app/frontend/dist ./dist

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD npm run health || exit 1

# Start server
CMD ["serve", "-s", "dist", "-l", "3000"]
```

#### Build and Run

```bash
# Build image
docker build -f Dockerfile -t gemmapp-web:latest .

# Run container
docker run -p 3000:3000 \
  -e VITE_API_URL=http://api:5000 \
  gemmapp-web:latest

# Or with docker-compose
docker-compose up
```

### 4. Docker Compose (Full Stack)

```yaml
version: '3.8'

services:
  # Frontend
  web:
    build:
      context: .
      dockerfile: webapp/Dockerfile
    ports:
      - "3000:3000"
    environment:
      VITE_API_URL: http://api:5000
    depends_on:
      - api

  # Backend API
  api:
    build:
      context: .
      dockerfile: src/Dockerfile
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: production
    depends_on:
      - ollama

  # Ollama Service
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

Run with:

```bash
docker-compose up -d
```

### 5. Traditional Server (Nginx + PM2)

#### Setup

1. Build the application:

```bash
npm run build
```

2. Copy `dist` folder to server

3. Install PM2 globally:

```bash
npm install -g pm2
```

4. Create `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'gemmapp-web',
    script: 'npx serve -s dist -l 3000',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
```

5. Start with PM2:

```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### Nginx Configuration

```nginx
upstream gemmapp {
  server localhost:3000;
}

server {
  listen 80;
  server_name your-domain.com;

  # Redirect HTTP to HTTPS
  return 301 https://$server_name$request_uri;
}

server {
  listen 443 ssl http2;
  server_name your-domain.com;

  ssl_certificate /path/to/certificate.crt;
  ssl_certificate_key /path/to/private.key;

  client_max_body_size 10M;

  location / {
    proxy_pass http://gemmapp;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  # API proxy
  location /api/ {
    proxy_pass http://your-api-server:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

## Pre-Deployment Checklist

- [ ] Update API URL in environment variables
- [ ] Set `VITE_LOG_LEVEL` to `warn` in production
- [ ] Remove sensitive data from code
- [ ] Run `npm run build` and test locally
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Enable HTTPS
- [ ] Configure CORS on API
- [ ] Set up monitoring and alerts
- [ ] Plan rollback strategy
- [ ] Document deployment process

## Environment Variables

### Production

```
VITE_API_URL=https://api.your-domain.com
VITE_API_TIMEOUT=30000
VITE_LOG_LEVEL=warn
VITE_ENABLE_RAG=true
VITE_ENABLE_COMPARISON=true
VITE_ENABLE_METRICS=true
```

### Staging

```
VITE_API_URL=https://staging-api.your-domain.com
VITE_API_TIMEOUT=30000
VITE_LOG_LEVEL=info
```

## Performance Optimization

### 1. Enable Gzip Compression

Nginx:
```nginx
gzip on;
gzip_types text/plain text/css text/javascript application/json;
gzip_min_length 1000;
```

### 2. Set Cache Headers

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}

location ~* \.(html)$ {
  expires 1h;
  add_header Cache-Control "public, must-revalidate";
}
```

### 3. Enable HTTP/2

```nginx
listen 443 ssl http2;
```

### 4. Content Delivery Network

Use a CDN like Cloudflare:

1. Add domain to Cloudflare
2. Update nameservers
3. Enable caching rules
4. Set up automatic HTTPS redirects

## Monitoring

### Application Monitoring

Use tools like:

- **Sentry**: Error tracking
- **Datadog**: Infrastructure monitoring
- **New Relic**: Performance monitoring

### Log Aggregation

```bash
# Send logs to cloud
pm2 install pm2-auto-log-rotate
```

### Uptime Monitoring

- UptimeRobot
- Pingdom
- CloudFlare

## Rollback Strategy

### Using Git Tags

```bash
# Tag release
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Checkout previous version
git checkout v1.0.0
npm run build
```

### Using Docker

```bash
# Tag image
docker tag gemmapp-web:latest gemmapp-web:v1.0.0

# Rollback
docker run gemmapp-web:v0.9.9
```

## Updating Frontend

### Rolling Update

1. Build new version
2. Push to staging
3. Test thoroughly
4. Push to production
5. Monitor for errors

### Blue-Green Deployment

1. Deploy new version to "green" environment
2. Test completely
3. Switch traffic to "green"
4. Keep "blue" as rollback

### Canary Deployment

1. Deploy to small percentage of users
2. Monitor for errors
3. Gradually increase percentage
4. Full rollout once stable

## Security Checklist

- [ ] Enable HTTPS/TLS
- [ ] Set secure headers
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Keep dependencies updated
- [ ] Regular security audits
- [ ] Rate limiting configured
- [ ] DDoS protection enabled
- [ ] Regular backups
- [ ] Log sensitive events

## Support & Troubleshooting

### Deployment Fails

1. Check build logs
2. Verify environment variables
3. Check API connectivity
4. Review error messages

### Application Errors

1. Check browser console
2. Check server logs
3. Verify API responses
4. Check network requests

### Performance Issues

1. Use Lighthouse audit
2. Check bundle size
3. Optimize images
4. Enable caching

---

**Last Updated**: October 29, 2025
