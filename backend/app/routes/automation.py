"""Automation API routes for Playwright test execution.

This module provides REST endpoints for:
- Test case and suite execution
- Execution status and results
- Trace and screenshot retrieval
- Browser and context management
- Real-time execution monitoring

Endpoints:
    POST   /execute/test-case/{test_case_id}  - Execute a single test case
    POST   /execute/test-suite/{suite_id}     - Execute a test suite
    POST   /execute/manual                    - Execute manual test with steps
    GET    /executions/{execution_id}         - Get execution details
    GET    /executions/{execution_id}/status  - Get execution status
    GET    /executions/{execution_id}/trace   - Get execution trace file
    GET    /executions/{execution_id}/screenshot - Get execution screenshot
    DELETE /executions/{execution_id}         - Stop running execution
    GET    /browsers                          - List available browsers
    POST   /contexts                          - Create browser context
    GET    /contexts                          - List active contexts
    DELETE /contexts/{context_id}             - Close a context
    POST   /actions                           - Execute a single action
    GET    /network-logs/{context_id}         - Get network logs
    GET    /status                            - Get runner status
    GET    /health                            - Health check
"""

import os
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TestCase, TestExecution, TestSuite, TestStatus, User
from app.auth import get_current_user
from app.dependencies import assert_create_permission, audit_log
from app.schemas.automation import (
    ExecutionRequest,
    SuiteExecutionRequest,
    ManualTestRequest,
    ContextCreateRequest,
    ActionRequest,
    ExecutionResponse,
    ExecutionStatusResponse,
    SuiteExecutionResponse,
    TraceResponse,
    ScreenshotResponse,
    BrowsersResponse,
    BrowserInfo,
    ContextCreateResponse,
    ContextListResponse,
    ContextInfo,
    ActionResultResponse,
    NetworkLogsResponse,
    NetworkLogEntry,
    RunnerStatusResponse,
    HealthResponse,
    StepResultResponse,
)
from app.services.automation.playwright_runner import (
    PlaywrightRunner,
    get_playwright_runner,
    cleanup_playwright_runner,
    BrowserType,
    ContextConfig,
)
from app.services.automation.execution_manager import (
    ExecutionManager,
    ExecutionConfig,
    get_execution_manager,
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Dependencies ============

def get_runner() -> PlaywrightRunner:
    """Dependency to get PlaywrightRunner instance."""
    return get_playwright_runner()


def get_manager(db: Session = Depends(get_db)) -> ExecutionManager:
    """Dependency to get ExecutionManager instance."""
    return get_execution_manager(db)


# ============ Execution Endpoints ============

@router.post(
    "/execute/test-case/{test_case_id}",
    response_model=ExecutionResponse,
    summary="Execute a test case",
    description="Execute a single test case using Playwright automation"
)
async def execute_test_case(
    test_case_id: int,
    request: Optional[ExecutionRequest] = None,
    executed_by: str = Query(default="automation", description="User or system executing the test"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a single test case.
    
    Args:
        test_case_id: ID of the test case to execute
        request: Execution configuration
        executed_by: User or system identifier
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        ExecutionResponse with complete execution details
    """
    # Verify test case exists
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail=f"Test case {test_case_id} not found")
    
    # Authorization check - user must have create permission on the project
    assert_create_permission(db, test_case.project_id, current_user.id)
    
    # Build execution config
    config = None
    if request:
        config = ExecutionConfig(
            browser_type=request.browser_type,
            headless=request.headless,
            viewport=request.viewport.model_dump() if request.viewport else {"width": 1280, "height": 720},
            timeout=request.timeout,
            base_url=request.base_url,
            user_agent=request.user_agent,
            locale=request.locale,
            timezone_id=request.timezone_id,
            geolocation=request.geolocation.model_dump() if request.geolocation else None,
            permissions=request.permissions,
            record_trace=request.record_trace,
            record_video=request.record_video,
            screenshot_on_failure=request.screenshot_on_failure,
            screenshot_on_step=request.screenshot_on_step,
            retry_count=request.retry_count,
            retry_delay_ms=request.retry_delay_ms,
            environment=request.environment,
            extra_headers=request.extra_headers,
            storage_state=request.storage_state,
        )
    
    manager = get_execution_manager(db)
    
    try:
        result = await manager.execute_test_case(
            test_case_id=test_case_id,
            config=config,
            executed_by=executed_by,
        )
        
        return ExecutionResponse(
            execution_id=result.execution_id,
            test_case_id=result.test_case_id,
            status=result.status,
            start_time=result.start_time,
            end_time=result.end_time,
            duration_ms=result.duration_ms,
            steps=[
                StepResultResponse(
                    step_number=s.step_number,
                    action_type=s.action_type,
                    description=s.description,
                    selector=s.selector,
                    status=s.status,
                    duration_ms=s.duration_ms,
                    timestamp=s.timestamp,
                    value=s.value,
                    error=s.error,
                    screenshot_path=s.screenshot_path,
                )
                for s in result.steps
            ],
            error_message=result.error_message,
            screenshot_path=result.screenshot_path,
            trace_path=result.trace_path,
            network_logs_count=len(result.network_logs) if result.network_logs else 0,
            browser_type=result.browser_type,
            environment=result.environment,
            defect_id=result.defect_id,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.post(
    "/execute/test-suite/{suite_id}",
    response_model=SuiteExecutionResponse,
    summary="Execute a test suite",
    description="Execute all test cases in a test suite"
)
async def execute_test_suite(
    suite_id: int,
    request: Optional[SuiteExecutionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute all test cases in a test suite.
    
    Args:
        suite_id: ID of the test suite
        request: Execution configuration and options
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        SuiteExecutionResponse with summary and individual results
    """
    # Verify suite exists
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail=f"Test suite {suite_id} not found")
    
    # Authorization check - user must have create permission on the project
    assert_create_permission(db, suite.project_id, current_user.id)
    
    # Build config
    config = None
    parallel = False
    executed_by = "automation"
    
    if request:
        parallel = request.parallel
        executed_by = request.executed_by
        if request.config:
            config = ExecutionConfig(
                browser_type=request.config.browser_type,
                headless=request.config.headless,
                viewport=request.config.viewport.model_dump() if request.config.viewport else {"width": 1280, "height": 720},
                timeout=request.config.timeout,
                base_url=request.config.base_url,
                record_trace=request.config.record_trace,
                screenshot_on_failure=request.config.screenshot_on_failure,
                retry_count=request.config.retry_count,
                environment=request.config.environment,
            )
    
    manager = get_execution_manager(db)
    
    try:
        result = await manager.execute_test_suite(
            suite_id=suite_id,
            config=config,
            executed_by=executed_by,
            parallel=parallel,
        )
        
        return SuiteExecutionResponse(
            suite_id=result["suite_id"],
            suite_name=result["suite_name"],
            total=result["total"],
            passed=result["passed"],
            failed=result["failed"],
            skipped=result["skipped"],
            errors=result.get("errors", 0),
            pass_rate=result["pass_rate"],
            total_duration_ms=result["total_duration_ms"],
            results=[
                ExecutionResponse(**r) for r in result["results"]
            ],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Suite execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Suite execution failed: {str(e)}")


@router.post(
    "/execute/manual",
    response_model=ExecutionResponse,
    summary="Execute manual test",
    description="Execute a test with provided steps (not from database)"
)
async def execute_manual_test(
    request: ManualTestRequest,
    db: Session = Depends(get_db),
):
    """Execute a manual test with provided steps.
    
    Useful for ad-hoc testing or when test steps are generated dynamically.
    """
    # Create a temporary test case structure
    runner = get_playwright_runner()
    manager = get_execution_manager(db)
    
    config = None
    if request.config:
        config = ExecutionConfig(
            browser_type=request.config.browser_type,
            headless=request.config.headless,
            timeout=request.config.timeout,
            base_url=request.config.base_url,
            record_trace=request.config.record_trace,
            screenshot_on_failure=request.config.screenshot_on_failure,
        )
    else:
        config = ExecutionConfig()
    
    start_time = datetime.utcnow()
    context_id = f"manual-{start_time.strftime('%Y%m%d%H%M%S')}"
    steps_results = []
    error_message = None
    screenshot_path = None
    trace_path = None
    final_status = "passed"
    
    try:
        # Start browser if needed
        if not runner.is_running:
            await runner.start(config.browser_type)
        
        # Create context
        await runner.create_context(context_id, config.to_context_config())
        
        # Start trace
        if config.record_trace:
            await runner.start_trace(context_id, f"manual_{context_id}")
        
        # Create page
        await runner.new_page(context_id)
        
        # Execute steps
        for step_num, step in enumerate(request.steps, 1):
            step_start = datetime.utcnow()
            step_data = step.model_dump()
            
            action_type = step_data.get("type", "")
            selector = step_data.get("selector")
            
            # Build kwargs
            kwargs = {}
            for key in ["url", "value", "text", "expected", "expected_status", "expected_contains", 
                       "method", "headers", "body", "timeout", "duration_ms"]:
                if step_data.get(key) is not None:
                    if key == "duration_ms":
                        kwargs["duration"] = step_data[key]
                    else:
                        kwargs[key] = step_data[key]
            
            result = await runner.execute_action(
                action_type=action_type,
                selector=selector,
                context_id=context_id,
                **kwargs,
            )
            
            step_result = StepResultResponse(
                step_number=step_num,
                action_type=action_type,
                description=step_data.get("description", f"Step {step_num}"),
                selector=selector,
                status="passed" if result.success else "failed",
                duration_ms=result.duration_ms,
                timestamp=step_start,
                value=result.value,
                error=result.error,
                screenshot_path=result.screenshot_path,
            )
            steps_results.append(step_result)
            
            if not result.success:
                final_status = "failed"
                error_message = result.error
                screenshot_path = result.screenshot_path
                break
                
    except Exception as e:
        final_status = "failed"
        error_message = str(e)
        logger.error(f"Manual test execution failed: {e}")
    
    finally:
        # Stop trace
        try:
            if config.record_trace and runner._tracing_active.get(context_id):
                trace_path = await runner.stop_trace(context_id)
        except Exception:
            pass
        
        # Close context
        try:
            if context_id in runner._contexts:
                await runner.close_context(context_id)
        except Exception:
            pass
    
    end_time = datetime.utcnow()
    duration_ms = (end_time - start_time).total_seconds() * 1000
    
    return ExecutionResponse(
        execution_id=0,  # No database record for manual tests
        test_case_id=0,
        status=final_status,
        start_time=start_time,
        end_time=end_time,
        duration_ms=duration_ms,
        steps=steps_results,
        error_message=error_message,
        screenshot_path=screenshot_path,
        trace_path=trace_path,
        network_logs_count=len(runner.get_network_logs(context_id)) if context_id in runner._network_logs else 0,
        browser_type=config.browser_type,
        environment=config.environment,
    )


# ============ Execution Status/Results Endpoints ============

@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionStatusResponse,
    summary="Get execution details",
    description="Get detailed status and results of an execution"
)
async def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
):
    """Get execution details and results."""
    manager = get_execution_manager(db)
    
    try:
        status = manager.get_execution_status(execution_id)
        return ExecutionStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/executions/{execution_id}/status",
    response_model=ExecutionStatusResponse,
    summary="Get execution status",
    description="Get current status of an execution (useful for polling)"
)
async def get_execution_status(
    execution_id: int,
    db: Session = Depends(get_db),
):
    """Get current execution status for polling."""
    manager = get_execution_manager(db)
    
    try:
        status = manager.get_execution_status(execution_id)
        return ExecutionStatusResponse(**status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/executions/{execution_id}/trace",
    summary="Get execution trace",
    description="Download or get info about execution trace file"
)
async def get_execution_trace(
    execution_id: int,
    download: bool = Query(default=False, description="Download trace file"),
    db: Session = Depends(get_db),
):
    """Get trace file for an execution."""
    manager = get_execution_manager(db)
    trace_path = manager.get_execution_trace(execution_id)
    
    if not trace_path or not os.path.exists(trace_path):
        return TraceResponse(
            execution_id=execution_id,
            trace_path=None,
            download_url=None,
            exists=False,
        )
    
    if download:
        return FileResponse(
            trace_path,
            media_type="application/zip",
            filename=os.path.basename(trace_path),
        )
    
    return TraceResponse(
        execution_id=execution_id,
        trace_path=trace_path,
        download_url=f"/api/automation/executions/{execution_id}/trace?download=true",
        exists=True,
    )


@router.get(
    "/executions/{execution_id}/screenshot",
    summary="Get execution screenshot",
    description="Get screenshot from execution (if captured)"
)
async def get_execution_screenshot(
    execution_id: int,
    download: bool = Query(default=False, description="Download screenshot"),
    db: Session = Depends(get_db),
):
    """Get screenshot for an execution."""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    screenshots = execution.screenshots or []
    if not screenshots:
        raise HTTPException(status_code=404, detail="No screenshots available for this execution")
    
    screenshot_path = screenshots[0]
    if not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Screenshot file not found")
    
    if download:
        return FileResponse(
            screenshot_path,
            media_type="image/png",
            filename=os.path.basename(screenshot_path),
        )
    
    return ScreenshotResponse(
        execution_id=execution_id,
        screenshot_path=screenshot_path,
        download_url=f"/api/automation/executions/{execution_id}/screenshot?download=true",
        timestamp=execution.executed_at,
    )


@router.delete(
    "/executions/{execution_id}",
    summary="Stop execution",
    description="Stop a running test execution"
)
async def stop_execution(
    execution_id: int,
    db: Session = Depends(get_db),
):
    """Stop a running execution."""
    manager = get_execution_manager(db)
    
    stopped = await manager.stop_execution(execution_id)
    
    if not stopped:
        raise HTTPException(
            status_code=404,
            detail=f"Execution {execution_id} not found or not running"
        )
    
    return {"message": f"Execution {execution_id} stopped", "execution_id": execution_id}


# ============ Browser Management Endpoints ============

@router.get(
    "/browsers",
    response_model=BrowsersResponse,
    summary="List available browsers",
    description="Get list of available browser types for testing"
)
async def list_browsers():
    """List available browsers."""
    runner = get_playwright_runner()
    
    browsers = [
        BrowserInfo(
            type=bt.value,
            name=bt.value.capitalize(),
            available=True,
        )
        for bt in BrowserType
    ]
    
    return BrowsersResponse(
        browsers=browsers,
        current_browser=runner.browser_type,
        is_running=runner.is_running,
    )


@router.post(
    "/browsers/start/{browser_type}",
    summary="Start browser",
    description="Start a specific browser type"
)
async def start_browser(browser_type: str):
    """Start a browser."""
    runner = get_playwright_runner()
    
    try:
        await runner.start(browser_type)
        return {
            "message": f"Browser {browser_type} started",
            "browser_type": browser_type,
            "is_running": True,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start browser: {str(e)}")


@router.post(
    "/browsers/stop",
    summary="Stop browser",
    description="Stop the current browser"
)
async def stop_browser():
    """Stop the browser."""
    runner = get_playwright_runner()
    
    if not runner.is_running:
        return {"message": "Browser not running", "is_running": False}
    
    await runner.stop()
    return {"message": "Browser stopped", "is_running": False}


# ============ Context Management Endpoints ============

@router.post(
    "/contexts",
    response_model=ContextCreateResponse,
    summary="Create browser context",
    description="Create an isolated browser context for testing"
)
async def create_context(request: ContextCreateRequest):
    """Create a new browser context."""
    runner = get_playwright_runner()
    
    # Start browser if needed
    if not runner.is_running:
        await runner.start(request.browser_type)
    
    # Build context config
    config = ContextConfig(
        viewport=request.viewport.model_dump() if request.viewport else {"width": 1280, "height": 720},
        user_agent=request.user_agent,
        locale=request.locale,
        timezone_id=request.timezone_id,
        geolocation=request.geolocation.model_dump() if request.geolocation else None,
        permissions=request.permissions,
        color_scheme=request.color_scheme,
        device_scale_factor=request.device_scale_factor,
        is_mobile=request.is_mobile,
        has_touch=request.has_touch,
        javascript_enabled=request.javascript_enabled,
        accept_downloads=request.accept_downloads,
        ignore_https_errors=request.ignore_https_errors,
        offline=request.offline,
        base_url=request.base_url,
    )
    
    try:
        context_id = await runner.create_context(
            context_id=request.context_id,
            config=config,
        )
        
        return ContextCreateResponse(
            context_id=context_id,
            browser_type=runner.browser_type,
            created_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create context: {str(e)}")


@router.get(
    "/contexts",
    response_model=ContextListResponse,
    summary="List contexts",
    description="List all active browser contexts"
)
async def list_contexts():
    """List all active contexts."""
    runner = get_playwright_runner()
    
    contexts = runner.list_contexts()
    
    return ContextListResponse(
        contexts=[ContextInfo(**ctx) for ctx in contexts],
        count=len(contexts),
    )


@router.get(
    "/contexts/{context_id}",
    response_model=ContextInfo,
    summary="Get context info",
    description="Get information about a specific context"
)
async def get_context(context_id: str):
    """Get context information."""
    runner = get_playwright_runner()
    
    try:
        info = runner.get_context_info(context_id)
        return ContextInfo(**info)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Context {context_id} not found")


@router.delete(
    "/contexts/{context_id}",
    summary="Close context",
    description="Close a browser context"
)
async def close_context(context_id: str):
    """Close a browser context."""
    runner = get_playwright_runner()
    
    try:
        await runner.close_context(context_id)
        return {"message": f"Context {context_id} closed", "context_id": context_id}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Context {context_id} not found")


# ============ Action Execution Endpoints ============

@router.post(
    "/actions",
    response_model=ActionResultResponse,
    summary="Execute action",
    description="Execute a single action in a browser context"
)
async def execute_action(request: ActionRequest):
    """Execute a single browser action."""
    runner = get_playwright_runner()
    
    if not runner.is_running:
        await runner.start("chromium")
    
    # Create context if needed
    context_id = request.context_id
    if not context_id or context_id not in runner._contexts:
        context_id = await runner.create_context()
        await runner.new_page(context_id)
    
    # Build kwargs
    kwargs = {}
    action_params = [
        "url", "value", "text", "key", "expected", "attribute", "duration",
        "timeout", "wait_until", "full_page", "button", "click_count", "force",
        "files", "target", "expression", "method", "headers", "body",
        "expected_status", "expected_contains"
    ]
    
    for param in action_params:
        val = getattr(request, param, None)
        if val is not None:
            kwargs[param] = val
    
    try:
        result = await runner.execute_action(
            action_type=request.action_type,
            selector=request.selector,
            context_id=context_id,
            page_id=request.page_id,
            **kwargs,
        )
        
        return ActionResultResponse(
            success=result.success,
            action_type=result.action_type,
            selector=result.selector,
            duration_ms=result.duration_ms,
            timestamp=result.timestamp,
            value=result.value,
            error=result.error,
            screenshot_path=result.screenshot_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")


# ============ Network Logs Endpoints ============

@router.get(
    "/network-logs/{context_id}",
    response_model=NetworkLogsResponse,
    summary="Get network logs",
    description="Get captured network logs for a context"
)
async def get_network_logs(context_id: str):
    """Get network logs for a context."""
    runner = get_playwright_runner()
    
    if context_id not in runner._network_logs:
        raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
    
    logs = runner.get_network_logs(context_id)
    
    return NetworkLogsResponse(
        context_id=context_id,
        logs=[NetworkLogEntry(**log) for log in logs],
        count=len(logs),
    )


@router.delete(
    "/network-logs/{context_id}",
    summary="Clear network logs",
    description="Clear network logs for a context"
)
async def clear_network_logs(context_id: str):
    """Clear network logs for a context."""
    runner = get_playwright_runner()
    
    if context_id not in runner._network_logs:
        raise HTTPException(status_code=404, detail=f"Context {context_id} not found")
    
    runner.clear_network_logs(context_id)
    return {"message": f"Network logs cleared for context {context_id}"}


# ============ Status/Health Endpoints ============

@router.get(
    "/status",
    response_model=RunnerStatusResponse,
    summary="Get runner status",
    description="Get status of the Playwright runner"
)
async def get_runner_status(db: Session = Depends(get_db)):
    """Get current runner status."""
    runner = get_playwright_runner()
    manager = get_execution_manager(db)
    
    return RunnerStatusResponse(
        is_running=runner.is_running,
        browser_type=runner.browser_type,
        contexts_count=len(runner._contexts),
        active_executions_count=len(manager._active_executions),
        queued_executions_count=manager.queue.queued_count,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check health of automation service"
)
async def health_check():
    """Health check for automation service."""
    runner = get_playwright_runner()
    
    return HealthResponse(
        status="healthy",
        service="VeriShip Playwright Automation",
        playwright_running=runner.is_running,
        browser_type=runner.browser_type,
        contexts=len(runner._contexts),
        timestamp=datetime.utcnow(),
    )


# ============ Cleanup on shutdown ============

async def shutdown_automation():
    """Cleanup automation resources on shutdown."""
    await cleanup_playwright_runner()
