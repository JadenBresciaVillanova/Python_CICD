from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles #commented for ruff failing the build since unused
import httpx
from src.calculator import add, divide
# import os #commented for ruff failing the build since unused

app = FastAPI(title="CI/CD Math API")

# Update this to your exact GitHub Username and Repo name!
GITHUB_REPO = "JadenBresciaVillanova/Python_CICD"

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    # ADD encoding="utf-8" right here! 👇
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()
    
@app.get("/api/cicd-status")
async def get_cicd_status():
    """Fetches the latest CI/CD pipeline status directly from GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
    
    # We use httpx to make an asynchronous web request to GitHub
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Could not fetch GitHub data")
            
        data = response.json()
        
        if not data.get("workflow_runs"):
            return {"message": "No CI/CD runs found yet."}

        # Get the most recent pipeline run
        latest_run = data["workflow_runs"][0]
        
        return {
            "pipeline_name": latest_run["name"],
            "status": latest_run["status"],           # e.g., "completed", "in_progress"
            "conclusion": latest_run["conclusion"],   # e.g., "success", "failure"
            "branch": latest_run["head_branch"],
            "commit_message": latest_run["head_commit"]["message"],
            "url": latest_run["html_url"]
        }

@app.get("/add")
def add_route(a: float, b: float):
    return {"result": add(a, b)}

@app.get("/divide")
def divide_route(a: float, b: float):
    try:
        return {"result": divide(a, b)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))