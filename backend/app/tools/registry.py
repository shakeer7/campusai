import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import User, RoleEnum
from app.models.profile import Student, Faculty
from app.models.academic import Subject, SyllabusTopic, Timetable
from app.models.records import ExamSchedule, AttendanceRecord, AttendanceStatusEnum
from app.models.workflow import CorrectionRequest, CorrectionStatusEnum
from app.services.academic_service import (
    get_student_attendance_summary,
    calculate_attendance_math,
    get_student_timetable,
    get_student_results,
    get_student_fees,
    generate_structured_study_plan,
)
from app.services.audit_service import log_audit
from app.services.notification_service import send_notification

logger = logging.getLogger(__name__)

# Bedrock Converse API Tool Specifications
ACADEMIC_TOOL_SPECS = [
    {
        "toolSpec": {
            "name": "get_my_attendance",
            "description": "Retrieves the authenticated student's overall and subject-wise attendance percentages, total classes, and 75% eligibility status.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "calculate_attendance_target",
            "description": "Calculates how many consecutive classes the student must attend to reach a target attendance percentage (default 75%), or how many classes they can safely miss.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "subject_code": {
                            "type": "string",
                            "description": "Optional course/subject code (e.g. 20CSC01) to calculate for a specific subject. Leave empty for overall attendance."
                        },
                        "target_percentage": {
                            "type": "number",
                            "description": "Desired target percentage, e.g., 75.0 or 80.0. Defaults to 75.0."
                        }
                    },
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_my_timetable",
            "description": "Fetches the student's class schedule, classroom numbers, and faculty details for today or a specific day of the week.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "day_of_week": {
                            "type": "string",
                            "description": "Optional day name: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday."
                        }
                    },
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_my_exam_results",
            "description": "Fetches semester exam results, subject grades, SGPA, and cumulative CGPA for the authenticated student.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "semester": {
                            "type": "integer",
                            "description": "Optional semester number (1 to 8). Omit to retrieve all semesters."
                        }
                    },
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_my_exam_schedule",
            "description": "Retrieves upcoming university and mid-term exam timetables, dates, timings, and examination halls.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "semester": {
                            "type": "integer",
                            "description": "Semester number. Defaults to current semester."
                        }
                    },
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_subject_topics",
            "description": "Retrieves the unit-wise syllabus topics and learning outcomes for a specified subject code or name.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "subject_code_or_name": {
                            "type": "string",
                            "description": "Subject code (e.g., 20CSC01) or name (e.g., Cloud Computing, Strategic Management)."
                        }
                    },
                    "required": ["subject_code_or_name"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_pending_fees",
            "description": "Retrieves mock college ERP fee records, tuition dues, payment status, and due dates.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "search_academic_documents",
            "description": "Searches college regulations, syllabus PDFs, and official academic circulars using semantic similarity.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Specific academic or regulation question, topic, or policy."
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "generate_study_plan",
            "description": "Generates an AI-structured day-by-day revision schedule for a subject given exam timeline.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "subject_code_or_name": {
                            "type": "string",
                            "description": "Subject name or code."
                        },
                        "days_until_exam": {
                            "type": "integer",
                            "description": "Days remaining until the exam. Defaults to 7."
                        },
                        "hours_per_day": {
                            "type": "number",
                            "description": "Study hours available per day. Defaults to 3.0."
                        }
                    },
                    "required": ["subject_code_or_name"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "create_attendance_correction_request",
            "description": "Submits an attendance discrepancy correction request for faculty review after student confirmation.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "subject_code_or_name": {
                            "type": "string",
                            "description": "The subject name or code."
                        },
                        "attendance_date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format."
                        },
                        "period_number": {
                            "type": "integer",
                            "description": "Class period (1-7). Defaults to 1."
                        },
                        "reason": {
                            "type": "string",
                            "description": "Justification for correction (e.g. attended on-duty, biometric issue)."
                        }
                    },
                    "required": ["subject_code_or_name", "attendance_date", "reason"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_correction_request_status",
            "description": "Checks the current review status of raised attendance correction requests.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "integer",
                            "description": "Optional specific ticket ID. If omitted, returns all recent requests."
                        }
                    },
                    "required": []
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "approve_attendance_correction",
            "description": "Faculty action: Approves an attendance correction request and updates the student attendance record to present.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "integer",
                            "description": "The correction request ticket ID."
                        },
                        "faculty_notes": {
                            "type": "string",
                            "description": "Approval remarks or justification."
                        }
                    },
                    "required": ["request_id"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "reject_attendance_correction",
            "description": "Faculty action: Rejects an attendance correction request with an explanation.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "integer",
                            "description": "The correction request ticket ID."
                        },
                        "faculty_notes": {
                            "type": "string",
                            "description": "Mandatory reason for rejection."
                        }
                    },
                    "required": ["request_id", "faculty_notes"]
                }
            }
        }
    }
]


def execute_tool(tool_name: str, tool_input: Dict[str, Any], current_user: User, db: Session) -> Dict[str, Any]:
    """
    Executes an academic tool with strict identity resolution from current_user session.
    Never trusts external student_id or user_id supplied by LLM parameters.
    """
    logger.info(f"Executing tool {tool_name} for user={current_user.id} ({current_user.role.value})")

    # 1. get_my_attendance
    if tool_name == "get_my_attendance":
        if current_user.role != RoleEnum.STUDENT:
            return {"error": "Attendance records are only available for authenticated students."}
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return {"error": "Student profile not found."}
        summary = get_student_attendance_summary(db, student.id)
        return summary.model_dump()

    # 2. calculate_attendance_target
    elif tool_name == "calculate_attendance_target":
        if current_user.role != RoleEnum.STUDENT:
            return {"error": "Only students can calculate attendance targets."}
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return {"error": "Student profile not found."}
        
        target_pct = float(tool_input.get("target_percentage", 75.0))
        subject_code = tool_input.get("subject_code")

        if subject_code:
            subject = db.query(Subject).filter(
                (Subject.code.ilike(f"%{subject_code}%")) | (Subject.name.ilike(f"%{subject_code}%"))
            ).first()
            if not subject:
                return {"error": f"Subject '{subject_code}' not found."}
            records = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.subject_id == subject.id
            ).all()
            total = len(records)
            attended = sum(1 for r in records if r.status in [AttendanceStatusEnum.PRESENT, AttendanceStatusEnum.EXCUSED])
            res = calculate_attendance_math(attended, total, target_pct)
            res["subject_name"] = subject.name
            res["subject_code"] = subject.code
            return res
        else:
            summary = get_student_attendance_summary(db, student.id)
            res = calculate_attendance_math(summary.overall_attended_classes, summary.overall_total_classes, target_pct)
            res["subject_name"] = "Overall All Subjects"
            return res

    # 3. get_my_timetable
    elif tool_name == "get_my_timetable":
        if current_user.role != RoleEnum.STUDENT:
            return {"error": "Timetable lookup is restricted to enrolled students."}
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return {"error": "Student profile not found."}
        day = tool_input.get("day_of_week")
        entries = get_student_timetable(db, student.id, day_of_week=day)
        return {"timetable": [e.model_dump() for e in entries]}

    # 4. get_my_exam_results
    elif tool_name == "get_my_exam_results":
        if current_user.role != RoleEnum.STUDENT:
            return {"error": "Exam results are private to the authenticated student."}
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return {"error": "Student profile not found."}
        sem = tool_input.get("semester")
        results = get_student_results(db, student.id, semester=sem)
        return {
            "student_roll": student.roll_number,
            "cgpa": student.cgpa,
            "semesters": [r.model_dump() for r in results]
        }

    # 5. get_my_exam_schedule
    elif tool_name == "get_my_exam_schedule":
        if current_user.role != RoleEnum.STUDENT:
            return {"error": "Exam schedule is available for enrolled students."}
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return {"error": "Student profile not found."}
        sem = tool_input.get("semester", student.current_semester)
        schedules = db.query(ExamSchedule).filter(ExamSchedule.semester == sem).all()
        return {
            "semester": sem,
            "schedules": [
                {
                    "subject_code": s.subject.code,
                    "subject_name": s.subject.name,
                    "exam_type": s.exam_type,
                    "exam_date": str(s.exam_date),
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "hall_number": s.hall_number
                }
                for s in schedules
            ]
        }

    # 6. get_subject_topics
    elif tool_name == "get_subject_topics":
        target = tool_input.get("subject_code_or_name", "")
        subject = db.query(Subject).filter(
            (Subject.code.ilike(f"%{target}%")) | (Subject.name.ilike(f"%{target}%"))
        ).first()
        if not subject:
            return {"error": f"Subject '{target}' not found in college catalog."}
        topics = db.query(SyllabusTopic).filter(SyllabusTopic.subject_id == subject.id).order_by(SyllabusTopic.unit_number).all()
        return {
            "subject_code": subject.code,
            "subject_name": subject.name,
            "credits": subject.credits,
            "overview": subject.syllabus_overview,
            "units": [
                {
                    "unit_number": t.unit_number,
                    "unit_title": t.unit_title,
                    "topic_name": t.topic_name,
                    "hours_allocated": t.hours_allocated,
                    "learning_outcomes": t.learning_outcomes
                }
                for t in topics
            ]
        }

    # 7. get_pending_fees
    elif tool_name == "get_pending_fees":
        if current_user.role != RoleEnum.STUDENT:
            return {"error": "Fee accounts are restricted to the student."}
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return {"error": "Student profile not found."}
        fees = get_student_fees(db, student.id)
        total_due = sum(f.due_amount for f in fees)
        return {
            "student_roll": student.roll_number,
            "total_pending_due": total_due,
            "records": [f.model_dump() for f in fees]
        }

    # 8. search_academic_documents (RAG Tool)
    elif tool_name == "search_academic_documents":
        query = tool_input.get("query", "")
        from app.rag.retriever import search_documents
        results = search_documents(db, query, user=current_user, top_k=4)
        return {"query": query, "results": results}

    # 9. generate_study_plan
    elif tool_name == "generate_study_plan":
        sub_name = tool_input.get("subject_code_or_name", "")
        days = int(tool_input.get("days_until_exam", 7))
        hours = float(tool_input.get("hours_per_day", 3.0))
        subject = db.query(Subject).filter(
            (Subject.code.ilike(f"%{sub_name}%")) | (Subject.name.ilike(f"%{sub_name}%"))
        ).first()
        if not subject:
            return {"error": f"Subject '{sub_name}' not found."}
        plan = generate_structured_study_plan(db, subject.id, days, hours)
        return plan.model_dump()

    # 10. create_attendance_correction_request
    elif tool_name == "create_attendance_correction_request":
        if current_user.role != RoleEnum.STUDENT:
            return {"error": "Only students can raise attendance correction requests."}
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return {"error": "Student profile not found."}

        sub_str = tool_input.get("subject_code_or_name", "")
        subject = db.query(Subject).filter(
            (Subject.code.ilike(f"%{sub_str}%")) | (Subject.name.ilike(f"%{sub_str}%"))
        ).first()
        if not subject:
            return {"error": f"Could not match subject '{sub_str}'."}

        att_date_str = tool_input.get("attendance_date")
        try:
            att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()
        except Exception:
            return {"error": "Invalid date format. Expected YYYY-MM-DD."}

        period = int(tool_input.get("period_number", 1))
        reason = tool_input.get("reason", "")

        # Find assigned faculty from timetable or recent attendance
        timetable_slot = db.query(Timetable).filter(
            Timetable.subject_id == subject.id,
            Timetable.department_id == student.department_id,
            Timetable.semester == student.current_semester
        ).first()
        faculty_id = timetable_slot.faculty_id if timetable_slot else None

        correction = CorrectionRequest(
            student_id=student.id,
            subject_id=subject.id,
            faculty_id=faculty_id,
            attendance_date=att_date,
            period_number=period,
            current_status="absent",
            requested_status="present",
            reason=reason,
            review_status=CorrectionStatusEnum.PENDING_FACULTY_APPROVAL
        )
        db.add(correction)
        db.commit()
        db.refresh(correction)

        # Notify faculty if assigned
        if faculty_id:
            fac = db.query(Faculty).filter(Faculty.id == faculty_id).first()
            if fac:
                send_notification(
                    db,
                    user_id=fac.user_id,
                    title="New Attendance Correction Request",
                    message=f"Student {student.roll_number} requested attendance correction for {subject.code} on {att_date}.",
                    notification_type="workflow",
                    link=f"/faculty/approvals?id={correction.id}"
                )

        log_audit(db, current_user.id, "CORRECTION_REQUESTED", "correction_request", str(correction.id), {
            "subject": subject.code,
            "date": str(att_date),
            "period": period,
            "reason": reason
        })

        return {
            "ticket_id": correction.id,
            "status": "Submitted for Faculty Approval",
            "subject": subject.name,
            "attendance_date": str(att_date),
            "period": period,
            "message": f"Correction ticket #{correction.id} created successfully and routed to faculty for verification."
        }

    # 11. get_correction_request_status
    elif tool_name == "get_correction_request_status":
        req_id = tool_input.get("request_id")
        if current_user.role == RoleEnum.STUDENT:
            student = db.query(Student).filter(Student.user_id == current_user.id).first()
            query = db.query(CorrectionRequest).filter(CorrectionRequest.student_id == student.id)
        elif current_user.role == RoleEnum.FACULTY:
            faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
            query = db.query(CorrectionRequest).filter(CorrectionRequest.faculty_id == faculty.id)
        else:
            query = db.query(CorrectionRequest)

        if req_id:
            query = query.filter(CorrectionRequest.id == int(req_id))

        requests = query.order_by(CorrectionRequest.created_at.desc()).all()
        return {
            "requests": [
                {
                    "ticket_id": r.id,
                    "date": str(r.attendance_date),
                    "period": r.period_number,
                    "subject": r.subject.code if hasattr(r, 'subject') and r.subject else "N/A",
                    "reason": r.reason,
                    "review_status": r.review_status.value,
                    "faculty_notes": r.faculty_notes,
                    "created_at": str(r.created_at)
                }
                for r in requests
            ]
        }

    # 12. approve_attendance_correction (Faculty action)
    elif tool_name == "approve_attendance_correction":
        if current_user.role not in [RoleEnum.FACULTY, RoleEnum.ADMIN]:
            return {"error": "Unauthorized: Only faculty members or administrators can approve attendance corrections."}
        req_id = int(tool_input.get("request_id", 0))
        notes = tool_input.get("faculty_notes", "Approved upon verification.")

        ticket = db.query(CorrectionRequest).filter(CorrectionRequest.id == req_id).first()
        if not ticket:
            return {"error": f"Correction ticket #{req_id} not found."}

        ticket.review_status = CorrectionStatusEnum.APPROVED
        ticket.faculty_notes = notes

        # Update or insert matching attendance record
        att_rec = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == ticket.student_id,
            AttendanceRecord.subject_id == ticket.subject_id,
            AttendanceRecord.date == ticket.attendance_date,
            AttendanceRecord.period_number == ticket.period_number
        ).first()

        if att_rec:
            att_rec.status = AttendanceStatusEnum.PRESENT
            att_rec.remarks = f"Corrected by Faculty ID {current_user.id}"
        else:
            new_rec = AttendanceRecord(
                student_id=ticket.student_id,
                subject_id=ticket.subject_id,
                faculty_id=ticket.faculty_id,
                date=ticket.attendance_date,
                period_number=ticket.period_number,
                status=AttendanceStatusEnum.PRESENT,
                remarks="Created via approved correction"
            )
            db.add(new_rec)

        db.commit()

        # Notify student
        send_notification(
            db,
            user_id=ticket.student.user_id,
            title="Attendance Correction Approved",
            message=f"Your attendance request for ticket #{ticket.id} on {ticket.attendance_date} has been approved.",
            notification_type="workflow"
        )

        log_audit(db, current_user.id, "CORRECTION_APPROVED", "correction_request", str(ticket.id), {
            "student_id": ticket.student_id,
            "faculty_notes": notes
        })

        return {
            "ticket_id": ticket.id,
            "status": "APPROVED",
            "message": f"Ticket #{ticket.id} approved successfully. Student attendance updated to PRESENT."
        }

    # 13. reject_attendance_correction (Faculty action)
    elif tool_name == "reject_attendance_correction":
        if current_user.role not in [RoleEnum.FACULTY, RoleEnum.ADMIN]:
            return {"error": "Unauthorized: Only faculty members or administrators can reject attendance corrections."}
        req_id = int(tool_input.get("request_id", 0))
        notes = tool_input.get("faculty_notes", "Rejected: Absence confirmed.")

        ticket = db.query(CorrectionRequest).filter(CorrectionRequest.id == req_id).first()
        if not ticket:
            return {"error": f"Correction ticket #{req_id} not found."}

        ticket.review_status = CorrectionStatusEnum.REJECTED
        ticket.faculty_notes = notes
        db.commit()

        # Notify student
        send_notification(
            db,
            user_id=ticket.student.user_id,
            title="Attendance Correction Rejected",
            message=f"Your attendance request #{ticket.id} was rejected. Note: {notes}",
            notification_type="workflow"
        )

        log_audit(db, current_user.id, "CORRECTION_REJECTED", "correction_request", str(ticket.id), {
            "student_id": ticket.student_id,
            "faculty_notes": notes
        })

        return {
            "ticket_id": ticket.id,
            "status": "REJECTED",
            "message": f"Ticket #{ticket.id} rejected. Reason: {notes}"
        }

    else:
        return {"error": f"Unknown tool name: {tool_name}"}
