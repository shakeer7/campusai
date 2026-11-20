import os
import sys
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, get_db
from app.main import app
from app.auth.security import get_password_hash, create_access_token
from app.models.user import User, RoleEnum
from app.models.academic import Department, Course, Subject, SyllabusTopic, Enrollment, Timetable
from app.models.profile import Student, Faculty
from app.models.records import AttendanceRecord, AttendanceStatusEnum, ExamResult, Fee, FeeStatusEnum
from app.models.rag import Document, DocumentChunk, DocumentTypeEnum
from app.rag.embedder import generate_embedding

# Use SQLite in-memory database with StaticPool so all threads & test sessions share the exact same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed Department & Course
    dept = Department(code="CSE", name="Computer Science and Engineering")
    db.add(dept)
    db.flush()

    course = Course(department_id=dept.id, name="B.E. CSE", degree="B.E.")
    db.add(course)
    db.flush()

    # Seed Subjects
    sub_ds = Subject(code="20CSC01", name="Data Structures", department_id=dept.id, semester=6, credits=4)
    sub_cloud = Subject(code="20ITC08", name="Cloud Computing", department_id=dept.id, semester=6, credits=3)
    db.add_all([sub_ds, sub_cloud])
    db.flush()

    # Seed Admin
    u_admin = User(email="admin@test.ac.in", hashed_password=get_password_hash("Pass@123"), full_name="Admin User", role=RoleEnum.ADMIN)
    db.add(u_admin)
    db.flush()

    # Seed Faculty
    u_fac = User(email="faculty@test.ac.in", hashed_password=get_password_hash("Pass@123"), full_name="Dr. Srinivas", role=RoleEnum.FACULTY)
    db.add(u_fac)
    db.flush()

    fac = Faculty(user_id=u_fac.id, employee_id="FAC-001", department_id=dept.id, designation="Professor")
    db.add(fac)
    db.flush()

    # Seed Student 1 (Rohan)
    u_stud1 = User(email="rohan@test.ac.in", hashed_password=get_password_hash("Pass@123"), full_name="Rohan Reddy", role=RoleEnum.STUDENT)
    db.add(u_stud1)
    db.flush()

    stud1 = Student(user_id=u_stud1.id, roll_number="160121733001", department_id=dept.id, course_id=course.id, current_semester=6, cgpa=8.5)
    db.add(stud1)
    db.flush()

    # Seed Student 2 (Ananya)
    u_stud2 = User(email="ananya@test.ac.in", hashed_password=get_password_hash("Pass@123"), full_name="Ananya Sharma", role=RoleEnum.STUDENT)
    db.add(u_stud2)
    db.flush()

    stud2 = Student(user_id=u_stud2.id, roll_number="160121733045", department_id=dept.id, course_id=course.id, current_semester=6, cgpa=7.8)
    db.add(stud2)
    db.flush()

    # Enrollments
    db.add_all([
        Enrollment(student_id=stud1.id, subject_id=sub_ds.id, semester=6, academic_year="2025-2026"),
        Enrollment(student_id=stud1.id, subject_id=sub_cloud.id, semester=6, academic_year="2025-2026"),
        Enrollment(student_id=stud2.id, subject_id=sub_ds.id, semester=6, academic_year="2025-2026")
    ])
    db.flush()

    # Attendance: 10 classes for stud1 (8 present, 2 absent = 80%)
    for i in range(10):
        status = AttendanceStatusEnum.PRESENT if i < 8 else AttendanceStatusEnum.ABSENT
        db.add(AttendanceRecord(
            student_id=stud1.id,
            subject_id=sub_ds.id,
            faculty_id=fac.id,
            date=date.today() - timedelta(days=i),
            period_number=1,
            status=status
        ))

    # Fee Record
    db.add(Fee(
        student_id=stud1.id,
        academic_year="2025-2026",
        semester=6,
        fee_type="Tuition Fee",
        total_amount=50000.0,
        paid_amount=50000.0,
        due_date=date.today() + timedelta(days=30),
        status=FeeStatusEnum.PAID
    ))

    # Exam Result
    db.add(ExamResult(
        student_id=stud1.id,
        subject_id=sub_ds.id,
        semester=5,
        internal_marks=28.0,
        external_marks=62.0,
        total_marks=90.0,
        grade="O",
        grade_points=10.0,
        sgpa=9.0,
        credits_earned=4
    ))

    # Timetable
    db.add(Timetable(
        department_id=dept.id,
        semester=6,
        section="A",
        subject_id=sub_ds.id,
        faculty_id=fac.id,
        day_of_week="Monday",
        start_time="09:30",
        end_time="10:30",
        room_number="L-304"
    ))

    # RAG Document
    doc = Document(title="CSE Academic Regulations", doc_type=DocumentTypeEnum.REGULATION, department_id=dept.id)
    db.add(doc)
    db.flush()

    sample_text = "Minimum 75% attendance is required to appear in examinations. Medical condonation is allowed down to 65%."
    db.add(DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content=sample_text,
        page_number=1,
        token_count=len(sample_text.split()),
        embedding=generate_embedding(sample_text)
    ))

    db.commit()
    yield db
    db.close()


@pytest.fixture
def db_session(setup_db):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, raise_server_exceptions=True)
    app.dependency_overrides.clear()


@pytest.fixture
def student_auth_headers(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    token = create_access_token(user_id=u.id, email=u.email, role=u.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student2_auth_headers(db_session):
    u = db_session.query(User).filter(User.email == "ananya@test.ac.in").first()
    token = create_access_token(user_id=u.id, email=u.email, role=u.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def faculty_auth_headers(db_session):
    u = db_session.query(User).filter(User.email == "faculty@test.ac.in").first()
    token = create_access_token(user_id=u.id, email=u.email, role=u.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(db_session):
    u = db_session.query(User).filter(User.email == "admin@test.ac.in").first()
    token = create_access_token(user_id=u.id, email=u.email, role=u.role)
    return {"Authorization": f"Bearer {token}"}
