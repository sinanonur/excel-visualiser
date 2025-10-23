# Multi-stage build for compact Excel Data Visualizer
# This Dockerfile creates a production-ready container with minimal size

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with production flag and clean cache
RUN npm ci --only=production && \
    npm cache clean --force

# Copy frontend source
COPY public ./public
COPY src ./src

# Build frontend for production
RUN npm run build

# Stage 2: Build Python backend with minimal dependencies
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install system dependencies required for Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 3: Final production image
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=backend-builder /root/.local /root/.local

# Copy backend application
COPY backend ./backend
COPY start_backend.py .

# Copy built frontend from frontend-builder
COPY --from=frontend-builder /app/build ./frontend/build

# Install minimal Node.js for serving frontend (optional, can use Python)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    npm install -g serve && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Make sure scripts use the user Python packages
ENV PATH=/root/.local/bin:$PATH

# Expose ports
EXPOSE 5001 3000

# Create startup script
RUN echo '#!/bin/sh\n\
python start_backend.py &\n\
cd frontend/build && serve -s . -l 3000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5001/ || exit 1

# Start both services
CMD ["/app/start.sh"]
