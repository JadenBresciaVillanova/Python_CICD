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

            # If GitHub API returns an error status (>= 400), we re-raise it as an HTTPException
            # with the original status code. This means if GitHub sends 403, our API sends 403.
            if response.status_code >= 400:
                # IMPORTANT: FastAPI's internal routing will catch this HTTPException and
                # automatically turn it into an HTTP response with the specified status code (e.g., 403).
                # It will NOT be caught by the general `except Exception` below.
                raise HTTPException(status_code=response.status_code, detail=f"GitHub API Error: {response.status_code} - {response.text}")
                    
            # If we reach here, response.status_code is < 400 (ideally 200 OK)
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
    # Catch httpx specific errors (e.g., network connection failure, DNS issues)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"An error occurred while requesting GitHub API: {exc}")
    # Catch any other truly unexpected errors that were NOT httpx.RequestError or HTTPException.
    # This ensures that if processing the data (e.g., data.get('workflow_runs')) fails unexpectedly,
    # it still results in a 500, but doesn't interfere with specific HTTP status codes.
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