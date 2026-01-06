# VeriShip QA Platform - Backend Setup Guide

## Prerequisites

- Docker & Docker Compose installed
- Python 3.10+ installed
- Node.js 18+ (for frontend)

## Quick Start (5 minutes)

### Step 1: Start Docker Containers

```bash
# From project root
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)

Verify they're running:
```bash
docker-compose ps
```

### Step 2: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env  # Windows
# OR
cp .env.example .env  # Mac/Linux

# Seed database with demo data
python seed.py

# Start API server
python run.py
```

**API is now running at:** `http://localhost:8000`

### Step 3: Access the API

- **Swagger UI (Interactive Docs):** http://localhost:8000/docs
- **ReDoc (API Reference):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### Step 4: Test the Backend (Optional)

```bash
# Get all projects
curl http://localhost:8000/api/projects/

# Create a new project
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "A test project"
  }'
```

### Step 5: Start Frontend (In another terminal)

```bash
# From project root
npm install  # If not done yet
npm run dev
```

Frontend will be at: `http://localhost:5173`

---

## Database

### Connection Details

- **Host:** localhost
- **Port:** 5432
- **Database:** veriship_db
- **Username:** veriship_user
- **Password:** veriship_dev_password

### View Database

Use any PostgreSQL client (pgAdmin, DBeaver, etc.) or psql:

```bash
psql -h localhost -U veriship_user -d veriship_db
```

### Reset Database

```bash
# Delete PostgreSQL volume and restart
docker-compose down -v
docker-compose up -d
python seed.py
```

---

## Project Structure

```
veriship-quality-governance/
├── frontend/                    # React + Vite frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
│
├── backend/                     # FastAPI Python backend
│   ├── app/
│   │   ├── models/             # Database models (15+ tables)
│   │   ├── routes/             # API endpoints
│   │   ├── main.py             # FastAPI app
│   │   ├── database.py         # DB setup
│   │   └── config.py           # Settings
│   ├── requirements.txt
│   ├── seed.py                 # Demo data
│   ├── run.py                  # Entry point
│   └── README.md
│
├── docker-compose.yml          # PostgreSQL + Redis
└── README.md
```

---

## API Overview

### Projects Module
```
GET    /api/projects/              # List all projects
GET    /api/projects/{id}          # Get project details
POST   /api/projects/              # Create project
PUT    /api/projects/{id}          # Update project
DELETE /api/projects/{id}          # Delete project
```

### Requirements Module
```
GET    /api/requirements/{proj_id} # List requirements
POST   /api/requirements/          # Create requirement
```

### Test Cases Module
```
GET    /api/test-cases/{proj_id}   # List test cases
POST   /api/test-cases/            # Create test case
```

### Defects Module
```
GET    /api/defects/{proj_id}      # List defects
POST   /api/defects/               # Create defect
```

### Releases Module
```
GET    /api/releases/{proj_id}     # List releases
POST   /api/releases/              # Create release
```

---

## Database Schema

### 15+ Tables covering 6 modules:

**Module 1: Requirements QA**
- `projects` - Project master data
- `requirements` - Business requirements with AI analysis
- `acceptance_criteria` - Detailed AC for each requirement

**Module 2: Test Design**
- `test_cases` - Test cases with traceability
- `test_suites` - Test groupings

**Module 3: Test Execution**
- `test_executions` - Test run results
- `ci_cd_pipelines` - Pipeline tracking

**Module 4: Defect Intelligence**
- `defects` - Bug tracking with AI risk scoring
- `quality_metrics` - Aggregated metrics

**Module 5: Release Readiness**
- `releases` - Release versions
- `release_approvals` - Approval workflow

**Module 6: Post-Release**
- `production_issues` - Production incidents
- `qa_insights` - AI-generated insights

**Other**
- `team_members` - Project team assignments

---

## Troubleshooting

### PostgreSQL Connection Error
```
Error: could not connect to server
```
Check if Docker is running:
```bash
docker-compose ps
```

### Port Already in Use
```
Address already in use
```
Kill process on port 8000 or change port in `run.py`

### Import Error: No module named 'app'
Make sure you're in the `backend/` directory when running the server.

### Database Locked
```bash
docker-compose down -v
docker-compose up -d
python seed.py
```

---

## Next Steps

1. ✅ **Backend Foundation** - DONE
   - FastAPI app with 6 modules
   - PostgreSQL database with 15+ tables
   - Demo data (seed.py)
   - Basic CRUD endpoints

2. 🔄 **Connect Frontend to Backend**
   - Replace mock data with real API calls
   - Update dashboard components
   - Add state management for API data

3. 🚀 **Core Features**
   - AI/LLM integration for requirement analysis
   - Automated test case generation
   - Risk scoring algorithms
   - Release gate logic

4. 🔧 **Integrations**
   - Jira/GitHub for requirement ingestion
   - CI/CD pipeline execution
   - Slack notifications

---

## Commands Reference

```bash
# Start everything
docker-compose up -d
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python run.py

# View logs
docker-compose logs postgres
docker-compose logs redis

# Stop everything
docker-compose down

# Restart fresh
docker-compose down -v
docker-compose up -d
python seed.py
python run.py
```

---

## Support

For issues or questions, check the backend README at `backend/README.md`
