from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password,verify_password,create_access_token,create_refresh_token
from app.core.dependencies import current_user
from app.models.entities import User,Organization,Role,Bidder
from app.schemas.auth import RegisterRequest,LoginRequest,TokenResponse,RefreshRequest,UserResponse
router=APIRouter(prefix="/auth",tags=["auth"])

def _user_to_response(user: User, db: Session) -> UserResponse:
    org_name = None
    if user.organization_id:
        org = db.get(Organization, user.organization_id)
        if org:
            org_name = org.name
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        organization_id=str(user.organization_id) if user.organization_id else None,
        organization_name=org_name,
    )

@router.post("/register",response_model=TokenResponse)
def register(data:RegisterRequest,db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==data.email)): raise HTTPException(409,"Email already registered")
    org=None
    if data.organization_name:
        org=Organization(name=data.organization_name); db.add(org); db.flush()
    if data.role == Role.BIDDER and org is None:
        org=Organization(name=f"{data.full_name}'s Organization"); db.add(org); db.flush()
    user=User(email=data.email,password_hash=hash_password(data.password),full_name=data.full_name,role=data.role,organization_id=org.id if org else None)
    db.add(user); db.flush()
    if data.role == Role.BIDDER and org is not None:
        db.add(Bidder(organization_id=org.id, organization_name=org.name))
    db.commit()
    return TokenResponse(
        access_token=create_access_token(str(user.id),user.role.value),
        refresh_token=create_refresh_token(str(user.id),user.role.value),
        user=_user_to_response(user, db),
    )

@router.post("/login",response_model=TokenResponse)
def login(data:LoginRequest,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==data.email))
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,"Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(str(user.id),user.role.value),
        refresh_token=create_refresh_token(str(user.id),user.role.value),
        user=_user_to_response(user, db),
    )

@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _user_to_response(user, db)

@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    from jose import jwt, JWTError
    try:
        payload=jwt.decode(data.refresh_token, __import__('app.core.config',fromlist=['settings']).settings.JWT_SECRET, algorithms=[__import__('app.core.config',fromlist=['settings']).settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(401,"Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(401,"Invalid refresh token")
    user=db.get(User,payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(401,"User not found or inactive")
    return TokenResponse(
        access_token=create_access_token(str(user.id),user.role.value),
        refresh_token=create_refresh_token(str(user.id),user.role.value),
        user=_user_to_response(user, db),
    )
