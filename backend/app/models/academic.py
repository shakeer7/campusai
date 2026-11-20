from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # e.g., CSE, IT, ECE, AIDS
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    courses = relationship("Course", back_populates="department")
    subjects = relationship("Subject", back_populates="department")
    students = relationship("Student", back_populates="department")
    faculty_members = relationship("Faculty", back_populates="department")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)  # e.g., Bachelor of Engineering in Computer Science
    degree = Column(String(50), nullable=False, default="B.E.")  # B.E., B.Tech, M.Tech
    duration_years = Column(Integer, default=4, nullable=False)
    total_semesters = Column(Integer, default=8, nullable=False)

    department = relationship("Department", back_populates="courses")
    students = relationship("Student", back_populates="course")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # e.g., 20CSC01
    name = Column(String(255), nullable=False)  # e.g., Data Structures and Algorithms
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    semester = Column(Integer, nullable=False)
    credits = Column(Integer, default=3, nullable=False)
    syllabus_overview = Column(Text, nullable=True)

    department = relationship("Department", back_populates="subjects")
    enrollments = relationship("Enrollment", back_populates="subject")
    attendance_records = relationship("AttendanceRecord", back_populates="subject")
    exam_schedules = relationship("ExamSchedule", back_populates="subject")
    exam_results = relationship("ExamResult", back_populates="subject")
    syllabus_topics = relationship("SyllabusTopic", back_populates="subject", cascade="all, delete-orphan")


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    unit_number = Column(Integer, nullable=False)  # 1 to 5
    unit_title = Column(String(255), nullable=False)
    topic_name = Column(String(255), nullable=False)
    hours_allocated = Column(Integer, default=2)
    learning_outcomes = Column(Text, nullable=True)

    subject = relationship("Subject", back_populates="syllabus_topics")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    semester = Column(Integer, nullable=False)
    academic_year = Column(String(20), nullable=False)  # e.g., "2025-2026"
    status = Column(String(20), default="active", nullable=False)  # active, completed, dropped

    student = relationship("Student", back_populates="enrollments")
    subject = relationship("Subject", back_populates="enrollments")


class Timetable(Base):
    __tablename__ = "timetables"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String(10), default="A", nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)
    day_of_week = Column(String(20), nullable=False)  # Monday, Tuesday, ...
    start_time = Column(String(10), nullable=False)  # "09:30"
    end_time = Column(String(10), nullable=False)    # "10:30"
    room_number = Column(String(50), nullable=False)  # "L-304", "CSE-LAB-2"

    subject = relationship("Subject")
    faculty = relationship("Faculty")
