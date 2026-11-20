from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field
from app.models.records import AttendanceStatusEnum, FeeStatusEnum


class SubjectAttendance(BaseModel):
    subject_id: int
    subject_code: str
    subject_name: str
    total_classes: int
    attended_classes: int
    percentage: float
    is_eligible: bool  # >= 75%
    status_indicator: str  # "Good", "Warning", "Critical"


class AttendanceSummaryResponse(BaseModel):
    student_id: int
    roll_number: str
    overall_total_classes: int
    overall_attended_classes: int
    overall_percentage: float
    overall_eligible: bool
    subjects: List[SubjectAttendance]


class AttendanceTargetRequest(BaseModel):
    subject_id: Optional[int] = None
    target_percentage: float = Field(default=75.0, ge=0.0, le=100.0)


class AttendanceTargetResponse(BaseModel):
    subject_id: Optional[int]
    subject_name: Optional[str]
    current_attended: int
    current_total: int
    current_percentage: float
    target_percentage: float
    classes_needed: int
    can_miss_classes: int
    message: str


class TimetableEntryResponse(BaseModel):
    id: int
    day_of_week: str
    start_time: str
    end_time: str
    subject_code: str
    subject_name: str
    faculty_name: str
    room_number: str


class ExamResultResponse(BaseModel):
    subject_code: str
    subject_name: str
    credits: int
    internal_marks: float
    external_marks: float
    total_marks: float
    grade: str
    grade_points: float


class SemesterResultSummary(BaseModel):
    semester: int
    sgpa: float
    total_credits: int
    results: List[ExamResultResponse]


class FeeResponse(BaseModel):
    id: int
    fee_type: str
    academic_year: str
    semester: int
    total_amount: float
    paid_amount: float
    due_amount: float
    due_date: date
    status: FeeStatusEnum


class StudyPlanRequest(BaseModel):
    subject_id: int
    days_until_exam: int = Field(default=7, ge=1, le=60)
    hours_per_day: float = Field(default=3.0, ge=0.5, le=12.0)
    focus_topics: Optional[List[str]] = None


class StudyPlanDay(BaseModel):
    day_number: int
    date_str: str
    unit_number: int
    topics: List[str]
    hours: float
    practice_problems_count: int
    tips: str


class StudyPlanResponse(BaseModel):
    subject_code: str
    subject_name: str
    total_days: int
    daily_schedule: List[StudyPlanDay]
    ai_recommendation: str
