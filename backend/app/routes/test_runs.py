import asyncio
import uuid
import shlex
import subprocess
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()

# In-memory job queues: job_id -> asyncio.Queue[str]
JOB_QUEUES: Dict[str, asyncio.Queue] = {}


def _start_process_and_stream(job_id: str, cmd: str):
    """Start subprocess and push stdout/stderr lines into the asyncio queue."""
    loop = asyncio.get_event_loop()
    queue = JOB_QUEUES.get(job_id)
    if queue is None:
        return

    # Start the subprocess
    # Use shell=False for safety; split the command
    try:
        parts = shlex.split(cmd)
        proc = subprocess.Popen(parts, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, text=True)
    except Exception as e:
        loop.call_soon_threadsafe(queue.put_nowait, f"ERROR: failed to start process: {e}\n")
        loop.call_soon_threadsafe(queue.put_nowait, "__DONE__")
        return

    # Read lines and forward to queue
    try:
        for line in proc.stdout:
            loop.call_soon_threadsafe(queue.put_nowait, line.rstrip('\n'))
    except Exception as e:
        loop.call_soon_threadsafe(queue.put_nowait, f"ERROR: reading process output: {e}")

    proc.wait()
    loop.call_soon_threadsafe(queue.put_nowait, f"PROCESS_EXIT_CODE: {proc.returncode}")
    loop.call_soon_threadsafe(queue.put_nowait, "__DONE__")


@router.post("/start")
def start_test_run(background_tasks: BackgroundTasks, payload: dict):
    """Start a test run.

    Payload example:
      { "type": "e2e", "cmd": "npx playwright test --config=load-tests/playwright.config.ts" }

    The handler will return a `job_id`. Use the SSE endpoint to stream logs.
    """
    job_id = str(uuid.uuid4())
    cmd = payload.get("cmd")
    if not cmd:
        raise HTTPException(status_code=400, detail="Missing 'cmd' in payload")

    queue: asyncio.Queue = asyncio.Queue()
    JOB_QUEUES[job_id] = queue

    # Run the process in a background thread to avoid blocking the event loop
    background_tasks.add_task(_start_process_and_stream, job_id, cmd)

    return {"job_id": job_id}


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
            # Escape data newlines
            yield f"data: {line}\n\n"
    finally:
        # cleanup queue
        JOB_QUEUES.pop(job_id, None)


@router.get("/{job_id}/events")
def stream_test_run_events(job_id: str):
    """SSE endpoint streaming stdout lines for a job id."""
    return StreamingResponse(_sse_generator(job_id), media_type="text/event-stream")
