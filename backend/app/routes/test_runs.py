import asyncio
import uuid
import shlex
import subprocess
import json
import re
import tempfile
import os
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement, User, UserProjectAssignment
from app.auth import get_current_user
from app.dependencies import assert_project_access
from app.config import settings
import requests

router = APIRouter()

# In-memory job queues: job_id -> asyncio.Queue[str]
JOB_QUEUES: Dict[str, asyncio.Queue] = {}


def _start_process_and_stream(job_id: str, cmd: str):
    """Start subprocess and push stdout/stderr lines into the asyncio queue."""
    loop = asyncio.get_event_loop()
    queue = JOB_QUEUES.get(job_id)
    if queue is None:
        return

    try:
        parts = shlex.split(cmd)
        proc = subprocess.Popen(
            parts, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            bufsize=1, 
            text=True
        )
    except Exception as e:
        loop.call_soon_threadsafe(queue.put_nowait, f"ERROR: failed to start process: {e}\n")
        loop.call_soon_threadsafe(queue.put_nowait, "__DONE__")
        return

    try:
        for line in proc.stdout:
            loop.call_soon_threadsafe(queue.put_nowait, line.rstrip('\n'))
    except Exception as e:
        loop.call_soon_threadsafe(queue.put_nowait, f"ERROR: reading process output: {e}")

    proc.wait()
    loop.call_soon_threadsafe(queue.put_nowait, f"PROCESS_EXIT_CODE: {proc.returncode}")
    loop.call_soon_threadsafe(queue.put_nowait, "__DONE__")


def _call_openrouter(api_key: str, user_message: str) -> str:
    """Call OpenRouter API for test code generation."""
    try:
        response = requests.post(
            settings.openrouter_api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": settings.openrouter_site_url,
                "X-Title": settings.openrouter_site_name,
                "Content-Type": "application/json"
            },
            json={
                "model": settings.openrouter_model,
                "messages": [{"role": "user", "content": user_message}]
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenRouter API error: {response.text}"
            )
        
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to call OpenRouter API: {str(e)}"
        )


def _validate_playwright_code(code: str) -> bool:
    """Validate that generated Playwright code is safe to execute."""
    dangerous_patterns = [
        r'__import__',
        r'eval\s*\(',
        r'exec\s*\(',
        r'subprocess',
        r'os\.system',
        r'open\s*\(',
        r'rmdir',
        r'remove\s*\(',
        r'os\.remove',
        r'os\.unlink',
        r'shutil',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return False
    
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError:
        return False
    
    return True


@router.post("/generate-and-run")
def generate_and_run_test(
    background_tasks: BackgroundTasks,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate Playwright test code from a requirement and execute it.
    Only users assigned to the project can run tests for its requirements.
    """
    job_id = str(uuid.uuid4())
    requirement_id = payload.get("requirement_id")
    target_base_url = payload.get("target_base_url", "http://localhost:3000")
    browser = payload.get("browser", "chromium")
    
    if not requirement_id:
        raise HTTPException(status_code=400, detail="Missing 'requirement_id'")

    # Fetch requirement
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # === OWNERSHIP CHECK using centralized helper ===
    assert_project_access(db, requirement.project_id, current_user.id)

    # Create queue for this job
    queue: asyncio.Queue = asyncio.Queue()
    JOB_QUEUES[job_id] = queue
    
    def _generate_and_execute():
        loop = asyncio.get_event_loop()
        
        try:
            loop.call_soon_threadsafe(queue.put_nowait, "📋 Generating Playwright test code from requirement...")
            
            prompt = f"""Generate a complete Playwright test script for the following requirement:

Requirement: {requirement.title}
Description: {requirement.description}
Target URL: {target_base_url}

Generate production-ready Playwright code that:
1. Tests the requirement thoroughly
2. Uses best practices (waits, selectors, assertions)
3. Includes error handling
4. Is ready to execute immediately

Return ONLY the TypeScript Playwright code, no explanations.
The code should be a complete test file that can be run with: npx playwright test <filename>

Wrap the code in ```typescript"""

            ai_response = _call_openrouter(
                settings.openrouter_testcase_api_key,
                prompt
            )
            
            # Extract code from markdown block
            code_match = re.search(r'```(?:typescript|javascript|ts|js)?\n(.*?)\n```', ai_response, re.DOTALL)
            test_code = code_match.group(1).strip() if code_match else ai_response.strip()
            
            loop.call_soon_threadsafe(queue.put_nowait, "✓ Test code generated successfully")
            loop.call_soon_threadsafe(queue.put_nowait, "🔍 Validating code...")
            
            if not _validate_playwright_code(test_code):
                loop.call_soon_threadsafe(queue.put_nowait, "❌ Validation failed: Code contains unsafe patterns or syntax errors")
                loop.call_soon_threadsafe(queue.put_nowait, "__DONE__")
                return
            
            loop.call_soon_threadsafe(queue.put_nowait, "✓ Code validation passed")
            
            # Write to temp file and run
            with tempfile.NamedTemporaryFile(mode='w', suffix='.spec.ts', delete=False) as f:
                f.write(test_code)
                temp_file = f.name
            
            try:
                loop.call_soon_threadsafe(queue.put_nowait, f"🚀 Starting test execution: {temp_file}")
                cmd = f"npx playwright test {temp_file} --reporter=list"
                _start_process_and_stream(job_id, cmd)
            finally:
                # Cleanup
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        except HTTPException as e:
            loop.call_soon_threadsafe(queue.put_nowait, f"ERROR: {e.detail}")
            loop.call_soon_threadsafe(queue.put_nowait, "__DONE__")
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, f"ERROR: {str(e)}")
            loop.call_soon_threadsafe(queue.put_nowait, "__DONE__")
    
    # Start the generation + execution in background
    background_tasks.add_task(_generate_and_execute)
    
    return {
        "job_id": job_id,
        "requirement": {
            "id": requirement.id,
            "requirement_id": requirement.requirement_id,
            "title": requirement.title,
            "description": requirement.description
        }
    }


async def _sse_generator(job_id: str):
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
def stream_test_run_events(job_id: str):
    """SSE endpoint streaming logs for a job id."""
    return StreamingResponse(_sse_generator(job_id), media_type="text/event-stream")