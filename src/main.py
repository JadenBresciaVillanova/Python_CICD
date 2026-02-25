from fastapi import FastAPI, HTTPException
from src.calculator import add, divide

app = FastAPI(title="CI/CD Math API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the CI/CD API"}

@app.get("/add")
def add_route(a: float, b: float):
    return {"result": add(a, b)}

@app.get("/divide")
def divide_route(a: float, b: float):
    try:
        return {"result": divide(a, b)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))