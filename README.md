# VeriShip - Enterprise QA Intelligence & Release Governance

An intelligent quality assurance platform for enterprise software teams. VeriShip provides real-time visibility into requirements QA, test design & execution, defect intelligence, and release governance across all projects.

## 🚀 Key Features

### 🧠 Quality Copilot (AI Layer)
- **Requirement Clarity Analysis** - AI-powered scoring (0-100) of requirement testability and ambiguity.
- **Automated Test Generation** - Instant generation of Playwright test steps and edge-case scenarios using LLMs.
- **Release Readiness Check** - Deterministic risk scoring and AI-driven GO/NO-GO recommendations.
- **Intelligent Failure Analysis** - Root cause analysis and automated fix suggestions for failing test runs.

### 🤖 Autonomous Operations
- **MCP Server** - Built-in **Model Context Protocol** server (`veriship_mcp.py`) exposing the entire platform as tools for AI agents (Claude, GPT).
- **n8n Orchestration** - First-class support for n8n workflows using dedicated **Service Accounts** and non-expiring JWTs.
- **Agentic Workflows** - Autonomous monitoring of "Coverage Gaps" and "Ambiguous Requirements" with automated healing and notifications.

### 📊 Governance & Intelligence
- **Real-time Dashboard** - Live metrics on quality coverage, risk scores, and team activity.
- **Defect Intelligence** - Smart tracking with severity prediction and recurrence analysis.

## 🛠️ Tech Stack

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Redis
- **AI Gateway**: **OpenRouter** (Default: `google/gemma-3-27b-it:free`)
- **Automation**: Playwright
- **Integration**: n8n + MCP (Model Context Protocol)
- **Infrastructure**: Docker + Docker Compose

## 🏁 Quick Start

### Prerequisites
- Node.js & npm
- Python 3.10+
- Docker & Docker Compose

### Development Setup

1. **Clone & Install**
   ```sh
   # Install frontend dependencies
   npm install

   # Setup backend environment
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Configuration**
   - Copy `backend/.env.example` to `backend/.env`.
   - Add your `OPENROUTER_API_KEY` for AI features.

3. **Launch Services**
   ```sh
   # Start Docker services (PostgreSQL, Redis)
   docker-compose up -d

   # Run backend (port 8000)
   python run.py

   # Start frontend (port 8082)
   # Back in root directory
   npm run dev
   ```

## 🔌 Integration & Agentic Access

### MCP Server (Model Context Protocol)
Expose VeriShip to your AI tools:
```sh
python veriship_mcp.py
```

### n8n Service Account
Provision an automated agent:
```sh
curl -X POST http://localhost:8000/api/auth/service-account \
  -H "Content-Type: application/json" \
  -d '{"name": "n8n-agent", "description": "QA Automation Orchestrator", "role": "agent"}'
```

## 📂 Project Structure

- `src/` - React frontend components and pages
- `backend/` - FastAPI application, models, and routes
- `mcp/` - MCP server implementation and tool definitions
- `docker-compose.yml` - Docker services configuration
- `veriship_mcp.py` - Main entry point for the MCP server

## 📄 License

Proprietary - VeriShip Quality Governance Platform.
