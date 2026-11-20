from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.profile import Faculty
from app.models.academic import Subject, Timetable, Enrollment
from app.models.records import AttendanceRecord, AttendanceStatusEnum
from app.models.workflow import CorrectionRequest, CorrectionStatusEnum
from app.auth.dependencies import get_current_faculty
from app.schemas.faculty import (
    FacultySubjectSummary,
    BatchAttendanceMarkRequest,
    CorrectionReviewDecision,
    CorrectionItemDetail,
)
from app.agents.attendance_correction import process_faculty_approval_workflow

router = APIRouter(prefix="/faculty", tags=["Faculty"])


@router.get("/me")
def get_my_faculty_profile(faculty: Faculty = Depends(get_current_faculty)):
    return {
        "id": faculty.id,
        "employee_id": faculty.employee_id,
        "full_name": faculty.user.full_name,
        "email": faculty.user.email,
        "designation": faculty.designation,
        "department": faculty.department.name,
        "cabin_location": faculty.cabin_location
    }


@router.get("/subjects", response_model=List[FacultySubjectSummary])
def get_faculty_assigned_subjects(
    faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    timetables = db.query(Timetable).filter(Timetable.faculty_id == faculty.id).all()
    subject_ids = list({t.subject_id for t in timetables})

    summaries = []
    for sid in subject_ids:
        subject = db.query(Subject).filter(Subject.id == sid).first()
        if not subject:
            continue
        enrollments = db.query(Enrollment).filter(
            Enrollment.subject_id == sid,
            Enrollment.status == "active"
        ).all()
        student_count = len(enrollments)

        records = db.query(AttendanceRecord).filter(AttendanceRecord.subject_id == sid).all()
        total_recs = len(records)
        attended_recs = sum(1 for r in records if r.status in [AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.EXCUSED])
        avg_pct = round((attended_recs / total_recs * 100), 2) if total_recs > 0 else 0.0

        summaries.append(FacultySubjectSummary(
            subject_id=subject.id,
            code=subject.code,
            name=subject.name,
            semester=subject.semester,
            total_students=student_count,
            average_attendance=avg_pct
        ))

    return summaries


@router.get("/corrections", response_model=List[CorrectionItemDetail])
def get_pending_corrections(
    faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    requests = db.query(CorrectionRequest).filter(
        CorrectionRequest.faculty_id == faculty.id,
        CorrectionRequest.review_status == CorrectionStatusEnum.PENDING_FACULTY_APPROVAL
    ).order_by(CorrectionRequest.created_at.desc()).all()

    return [
        CorrectionItemDetail(
            id=r.id,
            student_id=r.student_id,
            student_name=r.student.user.full_name,
            roll_number=r.student.roll_number,
            subject_id=r.subject_id,
            subject_code=r.subject.code,
            subject_name=r.subject.name,
            attendance_date=r.attendance_date,
            period_number=r.period_number,
            current_status=r.current_status,
            requested_status=r.requested_status,
            reason=r.reason,
            proof_url=r.proof_url,
            review_status=r.review_status,
            faculty_notes=r.faculty_notes,
            created_at=str(r.created_at)
        )
        for r in requests
    ]


@router.post("/corrections/decide")
def decide_correction_request(
    req: CorrectionReviewDecision,
    faculty: Faculty = Depends(get_current_faculty),
    db: Session = Depends(get_db)
):
    ticket = db.query(CorrectionRequest).filter(CorrectionRequest.id == req.request_id).first()
    if not ticket or ticket.faculty_id != faculty.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction ticket not found or not assigned to you."
        )

    is_approved = (req.decision == CorrectionStatusEnum.APPROVED)
    notes = req.faculty_notes or ("Approved by faculty." if is_approved else "Rejected by faculty.")

    res = process_faculty_approval_workflow(
        db=db,
        ticket_id=ticket.id,
        faculty_user_id=faculty.user_id,
        approved=is_approved,
        notes=notes
    )
    return res
