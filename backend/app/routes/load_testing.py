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
from app.models import Project, User
from app.routes.auth import get_current_user
from app.dependencies import assert_create_permission

router = APIRouter()

# In-memory job tracking
LOAD_TEST_JOBS: Dict[str, dict] = {}
JOB_QUEUES: Dict[str, asyncio.Queue] = {}

# Paths
REPORTS_DIR = Path("./load_test_reports")
REPORTS_DIR.mkdir(exist_ok=True)

JOBS_FILE = REPORTS_DIR / "jobs.json"


def _load_jobs():
    """Load jobs from disk on startup."""
    if JOBS_FILE.exists():
        try:
            with open(JOBS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def _save_jobs():
    """Save jobs to disk."""
    try:
        with open(JOBS_FILE, "w") as f:
            json.dump(LOAD_TEST_JOBS, f, indent=2)
    except Exception as e:
        print(f"Failed to save jobs: {e}")


# In-memory job tracking
LOAD_TEST_JOBS: Dict[str, dict] = _load_jobs()
JOB_QUEUES: Dict[str, asyncio.Queue] = {}


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
        await queue.put("Initializing load test...")
        await queue.put(f"Target Application: {host}")
        await queue.put(f"Simulating {users} concurrent users")
        await queue.put(f"Test Duration: {run_time}")
        await queue.put("")
        await queue.put("Starting user simulation...")
        
        # Run Locust
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        import re
        users_spawned = False
        test_started = False
        
        # Parse and humanize output
        for line in proc.stdout:
            line = line.rstrip()
            
            # Skip Locust table headers and technical output
            if "Type" in line and "Name" in line and "# reqs" in line:
                continue
            if line.startswith("-----") or line.startswith("====="):
                continue
            if not line.strip():
                continue
            
            # Extract meaningful information
            if "Spawning" in line or "spawning" in line:
                if not users_spawned:
                    await queue.put("Users are being created and starting to send requests...")
                    users_spawned = True
            elif "All users spawned" in line:
                await queue.put(f"All {users} virtual users are now active!")
                await queue.put("")
                await queue.put("Test is running... Collecting performance data...")
                test_started = True
            elif "requests/s" in line.lower() or "rps" in line.lower():
                # Skip table headers
                if "Type" in line or "Name" in line or "#" in line:
                    continue
                # Extract RPS if available from actual data rows
                match = re.search(r'(\d+\.?\d*)\s*(?:requests?/s|RPS)', line, re.IGNORECASE)
                if match and test_started:
                    rps = match.group(1)
                    await queue.put(f"Current load: ~{rps} requests per second")
            elif "percentile" in line.lower():
                # Show response time updates
                match = re.search(r'(\d+)\s*ms', line)
                if match:
                    await queue.put(f"Response times looking good (~{match.group(1)}ms average)")
            elif "Shutting down" in line or "stopping" in line.lower():
                await queue.put("")
                await queue.put("Test duration completed. Finalizing results...")
            elif "error" in line.lower() and "0 error" not in line.lower():
                # Only show actual errors, not headers or stats lines
                if "Type" not in line and "#" not in line and "Name" not in line:
                    await queue.put(f"ERROR: {line}")
            elif "fail" in line.lower() and "0 fail" not in line.lower():
                # Only show actual failures, not headers or stats lines
                if "Type" not in line and "#" not in line and "Name" not in line and "failures/s" not in line.lower():
                    await queue.put(f"ERROR: {line}")
        
        proc.wait()
        
        if proc.returncode == 0:
            await queue.put("")
            await queue.put("Load test completed successfully!")
            await queue.put("Performance data has been collected and analyzed")
            await queue.put(f"Detailed report is ready to view")
            
            # Update job status
            LOAD_TEST_JOBS[job_id]["status"] = "completed"
            LOAD_TEST_JOBS[job_id]["report_path"] = str(report_dir / "report.html")
            _save_jobs()
        else:
            await queue.put(f"Load test failed with exit code {proc.returncode}")
            LOAD_TEST_JOBS[job_id]["status"] = "failed"
            _save_jobs()
        
    except Exception as e:
        await queue.put(f"ERROR: {str(e)}")
        LOAD_TEST_JOBS[job_id]["status"] = "failed"
        _save_jobs()
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
        
        # Authorization check - user must have create permission on the project
        assert_create_permission(db, project_id, current_user.id)
    
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
    _save_jobs()
    
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


@router.get("/{job_id}/summary")
def get_load_test_summary(job_id: str):
    """Get a user-friendly summary of the load test results."""
    job = LOAD_TEST_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        return {
            "job_id": job_id,
            "status": job["status"],
            "message": "Test is still running or failed"
        }
    
    # Read the CSV stats file
    report_dir = REPORTS_DIR / job_id
    stats_file = report_dir / "stats_stats.csv"
    
    if not stats_file.exists():
        raise HTTPException(status_code=404, detail="Stats file not found")
    
    import csv
    summary = {
        "job_id": job_id,
        "status": "completed",
        "target_host": job.get("base_url"),
        "users": job.get("users"),
        "duration": job.get("run_time"),
        "endpoints": [],
        "overall": {}
    }
    
    has_data = False
    with open(stats_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            has_data = True
            if row["Name"] == "Aggregated":
                summary["overall"] = {
                    "total_requests": int(row["Request Count"]),
                    "failures": int(row["Failure Count"]),
                    "success_rate": round((1 - int(row["Failure Count"]) / max(int(row["Request Count"]), 1)) * 100, 2),
                    "avg_response_time": round(float(row["Average Response Time"]), 2),
                    "min_response_time": round(float(row["Min Response Time"]), 2),
                    "max_response_time": round(float(row["Max Response Time"]), 2),
                    "requests_per_second": round(float(row["Requests/s"]), 2),
                    "median_response_time": round(float(row["Median Response Time"]), 2),
                    "percentile_95": round(float(row["95%"]), 2),
                    "percentile_99": round(float(row["99%"]), 2)
                }
            elif row["Type"] == "GET":
                summary["endpoints"].append({
                    "name": row["Name"],
                    "requests": int(row["Request Count"]),
                    "failures": int(row["Failure Count"]),
                    "avg_response_time": round(float(row["Average Response Time"]), 2),
                    "rps": round(float(row["Requests/s"]), 2)
                })
    
    # If no data was collected, return a message
    if not has_data or not summary["overall"]:
        raise HTTPException(
            status_code=400, 
            detail="No test data available. The test may have completed too quickly or failed to collect stats."
        )
    
    return summary


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
    
    # Only generate PDF if it doesn't exist yet
    if not pdf_path.exists():
        try:
            from weasyprint import HTML
            
            # Read the HTML content
            with open(report_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Generate PDF
            HTML(string=html_content).write_pdf(pdf_path)
        except ImportError:
            raise HTTPException(
                status_code=500, 
                detail="PDF generation not available. Please install weasyprint."
            )
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
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all load test jobs, optionally filtered by project."""
    jobs = list(LOAD_TEST_JOBS.values())
    
    if project_id:
        # Authorization check - user must have access to the project
        assert_create_permission(db, project_id, current_user.id)
        jobs = [j for j in jobs if j.get("project_id") == project_id]
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "total": len(jobs),
        "jobs": jobs[:limit]
    }


@router.delete("/{job_id}")
def delete_load_test(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a load test job and its reports."""
    job = LOAD_TEST_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Authorization check - verify user has access to the project
    if job.get("project_id"):
        assert_create_permission(db, job["project_id"], current_user.id)
    
    # Delete reports
    report_dir = REPORTS_DIR / job_id
    if report_dir.exists():
        import shutil
        shutil.rmtree(report_dir)
    
    # Remove from tracking
    LOAD_TEST_JOBS.pop(job_id, None)
    JOB_QUEUES.pop(job_id, None)
    _save_jobs()
    
    return {"message": "Load test deleted successfully"}
