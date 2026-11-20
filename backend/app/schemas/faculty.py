from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field
from app.models.records import AttendanceStatusEnum
from app.models.workflow import CorrectionStatusEnum


class FacultySubjectSummary(BaseModel):
    subject_id: int
    code: str
    name: str
    semester: int
    total_students: int
    average_attendance: float


class MarkAttendanceItem(BaseModel):
    student_id: int
    status: AttendanceStatusEnum
    remarks: Optional[str] = None


class BatchAttendanceMarkRequest(BaseModel):
    subject_id: int
    attendance_date: date
    period_number: int = Field(default=1, ge=1, le=8)
    records: List[MarkAttendanceItem]


class CorrectionReviewDecision(BaseModel):
    request_id: int
    decision: CorrectionStatusEnum  # APPROVED or REJECTED
    faculty_notes: Optional[str] = None


class CorrectionItemDetail(BaseModel):
    id: int
    student_id: int
    student_name: str
    roll_number: str
    subject_id: int
    subject_code: str
    subject_name: str
    attendance_date: date
    period_number: int
    current_status: str
    requested_status: str
    reason: str
    proof_url: Optional[str]
    review_status: CorrectionStatusEnum
    faculty_notes: Optional[str]
    created_at: str
