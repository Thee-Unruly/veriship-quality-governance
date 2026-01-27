"""Playwright Runner - Core automation service for browser-based test execution.

This module implements Playwright's architectural patterns:
- Client-Server Architecture: Python async API communicating with Playwright server
- Browser Context Isolation: Multiple isolated test sessions in one browser
- Auto-Waiting Mechanism: Built-in waits for element actionability
- Network Interception: Capture and modify network requests/responses
- Trace Recording: Full execution traces for debugging
- Multi-Browser Support: Chromium, Firefox, WebKit

Usage:
    runner = PlaywrightRunner()
    await runner.start("chromium")
    context_id = await runner.create_context("test-session-1", {...config})
    page = await runner.new_page(context_id)
    await runner.execute_action("navigate", None, url="https://example.com")
    await runner.stop()
"""

import asyncio
import uuid
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List, Union
from dataclasses import dataclass, field
from enum import Enum

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Route,
    Request,
    Response,
    Error as PlaywrightError,
)

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class BrowserType(str, Enum):
    """Supported browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class ActionType(str, Enum):
    """Supported action types for test execution."""
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    TYPE = "type"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    HOVER = "hover"
    FOCUS = "focus"
    PRESS = "press"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    WAIT_FOR_NAVIGATION = "wait_for_navigation"
    WAIT_FOR_LOAD_STATE = "wait_for_load_state"
    EVALUATE = "evaluate"
    GET_TEXT = "get_text"
    GET_ATTRIBUTE = "get_attribute"
    GET_VALUE = "get_value"
    ASSERT_TEXT = "assert_text"
    ASSERT_VISIBLE = "assert_visible"
    ASSERT_HIDDEN = "assert_hidden"
    ASSERT_URL = "assert_url"
    ASSERT_TITLE = "assert_title"
    UPLOAD_FILE = "upload_file"
    DOWNLOAD = "download"
    DRAG_AND_DROP = "drag_and_drop"
    SCROLL = "scroll"


@dataclass
class ContextConfig:
    """Configuration for browser context creation."""
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    geolocation: Optional[Dict[str, float]] = None
    permissions: List[str] = field(default_factory=list)
    color_scheme: str = "light"
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False
    javascript_enabled: bool = True
    accept_downloads: bool = True
    ignore_https_errors: bool = False
    offline: bool = False
    http_credentials: Optional[Dict[str, str]] = None
    extra_http_headers: Optional[Dict[str, str]] = None
    storage_state: Optional[Union[str, Dict]] = None
    record_video: bool = False
    video_size: Optional[Dict[str, int]] = None
    base_url: Optional[str] = None

    def to_playwright_config(self) -> Dict[str, Any]:
        """Convert to Playwright context options."""
        config: Dict[str, Any] = {
            "viewport": self.viewport,
            "locale": self.locale,
            "timezone_id": self.timezone_id,
            "color_scheme": self.color_scheme,
            "device_scale_factor": self.device_scale_factor,
            "is_mobile": self.is_mobile,
            "has_touch": self.has_touch,
            "java_script_enabled": self.javascript_enabled,
            "accept_downloads": self.accept_downloads,
            "ignore_https_errors": self.ignore_https_errors,
            "offline": self.offline,
        }
        
        if self.user_agent:
            config["user_agent"] = self.user_agent
        if self.geolocation:
            config["geolocation"] = self.geolocation
        if self.permissions:
            config["permissions"] = self.permissions
        if self.http_credentials:
            config["http_credentials"] = self.http_credentials
        if self.extra_http_headers:
            config["extra_http_headers"] = self.extra_http_headers
        if self.storage_state:
            config["storage_state"] = self.storage_state
        if self.record_video:
            config["record_video_dir"] = settings.videos_dir
            if self.video_size:
                config["record_video_size"] = self.video_size
        if self.base_url:
            config["base_url"] = self.base_url
            
        return config


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    action_type: str
    selector: Optional[str]
    duration_ms: float
    timestamp: datetime
    value: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "action_type": self.action_type,
            "selector": self.selector,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "error": self.error,
            "screenshot_path": self.screenshot_path,
        }


@dataclass
class NetworkLog:
    """Captured network request/response."""
    request_id: str
    url: str
    method: str
    resource_type: str
    request_headers: Dict[str, str]
    request_post_data: Optional[str]
    response_status: Optional[int]
    response_headers: Optional[Dict[str, str]]
    response_body: Optional[str]
    timing: Dict[str, float]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "url": self.url,
            "method": self.method,
            "resource_type": self.resource_type,
            "request_headers": self.request_headers,
            "request_post_data": self.request_post_data,
            "response_status": self.response_status,
            "response_headers": self.response_headers,
            "response_body": self.response_body,
            "timing": self.timing,
            "timestamp": self.timestamp.isoformat(),
        }


class PlaywrightRunner:
    """Core Playwright automation runner implementing browser test execution.
    
    This class manages the complete lifecycle of browser automation:
    - Browser instance management (start, stop, restart)
    - Context creation with isolation
    - Page management within contexts
    - Action execution with auto-waiting
    - Network interception and logging
    - Trace recording for debugging
    - Screenshot capture on demand or failure
    
    Attributes:
        browser_type: Current browser type (chromium, firefox, webkit)
        headless: Whether browser runs in headless mode
        slow_mo: Slow down operations by specified milliseconds
        timeout: Default timeout for operations in milliseconds
        
    Example:
        >>> runner = PlaywrightRunner(headless=True)
        >>> await runner.start("chromium")
        >>> ctx_id = await runner.create_context("session-1", ContextConfig())
        >>> await runner.new_page(ctx_id)
        >>> result = await runner.execute_action("navigate", None, url="https://example.com")
        >>> await runner.stop()
    """
    
    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 0,
        timeout: int = 30000,
        traces_dir: Optional[str] = None,
        screenshots_dir: Optional[str] = None,
    ):
        """Initialize PlaywrightRunner.
        
        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by milliseconds
            timeout: Default timeout for operations
            traces_dir: Directory to store trace files
            screenshots_dir: Directory to store screenshots
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.traces_dir = traces_dir or settings.traces_dir
        self.screenshots_dir = screenshots_dir or settings.screenshots_dir
        
        # Runtime state
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._browser_type: Optional[BrowserType] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Dict[str, Page]] = {}  # context_id -> {page_id: Page}
        self._active_pages: Dict[str, str] = {}  # context_id -> active page_id
        self._network_logs: Dict[str, List[NetworkLog]] = {}  # context_id -> logs
        self._tracing_active: Dict[str, bool] = {}  # context_id -> is_tracing
        self._network_handlers: Dict[str, List[tuple]] = {}  # context_id -> [(pattern, handler)]
        
        # Ensure directories exist
        os.makedirs(self.traces_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        logger.info(f"PlaywrightRunner initialized: headless={headless}, timeout={timeout}")
    
    @property
    def is_running(self) -> bool:
        """Check if browser is running."""
        return self._browser is not None and self._browser.is_connected()
    
    @property
    def browser_type(self) -> Optional[str]:
        """Get current browser type."""
        return self._browser_type.value if self._browser_type else None
    
    @property
    def available_browsers(self) -> List[str]:
        """Get list of available browser types."""
        return [bt.value for bt in BrowserType]
    
    async def start(self, browser_type: str = "chromium") -> None:
        """Start the browser instance.
        
        Args:
            browser_type: Type of browser to launch (chromium, firefox, webkit)
            
        Raises:
            ValueError: If browser_type is not supported
            PlaywrightError: If browser fails to launch
        """
        if self.is_running:
            logger.warning("Browser already running, stopping first")
            await self.stop()
        
        try:
            browser_enum = BrowserType(browser_type.lower())
        except ValueError:
            raise ValueError(f"Unsupported browser type: {browser_type}. "
                           f"Supported: {self.available_browsers}")
        
        self._browser_type = browser_enum
        
        logger.info(f"Starting Playwright with {browser_type}")
        self._playwright = await async_playwright().start()
        
        # Get browser launcher
        browser_launcher = getattr(self._playwright, browser_type.lower())
        
        # Launch browser
        self._browser = await browser_launcher.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ] if browser_type == "chromium" else None,
        )
        
        logger.info(f"Browser {browser_type} started successfully")
    
    async def stop(self) -> None:
        """Stop the browser and cleanup all resources."""
        logger.info("Stopping PlaywrightRunner")
        
        # Stop all traces first
        for context_id in list(self._tracing_active.keys()):
            if self._tracing_active.get(context_id):
                try:
                    await self.stop_trace(context_id)
                except Exception as e:
                    logger.warning(f"Error stopping trace for {context_id}: {e}")
        
        # Close all contexts
        for context_id in list(self._contexts.keys()):
            try:
                await self.close_context(context_id)
            except Exception as e:
                logger.warning(f"Error closing context {context_id}: {e}")
        
        # Close browser
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            self._browser = None
        
        # Stop playwright
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")
            self._playwright = None
        
        self._browser_type = None
        logger.info("PlaywrightRunner stopped")
    
    async def restart(self, browser_type: Optional[str] = None) -> None:
        """Restart the browser with optionally different browser type.
        
        Args:
            browser_type: New browser type, or None to use current
        """
        current_type = self.browser_type or "chromium"
        await self.stop()
        await self.start(browser_type or current_type)
    
    async def create_context(
        self,
        context_id: Optional[str] = None,
        config: Optional[Union[ContextConfig, Dict[str, Any]]] = None,
    ) -> str:
        """Create a new isolated browser context.
        
        Each context has isolated cookies, local storage, and sessions,
        enabling parallel test execution without interference.
        
        Args:
            context_id: Optional ID for the context, auto-generated if not provided
            config: Context configuration (viewport, user agent, etc.)
            
        Returns:
            The context ID
            
        Raises:
            RuntimeError: If browser is not started
        """
        if not self.is_running:
            raise RuntimeError("Browser not started. Call start() first.")
        
        context_id = context_id or str(uuid.uuid4())
        
        if context_id in self._contexts:
            logger.warning(f"Context {context_id} already exists, closing it first")
            await self.close_context(context_id)
        
        # Parse config
        if isinstance(config, dict):
            context_config = ContextConfig(**config)
        else:
            context_config = config or ContextConfig()
        
        playwright_options = context_config.to_playwright_config()
        
        logger.info(f"Creating context {context_id}")
        context = await self._browser.new_context(**playwright_options)
        
        # Set default timeout
        context.set_default_timeout(self.timeout)
        
        # Setup network logging
        self._network_logs[context_id] = []
        await self._setup_network_logging(context, context_id)
        
        # Store context
        self._contexts[context_id] = context
        self._pages[context_id] = {}
        self._tracing_active[context_id] = False
        self._network_handlers[context_id] = []
        
        logger.info(f"Context {context_id} created successfully")
        return context_id
    
    async def _setup_network_logging(self, context: BrowserContext, context_id: str) -> None:
        """Setup network request/response logging for a context."""
        
        async def on_request(request: Request):
            start_time = datetime.utcnow()
            request._veriship_start_time = start_time
        
        async def on_response(response: Response):
            request = response.request
            start_time = getattr(request, '_veriship_start_time', datetime.utcnow())
            end_time = datetime.utcnow()
            
            try:
                # Try to get response body for API calls
                response_body = None
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type or "text/" in content_type:
                    try:
                        response_body = await response.text()
                        # Limit body size
                        if len(response_body) > 10000:
                            response_body = response_body[:10000] + "... [truncated]"
                    except Exception:
                        pass
                
                log = NetworkLog(
                    request_id=str(uuid.uuid4()),
                    url=request.url,
                    method=request.method,
                    resource_type=request.resource_type,
                    request_headers=dict(request.headers),
                    request_post_data=request.post_data,
                    response_status=response.status,
                    response_headers=dict(response.headers),
                    response_body=response_body,
                    timing={
                        "start": start_time.timestamp(),
                        "end": end_time.timestamp(),
                        "duration_ms": (end_time - start_time).total_seconds() * 1000,
                    },
                    timestamp=start_time,
                )
                self._network_logs[context_id].append(log)
            except Exception as e:
                logger.warning(f"Error logging network response: {e}")
        
        context.on("request", on_request)
        context.on("response", on_response)
    
    async def new_page(self, context_id: str, page_id: Optional[str] = None) -> str:
        """Create a new page in the specified context.
        
        Args:
            context_id: The context to create the page in
            page_id: Optional ID for the page
            
        Returns:
            The page ID
            
        Raises:
            KeyError: If context not found
        """
        if context_id not in self._contexts:
            raise KeyError(f"Context {context_id} not found")
        
        page_id = page_id or str(uuid.uuid4())
        
        context = self._contexts[context_id]
        page = await context.new_page()
        
        self._pages[context_id][page_id] = page
        self._active_pages[context_id] = page_id
        
        logger.info(f"Page {page_id} created in context {context_id}")
        return page_id
    
    def get_page(self, context_id: str, page_id: Optional[str] = None) -> Page:
        """Get a page instance.
        
        Args:
            context_id: The context ID
            page_id: The page ID, or None for active page
            
        Returns:
            The Page instance
        """
        if context_id not in self._pages:
            raise KeyError(f"Context {context_id} not found")
        
        page_id = page_id or self._active_pages.get(context_id)
        if not page_id or page_id not in self._pages[context_id]:
            raise KeyError(f"Page {page_id} not found in context {context_id}")
        
        return self._pages[context_id][page_id]
    
    async def execute_action(
        self,
        action_type: str,
        selector: Optional[str] = None,
        context_id: Optional[str] = None,
        page_id: Optional[str] = None,
        screenshot_on_error: bool = True,
        **kwargs,
    ) -> ActionResult:
        """Execute an action on the page with auto-waiting.
        
        Playwright automatically waits for elements to be actionable before
        performing actions (visible, enabled, stable, etc.).
        
        Args:
            action_type: Type of action (click, fill, navigate, etc.)
            selector: CSS selector for element-based actions
            context_id: Context to use, or first available
            page_id: Page to use, or active page
            screenshot_on_error: Capture screenshot on failure
            **kwargs: Additional action-specific parameters
            
        Returns:
            ActionResult with execution details
        """
        start_time = datetime.utcnow()
        
        # Get context and page
        if not context_id:
            if not self._contexts:
                raise RuntimeError("No contexts available. Create a context first.")
            context_id = next(iter(self._contexts.keys()))
        
        try:
            page = self.get_page(context_id, page_id)
        except KeyError:
            # Create a page if none exists
            await self.new_page(context_id)
            page = self.get_page(context_id)
        
        error: Optional[str] = None
        value: Optional[Any] = None
        screenshot_path: Optional[str] = None
        
        try:
            action = ActionType(action_type.lower())
            value = await self._perform_action(page, action, selector, **kwargs)
        except Exception as e:
            error = str(e)
            logger.error(f"Action {action_type} failed: {e}")
            
            if screenshot_on_error:
                try:
                    screenshot_path = await self._capture_error_screenshot(
                        page, context_id, action_type
                    )
                except Exception as ss_error:
                    logger.warning(f"Failed to capture error screenshot: {ss_error}")
        
        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        result = ActionResult(
            success=error is None,
            action_type=action_type,
            selector=selector,
            duration_ms=duration_ms,
            timestamp=start_time,
            value=value,
            error=error,
            screenshot_path=screenshot_path,
        )
        
        return result
    
    async def _perform_action(
        self,
        page: Page,
        action: ActionType,
        selector: Optional[str],
        **kwargs,
    ) -> Optional[Any]:
        """Perform the actual action on the page.
        
        All actions use Playwright's auto-waiting mechanism.
        """
        
        if action == ActionType.NAVIGATE:
            url = kwargs.get("url")
            wait_until = kwargs.get("wait_until", "load")
            await page.goto(url, wait_until=wait_until)
            return page.url
        
        elif action == ActionType.CLICK:
            button = kwargs.get("button", "left")
            click_count = kwargs.get("click_count", 1)
            force = kwargs.get("force", False)
            await page.click(selector, button=button, click_count=click_count, force=force)
        
        elif action == ActionType.FILL:
            value = kwargs.get("value", "")
            await page.fill(selector, value)
        
        elif action == ActionType.TYPE:
            text = kwargs.get("text", "")
            delay = kwargs.get("delay", 0)
            await page.type(selector, text, delay=delay)
        
        elif action == ActionType.SELECT:
            value = kwargs.get("value")
            label = kwargs.get("label")
            index = kwargs.get("index")
            if value:
                await page.select_option(selector, value=value)
            elif label:
                await page.select_option(selector, label=label)
            elif index is not None:
                await page.select_option(selector, index=index)
        
        elif action == ActionType.CHECK:
            await page.check(selector)
        
        elif action == ActionType.UNCHECK:
            await page.uncheck(selector)
        
        elif action == ActionType.HOVER:
            await page.hover(selector)
        
        elif action == ActionType.FOCUS:
            await page.focus(selector)
        
        elif action == ActionType.PRESS:
            key = kwargs.get("key", "Enter")
            if selector:
                await page.press(selector, key)
            else:
                await page.keyboard.press(key)
        
        elif action == ActionType.SCREENSHOT:
            path = kwargs.get("path")
            full_page = kwargs.get("full_page", False)
            if not path:
                filename = f"screenshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
                path = os.path.join(self.screenshots_dir, filename)
            if selector:
                element = await page.query_selector(selector)
                if element:
                    await element.screenshot(path=path)
            else:
                await page.screenshot(path=path, full_page=full_page)
            return path
        
        elif action == ActionType.WAIT:
            duration = kwargs.get("duration", 1000)
            await page.wait_for_timeout(duration)
        
        elif action == ActionType.WAIT_FOR_SELECTOR:
            state = kwargs.get("state", "visible")
            timeout = kwargs.get("timeout", self.timeout)
            await page.wait_for_selector(selector, state=state, timeout=timeout)
        
        elif action == ActionType.WAIT_FOR_NAVIGATION:
            url = kwargs.get("url")
            wait_until = kwargs.get("wait_until", "load")
            await page.wait_for_url(url, wait_until=wait_until) if url else await page.wait_for_load_state(wait_until)
        
        elif action == ActionType.WAIT_FOR_LOAD_STATE:
            state = kwargs.get("state", "load")
            await page.wait_for_load_state(state)
        
        elif action == ActionType.EVALUATE:
            expression = kwargs.get("expression", "")
            return await page.evaluate(expression)
        
        elif action == ActionType.GET_TEXT:
            element = await page.query_selector(selector)
            if element:
                return await element.text_content()
            return None
        
        elif action == ActionType.GET_ATTRIBUTE:
            attribute = kwargs.get("attribute", "")
            return await page.get_attribute(selector, attribute)
        
        elif action == ActionType.GET_VALUE:
            return await page.input_value(selector)
        
        elif action == ActionType.ASSERT_TEXT:
            expected = kwargs.get("expected", "")
            element = await page.query_selector(selector)
            if element:
                text = await element.text_content()
                if expected not in (text or ""):
                    raise AssertionError(f"Expected text '{expected}' not found in '{text}'")
            else:
                raise AssertionError(f"Element not found: {selector}")
        
        elif action == ActionType.ASSERT_VISIBLE:
            is_visible = await page.is_visible(selector)
            if not is_visible:
                raise AssertionError(f"Element not visible: {selector}")
        
        elif action == ActionType.ASSERT_HIDDEN:
            is_visible = await page.is_visible(selector)
            if is_visible:
                raise AssertionError(f"Element is visible but expected hidden: {selector}")
        
        elif action == ActionType.ASSERT_URL:
            expected = kwargs.get("expected", "")
            current_url = page.url
            if expected not in current_url:
                raise AssertionError(f"Expected URL '{expected}' not in '{current_url}'")
        
        elif action == ActionType.ASSERT_TITLE:
            expected = kwargs.get("expected", "")
            title = await page.title()
            if expected not in title:
                raise AssertionError(f"Expected title '{expected}' not in '{title}'")
        
        elif action == ActionType.UPLOAD_FILE:
            files = kwargs.get("files", [])
            await page.set_input_files(selector, files)
        
        elif action == ActionType.DOWNLOAD:
            async with page.expect_download() as download_info:
                await page.click(selector)
            download = await download_info.value
            save_path = kwargs.get("save_path", os.path.join(self.screenshots_dir, download.suggested_filename))
            await download.save_as(save_path)
            return save_path
        
        elif action == ActionType.DRAG_AND_DROP:
            target = kwargs.get("target", "")
            await page.drag_and_drop(selector, target)
        
        elif action == ActionType.SCROLL:
            x = kwargs.get("x", 0)
            y = kwargs.get("y", 0)
            if selector:
                await page.locator(selector).scroll_into_view_if_needed()
            else:
                await page.evaluate(f"window.scrollBy({x}, {y})")
        
        else:
            raise ValueError(f"Unsupported action type: {action}")
        
        return None
    
    async def _capture_error_screenshot(
        self,
        page: Page,
        context_id: str,
        action_type: str,
    ) -> str:
        """Capture screenshot on error."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"error_{context_id}_{action_type}_{timestamp}.png"
        path = os.path.join(self.screenshots_dir, filename)
        await page.screenshot(path=path, full_page=True)
        return path
    
    async def start_trace(
        self,
        context_id: str,
        trace_name: Optional[str] = None,
        screenshots: bool = True,
        snapshots: bool = True,
        sources: bool = True,
    ) -> None:
        """Start trace recording for debugging.
        
        Traces capture:
        - DOM snapshots before and after actions
        - Screenshots at each step
        - Network activity
        - Console logs
        
        Args:
            context_id: Context to trace
            trace_name: Name for the trace
            screenshots: Include screenshots
            snapshots: Include DOM snapshots
            sources: Include source code
        """
        if context_id not in self._contexts:
            raise KeyError(f"Context {context_id} not found")
        
        if self._tracing_active.get(context_id):
            logger.warning(f"Trace already active for context {context_id}")
            return
        
        context = self._contexts[context_id]
        
        await context.tracing.start(
            name=trace_name or f"trace_{context_id}",
            screenshots=screenshots,
            snapshots=snapshots,
            sources=sources,
        )
        
        self._tracing_active[context_id] = True
        logger.info(f"Trace started for context {context_id}")
    
    async def stop_trace(self, context_id: str) -> str:
        """Stop trace recording and save to file.
        
        Args:
            context_id: Context to stop tracing
            
        Returns:
            Path to the trace file (.zip)
        """
        if context_id not in self._contexts:
            raise KeyError(f"Context {context_id} not found")
        
        if not self._tracing_active.get(context_id):
            raise RuntimeError(f"No active trace for context {context_id}")
        
        context = self._contexts[context_id]
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        trace_path = os.path.join(self.traces_dir, f"trace_{context_id}_{timestamp}.zip")
        
        await context.tracing.stop(path=trace_path)
        
        self._tracing_active[context_id] = False
        logger.info(f"Trace saved to {trace_path}")
        
        return trace_path
    
    async def intercept_network(
        self,
        context_id: str,
        pattern: str,
        handler: Callable[[Route], Any],
    ) -> None:
        """Setup network request interception.
        
        Allows modifying or mocking network requests/responses.
        
        Args:
            context_id: Context to intercept
            pattern: URL pattern to match (glob or regex)
            handler: Async function to handle matched routes
            
        Example:
            async def mock_api(route):
                await route.fulfill(json={"mocked": True})
            
            await runner.intercept_network(ctx_id, "**/api/**", mock_api)
        """
        if context_id not in self._contexts:
            raise KeyError(f"Context {context_id} not found")
        
        context = self._contexts[context_id]
        await context.route(pattern, handler)
        
        self._network_handlers[context_id].append((pattern, handler))
        logger.info(f"Network interception set for pattern: {pattern}")
    
    async def remove_network_intercept(self, context_id: str, pattern: str) -> None:
        """Remove network interception for a pattern."""
        if context_id not in self._contexts:
            raise KeyError(f"Context {context_id} not found")
        
        context = self._contexts[context_id]
        await context.unroute(pattern)
        
        self._network_handlers[context_id] = [
            (p, h) for p, h in self._network_handlers[context_id] if p != pattern
        ]
    
    def get_network_logs(self, context_id: str) -> List[Dict[str, Any]]:
        """Get captured network logs for a context.
        
        Args:
            context_id: Context to get logs for
            
        Returns:
            List of network log dictionaries
        """
        if context_id not in self._network_logs:
            return []
        
        return [log.to_dict() for log in self._network_logs[context_id]]
    
    def clear_network_logs(self, context_id: str) -> None:
        """Clear network logs for a context."""
        if context_id in self._network_logs:
            self._network_logs[context_id] = []
    
    async def take_screenshot(
        self,
        context_id: str,
        page_id: Optional[str] = None,
        full_page: bool = False,
        selector: Optional[str] = None,
    ) -> str:
        """Capture a screenshot.
        
        Args:
            context_id: Context ID
            page_id: Page ID (optional, uses active page)
            full_page: Capture full scrollable page
            selector: Optional selector to screenshot specific element
            
        Returns:
            Path to saved screenshot
        """
        page = self.get_page(context_id, page_id)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{context_id}_{timestamp}.png"
        path = os.path.join(self.screenshots_dir, filename)
        
        if selector:
            element = await page.query_selector(selector)
            if element:
                await element.screenshot(path=path)
            else:
                raise ValueError(f"Element not found: {selector}")
        else:
            await page.screenshot(path=path, full_page=full_page)
        
        logger.info(f"Screenshot saved to {path}")
        return path
    
    async def close_page(self, context_id: str, page_id: str) -> None:
        """Close a specific page."""
        if context_id not in self._pages:
            raise KeyError(f"Context {context_id} not found")
        
        if page_id not in self._pages[context_id]:
            raise KeyError(f"Page {page_id} not found")
        
        page = self._pages[context_id][page_id]
        await page.close()
        
        del self._pages[context_id][page_id]
        
        if self._active_pages.get(context_id) == page_id:
            remaining = list(self._pages[context_id].keys())
            self._active_pages[context_id] = remaining[0] if remaining else None
        
        logger.info(f"Page {page_id} closed")
    
    async def close_context(self, context_id: str) -> None:
        """Close a browser context and all its pages."""
        if context_id not in self._contexts:
            raise KeyError(f"Context {context_id} not found")
        
        # Stop tracing if active
        if self._tracing_active.get(context_id):
            try:
                await self.stop_trace(context_id)
            except Exception as e:
                logger.warning(f"Error stopping trace: {e}")
        
        context = self._contexts[context_id]
        await context.close()
        
        # Cleanup
        del self._contexts[context_id]
        del self._pages[context_id]
        del self._network_logs[context_id]
        del self._tracing_active[context_id]
        del self._network_handlers[context_id]
        
        if context_id in self._active_pages:
            del self._active_pages[context_id]
        
        logger.info(f"Context {context_id} closed")
    
    def get_context_info(self, context_id: str) -> Dict[str, Any]:
        """Get information about a context."""
        if context_id not in self._contexts:
            raise KeyError(f"Context {context_id} not found")
        
        return {
            "context_id": context_id,
            "pages": list(self._pages[context_id].keys()),
            "active_page": self._active_pages.get(context_id),
            "tracing_active": self._tracing_active.get(context_id, False),
            "network_handlers_count": len(self._network_handlers.get(context_id, [])),
            "network_logs_count": len(self._network_logs.get(context_id, [])),
        }
    
    def list_contexts(self) -> List[Dict[str, Any]]:
        """List all active contexts with their info."""
        return [self.get_context_info(ctx_id) for ctx_id in self._contexts.keys()]


# Singleton instance for global access
_runner_instance: Optional[PlaywrightRunner] = None


def get_playwright_runner() -> PlaywrightRunner:
    """Get or create the global PlaywrightRunner instance."""
    global _runner_instance
    if _runner_instance is None:
        _runner_instance = PlaywrightRunner(
            headless=settings.playwright_headless,
            slow_mo=settings.playwright_slow_mo,
            timeout=settings.playwright_timeout,
        )
    return _runner_instance


async def cleanup_playwright_runner() -> None:
    """Cleanup the global PlaywrightRunner instance."""
    global _runner_instance
    if _runner_instance is not None:
        await _runner_instance.stop()
        _runner_instance = None
