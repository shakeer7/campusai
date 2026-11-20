from datetime import date
from app.models.user import User
from app.models.profile import Student, Faculty
from app.agents.attendance_correction import (
    create_initial_workflow,
    confirm_and_submit_workflow,
    process_faculty_approval_workflow,
)


def test_correction_workflow_lifecycle(db_session):
    student_user = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    student = db_session.query(Student).filter(Student.user_id == student_user.id).first()
    faculty_user = db_session.query(User).filter(User.email == "faculty@test.ac.in").first()

    # Step 1: Draft workflow
    draft_state = create_initial_workflow(
        db=db_session,
        student=student,
        conversation_id="test-conv-001",
        subject_input="Data Structures",
        attendance_date=date.today(),
        period_number=1,
        reason="Biometric device did not record attendance on entry."
    )
    assert draft_state["status"] == "waiting_student_confirmation"
    assert draft_state["subject_name"] == "Data Structures"
    wf_id = draft_state["workflow_id"]

    # Step 2: Student Confirms
    confirmed_state = confirm_and_submit_workflow(
        db=db_session,
        workflow_id=wf_id,
        student=student,
        confirmed=True
    )
    assert confirmed_state["status"] == "pending_faculty_approval"
    ticket_id = confirmed_state["ticket_id"]
    assert ticket_id is not None

    # Step 3: Faculty Approves
    decision_res = process_faculty_approval_workflow(
        db=db_session,
        ticket_id=ticket_id,
        faculty_user_id=faculty_user.id,
        approved=True,
        notes="Verified lab logbook. Student was present."
    )
    assert decision_res["status"] == "APPROVED"
