"""
FilmPulse AI — JWT Authentication & Role-Based Access Control
=============================================================
Roles:
  producer  — default; can manage their own films & run analysis
  admin     — full access; can see all films, delete any, promote users

JWT payload: { "sub": email, "role": role, "exp": ... }
"""
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db, User
import os

SECRET_KEY = os.getenv("SECRET_KEY", "filmpulse-super-secret-key-change-in-production-2025")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ── Password helpers ──────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Token helpers ─────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire    = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ── FastAPI dependencies ──────────────────────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return the current user or None (for optional-auth endpoints)."""
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    email: str = payload.get("sub")
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()


def require_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Raises 401 if not authenticated."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")
    return current_user


def require_role(allowed_roles: List[str]):
    """
    Factory: returns a FastAPI dependency that enforces role-based access.

    Usage:
        @router.delete("/films/{id}", dependencies=[Depends(require_role(["admin"]))])
        @router.get("/admin/users",   dependencies=[Depends(require_role(["admin"]))])
        @router.post("/upload-film",  dependencies=[Depends(require_role(["producer","admin"]))])
    """
    def _check(current_user: User = Depends(require_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(allowed_roles)}. "
                       f"Your role: {current_user.role}",
            )
        return current_user
    return _check


# ── Convenience shortcuts ─────────────────────────────────────────────────────
def require_admin(current_user: User = Depends(require_user)) -> User:
    """Only admins may access this endpoint."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


def require_producer_or_admin(current_user: User = Depends(require_user)) -> User:
    """Producers and admins may access this endpoint."""
    if current_user.role not in ("producer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Producer or Admin access required.",
        )
    return current_user
