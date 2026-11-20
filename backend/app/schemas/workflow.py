from typing import List, Optional, Dict, Any
from datetime import date
from pydantic import BaseModel
from app.models.workflow import CorrectionStatusEnum, WorkflowStatusEnum


class CorrectionDraftRequest(BaseModel):
    subject_code_or_name: str
    attendance_date: date
    period_number: Optional[int] = 1
    reason: str


class CorrectionDraftPreview(BaseModel):
    workflow_id: str
    student_roll: str
    student_name: str
    subject_code: str
    subject_name: str
    faculty_name: str
    attendance_date: date
    period_number: int
    current_status: str
    requested_status: str
    reason: str
    needs_confirmation: bool = True
    confirmation_prompt: str


class CorrectionConfirmationSubmission(BaseModel):
    workflow_id: str
    confirmed: bool
    modified_reason: Optional[str] = None


class WorkflowStepResponse(BaseModel):
    workflow_id: str
    conversation_id: str
    current_step: str
    status: WorkflowStatusEnum
    data: Dict[str, Any]
    message: str
