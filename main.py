# main.py
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.users import Users
from app.models.calculator import Calculator, CalculatorFactory
from app.schemas.userSchema import UserCreate, UserRead, UserLogin
from app.schemas.calculatorSchema import CalculationRead, CalculationCreate, CalculationAdd

from fastapi import FastAPI, HTTPException, Request, Depends, status 
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator  # Use @validator for Pydantic 1.x
from fastapi.exceptions import RequestValidationError
from app.operations import add, subtract, multiply, divide  # Ensure correct import path
import uvicorn
import logging



# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

@app.post("/users/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags = ["auth"])
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user = Users(username=user_data.username, email=str(user_data.email),
                 password_hash=Users.hash_password(user_data.password))
    # User Registration endpoint
    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if getattr(e.orig, 'pgcode', None) == '23505':
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Username or email already exists.") from e
        raise 
    db.refresh(user)
    return user
@app.post("/users/login", response_model=UserRead, tags = ["auth"])
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.execute(select(Users).where(Users.username == login_data.username)).scalar_one_or_none()
    if not user or not user.verify_password(login_data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid username or password.")
    return user
"Browse calculations"
@app.get("/calculations", response_model=list[CalculationRead], status_code=status.HTTP_200_OK, tags=["calculations"])
def list_calculations(db: Session = Depends(get_db)):
    calculations = db.execute(select(Calculator)).scalars().all()
    return calculations
"Retrieve a specific calculation by ID"
@app.get("/calculations/{id}", response_model=CalculationRead, status_code=status.HTTP_200_OK, tags=["calculations"])
def get_calculation(id: int, db: Session = Depends(get_db)):
    calculation = db.get(Calculator, id)
    if calculation is None:
        raise HTTPException(status_code=404, detail="This calculation does not exist")
    return calculation
"Update a specific calculation by ID"
@app.put("/calculations/{id}", response_model=CalculationRead, status_code=status.HTTP_200_OK, tags=["calculations"])
def update_calculation(id: int, calculation_data: CalculationCreate, db:
                       Session = Depends(get_db)):
    operation = db.get(Calculator, id)
    if operation is None:
        raise HTTPException(status_code=404, detail="This calculation does not exist")
    new_data = CalculatorFactory.create(user_id=operation.user_id, type=calculation_data.type,
                                        a=calculation_data.a, b=calculation_data.b)
    operation.a = new_data.a
    operation.b = new_data.b
    operation.type = new_data.type
    operation.result = new_data.result

    db.commit()
    db.refresh(operation)
    return operation
"Add a new calculation"
@app.post("/calculations", response_model=CalculationRead, status_code=status.HTTP_201_CREATED, tags=["calculations"])
def create_calculation(calculation_data: CalculationAdd, db: Session = Depends(get_db)):
    if db.get(Users, calculation_data.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    new_calculation = CalculatorFactory.create(user_id=calculation_data.user_id, type=calculation_data.type,
                                               a=calculation_data.a, b=calculation_data.b)
    db.add(new_calculation)
    db.commit()
    db.refresh(new_calculation)
    return new_calculation
"Delete a calculation by ID"
@app.delete("/calculations/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["calculations"])
def delete_calculations(id: int, db: Session = Depends(get_db)):
    calculation = db.get(Calculator, id)
    if calculation is None:
        raise HTTPException(status_code=404, detail="This calculation does not exist")
    db.delete(calculation)
    db.commit()
    return {"detail": "Calculation deleted successfully."}
    

@app.get("/health")
def health_check():
    return {"status": "healthy"}
# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Pydantic model for request data
class OperationRequest(BaseModel):
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")

    @field_validator('a', 'b')  # Correct decorator for Pydantic 1.x
    def validate_numbers(cls, value):
        if not isinstance(value, (int, float)):
            raise ValueError('Both a and b must be numbers.')
        return value

# Pydantic model for successful response
class OperationResponse(BaseModel):
    result: float = Field(..., description="The result of the operation")

# Pydantic model for error response
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")

# Custom Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Extracting error messages
    error_messages = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    logger.error(f"ValidationError on {request.url.path}: {error_messages}")
    return JSONResponse(
        status_code=400,
        content={"error": error_messages},
    )

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.post("/add", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def add_route(operation: OperationRequest):
    """
    Add two numbers.
    """
    try:
        result = add(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Add Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subtract", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def subtract_route(operation: OperationRequest):
    """
    Subtract two numbers.
    """
    try:
        result = subtract(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Subtract Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/multiply", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def multiply_route(operation: OperationRequest):
    """
    Multiply two numbers.
    """
    try:
        result = multiply(operation.a, operation.b)
        return OperationResponse(result=result)
    except Exception as e:
        logger.error(f"Multiply Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/divide", response_model=OperationResponse, responses={400: {"model": ErrorResponse}})
async def divide_route(operation: OperationRequest):
    """
    Divide two numbers.
    """
    try:
        result = divide(operation.a, operation.b)
        return OperationResponse(result=result)
    except ValueError as e:
        logger.error(f"Divide Operation Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Divide Operation Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
