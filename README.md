# VeriShip - Enterprise QA Intelligence & Release Governance

An intelligent quality assurance platform for enterprise software teams. VeriShip provides real-time visibility into requirements QA, test design & execution, defect intelligence, and release readiness across all projects.

## Key Features

- **Requirements QA** - AI-powered analysis of requirement clarity, traceability, and testability
- **Test Design & Execution** - Test case management with automation tracking and execution metrics
- **Defect Intelligence** - Smart defect tracking with risk scoring and recurrence prediction
- **Release Governance** - Automated release readiness assessment and approval workflows
- **Real-time Dashboard** - Live metrics on quality coverage, risk scores, and team activity
- **AI Insights** - Machine learning-powered recommendations for quality improvements

## Tech Stack

**Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui  
**Backend**: FastAPI + SQLAlchemy + PostgreSQL + Redis  
**Infrastructure**: Docker + Docker Compose

## Quick Start

### Prerequisites
- Node.js & npm
- Python 3.10+
- Docker & Docker Compose

### Development

```sh
# Install frontend dependencies
npm install

# Start frontend (port 8080)
npm run dev

# Start backend (in another terminal)
cd backend
python run.py

# Start Docker services (PostgreSQL, Redis)
docker-compose up -d
```

Visit `http://localhost:8080` to access the dashboard.

## Project Structure

- `src/` - React frontend components and pages
- `backend/` - FastAPI application, models, and routes
- `public/` - Static assets
- `docker-compose.yml` - Docker services configuration

## Architecture

The platform follows a modular design with 6 core QA modules, each with dedicated database schemas, API endpoints, and UI components for specialized quality governance workflows.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/REPLACE_WITH_PROJECT_ID) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
