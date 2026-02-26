from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import httpx
from src.calculator import add, divide
import os 

app = FastAPI(title="CI/CD Math API")

GITHUB_REPO = "JadenBresciaVillanova/Python_CICD" 

GITHUB_API_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_API_TOKEN:
    print("WARNING: GITHUB_TOKEN environment variable not set. API calls to GitHub might fail if repo is private or rate limits are hit.")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/cicd-status")
async def get_cicd_status():
    """Fetches the latest CI/CD pipeline status directly from GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
    
    headers = {}
    if GITHUB_API_TOKEN:
        headers["Authorization"] = f"token {GITHUB_API_TOKEN}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=f"GitHub API Error: {response.status_code} - {response.text}")
                    
            data = response.json()
            
            workflow_runs = data.get("workflow_runs")
            if not workflow_runs:
                return {"message": "No CI/CD runs found yet for this repository."}

            latest_run = workflow_runs[0]
            
            return {
                "pipeline_name": latest_run["name"],
                "status": latest_run["status"],
                "conclusion": latest_run["conclusion"],
                "branch": latest_run["head_branch"],
                "commit_message": latest_run["head_commit"]["message"],
                "url": latest_run["html_url"]
            }
            
    # --- NEW FIX: Let HTTPExceptions pass through untouched ---
    except HTTPException:
        raise
    # ----------------------------------------------------------
    
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"An error occurred while requesting GitHub API: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during processing: {exc}")


# --- Keep your existing calculator routes below ---
@app.get("/add")
def add_route(a: float, b: float):
    return {"result": add(a, b)}

@app.get("/divide")
def divide_route(a: float, b: float):
    try:
        return {"result": divide(a, b)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))