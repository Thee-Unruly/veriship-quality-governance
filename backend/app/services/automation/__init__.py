"""Playwright Automation Services for VeriShip QA Platform.

This module provides automated browser testing capabilities using Playwright,
implementing a client-server architecture with:
- Browser lifecycle management
- Isolated browser contexts
- Auto-waiting mechanisms
- Network interception
- Trace recording
- Multi-browser support (Chromium, Firefox, WebKit)
"""

from app.services.automation.playwright_runner import PlaywrightRunner
from app.services.automation.execution_manager import ExecutionManager

__all__ = ["PlaywrightRunner", "ExecutionManager"]
