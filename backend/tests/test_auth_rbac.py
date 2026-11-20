import pytest
from fastapi import HTTPException
from app.models.user import User, RoleEnum
from app.schemas.auth import LoginRequest
from app.api.auth import login
from app.api.admin import get_system_stats
from app.auth.dependencies import require_roles


def test_login_success(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    res = login(LoginRequest(email=u.email, password="Pass@123"), db_session)
    assert res.role == RoleEnum.STUDENT
    assert res.roll_number == "160121733001"
    assert res.access_token is not None


def test_login_invalid_password(db_session):
    with pytest.raises(HTTPException) as exc:
        login(LoginRequest(email="rohan@test.ac.in", password="WrongPassword!"), db_session)
    assert exc.value.status_code == 401


def test_student_cannot_access_faculty_endpoint(db_session):
    student_user = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    faculty_checker = require_roles([RoleEnum.FACULTY])
    with pytest.raises(HTTPException) as exc:
        faculty_checker(student_user)
    assert exc.value.status_code == 403
    assert "Operation not permitted" in exc.value.detail


def test_student_cannot_access_admin_stats(db_session):
    student_user = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    admin_checker = require_roles([RoleEnum.ADMIN])
    with pytest.raises(HTTPException) as exc:
        admin_checker(student_user)
    assert exc.value.status_code == 403


def test_admin_accesses_stats(db_session):
    admin_user = db_session.query(User).filter(User.email == "admin@test.ac.in").first()
    res = get_system_stats(admin_user, db_session)
    assert res["total_students"] >= 1
    assert res["system_status"] == "Healthy"
