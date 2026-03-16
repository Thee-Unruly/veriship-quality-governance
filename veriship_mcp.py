import httpx
from mcp.server.fastmcp import FastMCP

import os

# Initialize MCP Server
mcp = FastMCP("VeriShip")

# Configuration from Environment Variables
# Default to 'app' for Docker compose network
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BASE_URL = f"http://{BACKEND_HOST}:8000/api"
AGENT_TOKEN = os.getenv("AGENT_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYToxIiwibmFtZSI6Im44bi1hZ2VudCIsInJvbGUiOiJhZ2VudCIsInR5cGUiOiJzZXJ2aWNlX2FjY291bnQifQ.KyQQCPWaVQ8zJS1sXuLJ0QVkxPVevlnb-5cJP_SUDvM")

headers = {
    "Authorization": f"Bearer {AGENT_TOKEN}",
    "Content-Type": "application/json"
}

@mcp.tool()
async def list_projects() -> str:
    """Get a list of all VeriShip projects."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/projects/", headers=headers)
        return response.text

@mcp.tool()
async def create_defect(project_id: int, title: str, severity: str, description: str = "") -> str:
    """Log a new defect. Severity: critical, high, medium, low, trivial."""
    payload = {
        "project_id": project_id,
        "title": title,
        "severity": severity.lower(),
        "description": description
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/defects/", json=payload, headers=headers)
        return response.text

@mcp.tool()
async def update_project_status(project_id: int, status: str) -> str:
    """Update project status: planning, in-progress, on-track, at-risk, blocked, completed."""
    payload = {"status": status.lower()}
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{BASE_URL}/projects/{project_id}", json=payload, headers=headers)
        return response.text

@mcp.tool()
async def get_dashboard_metrics() -> str:
    """Get high-level QA metrics and system health."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/metrics/dashboard", headers=headers)
        return response.text

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "sse":
        import uvicorn
        from mcp.server.fastmcp import FastMCP
        # Get the starlette app from FastMCP
        app = mcp.get_streamable_http_app()
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        mcp.run()
