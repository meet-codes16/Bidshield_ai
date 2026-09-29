from typing import Generic, TypeVar, Any
from pydantic import BaseModel, Field
T=TypeVar("T")
class ApiResponse(BaseModel, Generic[T]):
    success: bool=True
    data: T
    message: str=""
    request_id: str=""
class ErrorBody(BaseModel):
    code: str
    message: str
