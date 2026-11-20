from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.security import decode_token
from app.models.user import User, RoleEnum
from app.models.profile import Student, Faculty

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user


def require_roles(allowed_roles: List[RoleEnum]):
    """Enforces Role-Based Access Control on FastAPI routes."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {[r.value for r in allowed_roles]}."
            )
        return current_user
    return role_checker


def get_current_student(
    current_user: User = Depends(require_roles([RoleEnum.STUDENT])),
    db: Session = Depends(get_db)
) -> Student:
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for this user."
        )
    return student


def get_current_faculty(
    current_user: User = Depends(require_roles([RoleEnum.FACULTY])),
    db: Session = Depends(get_db)
) -> Faculty:
    faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty profile not found for this user."
        )
    return faculty


def get_current_admin(
    current_user: User = Depends(require_roles([RoleEnum.ADMIN]))
) -> User:
    return current_user
