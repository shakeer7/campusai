import math
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.academic import Subject, Timetable, Enrollment, SyllabusTopic
from app.models.profile import Student
from app.models.records import AttendanceRecord, AttendanceStatusEnum, ExamResult, Fee, FeeStatusEnum
from app.schemas.student import (
    SubjectAttendance,
    AttendanceSummaryResponse,
    AttendanceTargetResponse,
    TimetableEntryResponse,
    ExamResultResponse,
    SemesterResultSummary,
    FeeResponse,
    StudyPlanDay,
    StudyPlanResponse,
)


def calculate_attendance_math(current_attended: int, current_total: int, target_pct: float = 75.0) -> Dict[str, Any]:
    """Calculates consecutive classes needed to reach target or number of classes student can safely miss."""
    if current_total == 0:
        return {
            "current_attended": 0,
            "current_total": 0,
            "current_percentage": 100.0,
            "target_percentage": target_pct,
            "classes_needed": 0,
            "can_miss_classes": 0,
            "message": "No classes have been conducted yet. Attendance is currently at 100%."
        }

    current_pct = round((current_attended / current_total) * 100, 2)

    if current_pct >= target_pct:
        # Student already satisfies target; calculate how many classes can be safely missed
        # A / (T + y) >= P / 100 => 100 * A >= P * T + P * y => y <= (100 * A - P * T) / P
        if target_pct <= 0:
            can_miss = 999
        else:
            can_miss = max(0, math.floor((100 * current_attended - target_pct * current_total) / target_pct))
        
        return {
            "current_attended": current_attended,
            "current_total": current_total,
            "current_percentage": current_pct,
            "target_percentage": target_pct,
            "classes_needed": 0,
            "can_miss_classes": can_miss,
            "message": f"Great! Your attendance ({current_pct}%) is above the {target_pct}% requirement. You can miss up to {can_miss} upcoming class(es) without falling below {target_pct}%."
        }
    else:
        # Student is below target; calculate consecutive classes needed
        # (A + x) / (T + x) >= P / 100 => (100 - P) * x >= P * T - 100 * A
        denominator = 100.0 - target_pct
        if denominator <= 0:
            classes_needed = 999
        else:
            numerator = (target_pct * current_total) - (100.0 * current_attended)
            classes_needed = max(1, math.ceil(numerator / denominator))

        return {
            "current_attended": current_attended,
            "current_total": current_total,
            "current_percentage": current_pct,
            "target_percentage": target_pct,
            "classes_needed": classes_needed,
            "can_miss_classes": 0,
            "message": f"Attention: Your attendance is currently {current_pct}%. You must attend the next {classes_needed} consecutive class(es) without absence to reach {target_pct}%."
        }


def get_student_attendance_summary(db: Session, student_id: int) -> AttendanceSummaryResponse:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError(f"Student with ID {student_id} not found.")

    # Get all active enrollments for this student
    enrollments = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.status == "active"
    ).all()

    subject_attendances: List[SubjectAttendance] = []
    overall_total = 0
    overall_attended = 0

    for enr in enrollments:
        subject = enr.subject
        # Count total records for this student and subject
        records = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.subject_id == subject.id
        ).all()

        total = len(records)
        attended = sum(1 for r in records if r.status in [AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.EXCUSED])
        pct = round((attended / total * 100), 2) if total > 0 else 100.0

        overall_total += total
        overall_attended += attended

        if pct >= 75.0:
            indicator = "Good"
        elif pct >= 65.0:
            indicator = "Warning"
        else:
            indicator = "Critical"

        subject_attendances.append(SubjectAttendance(
            subject_id=subject.id,
            subject_code=subject.code,
            subject_name=subject.name,
            total_classes=total,
            attended_classes=attended,
            percentage=pct,
            is_eligible=pct >= 75.0,
            status_indicator=indicator
        ))

    overall_pct = round((overall_attended / overall_total * 100), 2) if overall_total > 0 else 100.0

    return AttendanceSummaryResponse(
        student_id=student.id,
        roll_number=student.roll_number,
        overall_total_classes=overall_total,
        overall_attended_classes=overall_attended,
        overall_percentage=overall_pct,
        overall_eligible=overall_pct >= 75.0,
        subjects=subject_attendances
    )


def get_student_timetable(db: Session, student_id: int, day_of_week: Optional[str] = None) -> List[TimetableEntryResponse]:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return []

    query = db.query(Timetable).filter(
        Timetable.department_id == student.department_id,
        Timetable.semester == student.current_semester,
        Timetable.section == student.section
    )

    if day_of_week:
        query = query.filter(Timetable.day_of_week.ilike(day_of_week.strip()))

    entries = query.order_by(Timetable.day_of_week, Timetable.start_time).all()

    result = []
    for entry in entries:
        faculty_name = entry.faculty.user.full_name if entry.faculty and entry.faculty.user else "Faculty TBD"
        result.append(TimetableEntryResponse(
            id=entry.id,
            day_of_week=entry.day_of_week,
            start_time=entry.start_time,
            end_time=entry.end_time,
            subject_code=entry.subject.code,
            subject_name=entry.subject.name,
            faculty_name=faculty_name,
            room_number=entry.room_number
        ))
    return result


def get_student_results(db: Session, student_id: int, semester: Optional[int] = None) -> List[SemesterResultSummary]:
    query = db.query(ExamResult).filter(ExamResult.student_id == student_id)
    if semester:
        query = query.filter(ExamResult.semester == semester)

    all_results = query.order_by(ExamResult.semester, ExamResult.subject_id).all()

    # Group by semester
    semesters_map: Dict[int, List[ExamResult]] = {}
    for res in all_results:
        semesters_map.setdefault(res.semester, []).append(res)

    summaries = []
    for sem, results in sorted(semesters_map.items()):
        total_credits = sum(r.credits_earned for r in results)
        total_weighted_points = sum(r.grade_points * r.credits_earned for r in results)
        sgpa = round(total_weighted_points / total_credits, 2) if total_credits > 0 else 0.0

        item_list = [
            ExamResultResponse(
                subject_code=r.subject.code,
                subject_name=r.subject.name,
                credits=r.credits_earned,
                internal_marks=r.internal_marks,
                external_marks=r.external_marks,
                total_marks=r.total_marks,
                grade=r.grade,
                grade_points=r.grade_points
            )
            for r in results
        ]
        summaries.append(SemesterResultSummary(
            semester=sem,
            sgpa=sgpa,
            total_credits=total_credits,
            results=item_list
        ))

    return summaries


def get_student_fees(db: Session, student_id: int) -> List[FeeResponse]:
    fees = db.query(Fee).filter(Fee.student_id == student_id).order_by(Fee.due_date).all()
    return [
        FeeResponse(
            id=f.id,
            fee_type=f.fee_type,
            academic_year=f.academic_year,
            semester=f.semester,
            total_amount=f.total_amount,
            paid_amount=f.paid_amount,
            due_amount=round(max(0.0, f.total_amount - f.paid_amount), 2),
            due_date=f.due_date,
            status=f.status
        )
        for f in fees
    ]


def generate_structured_study_plan(db: Session, subject_id: int, days_until_exam: int, hours_per_day: float) -> StudyPlanResponse:
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise ValueError(f"Subject ID {subject_id} not found.")

    topics = db.query(SyllabusTopic).filter(SyllabusTopic.subject_id == subject_id).order_by(SyllabusTopic.unit_number).all()

    # Distribute topics across the available days
    daily_schedule: List[StudyPlanDay] = []
    total_units = max(1, len({t.unit_number for t in topics}) if topics else 5)

    for day in range(1, days_until_exam + 1):
        # Assign unit progressively, leaving last day for full mock exam and revision
        if day == days_until_exam:
            unit_num = 0
            day_topics = ["Comprehensive Full-Syllabus Mock Test", "Previous Year Question Paper Analysis", "Formula Sheet Review"]
            tips = "Simulate 3-hour exam conditions. Focus on time management and high-weightage topics."
        else:
            unit_index = ((day - 1) % total_units) + 1
            matching_topics = [t.topic_name for t in topics if t.unit_number == unit_index]
            day_topics = matching_topics if matching_topics else [f"Unit {unit_index} Core Principles and Numerical Problems"]
            tips = f"Dedicate first {hours_per_day * 0.6:.1f} hours to conceptual mastery, then solve 5 university questions."

        daily_schedule.append(StudyPlanDay(
            day_number=day,
            date_str=f"Day {day}",
            unit_number=unit_num if day == days_until_exam else (((day - 1) % total_units) + 1),
            topics=day_topics,
            hours=hours_per_day,
            practice_problems_count=5 if day < days_until_exam else 15,
            tips=tips
        ))

    recommendation = (
        f"Customized study plan for {subject.name} ({subject.code}): "
        f"{days_until_exam} days at {hours_per_day} hrs/day provides a total of {days_until_exam * hours_per_day:.1f} study hours. "
        "Units 1, 3, and 5 typically carry 60% of university exam weightage."
    )

    return StudyPlanResponse(
        subject_code=subject.code,
        subject_name=subject.name,
        total_days=days_until_exam,
        daily_schedule=daily_schedule,
        ai_recommendation=recommendation
    )
