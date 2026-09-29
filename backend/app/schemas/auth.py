from pydantic import BaseModel, EmailStr, Field
from app.models.entities import Role
class RegisterRequest(BaseModel):
    email: EmailStr; password: str=Field(min_length=8); full_name: str; role: Role=Role.BIDDER
    organization_name: str|None=None
class LoginRequest(BaseModel):
    email: EmailStr; password: str
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    organization_id: str | None = None
    organization_name: str | None = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None

class RefreshRequest(BaseModel):
    refresh_token: str
