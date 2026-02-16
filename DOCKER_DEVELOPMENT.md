# Running VeriShip with Docker - Capturing Latest Changes

## Overview

There are two approaches to running the app in Docker during development:

1. **Volume Mount Approach** (Recommended) - Code changes reflect immediately
2. **Rebuild Approach** - Rebuild image for each change

---

## ✅ Option 1: Volume Mount (Hot Reload) - RECOMMENDED

This is best for active development. Changes appear immediately without rebuilding.

### For Backend Only

```bash
# Start only supporting services (PostgreSQL, Redis)
docker compose up postgres redis

# Run backend directly on host (not in Docker)
cd backend
python run.py
```

This lets you:
- ✅ See changes immediately when you save files
- ✅ Debug with print statements in terminal
- ✅ Install new packages with `pip install`
- ✅ Run backend on http://localhost:8000

### For Everything with Volume Mounts

Create a new `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: veriship-postgres
    environment:
      POSTGRES_USER: veriship_user
      POSTGRES_PASSWORD: veriship_dev_password
      POSTGRES_DB: veriship_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U veriship_user -d veriship_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - veriship-network

  redis:
    image: redis:7-alpine
    container_name: veriship-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - veriship-network

  app:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: veriship-app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://veriship_user:veriship_dev_password@postgres:5432/veriship_db
      REDIS_URL: redis://redis:6379
      ENVIRONMENT: development
      CORS_ORIGINS: '["http://localhost:5173","http://localhost:8080"]'
    volumes:
      - ./backend/app:/app/app  # Mount source code for hot reload
      - ./backend/.env:/app/.env  # Mount .env file
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python run.py  # Run with reload
    networks:
      - veriship-network

volumes:
  postgres_data:

networks:
  veriship-network:
    driver: bridge
```

**Usage:**
```bash
# Start all services with volume mounts
docker compose -f docker-compose.dev.yml up

# In another terminal, run frontend
npm run dev

# Visit http://localhost:8082
```

**Benefits:**
- ✅ Changes in `backend/app/` appear immediately
- ✅ No rebuild needed
- ✅ Still uses containerized PostgreSQL/Redis
- ✅ Can edit `.env` and see changes on restart

---

## Option 2: Rebuild for Each Change

Use this when you need to test the production build or add dependencies.

```bash
# Rebuild image and restart
docker compose up --build app

# Or rebuild without starting
docker compose build --no-cache app

# Then start
docker compose up app
```

**When to use:**
- Adding new Python packages to `requirements.txt`
- Changing system dependencies in Dockerfile
- Testing production build behavior
- Preparing for deployment

---

## 🔄 Workflow for Active Development

### Best Practice Setup:

```bash
# Terminal 1: Start PostgreSQL and Redis only
docker compose up postgres redis

# Terminal 2: Run backend directly (auto-reload)
cd backend
python run.py

# Terminal 3: Run frontend dev server (auto-reload)
npm run dev
```

This gives you:
- ✅ Instant hot reload for both frontend and backend
- ✅ Full control over debugging
- ✅ Easy package installation
- ✅ Same network as production (PostgreSQL, Redis)
- ⏱️ Fastest development cycle

---

## 📝 Specific to Your Changes

For the **OpenRouter AI integration** changes, use the **hot reload approach**:

```bash
# Start services
docker compose up postgres redis

# In separate terminal
cd backend
python run.py

# When you update .env with OPENROUTER_API_KEY:
# - Edit backend/.env
# - Save file
# - Backend auto-reloads (Uvicorn with --reload flag)
# - No rebuild needed!
```

You can immediately test with:
```bash
curl http://localhost:8000/api/ai/test-connection
```

---

## 🐳 Production Build (Pre-Deployment)

Test the actual production Docker image:

```bash
# Build production image
docker compose build --no-cache app

# Start everything (including app in container)
docker compose up

# Test backend at http://localhost:8000
# Test frontend at http://localhost:8082
```

---

## 🔧 Troubleshooting Docker Development

| Issue | Solution |
|-------|----------|
| Changes not reflected | Check volume mount path, restart container |
| Port already in use | `docker ps` and `docker stop <container>` |
| `.env` not picked up | Restart container: `docker compose restart app` |
| Database connection error | Ensure `postgres` service is healthy: `docker compose logs postgres` |
| Need to install package | Add to `requirements.txt`, run `docker compose build app` |

---

## 📊 Comparison Table

| Aspect | Host Development | Volume Mount | Full Docker Build |
|--------|-----------------|---------------|-------------------|
| Hot Reload | ✅ Instant | ✅ Instant | ❌ Manual rebuild |
| Setup | ✅ Simple | ⚠️ Config needed | ⚠️ Full Docker |
| Dependencies | ❌ Install locally | ✅ In container | ✅ In container |
| Production Parity | ❌ Lower | ⚠️ Medium | ✅ Exact |
| Speed | ⚠️ Depends on OS | ✅ Fast | ⚠️ Slower |
| Debugging | ✅ Easy | ✅ Easy | ❌ Harder |

---

## 🎯 Recommended Setup for Your Project

For active development of OpenRouter AI features:

```bash
# Terminal 1: Database and cache
docker compose up postgres redis

# Terminal 2: Backend (on host)
cd backend
python run.py

# Terminal 3: Frontend
npm run dev
```

**Then:**
- Edit `backend/app/services/ai_testing.py` → Auto-reloads
- Edit `backend/.env` → Manual restart: `Ctrl+C` and rerun `python run.py`
- Edit `src/components/test-runner/AITestGenerator.tsx` → Auto-reloads
- Add to `requirements.txt` → Rebuild: `docker compose build app`

---

## 💡 Pro Tips

1. **Keep services in Docker, code on host**: Fastest development cycle
2. **Use `docker compose logs -f app`**: See backend output in real-time
3. **Volume mounts are relative**: Use `./backend/app:/app/app` from project root
4. **Multiple compose files**: Use `-f docker-compose.yml -f docker-compose.dev.yml` to combine
5. **Environment variables**: Override with `-e OPENROUTER_API_KEY=sk_...`

---

**Best Approach**: Run services in Docker, code on host for fastest iteration while keeping production environment consistency.
