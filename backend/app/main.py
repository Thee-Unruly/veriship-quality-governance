"""Main FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.models import *  # Import all models

# Create all tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    yield
    # Shutdown - cleanup Playwright resources
    from app.routes.automation import shutdown_automation
    await shutdown_automation()


# Initialize app
app = FastAPI(
    title="VeriShip QA Platform",
    description="Enterprise QA Intelligence & Release Governance",
    version="0.0.1",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from app.routes import projects, requirements, test_cases, defects, releases, metrics, auth, copilot, test_runs, trial, automation

# Include routers
app.include_router(auth.router)
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(requirements.router, prefix="/api/requirements", tags=["Requirements"])
app.include_router(test_cases.router, prefix="/api/test-cases", tags=["Test Cases"])
app.include_router(defects.router, prefix="/api/defects", tags=["Defects"])
app.include_router(releases.router, prefix="/api/releases", tags=["Releases"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["Copilot"])
app.include_router(test_runs.router, prefix="/api/test-runs", tags=["Test Runs"])
app.include_router(trial.router, prefix="/api/trial", tags=["Trial Runner"])
app.include_router(automation.router, prefix="/api/automation", tags=["Playwright Automation"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "VeriShip QA Platform",
        "environment": settings.environment
    }


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "VeriShip QA Platform API",
        "version": "0.0.1",
        "docs": "/docs"
    }
