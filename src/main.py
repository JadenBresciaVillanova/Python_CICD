from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import httpx
from src.calculator import add, divide
import os # We now need this 'os' import again to read env vars!

app = FastAPI(title="CI/CD Math API")

# Update this to your exact GitHub Username and Repo name!
# Make sure this is IDENTICAL to your GitHub repo name (case-sensitive for API paths)
GITHUB_REPO = "JadenBresciaVillanova/Python_CICD" 

# Get the GitHub token from environment variable
# It's good practice to make this configurable
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
    
    async with httpx.AsyncClient() as client:
        try:
            print(f"DEBUG: Requesting URL: {url} with headers: {headers}") # Debugging line
            response = await client.get(url, headers=headers)
            print(f"DEBUG: GitHub API response status: {response.status_code}") # Debugging line
            print(f"DEBUG: GitHub API response body: {response.text[:500]}...") # Debugging line (limit body length)

            # GitHub returns 404 for non-existent repos or sometimes for unauthorized private ones
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub repository or workflow runs not found. Check GITHUB_REPO or token permissions.")
            
            # Catch other client errors (403 Forbidden, 429 Rate Limited, etc.)
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=f"GitHub API Error: {response.status_code} - {response.text}")
                
            data = response.json()
            
            # Robustly check if workflow_runs exists and is not empty
            workflow_runs = data.get("workflow_runs")
            if not workflow_runs:
                # If there are no runs, return a message instead of failing
                return {"message": "No CI/CD runs found yet for this repository."}

            # Get the most recent pipeline run
            latest_run = workflow_runs[0] # Safely access now that we know it's not empty
            
            return {
                "pipeline_name": latest_run["name"],
                "status": latest_run["status"],           # e.g., "completed", "in_progress"
                "conclusion": latest_run["conclusion"],   # e.g., "success", "failure"
                "branch": latest_run["head_branch"],
                "commit_message": latest_run["head_commit"]["message"],
                "url": latest_run["html_url"]
            }
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"An error occurred while requesting GitHub API: {exc}")
        except Exception as exc:
            # Catch any other unexpected errors during processing
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {exc}")


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