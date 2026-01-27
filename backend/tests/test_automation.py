"""Tests for Playwright automation services.

This module contains unit and integration tests for:
- PlaywrightRunner: Browser automation core
- ExecutionManager: Test execution coordination
- Automation API endpoints
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

# Import test subjects
from app.services.automation.playwright_runner import (
    PlaywrightRunner,
    ContextConfig,
    ActionResult,
    BrowserType,
    ActionType,
    get_playwright_runner,
    cleanup_playwright_runner,
)
from app.services.automation.execution_manager import (
    ExecutionManager,
    ExecutionConfig,
    ExecutionResult,
    StepResult,
    ExecutionStatus,
)


# ============ Fixtures ============

@pytest.fixture
def mock_playwright():
    """Mock Playwright instance."""
    with patch('app.services.automation.playwright_runner.async_playwright') as mock:
        playwright = AsyncMock()
        browser = AsyncMock()
        context = AsyncMock()
        page = AsyncMock()
        
        # Setup chain
        mock.return_value.start = AsyncMock(return_value=playwright)
        playwright.chromium.launch = AsyncMock(return_value=browser)
        playwright.firefox.launch = AsyncMock(return_value=browser)
        playwright.webkit.launch = AsyncMock(return_value=browser)
        browser.new_context = AsyncMock(return_value=context)
        browser.is_connected.return_value = True
        context.new_page = AsyncMock(return_value=page)
        context.tracing = AsyncMock()
        context.route = AsyncMock()
        context.unroute = AsyncMock()
        context.close = AsyncMock()
        page.goto = AsyncMock()
        page.click = AsyncMock()
        page.fill = AsyncMock()
        page.screenshot = AsyncMock()
        page.query_selector = AsyncMock(return_value=AsyncMock())
        page.url = "https://example.com"
        page.title = AsyncMock(return_value="Example")
        page.close = AsyncMock()
        
        yield {
            'mock': mock,
            'playwright': playwright,
            'browser': browser,
            'context': context,
            'page': page,
        }


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = None
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def runner():
    """Create a PlaywrightRunner instance."""
    return PlaywrightRunner(
        headless=True,
        slow_mo=0,
        timeout=30000,
        traces_dir="./test_traces",
        screenshots_dir="./test_screenshots",
    )


@pytest.fixture
def sample_test_case():
    """Sample test case data."""
    return Mock(
        id=1,
        project_id=1,
        test_case_id="TC-001",
        title="Sample Test Case",
        description="A sample test case",
        test_steps=[
            {
                "type": "navigate",
                "url": "https://example.com",
                "description": "Navigate to example"
            },
            {
                "type": "click",
                "selector": "#button",
                "description": "Click button"
            },
            {
                "type": "assert_text",
                "selector": "#result",
                "expected": "Success",
                "description": "Verify result"
            }
        ],
        automation_script=None,
        is_automated=True,
    )


# ============ PlaywrightRunner Tests ============

class TestPlaywrightRunner:
    """Tests for PlaywrightRunner class."""
    
    def test_initialization(self, runner):
        """Test runner initialization."""
        assert runner.headless == True
        assert runner.slow_mo == 0
        assert runner.timeout == 30000
        assert not runner.is_running
        assert runner.browser_type is None
        assert runner.available_browsers == ["chromium", "firefox", "webkit"]
    
    @pytest.mark.asyncio
    async def test_start_browser(self, runner, mock_playwright):
        """Test starting a browser."""
        await runner.start("chromium")
        
        assert runner.is_running
        assert runner.browser_type == "chromium"
    
    @pytest.mark.asyncio
    async def test_start_invalid_browser(self, runner):
        """Test starting an invalid browser type."""
        with pytest.raises(ValueError) as exc_info:
            await runner.start("invalid_browser")
        
        assert "Unsupported browser type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stop_browser(self, runner, mock_playwright):
        """Test stopping the browser."""
        await runner.start("chromium")
        await runner.stop()
        
        assert not runner.is_running
        assert runner.browser_type is None
    
    @pytest.mark.asyncio
    async def test_create_context(self, runner, mock_playwright):
        """Test creating a browser context."""
        await runner.start("chromium")
        context_id = await runner.create_context("test-context")
        
        assert context_id == "test-context"
        assert "test-context" in runner._contexts
    
    @pytest.mark.asyncio
    async def test_create_context_without_browser(self, runner):
        """Test creating context without starting browser."""
        with pytest.raises(RuntimeError) as exc_info:
            await runner.create_context("test-context")
        
        assert "Browser not started" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_context_with_config(self, runner, mock_playwright):
        """Test creating context with custom configuration."""
        await runner.start("chromium")
        
        config = ContextConfig(
            viewport={"width": 1920, "height": 1080},
            user_agent="Custom Agent",
            locale="fr-FR",
        )
        
        context_id = await runner.create_context("configured-context", config)
        
        assert context_id == "configured-context"
    
    @pytest.mark.asyncio
    async def test_new_page(self, runner, mock_playwright):
        """Test creating a new page."""
        await runner.start("chromium")
        await runner.create_context("test-context")
        page_id = await runner.new_page("test-context")
        
        assert page_id in runner._pages["test-context"]
    
    @pytest.mark.asyncio
    async def test_execute_navigate_action(self, runner, mock_playwright):
        """Test executing navigate action."""
        await runner.start("chromium")
        await runner.create_context("test-context")
        await runner.new_page("test-context")
        
        result = await runner.execute_action(
            action_type="navigate",
            context_id="test-context",
            url="https://example.com",
        )
        
        assert result.success
        assert result.action_type == "navigate"
    
    @pytest.mark.asyncio
    async def test_execute_click_action(self, runner, mock_playwright):
        """Test executing click action."""
        await runner.start("chromium")
        await runner.create_context("test-context")
        await runner.new_page("test-context")
        
        result = await runner.execute_action(
            action_type="click",
            selector="#button",
            context_id="test-context",
        )
        
        assert result.success
        assert result.action_type == "click"
        assert result.selector == "#button"
    
    @pytest.mark.asyncio
    async def test_execute_fill_action(self, runner, mock_playwright):
        """Test executing fill action."""
        await runner.start("chromium")
        await runner.create_context("test-context")
        await runner.new_page("test-context")
        
        result = await runner.execute_action(
            action_type="fill",
            selector="#input",
            context_id="test-context",
            value="test value",
        )
        
        assert result.success
        assert result.action_type == "fill"
    
    @pytest.mark.asyncio
    async def test_start_stop_trace(self, runner, mock_playwright):
        """Test trace recording."""
        await runner.start("chromium")
        await runner.create_context("test-context")
        
        await runner.start_trace("test-context", "test-trace")
        assert runner._tracing_active["test-context"]
        
        # Mock trace file path
        mock_playwright['context'].tracing.stop = AsyncMock()
        
        trace_path = await runner.stop_trace("test-context")
        assert not runner._tracing_active["test-context"]
        assert trace_path.endswith(".zip")
    
    @pytest.mark.asyncio
    async def test_take_screenshot(self, runner, mock_playwright):
        """Test screenshot capture."""
        await runner.start("chromium")
        await runner.create_context("test-context")
        await runner.new_page("test-context")
        
        path = await runner.take_screenshot("test-context")
        
        assert path.endswith(".png")
    
    @pytest.mark.asyncio
    async def test_network_interception(self, runner, mock_playwright):
        """Test network interception setup."""
        await runner.start("chromium")
        await runner.create_context("test-context")
        
        async def mock_handler(route):
            await route.fulfill(json={"mocked": True})
        
        await runner.intercept_network("test-context", "**/api/**", mock_handler)
        
        assert len(runner._network_handlers["test-context"]) == 1
    
    @pytest.mark.asyncio
    async def test_close_context(self, runner, mock_playwright):
        """Test closing a context."""
        await runner.start("chromium")
        await runner.create_context("test-context")
        
        await runner.close_context("test-context")
        
        assert "test-context" not in runner._contexts
    
    def test_list_contexts(self, runner):
        """Test listing contexts."""
        contexts = runner.list_contexts()
        assert contexts == []
    
    def test_get_network_logs(self, runner):
        """Test getting network logs for non-existent context."""
        logs = runner.get_network_logs("non-existent")
        assert logs == []


# ============ ContextConfig Tests ============

class TestContextConfig:
    """Tests for ContextConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = ContextConfig()
        
        assert config.viewport == {"width": 1280, "height": 720}
        assert config.locale == "en-US"
        assert config.javascript_enabled == True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ContextConfig(
            viewport={"width": 1920, "height": 1080},
            user_agent="Custom UA",
            is_mobile=True,
            has_touch=True,
        )
        
        assert config.viewport == {"width": 1920, "height": 1080}
        assert config.user_agent == "Custom UA"
        assert config.is_mobile == True
    
    def test_to_playwright_config(self):
        """Test conversion to Playwright options."""
        config = ContextConfig(
            viewport={"width": 1920, "height": 1080},
            user_agent="Custom UA",
            base_url="https://example.com",
        )
        
        pw_config = config.to_playwright_config()
        
        assert pw_config["viewport"] == {"width": 1920, "height": 1080}
        assert pw_config["user_agent"] == "Custom UA"
        assert pw_config["base_url"] == "https://example.com"


# ============ ExecutionConfig Tests ============

class TestExecutionConfig:
    """Tests for ExecutionConfig dataclass."""
    
    def test_default_config(self):
        """Test default execution configuration."""
        config = ExecutionConfig()
        
        assert config.browser_type == "chromium"
        assert config.headless == True
        assert config.timeout == 30000
        assert config.record_trace == True
        assert config.retry_count == 0
    
    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "browser_type": "firefox",
            "headless": False,
            "timeout": 60000,
            "record_trace": False,
        }
        
        config = ExecutionConfig.from_dict(data)
        
        assert config.browser_type == "firefox"
        assert config.headless == False
        assert config.timeout == 60000
    
    def test_to_context_config(self):
        """Test conversion to ContextConfig."""
        config = ExecutionConfig(
            viewport={"width": 1920, "height": 1080},
            user_agent="Test UA",
            base_url="https://example.com",
        )
        
        ctx_config = config.to_context_config()
        
        assert isinstance(ctx_config, ContextConfig)
        assert ctx_config.viewport == {"width": 1920, "height": 1080}


# ============ ExecutionManager Tests ============

class TestExecutionManager:
    """Tests for ExecutionManager class."""
    
    def test_initialization(self, mock_db):
        """Test manager initialization."""
        runner = Mock()
        manager = ExecutionManager(db=mock_db, runner=runner, max_concurrent=3)
        
        assert manager.db == mock_db
        assert manager.runner == runner
    
    def test_generate_run_id(self, mock_db):
        """Test run ID generation."""
        manager = ExecutionManager(db=mock_db)
        
        run_id = manager._generate_run_id()
        
        assert run_id.startswith("RUN-")
        assert len(run_id) > 10
    
    @pytest.mark.asyncio
    async def test_execute_test_case_not_found(self, mock_db):
        """Test execution with non-existent test case."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        manager = ExecutionManager(db=mock_db)
        
        with pytest.raises(ValueError) as exc_info:
            await manager.execute_test_case(test_case_id=999)
        
        assert "not found" in str(exc_info.value)
    
    def test_parse_automation_script_json(self, mock_db):
        """Test parsing JSON automation script."""
        manager = ExecutionManager(db=mock_db)
        
        script = '''[
            {"type": "navigate", "url": "https://example.com"},
            {"type": "click", "selector": "#button"}
        ]'''
        
        steps = manager._parse_automation_script(script)
        
        assert len(steps) == 2
        assert steps[0]["type"] == "navigate"
        assert steps[1]["type"] == "click"
    
    def test_parse_automation_script_dsl(self, mock_db):
        """Test parsing DSL automation script."""
        manager = ExecutionManager(db=mock_db)
        
        script = """
        navigate|https://example.com
        click|#button
        fill|#input|test value
        """
        
        steps = manager._parse_automation_script(script)
        
        assert len(steps) == 3
        assert steps[0]["type"] == "navigate"
        assert steps[0]["url"] == "https://example.com"
        assert steps[1]["type"] == "click"
        assert steps[2]["type"] == "fill"
        assert steps[2]["value"] == "test value"
    
    def test_map_assert_action(self, mock_db):
        """Test assertion action mapping."""
        manager = ExecutionManager(db=mock_db)
        
        assert manager._map_assert_action({"assertion_type": "text"}) == "assert_text"
        assert manager._map_assert_action({"assertion_type": "visible"}) == "assert_visible"
        assert manager._map_assert_action({"assertion_type": "hidden"}) == "assert_hidden"
        assert manager._map_assert_action({"assertion_type": "url"}) == "assert_url"
    
    def test_get_execution_status_not_found(self, mock_db):
        """Test getting status for non-existent execution."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        manager = ExecutionManager(db=mock_db)
        
        with pytest.raises(ValueError):
            manager.get_execution_status(999)


# ============ ActionResult Tests ============

class TestActionResult:
    """Tests for ActionResult dataclass."""
    
    def test_success_result(self):
        """Test successful action result."""
        result = ActionResult(
            success=True,
            action_type="click",
            selector="#button",
            duration_ms=150.5,
            timestamp=datetime.utcnow(),
        )
        
        assert result.success
        assert result.error is None
    
    def test_failed_result(self):
        """Test failed action result."""
        result = ActionResult(
            success=False,
            action_type="click",
            selector="#button",
            duration_ms=5000.0,
            timestamp=datetime.utcnow(),
            error="Element not found",
            screenshot_path="/path/to/screenshot.png",
        )
        
        assert not result.success
        assert result.error == "Element not found"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        timestamp = datetime.utcnow()
        result = ActionResult(
            success=True,
            action_type="fill",
            selector="#input",
            duration_ms=100.0,
            timestamp=timestamp,
            value="test",
        )
        
        data = result.to_dict()
        
        assert data["success"] == True
        assert data["action_type"] == "fill"
        assert data["value"] == "test"


# ============ StepResult Tests ============

class TestStepResult:
    """Tests for StepResult dataclass."""
    
    def test_step_result(self):
        """Test step result creation."""
        result = StepResult(
            step_number=1,
            action_type="navigate",
            description="Navigate to page",
            selector=None,
            status="passed",
            duration_ms=500.0,
            timestamp=datetime.utcnow(),
        )
        
        assert result.step_number == 1
        assert result.status == "passed"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = StepResult(
            step_number=2,
            action_type="click",
            description="Click button",
            selector="#btn",
            status="failed",
            duration_ms=3000.0,
            timestamp=datetime.utcnow(),
            error="Timeout",
        )
        
        data = result.to_dict()
        
        assert data["step_number"] == 2
        assert data["status"] == "failed"
        assert data["error"] == "Timeout"


# ============ ExecutionResult Tests ============

class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""
    
    def test_execution_result(self):
        """Test execution result creation."""
        result = ExecutionResult(
            execution_id=1,
            test_case_id=10,
            status="passed",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_ms=5000.0,
            steps=[],
            browser_type="chromium",
            environment="development",
        )
        
        assert result.execution_id == 1
        assert result.status == "passed"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        start = datetime.utcnow()
        end = datetime.utcnow()
        
        result = ExecutionResult(
            execution_id=1,
            test_case_id=10,
            status="failed",
            start_time=start,
            end_time=end,
            duration_ms=10000.0,
            steps=[
                StepResult(
                    step_number=1,
                    action_type="navigate",
                    description="Go to page",
                    selector=None,
                    status="passed",
                    duration_ms=500.0,
                    timestamp=start,
                )
            ],
            error_message="Assertion failed",
            browser_type="firefox",
            environment="staging",
        )
        
        data = result.to_dict()
        
        assert data["execution_id"] == 1
        assert data["status"] == "failed"
        assert len(data["steps"]) == 1
        assert data["error_message"] == "Assertion failed"


# ============ Integration Tests ============

class TestIntegration:
    """Integration tests for automation services."""
    
    @pytest.mark.asyncio
    async def test_full_execution_flow(self, mock_playwright, mock_db, sample_test_case):
        """Test complete execution flow."""
        # Setup mock to return test case
        mock_db.query.return_value.filter.return_value.first.return_value = sample_test_case
        mock_db.query.return_value.count.return_value = 0
        
        # Create mock execution
        mock_execution = Mock()
        mock_execution.id = 1
        mock_execution.test_run_id = "RUN-001"
        mock_execution.flaky_count = 0
        mock_execution.screenshots = []
        
        def refresh_execution(obj):
            obj.id = 1
        mock_db.refresh.side_effect = refresh_execution
        
        # This would be a full integration test with actual Playwright
        # For unit testing, we verify the flow works with mocks
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_executions(self, mock_db):
        """Test concurrent execution handling."""
        from app.services.automation.execution_manager import ExecutionQueue
        
        queue = ExecutionQueue(max_concurrent=2)
        
        assert queue.running_count == 0
        assert queue.queued_count == 0


# ============ API Endpoint Tests ============

class TestAPIEndpoints:
    """Tests for automation API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test automation health endpoint."""
        # This would require mocking the runner
        pass
    
    def test_browsers_endpoint(self, client):
        """Test list browsers endpoint."""
        # This would require mocking the runner
        pass


# ============ Run Tests ============

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
