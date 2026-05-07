from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    decode_token,
)
from app.models.all import User
from app.schemas.__init__ import LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")

    if not user.is_active:
        raise HTTPException(403, "User account is disabled")

    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role}
    )

    return LoginResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            employee_id=user.employee_id,
            department=user.department,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


@router.post("/register")
def register(request: LoginRequest, db: Session = Depends(get_db)):
    """Simple registration for hackathon demo."""
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    user = User(
        email=request.email,
        full_name=request.email.split("@")[0],
        department="Revenue",
        role="NODAL_OFFICER",
        hashed_password=get_password_hash(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created", "user_id": str(user.id)}


@router.get("/me", response_model=UserResponse)
def get_current_user(db: Session = Depends(get_db)):
    """For demo: return first active user. Real auth would decode JWT."""
    user = db.query(User).filter(User.is_active == True).first()
    if not user:
        raise HTTPException(404, "No user found")
    return user
