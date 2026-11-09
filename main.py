"""FastAPI Calculator with PostgreSQL-backed secure user registration."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_engine, init_db
from app.operations import add, subtract, multiply, divide
from app.users import router as users_router

@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    yield
    get_engine().dispose()

app = FastAPI(title="Module 10 Secure Calculator", lifespan=lifespan)
app.include_router(users_router)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

class OperationRequest(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    a: float = Field(description="The first number")
    b: float = Field(description="The second number")

class OperationResponse(BaseModel):
    result: float

@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Do not echo submitted input (especially passwords) in a validation response.
    message = "; ".join(f"{error['loc'][-1]}: {error['msg']}" for error in exc.errors())
    status = 422 if request.url.path.startswith("/users") else 400
    return JSONResponse(status_code=status, content={"error": message})

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/health")
def health():
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"status": "ok", "database": "connected"}

@app.post("/add", response_model=OperationResponse)
def add_route(operation: OperationRequest):
    return {"result": add(operation.a, operation.b)}

@app.post("/subtract", response_model=OperationResponse)
def subtract_route(operation: OperationRequest):
    return {"result": subtract(operation.a, operation.b)}

@app.post("/multiply", response_model=OperationResponse)
def multiply_route(operation: OperationRequest):
    return {"result": multiply(operation.a, operation.b)}

@app.post("/divide", response_model=OperationResponse)
def divide_route(operation: OperationRequest):
    try:
        return {"result": divide(operation.a, operation.b)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
