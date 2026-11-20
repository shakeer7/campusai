import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class CorrectionStatusEnum(str, enum.Enum):
    DRAFT_PENDING_CONFIRMATION = "draft_pending_confirmation"
    PENDING_FACULTY_APPROVAL = "pending_faculty_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class WorkflowStatusEnum(str, enum.Enum):
    RUNNING = "running"
    WAITING_HUMAN_INPUT = "waiting_human_input"
    COMPLETED = "completed"
    FAILED = "failed"


class CorrectionRequest(Base):
    __tablename__ = "correction_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True, index=True)
    attendance_date = Column(Date, nullable=False)
    period_number = Column(Integer, default=1, nullable=False)
    current_status = Column(String(20), default="absent", nullable=False)
    requested_status = Column(String(20), default="present", nullable=False)
    reason = Column(Text, nullable=False)
    proof_url = Column(String(500), nullable=True)
    review_status = Column(Enum(CorrectionStatusEnum), default=CorrectionStatusEnum.DRAFT_PENDING_CONFIRMATION, nullable=False)
    faculty_notes = Column(Text, nullable=True)
    workflow_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="correction_requests")
    faculty = relationship("Faculty", back_populates="correction_reviews")


class AgentWorkflow(Base):
    __tablename__ = "agent_workflows"

    id = Column(Integer, primary_key=True, index=True)
    workflow_type = Column(String(50), default="attendance_correction", nullable=False)
    conversation_id = Column(String(100), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    current_step = Column(String(50), default="drafting", nullable=False)
    state_data = Column(JSON, default=dict, nullable=False)
    status = Column(Enum(WorkflowStatusEnum), default=WorkflowStatusEnum.RUNNING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="academic", nullable=False)  # attendance, exam, workflow, system
    is_read = Column(Integer, default=0, nullable=False)  # 0: unread, 1: read
    link = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # LOGIN, CORRECTION_RAISED, CORRECTION_APPROVED, etc.
    entity_type = Column(String(50), nullable=False)          # attendance_record, correction_request, user
    entity_id = Column(String(50), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
