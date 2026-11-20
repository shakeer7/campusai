from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.profile import Student
from app.auth.dependencies import get_current_student
from app.schemas.workflow import (
    CorrectionDraftRequest,
    CorrectionDraftPreview,
    CorrectionConfirmationSubmission,
    WorkflowStepResponse,
)
from app.agents.attendance_correction import (
    create_initial_workflow,
    confirm_and_submit_workflow,
)

router = APIRouter(prefix="/workflows", tags=["Agentic Workflows"])


@router.post("/correction/draft", response_model=CorrectionDraftPreview)
def draft_attendance_correction(
    req: CorrectionDraftRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    state = create_initial_workflow(
        db=db,
        student=student,
        conversation_id=f"wf-conv-{student.id}",
        subject_input=req.subject_code_or_name,
        attendance_date=req.attendance_date,
        period_number=req.period_number or 1,
        reason=req.reason
    )
    if state.get("status") == "failed":
        raise HTTPException(status_code=400, detail=state.get("error"))

    return CorrectionDraftPreview(
        workflow_id=state["workflow_id"],
        student_roll=state["roll_number"],
        student_name=state["student_name"],
        subject_code=state["subject_code_or_name"],
        subject_name=state["subject_name"],
        faculty_name=state["faculty_name"],
        attendance_date=req.attendance_date,
        period_number=req.period_number or 1,
        current_status=state["current_status"],
        requested_status=state["requested_status"],
        reason=state["reason"],
        needs_confirmation=True,
        confirmation_prompt="Please review the draft above and confirm submission."
    )


@router.post("/correction/confirm")
def confirm_attendance_correction(
    req: CorrectionConfirmationSubmission,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    result = confirm_and_submit_workflow(
        db=db,
        workflow_id=req.workflow_id,
        student=student,
        confirmed=req.confirmed,
        modified_reason=req.modified_reason
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
