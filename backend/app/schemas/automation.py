"""Pydantic schemas for Playwright automation API.

These schemas define the request/response models for the automation endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


# ============ Enums ============

class BrowserTypeEnum(str, Enum):
    """Supported browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class ExecutionStatusEnum(str, Enum):
    """Execution status values."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    ERROR = "error"


class ActionTypeEnum(str, Enum):
    """Supported action types."""
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
    HTTP = "http"
    DELAY = "delay"
    ASSERT = "assert"


# ============ Request Schemas ============

class ViewportConfig(BaseModel):
    """Viewport configuration."""
    width: int = Field(default=1280, ge=320, le=3840)
    height: int = Field(default=720, ge=240, le=2160)


class GeolocationConfig(BaseModel):
    """Geolocation configuration."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(default=0, ge=0)


class ExecutionRequest(BaseModel):
    """Request schema for test execution."""
    browser_type: BrowserTypeEnum = Field(
        default=BrowserTypeEnum.CHROMIUM,
        description="Browser to use for execution"
    )
    headless: bool = Field(
        default=True,
        description="Run browser in headless mode"
    )
    viewport: Optional[ViewportConfig] = Field(
        default=None,
        description="Viewport dimensions"
    )
    timeout: int = Field(
        default=30000,
        ge=1000,
        le=300000,
        description="Default timeout in milliseconds"
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for relative navigation"
    )
    user_agent: Optional[str] = Field(
        default=None,
        description="Custom user agent string"
    )
    locale: str = Field(
        default="en-US",
        description="Browser locale"
    )
    timezone_id: str = Field(
        default="America/New_York",
        description="Timezone ID"
    )
    geolocation: Optional[GeolocationConfig] = Field(
        default=None,
        description="Geolocation override"
    )
    permissions: List[str] = Field(
        default=[],
        description="Browser permissions to grant"
    )
    record_trace: bool = Field(
        default=True,
        description="Record execution trace for debugging"
    )
    record_video: bool = Field(
        default=False,
        description="Record video of execution"
    )
    screenshot_on_failure: bool = Field(
        default=True,
        description="Capture screenshot on test failure"
    )
    screenshot_on_step: bool = Field(
        default=False,
        description="Capture screenshot after each step"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Number of retries on failure"
    )
    retry_delay_ms: int = Field(
        default=1000,
        ge=0,
        le=60000,
        description="Delay between retries in milliseconds"
    )
    environment: str = Field(
        default="development",
        description="Execution environment (dev/staging/prod)"
    )
    extra_headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Extra HTTP headers to include"
    )
    storage_state: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Browser storage state (cookies, localStorage)"
    )

    class Config:
        use_enum_values = True


class SuiteExecutionRequest(BaseModel):
    """Request schema for test suite execution."""
    config: Optional[ExecutionRequest] = Field(
        default=None,
        description="Execution configuration"
    )
    parallel: bool = Field(
        default=False,
        description="Run tests in parallel"
    )
    executed_by: str = Field(
        default="automation",
        description="User or system executing the tests"
    )


class ContextCreateRequest(BaseModel):
    """Request schema for creating a browser context."""
    context_id: Optional[str] = Field(
        default=None,
        description="Custom context ID (auto-generated if not provided)"
    )
    browser_type: BrowserTypeEnum = Field(
        default=BrowserTypeEnum.CHROMIUM,
        description="Browser type"
    )
    viewport: Optional[ViewportConfig] = Field(default=None)
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    geolocation: Optional[GeolocationConfig] = None
    permissions: List[str] = []
    color_scheme: str = "light"
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False
    javascript_enabled: bool = True
    accept_downloads: bool = True
    ignore_https_errors: bool = False
    offline: bool = False
    base_url: Optional[str] = None

    class Config:
        use_enum_values = True


class ActionRequest(BaseModel):
    """Request schema for executing an action."""
    action_type: ActionTypeEnum = Field(..., description="Type of action to perform")
    selector: Optional[str] = Field(
        default=None,
        description="CSS selector for element-based actions"
    )
    context_id: Optional[str] = Field(
        default=None,
        description="Context ID (uses first available if not specified)"
    )
    page_id: Optional[str] = Field(
        default=None,
        description="Page ID (uses active page if not specified)"
    )
    
    # Action-specific parameters
    url: Optional[str] = Field(default=None, description="URL for navigate action")
    value: Optional[str] = Field(default=None, description="Value for fill/type actions")
    text: Optional[str] = Field(default=None, description="Text for type action")
    key: Optional[str] = Field(default=None, description="Key for press action")
    expected: Optional[str] = Field(default=None, description="Expected value for assertions")
    attribute: Optional[str] = Field(default=None, description="Attribute name for get_attribute")
    duration: Optional[int] = Field(default=None, description="Duration in ms for wait/delay")
    timeout: Optional[int] = Field(default=None, description="Custom timeout for this action")
    wait_until: Optional[str] = Field(default=None, description="Wait condition (load, domcontentloaded, networkidle)")
    full_page: bool = Field(default=False, description="Full page screenshot")
    button: str = Field(default="left", description="Mouse button (left, right, middle)")
    click_count: int = Field(default=1, description="Number of clicks")
    force: bool = Field(default=False, description="Force action without waiting")
    files: Optional[List[str]] = Field(default=None, description="Files for upload_file action")
    target: Optional[str] = Field(default=None, description="Target selector for drag_and_drop")
    expression: Optional[str] = Field(default=None, description="JavaScript expression for evaluate")
    
    # HTTP action parameters
    method: Optional[str] = Field(default=None, description="HTTP method for http action")
    headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers")
    body: Optional[Dict[str, Any]] = Field(default=None, description="HTTP request body")
    expected_status: Optional[int] = Field(default=None, description="Expected HTTP status code")
    expected_contains: Optional[str] = Field(default=None, description="Expected response content")

    class Config:
        use_enum_values = True


class TestStepSchema(BaseModel):
    """Schema for a test step."""
    type: str = Field(..., description="Action type")
    description: Optional[str] = None
    selector: Optional[str] = None
    url: Optional[str] = None
    value: Optional[str] = None
    text: Optional[str] = None
    expected: Optional[str] = None
    expected_status: Optional[int] = None
    expected_contains: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    duration_ms: Optional[int] = None


class ManualTestRequest(BaseModel):
    """Request for running a manual test with steps."""
    title: str = Field(..., description="Test title")
    description: Optional[str] = None
    steps: List[TestStepSchema] = Field(..., description="Test steps to execute")
    config: Optional[ExecutionRequest] = None


# ============ Response Schemas ============

class StepResultResponse(BaseModel):
    """Response schema for a step result."""
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


class ExecutionResponse(BaseModel):
    """Response schema for test execution."""
    execution_id: int
    test_case_id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: float
    steps: List[StepResultResponse]
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    network_logs_count: int = 0
    browser_type: str
    environment: str
    defect_id: Optional[int] = None


class ExecutionStatusResponse(BaseModel):
    """Response schema for execution status."""
    execution_id: int
    status: str
    is_running: bool
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    elapsed_ms: Optional[float] = None
    duration_seconds: Optional[int] = None
    executed_at: Optional[datetime] = None
    executed_by: Optional[str] = None
    browser: Optional[str] = None
    environment: Optional[str] = None
    error_message: Optional[str] = None


class SuiteExecutionResponse(BaseModel):
    """Response schema for test suite execution."""
    suite_id: int
    suite_name: str
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int = 0
    pass_rate: float
    total_duration_ms: float
    results: List[ExecutionResponse]


class TraceResponse(BaseModel):
    """Response schema for trace file."""
    execution_id: int
    trace_path: Optional[str]
    download_url: Optional[str]
    exists: bool


class ScreenshotResponse(BaseModel):
    """Response schema for screenshot."""
    execution_id: Optional[int] = None
    screenshot_path: str
    download_url: str
    timestamp: datetime


class BrowserInfo(BaseModel):
    """Information about a browser."""
    type: str
    name: str
    available: bool


class BrowsersResponse(BaseModel):
    """Response schema for available browsers."""
    browsers: List[BrowserInfo]
    current_browser: Optional[str] = None
    is_running: bool


class ContextInfo(BaseModel):
    """Information about a browser context."""
    context_id: str
    pages: List[str]
    active_page: Optional[str]
    tracing_active: bool
    network_handlers_count: int
    network_logs_count: int


class ContextCreateResponse(BaseModel):
    """Response schema for context creation."""
    context_id: str
    browser_type: str
    created_at: datetime


class ContextListResponse(BaseModel):
    """Response schema for listing contexts."""
    contexts: List[ContextInfo]
    count: int


class ActionResultResponse(BaseModel):
    """Response schema for action execution."""
    success: bool
    action_type: str
    selector: Optional[str]
    duration_ms: float
    timestamp: datetime
    value: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None


class NetworkLogEntry(BaseModel):
    """Schema for a network log entry."""
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


class NetworkLogsResponse(BaseModel):
    """Response schema for network logs."""
    context_id: str
    logs: List[NetworkLogEntry]
    count: int


class RunnerStatusResponse(BaseModel):
    """Response schema for runner status."""
    is_running: bool
    browser_type: Optional[str]
    contexts_count: int
    active_executions_count: int
    queued_executions_count: int


class HealthResponse(BaseModel):
    """Health check response for automation service."""
    status: str
    service: str
    playwright_running: bool
    browser_type: Optional[str]
    contexts: int
    timestamp: datetime


# ============ Execution Step Model (for database) ============

class ExecutionStepCreate(BaseModel):
    """Schema for creating an execution step record."""
    execution_id: int
    step_number: int
    action_type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    status: str
    duration_ms: float
    error: Optional[str] = None
    screenshot_path: Optional[str] = None


class ExecutionStepResponse(BaseModel):
    """Response schema for an execution step."""
    id: int
    execution_id: int
    step_number: int
    action_type: str
    selector: Optional[str]
    value: Optional[str]
    status: str
    duration_ms: float
    timestamp: datetime
    error: Optional[str]
    screenshot_path: Optional[str]

    class Config:
        from_attributes = True
