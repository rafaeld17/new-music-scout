# Multi-stage build for New Music Scout Frontend
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Accept build argument for API URL
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Debug: Verify source files are copied
RUN echo "Verifying source files..." && \
    ls -la && \
    echo "Contents of src/:" && \
    ls -la src/ && \
    echo "Checking index.html:" && \
    test -f index.html && echo "✓ index.html found" || echo "✗ index.html missing!"

# Debug: Show environment variable
RUN echo "Building with VITE_API_URL=$VITE_API_URL"

# Build the app with environment variable
RUN npm run build

# Debug: Show what was built
RUN echo "Build complete. Checking dist folder:" && \
    ls -la dist/ && \
    echo "Contents of dist/:" && \
    (test -f dist/index.html && echo "✓ index.html found" || echo "✗ index.html missing") && \
    (test -d dist/assets && echo "✓ assets folder found" || echo "✗ assets folder missing")

# Production stage with nginx
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Debug: List files to verify build output (force rebuild with date comment)
# Build date: 2025-10-20T17:15:00Z
RUN echo "Verifying nginx html directory:" && \
    ls -la /usr/share/nginx/html && \
    echo "Checking for critical files:" && \
    (test -f /usr/share/nginx/html/index.html && echo "✓ index.html found" || echo "✗ index.html MISSING!") && \
    (test -d /usr/share/nginx/html/assets && echo "✓ assets folder found" || echo "✗ assets folder MISSING!")

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
