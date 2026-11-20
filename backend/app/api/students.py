from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.profile import Student
from app.models.workflow import Notification
from app.auth.dependencies import get_current_student
from app.schemas.student import (
    AttendanceSummaryResponse,
    AttendanceTargetRequest,
    AttendanceTargetResponse,
    TimetableEntryResponse,
    SemesterResultSummary,
    FeeResponse,
    StudyPlanRequest,
    StudyPlanResponse,
)
from app.services.academic_service import (
    get_student_attendance_summary,
    calculate_attendance_math,
    get_student_timetable,
    get_student_results,
    get_student_fees,
    generate_structured_study_plan,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me")
def get_my_student_profile(student: Student = Depends(get_current_student)):
    return {
        "id": student.id,
        "roll_number": student.roll_number,
        "full_name": student.user.full_name,
        "email": student.user.email,
        "department": student.department.name,
        "department_code": student.department.code,
        "course": student.course.name,
        "current_semester": student.current_semester,
        "section": student.section,
        "batch": student.batch,
        "cgpa": student.cgpa
    }


@router.get("/attendance", response_model=AttendanceSummaryResponse)
def get_my_attendance(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return get_student_attendance_summary(db, student.id)


@router.post("/attendance/target", response_model=AttendanceTargetResponse)
def calculate_attendance_target_endpoint(
    req: AttendanceTargetRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    from app.models.records import AttendanceRecord, AttendanceStatusEnum
    from app.models.academic import Subject

    if req.subject_id:
        subject = db.query(Subject).filter(Subject.id == req.subject_id).first()
        records = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.subject_id == req.subject_id
        ).all()
        total = len(records)
        attended = sum(1 for r in records if r.status in [AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.EXCUSED])
        res = calculate_attendance_math(attended, total, req.target_percentage)
        res["subject_id"] = subject.id if subject else None
        res["subject_name"] = subject.name if subject else None
        return AttendanceTargetResponse(**res)
    else:
        summary = get_student_attendance_summary(db, student.id)
        res = calculate_attendance_math(summary.overall_attended_classes, summary.overall_total_classes, req.target_percentage)
        res["subject_id"] = None
        res["subject_name"] = "Overall"
        return AttendanceTargetResponse(**res)


@router.get("/timetable", response_model=List[TimetableEntryResponse])
def get_my_timetable_endpoint(
    day: Optional[str] = Query(None, description="Monday, Tuesday, etc."),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return get_student_timetable(db, student.id, day_of_week=day)


@router.get("/results", response_model=List[SemesterResultSummary])
def get_my_exam_results_endpoint(
    semester: Optional[int] = Query(None),
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return get_student_results(db, student.id, semester=semester)


@router.get("/fees", response_model=List[FeeResponse])
def get_my_fees_endpoint(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return get_student_fees(db, student.id)


@router.post("/study-plan", response_model=StudyPlanResponse)
def generate_study_plan_endpoint(
    req: StudyPlanRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    return generate_structured_study_plan(db, req.subject_id, req.days_until_exam, req.hours_per_day)


@router.get("/notifications")
def get_student_notifications(
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    notifs = db.query(Notification).filter(
        Notification.user_id == student.user_id
    ).order_by(Notification.created_at.desc()).limit(20).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.notification_type,
            "is_read": bool(n.is_read),
            "link": n.link,
            "created_at": str(n.created_at)
        }
        for n in notifs
    ]
