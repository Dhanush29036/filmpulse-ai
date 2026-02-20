"""
FilmPulse AI — Auth Router
Endpoints:
  POST /auth/register       — create producer account
  POST /auth/login          — get JWT
  GET  /auth/me             — get current user profile
  POST /auth/logout         — client-side token removal hint
  POST /auth/promote/{id}   — (admin only) promote user to a role
  GET  /admin/users         — (admin only) list all users
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, User
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_user, require_admin,
)
from datetime import datetime

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    company: str = ""
    role: str = "producer"   # front-end sends "producer" always; admin locked below


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class PromoteRequest(BaseModel):
    role: str  # "producer" | "admin"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _user_dict(user: User) -> dict:
    return {
        "id":              user.id,
        "email":           user.email,
        "name":            user.name,
        "company":         user.company or "",
        "role":            user.role,
        "avatar_initials": user.avatar_initials or user.name[0].upper(),
        "is_active":       user.is_active,
        "created_at":      user.created_at.isoformat() if user.created_at else None,
        "films_count":     len(user.films) if user.films else 0,
    }


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    Role is always forced to 'producer' to prevent self-escalation.
    Admins are promoted via POST /auth/promote/{id}.
    """
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered. Please log in.")

    initials = "".join(w[0].upper() for w in req.name.split()[:2])
    user = User(
        email=req.email,
        name=req.name,
        company=req.company,
        hashed_password=hash_password(req.password),
        avatar_initials=initials,
        role="producer",    # always producer on self-registration
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email, "role": user.role})
    return TokenResponse(access_token=token, token_type="bearer", user=_user_dict(user))


@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive a JWT token. Token embeds role for RBAC."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    token = create_access_token({"sub": user.email, "role": user.role})
    return TokenResponse(access_token=token, token_type="bearer", user=_user_dict(user))


@router.get("/auth/me")
def get_me(current_user: User = Depends(require_user)):
    """Return current authenticated user profile."""
    return _user_dict(current_user)


@router.post("/auth/logout")
def logout():
    """Logout hint — client should delete token from localStorage."""
    return {"message": "Logged out successfully. Delete your token client-side."}


@router.post("/auth/promote/{user_id}")
def promote_user(
    user_id: int,
    req: PromoteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    [ADMIN ONLY] Promote or demote a user's role.
    Allowed roles: 'producer', 'admin'
    """
    if req.role not in ("producer", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'producer' or 'admin'.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.role = req.role
    db.commit()
    return {"message": f"User {user.email} promoted to {req.role}.", "user": _user_dict(user)}


@router.get("/admin/users")
def list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """[ADMIN ONLY] List all registered users."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {
        "total": len(users),
        "users": [_user_dict(u) for u in users],
    }


@router.patch("/admin/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """[ADMIN ONLY] Deactivate a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = False
    db.commit()
    return {"message": f"User {user.email} deactivated."}
