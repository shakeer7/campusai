import enum
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class AttendanceStatusEnum(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class FeeStatusEnum(str, enum.Enum):
    PAID = "paid"
    PARTIAL = "partial"
    PENDING = "pending"


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)
    date = Column(Date, default=date.today, nullable=False, index=True)
    period_number = Column(Integer, default=1, nullable=False)  # 1 to 7
    status = Column(Enum(AttendanceStatusEnum), default=AttendanceStatusEnum.PRESENT, nullable=False)
    remarks = Column(String(255), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")
    faculty = relationship("Faculty", back_populates="attendance_records")

    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', 'date', 'period_number', name='uix_student_attendance_period'),
    )


class ExamSchedule(Base):
    __tablename__ = "exam_schedules"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    semester = Column(Integer, nullable=False)
    exam_type = Column(String(50), nullable=False)  # "Mid-Term 1", "Mid-Term 2", "Semester End Examination"
    exam_date = Column(Date, nullable=False)
    start_time = Column(String(10), nullable=False)  # "10:00"
    end_time = Column(String(10), nullable=False)    # "13:00"
    hall_number = Column(String(50), default="Exam Hall 1", nullable=False)
    max_marks = Column(Integer, default=100, nullable=False)

    subject = relationship("Subject", back_populates="exam_schedules")


class ExamResult(Base):
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    exam_type = Column(String(50), default="Semester End", nullable=False)
    semester = Column(Integer, nullable=False)
    internal_marks = Column(Float, default=0.0, nullable=False)
    external_marks = Column(Float, default=0.0, nullable=False)
    total_marks = Column(Float, default=0.0, nullable=False)
    grade = Column(String(5), default="A", nullable=False)  # O, A+, A, B+, B, C, F
    grade_points = Column(Float, default=8.0, nullable=False)
    sgpa = Column(Float, default=8.0, nullable=True)
    credits_earned = Column(Integer, default=3, nullable=False)

    student = relationship("Student", back_populates="exam_results")
    subject = relationship("Subject", back_populates="exam_results")


class Fee(Base):
    __tablename__ = "fees"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(20), default="2025-2026", nullable=False)
    semester = Column(Integer, default=6, nullable=False)
    fee_type = Column(String(100), default="Tuition Fee", nullable=False)  # Tuition, Exam, Hostel, Special
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(FeeStatusEnum), default=FeeStatusEnum.PENDING, nullable=False)

    student = relationship("Student", back_populates="fees")
