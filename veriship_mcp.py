"""VeriShip MCP Server - Expose VeriShip QA Platform as MCP tools for AI agents."""

import os
import httpx
from mcp.server.fastmcp import FastMCP

# ===== Config =====
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MCP_PORT = int(os.getenv("VERISHIP_MCP_PORT", "8001"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")  # stdio | streamable-http

mcp = FastMCP("VeriShip QA Platform", host="0.0.0.0", port=MCP_PORT)


def _auto_login():
    """Auto-login on startup using VERISHIP_DEFAULT_USERNAME/PASSWORD env vars (optional)."""
    username = os.getenv("VERISHIP_DEFAULT_USERNAME", "")
    password = os.getenv("VERISHIP_DEFAULT_PASSWORD", "")
    # Only auto-login if both credentials are explicitly set
    if username and password:
        try:
            resp = httpx.post(
                f"{BACKEND_URL}/api/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                token = resp.json().get("token", "")
                if token:
                    os.environ["VERISHIP_API_TOKEN"] = token
                    print(f"[MCP] Auto-logged in as '{username}'")
            else:
                print(f"[MCP] Auto-login failed: {resp.status_code}")
        except Exception as e:
            print(f"[MCP] Auto-login error: {e}")
    else:
        print("[MCP] No default credentials set. User must call login() tool first.")


_auto_login()


def _headers() -> dict:
    token = os.getenv("VERISHIP_API_TOKEN", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ===== Auth =====

@mcp.tool()
def set_token(token: str) -> dict:
    """Set the authentication token directly (used when frontend passes its own JWT)."""
    if not token:
        return {"error": "No token provided"}
    os.environ["VERISHIP_API_TOKEN"] = token
    return {"message": "Token set successfully"}


@mcp.tool()
def register(username: str, email: str, password: str, first_name: str = "", last_name: str = "") -> dict:
    """Register a new user account."""
    payload = {
        "username": username,
        "email": email,
        "password": password,
    }
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    resp = httpx.post(
        f"{BACKEND_URL}/api/auth/register",
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("token", "")
    if token:
        os.environ["VERISHIP_API_TOKEN"] = token
    return {"token": token, "user": data.get("user"), "message": f"User {username} registered successfully"}


@mcp.tool()
def login(username: str, password: str) -> dict:
    """Authenticate with VeriShip and store a JWT token for subsequent calls."""
    resp = httpx.post(
        f"{BACKEND_URL}/api/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("token", "")
    os.environ["VERISHIP_API_TOKEN"] = token
    return {"token": token, "user": data.get("user")}


@mcp.tool()
def logout() -> dict:
    """Clear the stored authentication token and logout the current user."""
    if "VERISHIP_API_TOKEN" in os.environ:
        del os.environ["VERISHIP_API_TOKEN"]
    return {"message": "Logged out successfully. Token cleared."}


# ===== Projects =====

@mcp.tool()
def list_projects() -> list:
    """List all QA projects."""
    resp = httpx.get(f"{BACKEND_URL}/api/projects", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def get_project(project_id: int) -> dict:
    """Get full details for a specific project."""
    resp = httpx.get(f"{BACKEND_URL}/api/projects/{project_id}", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def create_project(name: str, description: str = "", target_release_date: str = "") -> dict:
    """Create a new QA project. target_release_date format: YYYY-MM-DDTHH:MM:SS"""
    payload: dict = {"name": name, "description": description}
    if target_release_date:
        payload["target_release_date"] = target_release_date
    resp = httpx.post(f"{BACKEND_URL}/api/projects/", json=payload, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def update_project(project_id: int, name: str = "", description: str = "", status: str = "") -> dict:
    """Update an existing project. status values: on-track | at-risk | delayed | completed"""
    payload = {k: v for k, v in {"name": name, "description": description, "status": status}.items() if v}
    resp = httpx.put(f"{BACKEND_URL}/api/projects/{project_id}", json=payload, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


# ===== Requirements =====

@mcp.tool()
def list_requirements(project_id: int) -> list:
    """List all requirements for a project."""
    resp = httpx.get(f"{BACKEND_URL}/api/requirements?project_id={project_id}", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def create_requirement(project_id: int, title: str, description: str = "") -> dict:
    """Create a new requirement in a project."""
    payload = {"project_id": project_id, "title": title, "description": description}
    resp = httpx.post(f"{BACKEND_URL}/api/requirements/", json=payload, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


# ===== Test Cases =====

@mcp.tool()
def list_test_cases(project_id: int) -> list:
    """List all test cases for a project."""
    resp = httpx.get(f"{BACKEND_URL}/api/test-cases?project_id={project_id}", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def create_test_case(
    project_id: int,
    title: str,
    description: str = "",
    test_type: str = "manual",
    requirement_id: int = 0,
) -> dict:
    """Create a new test case. test_type: manual | automated"""
    payload: dict = {
        "project_id": project_id,
        "title": title,
        "description": description,
        "test_type": test_type,
    }
    if requirement_id:
        payload["requirement_id"] = requirement_id
    resp = httpx.post(f"{BACKEND_URL}/api/test-cases/", json=payload, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def update_test_case(test_case_id: int, status: str = "", is_automated: bool = None) -> dict:
    """Update a test case. status: ongoing | passed | failed | blocked"""
    payload = {}
    if status:
        payload["status"] = status
    if is_automated is not None:
        payload["is_automated"] = is_automated
    resp = httpx.put(f"{BACKEND_URL}/api/test-cases/{test_case_id}", json=payload, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


# ===== Defects =====

@mcp.tool()
def list_defects(project_id: int) -> list:
    """List all defects for a project."""
    resp = httpx.get(f"{BACKEND_URL}/api/defects?project_id={project_id}", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def create_defect(
    project_id: int,
    title: str,
    description: str = "",
    severity: str = "medium",
) -> dict:
    """Create a new defect. severity: low | medium | high | critical"""
    payload = {
        "project_id": project_id,
        "title": title,
        "description": description,
        "severity": severity,
    }
    resp = httpx.post(f"{BACKEND_URL}/api/defects/", json=payload, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def update_defect(defect_id: int, status: str = "", severity: str = "") -> dict:
    """Update a defect. status: open | in_progress | resolved | closed"""
    payload = {k: v for k, v in {"status": status, "severity": severity}.items() if v}
    resp = httpx.put(f"{BACKEND_URL}/api/defects/{defect_id}", json=payload, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


# ===== Releases =====

@mcp.tool()
def list_releases(project_id: int) -> list:
    """List all releases for a project."""
    resp = httpx.get(f"{BACKEND_URL}/api/releases?project_id={project_id}", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def create_release(project_id: int, version: str, description: str = "") -> dict:
    """Create a new release for a project."""
    payload = {"project_id": project_id, "version": version, "description": description}
    resp = httpx.post(f"{BACKEND_URL}/api/releases/", json=payload, headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


# ===== Metrics =====

@mcp.tool()
def get_project_metrics(project_id: int) -> dict:
    """Get quality metrics (coverage, defect density, pass rate) for a project."""
    resp = httpx.get(f"{BACKEND_URL}/api/metrics?project_id={project_id}", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


# ===== Test Runs =====

@mcp.tool()
def list_test_runs(project_id: int) -> list:
    """List all test runs for a project."""
    resp = httpx.get(f"{BACKEND_URL}/api/test-runs?project_id={project_id}", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()


# ===== Health =====

@mcp.tool()
def health_check() -> dict:
    """Check if the VeriShip backend is healthy."""
    resp = httpx.get(f"{BACKEND_URL}/health", timeout=5)
    resp.raise_for_status()
    return resp.json()


# ===== Entry point =====

if __name__ == "__main__":
    if MCP_TRANSPORT == "streamable-http":
        mcp.run(transport="streamable-http")
    elif MCP_TRANSPORT == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
