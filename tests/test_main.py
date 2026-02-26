from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    # Instead of checking for JSON, we just check if our HTML title is in the response
    assert "CI/CD Platform Dashboard" in response.text

def test_add_route():
    response = client.get("/add?a=5&b=5")
    assert response.status_code == 200
    assert response.json() == {"result": 10.0}

def test_divide_route_error():
    response = client.get("/divide?a=10&b=0")
    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot divide by zero"}

@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
def test_get_cicd_status_github_error(mock_get):
    # 1. Create a fake response object for an error (e.g., GitHub is down)
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = '{"message": "Forbidden", "documentation_url": "https://docs.github.com/rest/actions/workflows"}'
    
    # Tell the async network call to return this error response
    mock_get.return_value = mock_response
    
    # 2. Call our API
    response = client.get("/api/cicd-status")
    
    # 3. Assert that our error handling works!
    assert response.status_code == 403 # Our FastAPI now returns 403 directly, not 500
    
    # UPDATE THIS LINE: Assert against the more specific error message
    assert response.json()["detail"] == f"GitHub API Error: {mock_response.status_code} - {mock_response.text}"
    # OR, if you want it to catch the general HTTPException 
    # assert "GitHub API Error: 403" in response.json()["detail"]

@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
def test_get_cicd_status_empty_runs(mock_get):
    # 1. Simulate GitHub responding, but saying "0 workflows found"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"workflow_runs": []} # Empty list!
    
    mock_get.return_value = mock_response
    
    # 2. Call our API
    response = client.get("/api/cicd-status")
    
    # 3. Assert it returns our fallback message
    assert response.status_code == 200
    assert response.json() == {"message": "No CI/CD runs found yet for this repository."}

@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
def test_get_cicd_status_network_crash(mock_get):
    # 1. Simulate the internet going down completely (RequestError)
    # Note: We use side_effect to raise an error instead of returning a response
    mock_get.side_effect = httpx.RequestError("Network disconnected")
    
    # 2. Call our API
    response = client.get("/api/cicd-status")
    
    # 3. Assert our try/except block caught the network error
    assert response.status_code == 500
    assert "An error occurred while requesting GitHub API" in response.json()["detail"]