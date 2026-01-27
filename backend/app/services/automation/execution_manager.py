"""Execution Manager - Coordinates test execution with database integration.

This module manages the complete lifecycle of test executions:
- Orchestrates PlaywrightRunner for browser automation
- Integrates with VeriShip database models (TestCase, TestExecution)
- Updates execution status in PostgreSQL in real-time
- Stores execution results, screenshots, and traces
- Creates defects automatically on test failure
- Supports concurrent test execution with queue management
- Implements retry logic for flaky tests

Usage:
    manager = ExecutionManager(db_session)
    result = await manager.execute_test_case(test_case_id=123, config={...})
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.models import (
    TestCase,
    TestExecution,
    TestStatus,
    TestSuite,
    Defect,
    DefectSeverity,
    DefectStatus,
    Project,
)
from app.services.automation.playwright_runner import (
    PlaywrightRunner,
    ContextConfig,
    ActionResult,
    get_playwright_runner,
)
from app.config import settings

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Execution status states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ExecutionConfig:
    """Configuration for test execution."""
    browser_type: str = "chromium"
    headless: bool = True
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
    timeout: int = 30000
    base_url: Optional[str] = None
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    geolocation: Optional[Dict[str, float]] = None
    permissions: List[str] = field(default_factory=list)
    record_trace: bool = True
    record_video: bool = False
    screenshot_on_failure: bool = True
    screenshot_on_step: bool = False
    retry_count: int = 0
    retry_delay_ms: int = 1000
    environment: str = "development"
    extra_headers: Optional[Dict[str, str]] = None
    storage_state: Optional[Dict] = None
    
    def to_context_config(self) -> ContextConfig:
        """Convert to ContextConfig for PlaywrightRunner."""
        return ContextConfig(
            viewport=self.viewport,
            user_agent=self.user_agent,
            locale=self.locale,
            timezone_id=self.timezone_id,
            geolocation=self.geolocation,
            permissions=self.permissions,
            record_video=self.record_video,
            base_url=self.base_url,
            extra_http_headers=self.extra_headers,
            storage_state=self.storage_state,
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class StepResult:
    """Result of a single test step execution."""
    step_number: int
    action_type: str
    description: str
    selector: Optional[str]
    status: str  # passed, failed, skipped
    duration_ms: float
    timestamp: datetime
    value: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "action_type": self.action_type,
            "description": self.description,
            "selector": self.selector,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "error": self.error,
            "screenshot_path": self.screenshot_path,
        }


@dataclass
class ExecutionResult:
    """Complete result of a test execution."""
    execution_id: int
    test_case_id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: float
    steps: List[StepResult]
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    network_logs: Optional[List[Dict]] = None
    browser_type: str = "chromium"
    environment: str = "development"
    defect_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "test_case_id": self.test_case_id,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "steps": [s.to_dict() for s in self.steps],
            "error_message": self.error_message,
            "screenshot_path": self.screenshot_path,
            "trace_path": self.trace_path,
            "network_logs": self.network_logs,
            "browser_type": self.browser_type,
            "environment": self.environment,
            "defect_id": self.defect_id,
        }


class ExecutionQueue:
    """Simple async queue for managing concurrent executions."""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running: Dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._is_processing = False
    
    async def add(self, execution_id: str, coro: Callable) -> None:
        """Add an execution to the queue."""
        await self._queue.put((execution_id, coro))
        if not self._is_processing:
            asyncio.create_task(self._process_queue())
    
    async def _process_queue(self) -> None:
        """Process queued executions."""
        self._is_processing = True
        while not self._queue.empty():
            execution_id, coro = await self._queue.get()
            async with self._semaphore:
                task = asyncio.create_task(coro())
                self._running[execution_id] = task
                try:
                    await task
                finally:
                    del self._running[execution_id]
                    self._queue.task_done()
        self._is_processing = False
    
    def cancel(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        if execution_id in self._running:
            self._running[execution_id].cancel()
            return True
        return False
    
    @property
    def running_count(self) -> int:
        """Get count of running executions."""
        return len(self._running)
    
    @property
    def queued_count(self) -> int:
        """Get count of queued executions."""
        return self._queue.qsize()


class ExecutionManager:
    """Manages test execution lifecycle with database integration.
    
    This class coordinates:
    - Test case execution using PlaywrightRunner
    - Database updates for TestExecution records
    - Result storage (screenshots, traces, network logs)
    - Automatic defect creation on failures
    - Retry logic for flaky tests
    - Concurrent execution management
    
    Attributes:
        db: SQLAlchemy database session
        runner: PlaywrightRunner instance
        queue: ExecutionQueue for concurrent execution
        
    Example:
        >>> manager = ExecutionManager(db)
        >>> result = await manager.execute_test_case(
        ...     test_case_id=123,
        ...     config=ExecutionConfig(browser_type="firefox")
        ... )
    """
    
    def __init__(
        self,
        db: Session,
        runner: Optional[PlaywrightRunner] = None,
        max_concurrent: int = None,
    ):
        """Initialize ExecutionManager.
        
        Args:
            db: SQLAlchemy session for database operations
            runner: PlaywrightRunner instance (uses global if not provided)
            max_concurrent: Maximum concurrent executions
        """
        self.db = db
        self.runner = runner or get_playwright_runner()
        self.queue = ExecutionQueue(max_concurrent or settings.max_concurrent_executions)
        self._active_executions: Dict[int, Dict[str, Any]] = {}
        
        logger.info("ExecutionManager initialized")
    
    def _generate_run_id(self) -> str:
        """Generate a unique test run ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique = uuid.uuid4().hex[:6].upper()
        return f"RUN-{timestamp}-{unique}"
    
    async def execute_test_case(
        self,
        test_case_id: int,
        config: Optional[ExecutionConfig] = None,
        executed_by: str = "automation",
    ) -> ExecutionResult:
        """Execute a single test case.
        
        Args:
            test_case_id: ID of the test case to execute
            config: Execution configuration
            executed_by: User or system identifier
            
        Returns:
            ExecutionResult with complete execution details
            
        Raises:
            ValueError: If test case not found
            RuntimeError: If execution fails catastrophically
        """
        config = config or ExecutionConfig()
        
        # Fetch test case from database
        test_case = self.db.query(TestCase).filter(TestCase.id == test_case_id).first()
        if not test_case:
            raise ValueError(f"Test case {test_case_id} not found")
        
        # Create execution record
        run_id = self._generate_run_id()
        execution = TestExecution(
            test_case_id=test_case_id,
            test_run_id=run_id,
            status=TestStatus.IN_PROGRESS,
            executed_by=executed_by,
            executed_at=datetime.utcnow(),
            environment=config.environment,
            browser=config.browser_type,
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        logger.info(f"Starting execution {execution.id} for test case {test_case_id}")
        
        # Track active execution
        context_id = f"exec-{execution.id}"
        self._active_executions[execution.id] = {
            "context_id": context_id,
            "status": ExecutionStatus.RUNNING,
            "start_time": datetime.utcnow(),
        }
        
        start_time = datetime.utcnow()
        steps_results: List[StepResult] = []
        error_message: Optional[str] = None
        screenshot_path: Optional[str] = None
        trace_path: Optional[str] = None
        final_status = TestStatus.PASSED
        
        retry_count = 0
        max_retries = config.retry_count
        
        while retry_count <= max_retries:
            try:
                # Start browser if not running
                if not self.runner.is_running:
                    await self.runner.start(config.browser_type)
                
                # Create isolated context
                await self.runner.create_context(
                    context_id=context_id,
                    config=config.to_context_config(),
                )
                
                # Start tracing if enabled
                if config.record_trace:
                    await self.runner.start_trace(
                        context_id=context_id,
                        trace_name=f"test_{test_case_id}_{run_id}",
                    )
                
                # Create page
                await self.runner.new_page(context_id)
                
                # Execute test steps
                steps = test_case.test_steps or []
                
                if not steps and test_case.automation_script:
                    # Parse automation script if no steps defined
                    steps = self._parse_automation_script(test_case.automation_script)
                
                for step_num, step in enumerate(steps, 1):
                    step_result = await self._execute_step(
                        context_id=context_id,
                        step_number=step_num,
                        step=step,
                        config=config,
                    )
                    steps_results.append(step_result)
                    
                    # Update execution progress
                    self._active_executions[execution.id]["current_step"] = step_num
                    self._active_executions[execution.id]["total_steps"] = len(steps)
                    
                    if step_result.status == "failed":
                        final_status = TestStatus.FAILED
                        error_message = step_result.error
                        screenshot_path = step_result.screenshot_path
                        break
                
                # If all steps passed
                if final_status == TestStatus.PASSED:
                    break
                
                # Retry on failure
                if retry_count < max_retries:
                    retry_count += 1
                    logger.info(f"Retrying execution {execution.id}, attempt {retry_count + 1}")
                    await asyncio.sleep(config.retry_delay_ms / 1000)
                    steps_results = []
                    final_status = TestStatus.PASSED
                    error_message = None
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Execution {execution.id} error: {e}")
                final_status = TestStatus.FAILED
                error_message = str(e)
                
                # Capture error screenshot
                if config.screenshot_on_failure:
                    try:
                        screenshot_path = await self.runner.take_screenshot(context_id)
                    except Exception:
                        pass
                
                break
            
            finally:
                # Stop trace and get path
                try:
                    if config.record_trace and self.runner._tracing_active.get(context_id):
                        trace_path = await self.runner.stop_trace(context_id)
                except Exception as e:
                    logger.warning(f"Error stopping trace: {e}")
                
                # Get network logs
                network_logs = self.runner.get_network_logs(context_id)
                
                # Close context
                try:
                    if context_id in self.runner._contexts:
                        await self.runner.close_context(context_id)
                except Exception as e:
                    logger.warning(f"Error closing context: {e}")
        
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Update execution record
        execution.status = final_status
        execution.duration_seconds = int(duration_ms / 1000)
        execution.error_message = error_message
        execution.screenshots = [screenshot_path] if screenshot_path else []
        execution.output = json.dumps([s.to_dict() for s in steps_results])
        
        if final_status == TestStatus.FAILED:
            execution.flaky_count = (execution.flaky_count or 0) + 1
            if retry_count > 0:
                execution.is_flaky = True
        
        self.db.commit()
        
        # Create defect if failed and configured
        defect_id = None
        if final_status == TestStatus.FAILED:
            defect_id = await self._create_defect_for_failure(
                test_case=test_case,
                execution=execution,
                error_message=error_message,
                screenshot_path=screenshot_path,
            )
        
        # Cleanup active execution tracking
        if execution.id in self._active_executions:
            del self._active_executions[execution.id]
        
        result = ExecutionResult(
            execution_id=execution.id,
            test_case_id=test_case_id,
            status=final_status.value,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            steps=steps_results,
            error_message=error_message,
            screenshot_path=screenshot_path,
            trace_path=trace_path,
            network_logs=network_logs,
            browser_type=config.browser_type,
            environment=config.environment,
            defect_id=defect_id,
        )
        
        logger.info(f"Execution {execution.id} completed: {final_status.value}")
        return result
    
    async def _execute_step(
        self,
        context_id: str,
        step_number: int,
        step: Dict[str, Any],
        config: ExecutionConfig,
    ) -> StepResult:
        """Execute a single test step."""
        start_time = datetime.utcnow()
        
        action_type = step.get("type", step.get("action", ""))
        selector = step.get("selector", step.get("target", ""))
        description = step.get("description", f"Step {step_number}: {action_type}")
        
        # Build action kwargs from step data
        kwargs = {}
        if step.get("value"):
            kwargs["value"] = step["value"]
        if step.get("text"):
            kwargs["text"] = step["text"]
        if step.get("url"):
            kwargs["url"] = step["url"]
        if step.get("expected"):
            kwargs["expected"] = step["expected"]
        if step.get("timeout"):
            kwargs["timeout"] = step["timeout"]
        if step.get("wait_until"):
            kwargs["wait_until"] = step["wait_until"]
        if step.get("key"):
            kwargs["key"] = step["key"]
        if step.get("duration"):
            kwargs["duration"] = step["duration"]
        if step.get("duration_ms"):
            kwargs["duration"] = step["duration_ms"]
        
        # Handle HTTP step type for API testing
        if action_type == "http":
            return await self._execute_http_step(
                step_number=step_number,
                step=step,
                description=description,
                start_time=start_time,
            )
        
        # Handle assert step type
        if action_type == "assert":
            action_type = self._map_assert_action(step)
        
        # Handle delay step
        if action_type == "delay":
            action_type = "wait"
            kwargs["duration"] = step.get("duration_ms", 1000)
        
        # Execute action
        result = await self.runner.execute_action(
            action_type=action_type,
            selector=selector if selector else None,
            context_id=context_id,
            screenshot_on_error=config.screenshot_on_failure,
            **kwargs,
        )
        
        # Take screenshot if configured
        screenshot_path = result.screenshot_path
        if config.screenshot_on_step and result.success:
            try:
                screenshot_path = await self.runner.take_screenshot(context_id)
            except Exception:
                pass
        
        return StepResult(
            step_number=step_number,
            action_type=action_type,
            description=description,
            selector=selector,
            status="passed" if result.success else "failed",
            duration_ms=result.duration_ms,
            timestamp=start_time,
            value=result.value,
            error=result.error,
            screenshot_path=screenshot_path,
        )
    
    async def _execute_http_step(
        self,
        step_number: int,
        step: Dict[str, Any],
        description: str,
        start_time: datetime,
    ) -> StepResult:
        """Execute an HTTP request step (for API testing)."""
        import httpx
        
        method = step.get("method", "GET").upper()
        url = step.get("url", "")
        headers = step.get("headers", {})
        body = step.get("body")
        expected_status = step.get("expected_status")
        expected_contains = step.get("expected_contains")
        
        error = None
        status = "passed"
        value = None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body else None,
                    timeout=30.0,
                )
                
                value = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text[:1000] if response.text else None,
                }
                
                # Validate expectations
                if expected_status and response.status_code != expected_status:
                    status = "failed"
                    error = f"Expected status {expected_status}, got {response.status_code}"
                
                if expected_contains and expected_contains not in response.text:
                    status = "failed"
                    error = f"Expected response to contain '{expected_contains}'"
                    
        except Exception as e:
            status = "failed"
            error = str(e)
        
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return StepResult(
            step_number=step_number,
            action_type="http",
            description=description,
            selector=url,
            status=status,
            duration_ms=duration_ms,
            timestamp=start_time,
            value=value,
            error=error,
        )
    
    def _map_assert_action(self, step: Dict[str, Any]) -> str:
        """Map assert step to specific action type."""
        assertion_type = step.get("assertion_type", "text")
        
        mapping = {
            "text": "assert_text",
            "visible": "assert_visible",
            "hidden": "assert_hidden",
            "url": "assert_url",
            "title": "assert_title",
        }
        
        return mapping.get(assertion_type, "assert_text")
    
    def _parse_automation_script(self, script: str) -> List[Dict[str, Any]]:
        """Parse automation script into executable steps.
        
        Supports JSON format or simple DSL.
        """
        try:
            # Try JSON first
            steps = json.loads(script)
            if isinstance(steps, list):
                return steps
            if isinstance(steps, dict) and "steps" in steps:
                return steps["steps"]
        except json.JSONDecodeError:
            pass
        
        # Parse simple DSL format:
        # navigate|https://example.com
        # click|#button
        # fill|#input|value
        # assert_text|#result|expected
        
        steps = []
        for line_num, line in enumerate(script.strip().split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            parts = line.split("|")
            action = parts[0].strip().lower()
            
            step = {
                "type": action,
                "description": f"Step {line_num}: {action}",
            }
            
            if len(parts) > 1:
                if action == "navigate":
                    step["url"] = parts[1].strip()
                elif action in ("fill", "type"):
                    step["selector"] = parts[1].strip()
                    step["value"] = parts[2].strip() if len(parts) > 2 else ""
                elif action.startswith("assert"):
                    step["selector"] = parts[1].strip()
                    step["expected"] = parts[2].strip() if len(parts) > 2 else ""
                elif action == "wait":
                    step["duration"] = int(parts[1].strip())
                else:
                    step["selector"] = parts[1].strip()
            
            steps.append(step)
        
        return steps
    
    async def _create_defect_for_failure(
        self,
        test_case: TestCase,
        execution: TestExecution,
        error_message: Optional[str],
        screenshot_path: Optional[str],
    ) -> Optional[int]:
        """Automatically create a defect for test failure."""
        try:
            # Generate defect ID
            defect_count = self.db.query(Defect).filter(
                Defect.project_id == test_case.project_id
            ).count()
            defect_id_str = f"DEF-{defect_count + 1:04d}"
            
            defect = Defect(
                project_id=test_case.project_id,
                defect_id=defect_id_str,
                title=f"Test Failed: {test_case.title}",
                description=(
                    f"Automated test failure detected.\n\n"
                    f"**Test Case:** {test_case.test_case_id}\n"
                    f"**Title:** {test_case.title}\n"
                    f"**Execution ID:** {execution.test_run_id}\n"
                    f"**Browser:** {execution.browser}\n"
                    f"**Environment:** {execution.environment}\n\n"
                    f"**Error:**\n```\n{error_message}\n```\n\n"
                    f"**Screenshot:** {screenshot_path or 'N/A'}"
                ),
                severity=DefectSeverity.HIGH,
                status=DefectStatus.OPEN,
                test_case_id=test_case.id,
                found_by="Automation",
                root_cause="Automated Test Failure",
            )
            
            self.db.add(defect)
            self.db.commit()
            self.db.refresh(defect)
            
            logger.info(f"Created defect {defect_id_str} for failed test {test_case.test_case_id}")
            return defect.id
            
        except Exception as e:
            logger.error(f"Failed to create defect: {e}")
            return None
    
    async def execute_test_suite(
        self,
        suite_id: int,
        config: Optional[ExecutionConfig] = None,
        executed_by: str = "automation",
        parallel: bool = False,
    ) -> Dict[str, Any]:
        """Execute all test cases in a test suite.
        
        Args:
            suite_id: ID of the test suite
            config: Execution configuration
            executed_by: User or system identifier
            parallel: Run tests in parallel using separate contexts
            
        Returns:
            Summary of all test executions
        """
        config = config or ExecutionConfig()
        
        # Fetch test suite
        suite = self.db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            raise ValueError(f"Test suite {suite_id} not found")
        
        test_case_ids = suite.test_case_ids or []
        if not test_case_ids:
            return {
                "suite_id": suite_id,
                "suite_name": suite.name,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "results": [],
            }
        
        logger.info(f"Executing suite {suite_id} with {len(test_case_ids)} test cases")
        
        results: List[ExecutionResult] = []
        
        if parallel:
            # Execute in parallel
            tasks = [
                self.execute_test_case(tc_id, config, executed_by)
                for tc_id in test_case_ids
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            results = [
                r if isinstance(r, ExecutionResult)
                else ExecutionResult(
                    execution_id=0,
                    test_case_id=test_case_ids[i],
                    status="error",
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    duration_ms=0,
                    steps=[],
                    error_message=str(r),
                    browser_type=config.browser_type,
                    environment=config.environment,
                )
                for i, r in enumerate(results)
            ]
        else:
            # Execute sequentially
            for tc_id in test_case_ids:
                try:
                    result = await self.execute_test_case(tc_id, config, executed_by)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error executing test case {tc_id}: {e}")
                    results.append(ExecutionResult(
                        execution_id=0,
                        test_case_id=tc_id,
                        status="error",
                        start_time=datetime.utcnow(),
                        end_time=datetime.utcnow(),
                        duration_ms=0,
                        steps=[],
                        error_message=str(e),
                        browser_type=config.browser_type,
                        environment=config.environment,
                    ))
        
        # Calculate summary
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")
        
        return {
            "suite_id": suite_id,
            "suite_name": suite.name,
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "pass_rate": (passed / len(results) * 100) if results else 0,
            "total_duration_ms": sum(r.duration_ms for r in results),
            "results": [r.to_dict() for r in results],
        }
    
    async def stop_execution(self, execution_id: int) -> bool:
        """Stop a running execution.
        
        Args:
            execution_id: ID of the execution to stop
            
        Returns:
            True if stopped successfully
        """
        if execution_id not in self._active_executions:
            return False
        
        context_id = self._active_executions[execution_id].get("context_id")
        
        # Update status
        self._active_executions[execution_id]["status"] = ExecutionStatus.CANCELLED
        
        # Close context to stop execution
        if context_id and context_id in self.runner._contexts:
            try:
                await self.runner.close_context(context_id)
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
        
        # Update database
        execution = self.db.query(TestExecution).filter(
            TestExecution.id == execution_id
        ).first()
        
        if execution:
            execution.status = TestStatus.SKIPPED
            execution.error_message = "Execution cancelled by user"
            self.db.commit()
        
        # Remove from active
        del self._active_executions[execution_id]
        
        logger.info(f"Execution {execution_id} stopped")
        return True
    
    def get_execution_status(self, execution_id: int) -> Dict[str, Any]:
        """Get the current status of an execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Status information dictionary
        """
        # Check active executions first
        if execution_id in self._active_executions:
            active = self._active_executions[execution_id]
            return {
                "execution_id": execution_id,
                "status": active["status"].value,
                "is_running": True,
                "current_step": active.get("current_step", 0),
                "total_steps": active.get("total_steps", 0),
                "elapsed_ms": (datetime.utcnow() - active["start_time"]).total_seconds() * 1000,
            }
        
        # Check database
        execution = self.db.query(TestExecution).filter(
            TestExecution.id == execution_id
        ).first()
        
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        return {
            "execution_id": execution_id,
            "status": execution.status.value,
            "is_running": False,
            "duration_seconds": execution.duration_seconds,
            "executed_at": execution.executed_at.isoformat() if execution.executed_at else None,
            "executed_by": execution.executed_by,
            "browser": execution.browser,
            "environment": execution.environment,
            "error_message": execution.error_message,
        }
    
    def get_execution_trace(self, execution_id: int) -> Optional[str]:
        """Get the trace file path for an execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Path to trace file or None
        """
        import glob
        
        # Search for trace file
        pattern = f"{settings.traces_dir}/trace_exec-{execution_id}_*.zip"
        traces = glob.glob(pattern)
        
        if traces:
            return traces[0]
        
        return None
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Cancel all active executions
        for exec_id in list(self._active_executions.keys()):
            try:
                await self.stop_execution(exec_id)
            except Exception as e:
                logger.warning(f"Error stopping execution {exec_id}: {e}")
        
        logger.info("ExecutionManager cleaned up")


# Factory function for dependency injection
def get_execution_manager(db: Session) -> ExecutionManager:
    """Get ExecutionManager instance for dependency injection."""
    return ExecutionManager(db)
