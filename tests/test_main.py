from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the CI/CD API"}

def test_add_route():
    response = client.get("/add?a=5&b=5")
    assert response.status_code == 200
    assert response.json() == {"result": 10.0}

def test_divide_route_error():
    response = client.get("/divide?a=10&b=0")
    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot divide by zero"}