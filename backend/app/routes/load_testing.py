"""Load/Stress testing routes using Locust."""

import asyncio
import uuid
import subprocess
import os
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project

router = APIRouter()

# In-memory job tracking
LOAD_TEST_JOBS: Dict[str, dict] = {}
JOB_QUEUES: Dict[str, asyncio.Queue] = {}

# Paths
REPORTS_DIR = Path("./load_test_reports")
REPORTS_DIR.mkdir(exist_ok=True)


def _generate_locustfile(
    base_url: str,
    endpoints: list[str],
    min_wait: int = 1,
    max_wait: int = 3
) -> str:
    """Generate a custom locustfile based on user configuration."""
    
    # Generate custom tasks for each endpoint
    custom_tasks = ""
    if endpoints and any(e.strip() for e in endpoints):
        for i, endpoint in enumerate(endpoints, start=1):
            if not endpoint.strip():
                continue
            task_name = endpoint.replace("/", "_").replace("-", "_").strip("_") or f"endpoint_{i}"
            custom_tasks += f"""
    @task
    def {task_name}(self):
        \"\"\"Test {endpoint}\"\"\"
        self.client.get("{endpoint}")
"""
    else:
        # Default task if no endpoints provided
        custom_tasks = """
    @task
    def load_homepage(self):
        \"\"\"Load the homepage.\"\"\"
        self.client.get("/")
"""
    
    # Read template
    template_path = Path(__file__).parent.parent.parent / "locustfile_template.py"
    with open(template_path, "r") as f:
        template = f.read()
    
    # Replace placeholders
    locustfile_content = template.format(
        min_wait=min_wait,
        max_wait=max_wait,
        base_url=base_url,
        custom_tasks=custom_tasks
    )
    
    return locustfile_content


async def _run_locust_test_async(
    job_id: str,
    locustfile_path: str,
    users: int,
    spawn_rate: int,
    run_time: str,
    host: str
):
    """Run Locust load test in headless mode."""
    queue = JOB_QUEUES.get(job_id)
    
    if queue is None:
        return
    
    # Create report directory for this job
    report_dir = REPORTS_DIR / job_id
    report_dir.mkdir(exist_ok=True)
    
    # Locust command
    cmd = [
        "locust",
        "-f", locustfile_path,
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "--run-time", run_time,
        "--host", host,
        "--html", str(report_dir / "report.html"),
        "--csv", str(report_dir / "stats"),
    ]
    
    try:
        await queue.put(f"🚀 Starting load test with {users} users...")
        await queue.put(f"📊 Target: {host}")
        await queue.put(f"⏱️  Duration: {run_time}")
        await queue.put(f"🔧 Command: {' '.join(cmd[:5])}...")
        
        # Run Locust
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Stream output
        for line in proc.stdout:
            await queue.put(line.rstrip())
        
        proc.wait()
        
        if proc.returncode == 0:
            await queue.put("✅ Load test completed successfully!")
            await queue.put(f"📄 Report saved to: {report_dir / 'report.html'}")
            
            # Update job status
            LOAD_TEST_JOBS[job_id]["status"] = "completed"
            LOAD_TEST_JOBS[job_id]["report_path"] = str(report_dir / "report.html")
        else:
            await queue.put(f"❌ Load test failed with exit code {proc.returncode}")
            LOAD_TEST_JOBS[job_id]["status"] = "failed"
        
    except Exception as e:
        await queue.put(f"ERROR: {str(e)}")
        LOAD_TEST_JOBS[job_id]["status"] = "failed"
    finally:
        await queue.put("__DONE__")
        
        # Cleanup locustfile
        try:
            os.unlink(locustfile_path)
        except:
            pass


@router.post("/start")
def start_load_test(
    background_tasks: BackgroundTasks,
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Start a load test.
    
    Payload:
      {
        "project_id": <int>,
        "base_url": "https://example.com",
        "users": 100,
        "spawn_rate": 10,
        "run_time": "1m",
        "endpoints": ["/", "/api/users", "/api/products"]
      }
    """
    job_id = str(uuid.uuid4())
    
    # Extract params
    project_id = payload.get("project_id")
    base_url = payload.get("base_url")
    users = payload.get("users", 10)
    spawn_rate = payload.get("spawn_rate", 1)
    run_time = payload.get("run_time", "1m")
    endpoints = payload.get("endpoints", ["/"])
    
    if not base_url:
        raise HTTPException(status_code=400, detail="base_url is required")
    
    # Fetch project if provided
    project = None
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Generate locustfile
    locustfile_content = _generate_locustfile(
        base_url=base_url,
        endpoints=endpoints,
        min_wait=1,
        max_wait=3
    )
    
    # Save locustfile
    locustfile_path = f"/tmp/locustfile_{job_id}.py"
    with open(locustfile_path, "w") as f:
        f.write(locustfile_content)
    
    # Create queue
    queue = asyncio.Queue()
    JOB_QUEUES[job_id] = queue
    
    # Track job
    LOAD_TEST_JOBS[job_id] = {
        "id": job_id,
        "project_id": project_id,
        "project_name": project.name if project else None,
        "base_url": base_url,
        "users": users,
        "spawn_rate": spawn_rate,
        "run_time": run_time,
        "endpoints": endpoints,
        "status": "running",
        "created_at": datetime.utcnow().isoformat(),
        "report_path": None
    }
    
    # Start test in background
    background_tasks.add_task(
        _run_locust_test_async,
        job_id,
        locustfile_path,
        users,
        spawn_rate,
        run_time,
        base_url
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "project": {
            "id": project.id,
            "name": project.name
        } if project else None
    }


async def _sse_generator(job_id: str):
    """Stream load test output via SSE."""
    queue = JOB_QUEUES.get(job_id)
    if queue is None:
        yield "event: error\ndata: job_not_found\n\n"
        return

    try:
        while True:
            line = await queue.get()
            if line == "__DONE__":
                yield "event: done\ndata: done\n\n"
                break
            yield f"data: {line}\n\n"
    finally:
        JOB_QUEUES.pop(job_id, None)


@router.get("/{job_id}/events")
def stream_load_test_events(job_id: str):
    """SSE endpoint for streaming load test output."""
    return StreamingResponse(_sse_generator(job_id), media_type="text/event-stream")


@router.get("/{job_id}/status")
def get_load_test_status(job_id: str):
    """Get the status of a load test."""
    job = LOAD_TEST_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/report")
def get_load_test_report(job_id: str):
    """Get the HTML report for a completed load test."""
    job = LOAD_TEST_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Test not completed yet")
    
    report_path = Path(job["report_path"])
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        report_path,
        media_type="text/html",
        filename=f"load_test_report_{job_id}.html"
    )


@router.get("/{job_id}/report/pdf")
def download_pdf_report(job_id: str):
    """Download load test report as PDF."""
    job = LOAD_TEST_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Test not completed yet")
    
    report_path = Path(job["report_path"])
    pdf_path = report_path.parent / "report.pdf"
    
    # Convert HTML to PDF using pdfkit
    try:
        import pdfkit
        pdfkit.from_file(str(report_path), str(pdf_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF generation failed")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"load_test_report_{job_id}.pdf"
    )


@router.get("/jobs")
def list_load_tests(
    project_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """List all load test jobs, optionally filtered by project."""
    jobs = list(LOAD_TEST_JOBS.values())
    
    if project_id:
        jobs = [j for j in jobs if j.get("project_id") == project_id]
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "total": len(jobs),
        "jobs": jobs[:limit]
    }


@router.delete("/{job_id}")
def delete_load_test(job_id: str):
    """Delete a load test job and its reports."""
    job = LOAD_TEST_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete reports
    report_dir = REPORTS_DIR / job_id
    if report_dir.exists():
        import shutil
        shutil.rmtree(report_dir)
    
    # Remove from tracking
    LOAD_TEST_JOBS.pop(job_id, None)
    JOB_QUEUES.pop(job_id, None)
    
    return {"message": "Load test deleted successfully"}
