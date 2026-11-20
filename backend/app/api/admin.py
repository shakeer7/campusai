from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.user import User, RoleEnum
from app.models.profile import Student, Faculty
from app.models.academic import Subject
from app.models.records import AttendanceRecord, AttendanceStatusEnum
from app.models.workflow import AuditLog
from app.auth.dependencies import require_roles

router = APIRouter(prefix="/admin", tags=["Administrator Dashboard"])


@router.get("/stats")
def get_system_stats(
    admin: User = Depends(require_roles([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    total_students = db.query(Student).count()
    total_faculty = db.query(Faculty).count()
    total_subjects = db.query(Subject).count()

    total_attendance = db.query(AttendanceRecord).count()
    present_attendance = db.query(AttendanceRecord).filter(
        AttendanceRecord.status.in_([AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.EXCUSED])
    ).count()

    avg_attendance = round((present_attendance / total_attendance * 100), 2) if total_attendance > 0 else 0.0

    total_audits = db.query(AuditLog).count()

    return {
        "total_students": total_students,
        "total_faculty": total_faculty,
        "total_subjects": total_subjects,
        "average_attendance_percentage": avg_attendance,
        "total_audit_events": total_audits,
        "system_status": "Healthy",
        "bedrock_connectivity": "Configured",
        "database_storage": "PostgreSQL with pgvector"
    }


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    admin: User = Depends(require_roles([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "details": l.details,
            "timestamp": str(l.timestamp)
        }
        for l in logs
    ]


@router.get("/users")
def get_users_list(
    admin: User = Depends(require_roles([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    users = db.query(User).limit(50).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "created_at": str(u.created_at)
        }
        for u in users
    ]
