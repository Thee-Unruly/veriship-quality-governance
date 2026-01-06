# Backend for VeriShip QA Platform

Backend API built with FastAPI, PostgreSQL, and SQLAlchemy.

## Quick Start

### 1. Start PostgreSQL & Redis with Docker

```bash
docker-compose up -d
```

### 2. Create Python Virtual Environment

```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env` file

```bash
cp .env.example .env
```

### 5. Run Database Seeding

```bash
python seed.py
```

### 6. Start the API Server

```bash
python run.py
```

The API will be available at: **http://localhost:8000**

### 7. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── models/          # SQLAlchemy ORM models (all 6 modules)
│   ├── routes/          # API endpoints (projects, requirements, test-cases, defects, releases)
│   ├── schemas/         # Pydantic validation schemas (future)
│   ├── services/        # Business logic layer (future)
│   ├── main.py          # FastAPI application factory
│   ├── database.py      # Database configuration
│   ├── config.py        # Application settings
│   └── __init__.py
├── requirements.txt     # Python dependencies
├── run.py              # Application entry point
├── seed.py             # Database seeding script
├── .env.example        # Environment variables template
└── .gitignore
```

## API Endpoints

### Projects
- `GET /api/projects/` - List all projects
- `GET /api/projects/{id}` - Get project details
- `POST /api/projects/` - Create new project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Requirements
- `GET /api/requirements/{project_id}` - List project requirements
- `POST /api/requirements/` - Create requirement

### Test Cases
- `GET /api/test-cases/{project_id}` - List test cases
- `POST /api/test-cases/` - Create test case

### Defects
- `GET /api/defects/{project_id}` - List defects
- `POST /api/defects/` - Create defect

### Releases
- `GET /api/releases/{project_id}` - List releases
- `POST /api/releases/` - Create release

## Database Models

The system includes models for all 6 core modules:

1. **Module 1: Requirements QA**
   - Projects, Requirements, Acceptance Criteria

2. **Module 2: Test Design & Coverage**
   - TestCases, TestSuites, Traceability

3. **Module 3: Test Execution**
   - TestExecutions, CI/CD Pipeline tracking

4. **Module 4: Defect Intelligence**
   - Defects, QualityMetrics, Risk Scoring

5. **Module 5: Release Readiness**
   - Releases, ReleaseApprovals, QA Gates

6. **Module 6: Post-Release Learning**
   - ProductionIssues, QAInsights

## Next Steps

- [ ] Integrate with Jira/GitHub for requirement ingestion
- [ ] Build AI/LLM services for clarity scoring & test generation
- [ ] Implement CI/CD pipeline execution
- [ ] Add authentication & authorization
- [ ] Create advanced analytics & dashboards
- [ ] Build Celery tasks for async processing
