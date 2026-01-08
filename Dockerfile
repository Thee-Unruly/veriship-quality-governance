FROM python:3.11-slim AS backend-build

WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Backend dependencies
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy backend code
COPY backend .

# --- Frontend build stage ---
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY package.json bun.lockb ./
RUN npm install
COPY src ./src
COPY public ./public
COPY index.html vite.config.ts tailwind.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json ./
COPY postcss.config.js eslint.config.js components.json ./
RUN npm run build

# --- Final stage ---
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Backend dependencies
COPY --from=backend-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-build /usr/local/bin /usr/local/bin

# Backend code
COPY backend ./backend

# Frontend build
COPY --from=frontend-build /app/dist ./frontend-dist

# Copy start script and normalize line endings (fix CRLF -> LF on Windows hosts)
COPY start.sh ./start.sh
COPY spa_server.py ./spa_server.py
# Remove CR carriage returns if present and make executable
RUN sed -i 's/\r$//' ./start.sh && chmod +x ./start.sh

EXPOSE 8000 8080

CMD ["./start.sh"]
