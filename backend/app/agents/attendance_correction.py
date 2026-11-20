import uuid
import logging
from datetime import datetime, date
from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from app.models.profile import Student, Faculty
from app.models.academic import Subject, Timetable
from app.models.records import AttendanceRecord, AttendanceStatusEnum
from app.models.workflow import CorrectionRequest, CorrectionStatusEnum, AgentWorkflow, WorkflowStatusEnum
from app.services.audit_service import log_audit
from app.services.notification_service import send_notification

logger = logging.getLogger(__name__)


class CorrectionWorkflowState(TypedDict):
    workflow_id: str
    conversation_id: str
    student_id: int
    roll_number: str
    student_name: str
    subject_code_or_name: str
    subject_id: Optional[int]
    subject_name: Optional[str]
    attendance_date: str
    period_number: int
    current_status: str
    requested_status: str
    reason: str
    faculty_id: Optional[int]
    faculty_name: Optional[str]
    ticket_id: Optional[int]
    status: str
    preview_message: str
    error: Optional[str]


def create_initial_workflow(
    db: Session,
    student: Student,
    conversation_id: str,
    subject_input: str,
    attendance_date: date,
    period_number: int,
    reason: str
) -> Dict[str, Any]:
    """
    Step 1 & 2: Identifies student, searches attendance records, builds initial draft state.
    """
    workflow_id = f"wf-{uuid.uuid4().hex[:10]}"

    # Match subject
    subject = db.query(Subject).filter(
        (Subject.code.ilike(f"%{subject_input}%")) | (Subject.name.ilike(f"%{subject_input}%"))
    ).first()

    if not subject:
        return {
            "workflow_id": workflow_id,
            "status": "failed",
            "error": f"Subject '{subject_input}' not found in course catalog."
        }

    # Find assigned faculty
    slot = db.query(Timetable).filter(
        Timetable.subject_id == subject.id,
        Timetable.department_id == student.department_id,
        Timetable.semester == student.current_semester
    ).first()

    fac_id = slot.faculty_id if slot else None
    fac_name = slot.faculty.user.full_name if (slot and slot.faculty and slot.faculty.user) else "Course In-Charge"

    # Check existing attendance record
    att_rec = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id,
        AttendanceRecord.subject_id == subject.id,
        AttendanceRecord.date == attendance_date,
        AttendanceRecord.period_number == period_number
    ).first()

    current_status = att_rec.status.value if att_rec else "absent (unmarked)"

    preview_msg = (
        f"**Attendance Correction Draft Preview:**\n"
        f"- **Student Roll No**: {student.roll_number} ({student.user.full_name})\n"
        f"- **Subject**: {subject.name} ({subject.code})\n"
        f"- **Class Date & Period**: {attendance_date} (Period {period_number})\n"
        f"- **Recorded Status**: `{current_status}` ➔ **Requested**: `present`\n"
        f"- **Assigned Faculty**: {fac_name}\n"
        f"- **Reason Given**: *\"{reason}\"*\n\n"
        f"Do you confirm raising this official correction request for faculty review?"
    )

    state_data = {
        "workflow_id": workflow_id,
        "conversation_id": conversation_id,
        "student_id": student.id,
        "roll_number": student.roll_number,
        "student_name": student.user.full_name,
        "subject_code_or_name": subject_input,
        "subject_id": subject.id,
        "subject_name": subject.name,
        "attendance_date": str(attendance_date),
        "period_number": period_number,
        "current_status": current_status,
        "requested_status": "present",
        "reason": reason,
        "faculty_id": fac_id,
        "faculty_name": fac_name,
        "ticket_id": None,
        "status": "waiting_student_confirmation",
        "preview_message": preview_msg,
        "error": None
    }

    # Persist workflow state in database
    persisted_wf = AgentWorkflow(
        workflow_type="attendance_correction",
        conversation_id=conversation_id,
        user_id=student.user_id,
        current_step="waiting_student_confirmation",
        state_data=state_data,
        status=WorkflowStatusEnum.WAITING_HUMAN_INPUT
    )
    db.add(persisted_wf)
    db.commit()

    return state_data


def confirm_and_submit_workflow(
    db: Session,
    workflow_id: str,
    student: Student,
    confirmed: bool,
    modified_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Step 6 & 7: Receives student confirmation.
    If confirmed, creates ticket in DB and routes to assigned faculty.
    """
    wf_record = db.query(AgentWorkflow).filter(
        AgentWorkflow.user_id == student.user_id,
        AgentWorkflow.current_step == "waiting_student_confirmation"
    ).order_by(AgentWorkflow.created_at.desc()).first()

    if not wf_record or wf_record.state_data.get("workflow_id") != workflow_id:
        return {"error": "Active correction draft not found or session expired."}

    state = wf_record.state_data

    if not confirmed:
        wf_record.status = WorkflowStatusEnum.FAILED
        wf_record.current_step = "cancelled_by_student"
        state["status"] = "cancelled"
        state["preview_message"] = "Attendance correction request cancelled."
        wf_record.state_data = state
        db.commit()
        return state

    if modified_reason:
        state["reason"] = modified_reason

    # Create official correction ticket
    att_date = datetime.strptime(state["attendance_date"], "%Y-%m-%d").date()
    ticket = CorrectionRequest(
        student_id=state["student_id"],
        subject_id=state["subject_id"],
        faculty_id=state["faculty_id"],
        attendance_date=att_date,
        period_number=state["period_number"],
        current_status=state["current_status"],
        requested_status="present",
        reason=state["reason"],
        review_status=CorrectionStatusEnum.PENDING_FACULTY_APPROVAL,
        workflow_id=workflow_id
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    state["ticket_id"] = ticket.id
    state["status"] = "pending_faculty_approval"
    state["preview_message"] = f"Correction Ticket #{ticket.id} successfully lodged and routed to {state['faculty_name']} for verification."

    wf_record.current_step = "pending_faculty_approval"
    wf_record.status = WorkflowStatusEnum.RUNNING
    wf_record.state_data = state
    db.commit()

    # Send notification to faculty
    if state["faculty_id"]:
        fac = db.query(Faculty).filter(Faculty.id == state["faculty_id"]).first()
        if fac:
            send_notification(
                db,
                user_id=fac.user_id,
                title="Action Required: Attendance Correction",
                message=f"Student {student.roll_number} has requested attendance correction for {state['subject_name']} on {att_date}.",
                notification_type="workflow",
                link=f"/faculty/approvals?id={ticket.id}"
            )

    log_audit(db, student.user_id, "WORKFLOW_CONFIRMED", "correction_request", str(ticket.id), state)

    return state


def process_faculty_approval_workflow(
    db: Session,
    ticket_id: int,
    faculty_user_id: int,
    approved: bool,
    notes: str
) -> Dict[str, Any]:
    """
    Step 9, 10, 11: Human-in-the-loop faculty decision execution.
    Only authorized faculty can approve or reject. Updates records, notifies student, and records audit.
    """
    faculty = db.query(Faculty).filter(Faculty.user_id == faculty_user_id).first()
    ticket = db.query(CorrectionRequest).filter(CorrectionRequest.id == ticket_id).first()
    if not ticket:
        raise ValueError(f"Ticket #{ticket_id} not found.")

    if approved:
        ticket.review_status = CorrectionStatusEnum.APPROVED
        ticket.faculty_notes = notes

        # Update or create attendance record
        rec = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == ticket.student_id,
            AttendanceRecord.subject_id == ticket.subject_id,
            AttendanceRecord.date == ticket.attendance_date,
            AttendanceRecord.period_number == ticket.period_number
        ).first()

        if rec:
            rec.status = AttendanceStatusEnum.PRESENT
            rec.remarks = f"Approved by {faculty.user.full_name}: {notes}"
        else:
            rec = AttendanceRecord(
                student_id=ticket.student_id,
                subject_id=ticket.subject_id,
                faculty_id=faculty.id if faculty else None,
                date=ticket.attendance_date,
                period_number=ticket.period_number,
                status=AttendanceStatusEnum.PRESENT,
                remarks=f"Created via approved correction: {notes}"
            )
            db.add(rec)

        db.commit()

        # Notify student
        send_notification(
            db,
            user_id=ticket.student.user_id,
            title="Attendance Correction Approved",
            message=f"Your attendance for {ticket.attendance_date} has been updated to Present.",
            notification_type="workflow"
        )
        log_audit(db, faculty_user_id, "FACULTY_APPROVED_ATTENDANCE", "correction_request", str(ticket.id), {"notes": notes})
        return {"status": "APPROVED", "ticket_id": ticket.id, "message": "Attendance marked Present successfully."}

    else:
        ticket.review_status = CorrectionStatusEnum.REJECTED
        ticket.faculty_notes = notes
        db.commit()

        send_notification(
            db,
            user_id=ticket.student.user_id,
            title="Attendance Correction Rejected",
            message=f"Your attendance correction request #{ticket.id} was rejected: {notes}",
            notification_type="workflow"
        )
        log_audit(db, faculty_user_id, "FACULTY_REJECTED_ATTENDANCE", "correction_request", str(ticket.id), {"notes": notes})
        return {"status": "REJECTED", "ticket_id": ticket.id, "message": f"Request rejected: {notes}"}
