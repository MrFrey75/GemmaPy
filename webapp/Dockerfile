# Multi-Stage Dockerfile for GemmaPy WebApp

# Stage 1: Dependencies
FROM node:18-alpine AS dependencies
WORKDIR /app
COPY webapp/frontend/package*.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:18-alpine AS builder
WORKDIR /app
COPY webapp/frontend/package*.json ./
RUN npm ci

COPY webapp/frontend/ .
RUN npm run build

# Stage 3: Runtime
FROM node:18-alpine
WORKDIR /app

# Install serve to run static files
RUN npm install -g serve

# Copy production dependencies
COPY --from=dependencies /app/node_modules ./node_modules

# Copy built application
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json .

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
USER nextjs

# Expose port
EXPOSE 3000

# Environment variables
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["serve", "-s", "dist", "-l", "3000"]
