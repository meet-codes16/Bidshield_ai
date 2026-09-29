from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_token(subject: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "role": role, "type": token_type, "iat": now, "exp": now + expires_delta}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_access_token(subject: str, role: str) -> str:
    return create_token(subject, role, "access", timedelta(minutes=settings.ACCESS_TOKEN_MINUTES))

def create_refresh_token(subject: str, role: str) -> str:
    return create_token(subject, role, "refresh", timedelta(days=settings.REFRESH_TOKEN_DAYS))
