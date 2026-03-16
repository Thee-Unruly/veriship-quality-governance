"""
VeriShip MCP Server
===================
A complete Model Context Protocol server for the VeriShip QA Intelligence
& Release Governance platform.

Covers:
  - Projects (CRUD + team management)
  - Requirements (CRUD)
  - Test Cases (CRUD + batch)
  - Defects (CRUD + global listing)
  - Releases (CRUD + approvals + approve/reject)
  - Metrics (dashboard, per-project, activity, trends)
  - Copilot / AI (requirement clarity, test-case generation, release readiness, insights)
  - Users & Notifications

Usage
-----
Stdio (default, for Claude Desktop / n8n MCP node):
    python veriship_mcp.py

SSE / HTTP (for remote access):
    python veriship_mcp.py sse

Environment variables
---------------------
BACKEND_HOST   Host of the VeriShip FastAPI backend  (default: localhost)
BACKEND_PORT   Port of the FastAPI backend            (default: 8000)
AGENT_TOKEN    Service-account JWT                    (default: hardcoded dev token)
"""

import os
import sys
import json
import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8000")
BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api"

AGENT_TOKEN = os.getenv(
    "AGENT_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJzYToxIiwibmFtZSI6Im44bi1hZ2VudCIsInJvbGUiOiJhZ2VudCIsInR5cGUiOiJzZXJ2aWNlX2FjY291bnQifQ"
    ".KyQQCPWaVQ8zJS1sXuLJ0QVkxPVevlnb-5cJP_SUDvM",
)

HEADERS = {
    "Authorization": f"Bearer {AGENT_TOKEN}",
    "Content-Type": "application/json",
}

mcp = FastMCP("VeriShip")

# Disable strict host checking so it works inside Docker
mcp.settings.transport_security.enable_dns_rebinding_protection = False
mcp.settings.transport_security.allowed_hosts = ["*"]
mcp.settings.transport_security.allowed_origins = ["*"]

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
async def _get(path: str, params: dict = None) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE_URL}{path}", headers=HEADERS, params=params)
        return r.text


async def _post(path: str, payload: dict = None) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{BASE_URL}{path}", headers=HEADERS, json=payload or {})
        return r.text


async def _put(path: str, payload: dict) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.put(f"{BASE_URL}{path}", headers=HEADERS, json=payload)
        return r.text


async def _delete(path: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.delete(f"{BASE_URL}{path}", headers=HEADERS)
        return r.text


# ===========================================================================
# PROJECTS
# ===========================================================================

@mcp.tool()
async def list_projects() -> str:
    """List all VeriShip projects with their status, dates, and IDs."""
    return await _get("/projects/")


@mcp.tool()
async def get_project(project_id: int) -> str:
    """Get details of a single project by its numeric ID."""
    return await _get(f"/projects/{project_id}")


@mcp.tool()
async def create_project(name: str, description: str = "", target_release_date: str = "") -> str:
    """
    Create a new VeriShip project.

    Args:
        name: Project name (required).
        description: Optional description.
        target_release_date: ISO 8601 datetime string, e.g. '2026-06-01T00:00:00'.
    """
    payload: dict = {"name": name}
    if description:
        payload["description"] = description
    if target_release_date:
        payload["target_release_date"] = target_release_date
    return await _post("/projects/", payload)


@mcp.tool()
async def update_project(
    project_id: int,
    name: str = "",
    description: str = "",
    status: str = "",
    target_release_date: str = "",
) -> str:
    """
    Update a project.

    Args:
        project_id: Numeric project ID.
        name: New name (optional).
        description: New description (optional).
        status: One of: planning, in-progress, on-track, at-risk, blocked, completed.
        target_release_date: ISO 8601 datetime string (optional).
    """
    payload: dict = {}
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description
    if status:
        # normalise so AI typos don't break validation
        payload["status"] = status.lower().strip().replace(" ", "-")
    if target_release_date:
        payload["target_release_date"] = target_release_date
    return await _put(f"/projects/{project_id}", payload)


@mcp.tool()
async def delete_project(project_id: int) -> str:
    """Permanently delete a project and all its data."""
    return await _delete(f"/projects/{project_id}")


# ---- Project Team ----------------------------------------------------------

@mcp.tool()
async def get_project_team(project_id: int) -> str:
    """List all team members assigned to a project."""
    return await _get(f"/projects/{project_id}/team")


@mcp.tool()
async def add_team_member(project_id: int, name: str, email: str = "", role: str = "Member") -> str:
    """
    Add a team member to a project.

    Args:
        project_id: Numeric project ID.
        name: Full name of the team member.
        email: Email address (optional).
        role: Role on the project, e.g. 'QA Engineer', 'Developer'. Default 'Member'.
    """
    payload = {"name": name, "role": role}
    if email:
        payload["email"] = email
    return await _post(f"/projects/{project_id}/team", payload)


@mcp.tool()
async def remove_team_member(project_id: int, member_id: int) -> str:
    """Remove a team member from a project."""
    return await _delete(f"/projects/{project_id}/team/{member_id}")


# ===========================================================================
# REQUIREMENTS
# ===========================================================================

@mcp.tool()
async def list_requirements(project_id: int) -> str:
    """List all requirements for a given project."""
    return await _get(f"/requirements/{project_id}")


@mcp.tool()
async def create_requirement(
    project_id: int,
    title: str,
    description: str,
    acceptance_criteria: list[str] = None,
    priority: int = 1,
) -> str:
    """
    Create a new requirement.

    Args:
        project_id: Numeric project ID.
        title: Short title.
        description: Full requirement text.
        acceptance_criteria: List of acceptance criteria strings.
        priority: 1 = highest, 5 = lowest. Default 1.
    """
    payload = {
        "project_id": project_id,
        "title": title,
        "description": description,
        "acceptance_criteria": acceptance_criteria or [],
        "priority": priority,
    }
    return await _post("/requirements/", payload)


@mcp.tool()
async def update_requirement(
    requirement_id: int,
    title: str = "",
    description: str = "",
    status: str = "",
    priority: int = 0,
    acceptance_criteria: list[str] = None,
) -> str:
    """
    Update a requirement.

    Args:
        requirement_id: Numeric requirement ID.
        status: One of: draft, review, approved, deprecated.
        priority: 1–5.
    """
    payload: dict = {}
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description
    if status:
        payload["status"] = status.lower()
    if priority:
        payload["priority"] = priority
    if acceptance_criteria is not None:
        payload["acceptance_criteria"] = acceptance_criteria
    return await _put(f"/requirements/{requirement_id}", payload)


@mcp.tool()
async def delete_requirement(requirement_id: int) -> str:
    """Delete a requirement by ID."""
    return await _delete(f"/requirements/{requirement_id}")


# ===========================================================================
# TEST CASES
# ===========================================================================

@mcp.tool()
async def list_test_cases(project_id: int, status: str = "") -> str:
    """
    List test cases for a project.

    Args:
        project_id: Numeric project ID.
        status: Optional filter — ongoing, completed, or archived.
    """
    params = {"status": status} if status else None
    return await _get(f"/test-cases/{project_id}", params)


@mcp.tool()
async def create_test_case(
    project_id: int,
    title: str,
    description: str = "",
    test_type: str = "manual",
    priority: int = 1,
    requirement_id: int = 0,
) -> str:
    """
    Create a single test case.

    Args:
        project_id: Numeric project ID.
        title: Test case title.
        test_type: manual, automated, exploratory, etc. Default 'manual'.
        priority: 1 = highest. Default 1.
        requirement_id: Link to a requirement (optional, pass 0 to skip).
    """
    payload: dict = {
        "project_id": project_id,
        "title": title,
        "test_type": test_type,
        "priority": priority,
    }
    if description:
        payload["description"] = description
    if requirement_id:
        payload["requirement_id"] = requirement_id
    return await _post("/test-cases/", payload)


@mcp.tool()
async def update_test_case(
    test_case_id: int,
    title: str = "",
    status: str = "",
    priority: int = 0,
    is_automated: bool = None,
) -> str:
    """
    Update a test case.

    Args:
        test_case_id: Numeric test case ID.
        status: ongoing, completed, or archived.
        is_automated: True / False.
    """
    payload: dict = {}
    if title:
        payload["title"] = title
    if status:
        payload["status"] = status.lower()
    if priority:
        payload["priority"] = priority
    if is_automated is not None:
        payload["is_automated"] = is_automated
    return await _put(f"/test-cases/{test_case_id}", payload)


@mcp.tool()
async def delete_test_case(test_case_id: int) -> str:
    """Delete a test case."""
    return await _delete(f"/test-cases/{test_case_id}")


# ===========================================================================
# DEFECTS
# ===========================================================================

@mcp.tool()
async def list_defects(project_id: int) -> str:
    """List all defects for a specific project."""
    return await _get(f"/defects/{project_id}")


@mcp.tool()
async def list_all_defects(severity: str = "", status: str = "") -> str:
    """
    List defects across ALL projects.

    Args:
        severity: Optional filter — critical, high, medium, low, trivial.
        status: Optional filter — open, in-progress, resolved, closed.
    """
    params: dict = {}
    if severity:
        params["severity"] = severity.lower()
    if status:
        params["status"] = status.lower()
    return await _get("/defects/all", params or None)


@mcp.tool()
async def create_defect(
    project_id: int,
    title: str,
    severity: str = "medium",
    description: str = "",
    found_by: str = "",
) -> str:
    """
    Log a new defect / bug.

    Args:
        project_id: Numeric project ID.
        title: Short defect title.
        severity: critical, high, medium, low, or trivial. Default 'medium'.
        description: Full description of the defect.
        found_by: Name of the person who found the bug (optional).
    """
    payload: dict = {
        "project_id": project_id,
        "title": title,
        "severity": severity.lower().strip(),
    }
    if description:
        payload["description"] = description
    if found_by:
        payload["found_by"] = found_by
    return await _post("/defects/", payload)


@mcp.tool()
async def update_defect(
    defect_id: int,
    title: str = "",
    description: str = "",
    severity: str = "",
    status: str = "",
    found_by: str = "",
) -> str:
    """
    Update a defect.

    Args:
        defect_id: Numeric defect ID.
        severity: critical, high, medium, low, trivial.
        status: open, in-progress, resolved, closed, reopened.
    """
    payload: dict = {}
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description
    if severity:
        payload["severity"] = severity.lower().strip()
    if status:
        payload["status"] = status.lower().strip().replace(" ", "-")
    if found_by:
        payload["found_by"] = found_by
    return await _put(f"/defects/{defect_id}", payload)


@mcp.tool()
async def delete_defect(defect_id: int) -> str:
    """Delete a defect by ID."""
    return await _delete(f"/defects/{defect_id}")


# ===========================================================================
# RELEASES
# ===========================================================================

@mcp.tool()
async def list_all_releases() -> str:
    """List all releases across every project."""
    return await _get("/releases/")


@mcp.tool()
async def list_releases_for_project(project_id: int) -> str:
    """List releases for a specific project."""
    return await _get(f"/releases/{project_id}")


@mcp.tool()
async def create_release(
    project_id: int,
    version: str,
    planned_release_date: str = "",
) -> str:
    """
    Create a new release.

    Args:
        project_id: Numeric project ID.
        version: Version string, e.g. 'v1.2.0'.
        planned_release_date: ISO 8601 datetime string (optional).
    """
    payload: dict = {"project_id": project_id, "version": version}
    if planned_release_date:
        payload["planned_release_date"] = planned_release_date
    return await _post("/releases/", payload)


@mcp.tool()
async def update_release(
    release_id: int,
    version: str = "",
    status: str = "",
    planned_release_date: str = "",
    go_no_go_decision: str = "",
) -> str:
    """
    Update a release.

    Args:
        release_id: Numeric release ID.
        status: planning, in-testing, ready, approved, released, blocked, rollback.
        go_no_go_decision: 'GO', 'NO-GO', or 'CONDITIONAL'.
    """
    payload: dict = {}
    if version:
        payload["version"] = version
    if status:
        payload["status"] = status.lower()
    if planned_release_date:
        payload["planned_release_date"] = planned_release_date
    if go_no_go_decision:
        payload["go_no_go_decision"] = go_no_go_decision.upper()
    return await _put(f"/releases/{release_id}", payload)


@mcp.tool()
async def delete_release(release_id: int) -> str:
    """Delete a release."""
    return await _delete(f"/releases/{release_id}")


@mcp.tool()
async def get_release_approvals(release_id: int) -> str:
    """
    Get all approvals (pending & resolved) for a release.
    Always call this before approve_release to find valid approver names.
    """
    return await _get(f"/releases/{release_id}/approvals")


@mcp.tool()
async def approve_release(
    release_id: int,
    approver_name: str,
    decision: str,
    comments: str = "",
) -> str:
    """
    Approve or reject a release on behalf of a named approver.

    IMPORTANT: Call get_release_approvals first to find the exact approver_name
    from the pending approvals list. Use that exact string here.

    Args:
        release_id: Numeric release ID.
        approver_name: Must match the pending approval record exactly.
        decision: 'approved' or 'rejected' (lowercase).
        comments: Optional justification / comment.
    """
    payload: dict = {
        "approver_name": approver_name,
        "decision": decision.lower(),
    }
    if comments:
        payload["comments"] = comments
    return await _post(f"/releases/{release_id}/approve", payload)


# ===========================================================================
# METRICS
# ===========================================================================

@mcp.tool()
async def get_dashboard_metrics() -> str:
    """
    Get high-level QA dashboard metrics:
    total requirements, test cases, defects, open defects, critical defects,
    test pass rate, pending releases, overall risk score, coverage %.
    """
    return await _get("/metrics/dashboard")


@mcp.tool()
async def get_project_metrics() -> str:
    """Get per-project metrics: defects open/critical, risk score, coverage %."""
    return await _get("/metrics/projects")


@mcp.tool()
async def get_activity_feed(limit: int = 10) -> str:
    """
    Get recent activity across all projects.

    Args:
        limit: Number of activity entries to return. Default 10.
    """
    return await _get("/metrics/activity", {"limit": limit})


@mcp.tool()
async def get_quality_trends(project_id: int = 0, months: int = 6) -> str:
    """
    Get quality trend data (coverage, defects, risk) over time.

    Args:
        project_id: Numeric project ID, or 0 for all-projects aggregate.
        months: Number of months to look back. Default 6.
    """
    params: dict = {"months": months}
    if project_id:
        params["project_id"] = project_id
    return await _get("/metrics/trends", params)


# ===========================================================================
# COPILOT / AI FEATURES
# ===========================================================================

@mcp.tool()
async def analyze_requirement_clarity(requirement_id: int) -> str:
    """
    Use AI to analyse a requirement for clarity, testability, and completeness.
    Returns a clarity score, ambiguous terms, missing criteria, and suggestions.

    Args:
        requirement_id: Numeric requirement ID.
    """
    return await _post(f"/copilot/analyze-requirement-clarity/{requirement_id}")


@mcp.tool()
async def generate_test_cases_for_requirement(requirement_id: int) -> str:
    """
    Use AI to generate test case suggestions for a requirement.
    The suggestions are NOT automatically saved — review them first.

    Args:
        requirement_id: Numeric requirement ID.
    """
    return await _post(f"/copilot/generate-test-cases/{requirement_id}")


@mcp.tool()
async def check_release_readiness(release_id: int) -> str:
    """
    Use AI to perform a full release readiness check.
    Returns a risk score, GO / NO-GO / CONDITIONAL recommendation,
    summary, and a list of blocking issues.

    Args:
        release_id: Numeric release ID.
    """
    return await _post(f"/copilot/check-release-readiness/{release_id}")


@mcp.tool()
async def get_ai_insights() -> str:
    """
    Get AI-driven QA insights for the dashboard.
    Results are cached for 24 hours. Use refresh_ai_insights to force a refresh.
    """
    return await _get("/copilot/insights")


@mcp.tool()
async def refresh_ai_insights() -> str:
    """Force-refresh the AI insights cache and fetch new insights immediately."""
    return await _post("/copilot/insights/refresh")


@mcp.tool()
async def get_copilot_status() -> str:
    """Check whether the Copilot AI endpoints are configured and healthy."""
    return await _get("/copilot/status")


# ===========================================================================
# USERS
# ===========================================================================

@mcp.tool()
async def list_users() -> str:
    """List all users registered in VeriShip."""
    return await _get("/users/")


@mcp.tool()
async def create_user(name: str, email: str, role: str) -> str:
    """
    Create a new user.

    Args:
        name: Full name.
        email: Valid email address.
        role: User role, e.g. 'admin', 'qa', 'developer', 'viewer'.
    """
    return await _post("/users/", {"name": name, "email": email, "role": role})


@mcp.tool()
async def delete_user(user_id: int) -> str:
    """Delete a user by ID."""
    return await _delete(f"/users/{user_id}")


# ===========================================================================
# NOTIFICATIONS
# ===========================================================================

@mcp.tool()
async def get_notifications() -> str:
    """Get all pending notifications for the current agent context."""
    return await _get("/notifications/")


# ===========================================================================
# SYSTEM HEALTH
# ===========================================================================

@mcp.tool()
async def health_check() -> str:
    """Check whether the VeriShip backend is up and running."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"http://{BACKEND_HOST}:{BACKEND_PORT}/health",
            headers=HEADERS,
        )
        return r.text


# ===========================================================================
# Entry point
# ===========================================================================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sse":
        import uvicorn
        app = mcp.streamable_http_app()
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        mcp.run(transport="stdio")