# VeriShip QA Platform - Command Reference

## One-Command Quick Start

```bash
# Windows
docker-compose up -d && cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python seed.py && python run.py

# Mac/Linux
docker-compose up -d && cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python seed.py && python run.py
```

Then visit: http://localhost:8000/docs

---

## Step-by-Step Commands

### Phase 1: Infrastructure

```bash
# Start Docker containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs postgres
docker-compose logs redis

# Stop containers
docker-compose stop

# Stop and remove (keep volumes)
docker-compose down

# Stop and remove everything (reset database)
docker-compose down -v
```

### Phase 2: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
# Windows:
copy .env.example .env
# Mac/Linux:
cp .env.example .env
```

### Phase 3: Database

```bash
# Seed database with demo data
python seed.py

# Connect to database directly (requires psql installed)
psql -h localhost -U veriship_user -d veriship_db

# Common SQL queries
# List all tables:
\dt

# Show project data:
SELECT * FROM projects;

# Show requirements:
SELECT * FROM requirements;

# Count defects by severity:
SELECT severity, COUNT(*) FROM defects GROUP BY severity;

# Exit psql:
\q
```

### Phase 4: Run Application

```bash
# Start FastAPI server
python run.py

# Server runs at http://localhost:8000

# In browser, visit:
# Swagger UI:    http://localhost:8000/docs
# ReDoc:         http://localhost:8000/redoc
# Health Check:  http://localhost:8000/health
# API:           http://localhost:8000/api/projects/
```

### Phase 5: Frontend (In another terminal)

```bash
# From project root
npm install

# Start dev server
npm run dev

# Frontend at http://localhost:5173
```

---

## API Testing Commands

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# List projects
curl http://localhost:8000/api/projects/

# Get project by ID
curl http://localhost:8000/api/projects/1

# Create project
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Project",
    "description": "Test project"
  }'

# Update project
curl -X PUT http://localhost:8000/api/projects/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Project",
    "status": "on-track"
  }'

# Delete project
curl -X DELETE http://localhost:8000/api/projects/1

# List requirements for project
curl http://localhost:8000/api/requirements/1

# Create requirement
curl -X POST http://localhost:8000/api/requirements/ \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "requirement_id": "REQ-001",
    "title": "User Login",
    "description": "Users should be able to login"
  }'
```

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Get all projects
response = requests.get(f"{BASE_URL}/api/projects/")
projects = response.json()
print(projects)

# Create a project
new_project = {
    "name": "My Project",
    "description": "A test project"
}
response = requests.post(f"{BASE_URL}/api/projects/", json=new_project)
print(response.json())

# Get specific project
response = requests.get(f"{BASE_URL}/api/projects/1")
print(response.json())
```

---

## Development Workflow

### Starting Development Session

```bash
# Terminal 1: Start Docker
docker-compose up -d

# Terminal 2: Start Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python run.py

# Terminal 3: Start Frontend
npm run dev

# Open browser
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Making Database Changes

```bash
# 1. Modify models in backend/app/models/__init__.py
# 2. Restart FastAPI server (Ctrl+C, then python run.py)
# 3. New tables are auto-created by SQLAlchemy

# Or reset database completely:
docker-compose down -v
docker-compose up -d
cd backend && python seed.py && python run.py
```

### Debugging

```bash
# View detailed logs
python run.py

# Or use --reload flag for auto-reload
uvicorn app.main:app --reload

# Check database with psql
psql -h localhost -U veriship_user -d veriship_db
SELECT COUNT(*) FROM projects;

# View Docker logs
docker-compose logs -f postgres
docker-compose logs -f redis
```

---

## Common Issues & Fixes

### Port already in use

```bash
# Check what's using port 8000 (Windows)
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or change port in run.py
```

### Database connection refused

```bash
# Check Docker is running
docker ps

# Restart Docker
docker-compose restart postgres

# Or reset
docker-compose down -v
docker-compose up -d
python seed.py
```

### Module not found error

```bash
# Make sure you're in backend directory
cd backend

# Make sure venv is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Virtual environment issues

```bash
# Delete and recreate venv
rm -r venv  # Mac/Linux: rm -r venv
             # Windows: rmdir /s venv

# Create fresh venv
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install
pip install -r requirements.txt
```

---

## Useful Tips

### Run API tests
```bash
# Using curl with jq (pretty JSON)
curl http://localhost:8000/api/projects/ | jq

# Using Python
python -c "import requests; print(requests.get('http://localhost:8000/api/projects/').json())"
```

### View all endpoints
Visit http://localhost:8000/docs and you'll see all endpoints with their parameters

### Export database to file
```bash
pg_dump -h localhost -U veriship_user -d veriship_db > backup.sql
```

### Restore database from file
```bash
psql -h localhost -U veriship_user -d veriship_db < backup.sql
```

### Check Python version
```bash
python --version  # Should be 3.10+
```

### Check package versions
```bash
pip list
```

### Update all packages
```bash
pip install --upgrade -r requirements.txt
```

---

## Cleanup Commands

```bash
# Stop everything but keep volumes
docker-compose stop
deactivate  # Deactivate Python venv

# Remove containers but keep volumes
docker-compose down

# Remove everything including database
docker-compose down -v

# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

## Environment Variables

Edit `.env` file in backend directory:

```env
DATABASE_URL=postgresql://veriship_user:veriship_dev_password@localhost:5432/veriship_db
REDIS_URL=redis://localhost:6379/0
API_HOST=0.0.0.0
API_PORT=8000
API_ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
```

---

## File Structure Reference

```
backend/
├── app/
│   ├── models/__init__.py      # All database models (15+ tables)
│   ├── routes/
│   │   ├── projects.py
│   │   ├── requirements.py
│   │   ├── test_cases.py
│   │   ├── defects.py
│   │   ├── releases.py
│   │   └── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── database.py             # DB configuration
│   ├── config.py               # Settings
│   └── __init__.py
├── requirements.txt            # Dependencies
├── run.py                      # Entry point (python run.py)
├── seed.py                     # Database seeding (python seed.py)
├── .env.example
└── README.md
```

---

## Quick Reference Table

| Task | Command |
|------|---------|
| Start Docker | `docker-compose up -d` |
| Stop Docker | `docker-compose down` |
| Reset Database | `docker-compose down -v && docker-compose up -d && python seed.py` |
| Start Backend | `cd backend && python run.py` |
| Activate venv | `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux) |
| Install packages | `pip install -r requirements.txt` |
| Seed database | `python seed.py` |
| View API docs | `http://localhost:8000/docs` |
| List projects | `curl http://localhost:8000/api/projects/` |
| Check health | `curl http://localhost:8000/health` |

---

## Useful Links

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **API Root:** http://localhost:8000
- **Frontend:** http://localhost:5173
- **Database:** localhost:5432 (veriship_user / veriship_dev_password)

---

## Support

For issues:
1. Check BACKEND_SETUP.md for setup help
2. Check ARCHITECTURE.md for system design
3. Check backend/README.md for API details
4. Run `python seed.py` to reset demo data
5. View logs with `docker-compose logs`
