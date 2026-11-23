from typing import Literal
from pydantic import BaseModel, ConfigDict, model_validator
from datetime import datetime

class CalculationCreate(BaseModel):
    a: float
    b: float
    type: Literal["add", "subtract", "multiply", "divide"]

    @model_validator(mode="after")
    def check_divide_by_zero(self):
        if self.type == "divide" and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self

class CalculationAdd(CalculationCreate):
    user_id: int

class CalculationRead(BaseModel):
   # Validate that division by zero does not occur after the model is created
   id: int
   a: float
   b: float
   type: Literal["add", "subtract", "multiply", "divide"]
   result: float
   

   @model_validator(mode="after")
   def check_divide_by_zero(self):
        if self.type == "divide" and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self