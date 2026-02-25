from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import patch, AsyncMock, MagicMock

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
def test_get_cicd_status_success(mock_get):
    # 1. Create a fake response object using MagicMock (synchronous)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "workflow_runs": [{
            "name": "CI Pipeline",
            "status": "completed",
            "conclusion": "success",
            "head_branch": "main",
            "head_commit": {"message": "Testing Mocking"},
            "html_url": "https://github.com/..."
        }]
    }
    
    # Tell the async network call to return our synchronous fake response
    mock_get.return_value = mock_response
    
    # 2. Call our API
    response = client.get("/api/cicd-status")
    
    # 3. Assert it behaves correctly
    assert response.status_code == 200
    assert response.json()["pipeline_name"] == "CI Pipeline"
    assert response.json()["conclusion"] == "success"


@patch("httpx.AsyncClient.get", new_callable=AsyncMock)
def test_get_cicd_status_github_error(mock_get):
    # 1. Create a fake response object for an error (e.g., GitHub is down)
    mock_response = MagicMock()
    mock_response.status_code = 403
    
    # Tell the async network call to return this error response
    mock_get.return_value = mock_response
    
    # 2. Call our API
    response = client.get("/api/cicd-status")
    
    # 3. Assert that our error handling works!
    assert response.status_code == 500
    assert response.json()["detail"] == "Could not fetch GitHub data"