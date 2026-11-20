from app.models.user import User
from app.models.profile import Student
from app.api.students import (
    get_my_student_profile,
    get_my_attendance,
    calculate_attendance_target_endpoint,
    get_my_timetable_endpoint,
    get_my_exam_results_endpoint,
    get_my_fees_endpoint,
)
from app.schemas.student import AttendanceTargetRequest


def test_get_student_profile(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    student = db_session.query(Student).filter(Student.user_id == u.id).first()
    res = get_my_student_profile(student)
    assert res["roll_number"] == "160121733001"
    assert res["full_name"] == "Rohan Reddy"
    assert res["current_semester"] == 6


def test_get_student_attendance(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    student = db_session.query(Student).filter(Student.user_id == u.id).first()
    res = get_my_attendance(student, db_session)
    assert res.roll_number == "160121733001"
    assert res.overall_total_classes == 10
    assert res.overall_attended_classes == 8
    assert res.overall_percentage == 80.0
    assert res.overall_eligible is True


def test_calculate_target_endpoint(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    student = db_session.query(Student).filter(Student.user_id == u.id).first()
    res = calculate_attendance_target_endpoint(
        AttendanceTargetRequest(target_percentage=75.0),
        student,
        db_session
    )
    assert res.current_percentage == 80.0
    assert res.classes_needed == 0


def test_get_timetable(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    student = db_session.query(Student).filter(Student.user_id == u.id).first()
    res = get_my_timetable_endpoint(None, student, db_session)
    assert len(res) >= 1
    assert res[0].day_of_week == "Monday"
    assert res[0].room_number == "L-304"


def test_get_results(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    student = db_session.query(Student).filter(Student.user_id == u.id).first()
    res = get_my_exam_results_endpoint(None, student, db_session)
    assert len(res) >= 1
    assert res[0].semester == 5
    assert res[0].sgpa == 10.0


def test_get_fees(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    student = db_session.query(Student).filter(Student.user_id == u.id).first()
    res = get_my_fees_endpoint(student, db_session)
    assert len(res) >= 1
    assert res[0].fee_type == "Tuition Fee"
    assert res[0].status == "paid"
