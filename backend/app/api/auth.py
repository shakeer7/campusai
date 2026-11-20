from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, RoleEnum
from app.models.profile import Student, Faculty
from app.schemas.auth import Token, LoginRequest, RefreshTokenRequest, UserResponse
from app.auth.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is deactivated")

    access_token = create_access_token(user_id=user.id, email=user.email, role=user.role)
    refresh_token = create_refresh_token(user_id=user.id, email=user.email, role=user.role)

    roll_number = None
    employee_id = None
    if user.role == RoleEnum.STUDENT and user.student_profile:
        roll_number = user.student_profile.roll_number
    elif user.role == RoleEnum.FACULTY and user.faculty_profile:
        employee_id = user.faculty_profile.employee_id

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        roll_number=roll_number,
        employee_id=employee_id
    )


@router.post("/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        access_token = create_access_token(user_id=user.id, email=user.email, role=user.role)
        new_refresh = create_refresh_token(user_id=user.id, email=user.email, role=user.role)

        roll_number = user.student_profile.roll_number if user.student_profile else None
        employee_id = user.faculty_profile.employee_id if user.faculty_profile else None

        return Token(
            access_token=access_token,
            refresh_token=new_refresh,
            token_type="bearer",
            role=user.role,
            user_id=user.id,
            full_name=user.full_name,
            roll_number=roll_number,
            employee_id=employee_id
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token refresh failed: {e}")


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
