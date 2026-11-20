from app.models.user import User, RoleEnum
from app.tools.registry import execute_tool, ACADEMIC_TOOL_SPECS


def test_tool_specs_exist():
    tool_names = [t["toolSpec"]["name"] for t in ACADEMIC_TOOL_SPECS]
    assert "get_my_attendance" in tool_names
    assert "calculate_attendance_target" in tool_names
    assert "get_my_timetable" in tool_names
    assert "get_my_exam_results" in tool_names
    assert "create_attendance_correction_request" in tool_names
    assert "approve_attendance_correction" in tool_names


def test_execute_get_my_attendance(db_session):
    student_user = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    result = execute_tool("get_my_attendance", {}, student_user, db_session)
    assert "overall_percentage" in result
    assert result["overall_percentage"] == 80.0
    assert result["roll_number"] == "160121733001"


def test_student_cannot_call_approve_tool(db_session):
    student_user = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    result = execute_tool("approve_attendance_correction", {"request_id": 1}, student_user, db_session)
    assert "error" in result
    assert "Unauthorized" in result["error"]
