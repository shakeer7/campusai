import json
import logging
import time
from typing import List, Dict, Any, Optional
import boto3
from botocore.config import Config
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.tools.registry import ACADEMIC_TOOL_SPECS, execute_tool
from app.ai.multilingual import detect_language, build_multilingual_system_prompt
from app.ai.translator import translate_with_aws

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """Initializes AWS Bedrock Runtime client with strict timeouts and retries."""
    boto_config = Config(
        retries={"max_attempts": 3, "mode": "standard"},
        connect_timeout=5,
        read_timeout=35
    )
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        aws_session_token=settings.AWS_SESSION_TOKEN or None,
        config=boto_config
    )


def run_bedrock_orchestration(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    current_user: User,
    db: Session,
    preferred_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Unified AI Orchestrator:
    1. Detects input language
    2. Assembles authenticated context & tools
    3. Calls Bedrock Converse API (or intelligent mock fallback if credentials absent)
    4. Executes requested tools securely
    5. Returns final synthesized response with tool metadata and citations
    """
    start_time = time.time()
    detected_code, confidence, display_lang = detect_language(user_message)
    active_lang = preferred_language if preferred_language else detected_code

    # Check if active LLM provider is Ollama
    if settings.LLM_PROVIDER.lower() == "ollama":
        from app.ai.ollama_client import run_ollama_orchestration
        return run_ollama_orchestration(
            user_message=user_message,
            conversation_history=conversation_history,
            current_user=current_user,
            db=db,
            preferred_language=active_lang
        )

    system_prompt = build_multilingual_system_prompt(
        language_code=active_lang,
        user_role=current_user.role.value,
        user_name=current_user.full_name
    )

    tools_executed = []
    citations = []

    # Check if AWS credentials exist and mock fallback is not forced
    has_aws_creds = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
    use_live_bedrock = has_aws_creds and not settings.AWS_BEDROCK_MOCK_FALLBACK

    if use_live_bedrock:
        try:
            client = get_bedrock_client()

            # Format conversation messages for Converse API
            formatted_messages = []
            for m in conversation_history[-6:]:
                role = "user" if m.get("role") == "user" else "assistant"
                formatted_messages.append({
                    "role": role,
                    "content": [{"text": m.get("content", "")}]
                })
            # Add latest user message
            formatted_messages.append({
                "role": "user",
                "content": [{"text": user_message}]
            })

            # First Converse call
            response = client.converse(
                modelId=settings.BEDROCK_MODEL_ID,
                messages=formatted_messages,
                system=[{"text": system_prompt}],
                toolConfig={"tools": ACADEMIC_TOOL_SPECS},
                inferenceConfig={
                    "maxTokens": settings.BEDROCK_MAX_TOKENS,
                    "temperature": settings.BEDROCK_TEMPERATURE
                }
            )

            stop_reason = response.get("stopReason")
            output_msg = response["output"]["message"]

            # Handle Tool Calls
            if stop_reason == "tool_use":
                assistant_contents = output_msg.get("content", [])
                tool_results_content = []

                for part in assistant_contents:
                    if "toolUse" in part:
                        tool_use = part["toolUse"]
                        tool_name = tool_use["name"]
                        tool_input = tool_use.get("input", {})
                        use_id = tool_use["toolUseId"]

                        t0 = time.time()
                        tool_res = execute_tool(tool_name, tool_input, current_user, db)
                        elapsed_ms = round((time.time() - t0) * 1000, 2)

                        tools_executed.append({
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                            "tool_output": tool_res,
                            "status": "success" if "error" not in tool_res else "failed",
                            "execution_time_ms": elapsed_ms
                        })

                        tool_results_content.append({
                            "toolResult": {
                                "toolUseId": use_id,
                                "content": [{"json": tool_res}]
                            }
                        })

                # Append assistant message with toolUse and user message with toolResult
                formatted_messages.append(output_msg)
                formatted_messages.append({
                    "role": "user",
                    "content": tool_results_content
                })

                # Second Converse call to generate final answer
                final_resp = client.converse(
                    modelId=settings.BEDROCK_MODEL_ID,
                    messages=formatted_messages,
                    system=[{"text": system_prompt}],
                    inferenceConfig={
                        "maxTokens": settings.BEDROCK_MAX_TOKENS,
                        "temperature": settings.BEDROCK_TEMPERATURE
                    }
                )
                final_text = ""
                for c in final_resp["output"]["message"].get("content", []):
                    if "text" in c:
                        final_text += c["text"]

                return {
                    "message": final_text,
                    "detected_language": active_lang,
                    "language_confidence": confidence,
                    "tools_executed": tools_executed,
                    "citations": citations
                }
            else:
                # Direct response without tool call
                text_content = ""
                for c in output_msg.get("content", []):
                    if "text" in c:
                        text_content += c["text"]
                return {
                    "message": text_content,
                    "detected_language": active_lang,
                    "language_confidence": confidence,
                    "tools_executed": tools_executed,
                    "citations": citations
                }

        except Exception as e:
            logger.warning(f"AWS Bedrock converse call failed: {e}. Switching to deterministic academic AI responder.")

    # High-Fidelity Local Academic AI Engine (Deterministic Fallback)
    return _generate_local_academic_response(user_message, active_lang, current_user, db)


def _generate_local_academic_response(
    query: str,
    lang: str,
    user: User,
    db: Session
) -> Dict[str, Any]:
    """
    Intelligent local intent dispatcher for testing, CI/CD, and offline demonstration.
    Executes actual tools against PostgreSQL / SQLite database and formats responses.
    """
    q = query.lower()
    tools_executed = []
    citations = []

    # 1. Attendance Query
    if any(k in q for k in ["attendance", "present", "absent", "percentage", "haaziri"]):
        t_start = time.time()
        # Check if target calculation is requested
        if any(k in q for k in ["target", "reach", "need", "consecutive", "miss", "75%"]):
            tool_res = execute_tool("calculate_attendance_target", {"target_percentage": 75.0}, user, db)
            tools_executed.append({
                "tool_name": "calculate_attendance_target",
                "tool_input": {"target_percentage": 75.0},
                "tool_output": tool_res,
                "status": "success",
                "execution_time_ms": round((time.time() - t_start) * 1000, 2)
            })

            cur_pct = tool_res.get("current_percentage", 0.0)
            needed = tool_res.get("classes_needed", 0)
            can_miss = tool_res.get("can_miss_classes", 0)

            if lang == "te":
                resp_text = f"మీ ప్రస్తుత అటెండెన్స్ {cur_pct}%. 75% అర్హత సాధించడానికి మీరు తదుపరి {needed} క్లాసులకు వరుసగా హాజరు కావాలి." if needed > 0 else f"అద్భుతం! మీ అటెండెన్స్ {cur_pct}%. మీరు ఇప్పటికీ {can_miss} క్లాసులు మిస్ అయినా 75% పైన ఉంటారు."
            elif lang == "te-Latn":
                resp_text = f"Mee current attendance {cur_pct}% undi. 75% target reach avvadaniki meeru inka {needed} consecutive classes attend avvali." if needed > 0 else f"Super! Mee attendance {cur_pct}% undi. Meeru {can_miss} classes miss aina safe ga 75% paine untaru."
            elif lang == "hi":
                resp_text = f"आपकी वर्तमान उपस्थिति {cur_pct}% है। 75% का लक्ष्य पाने के लिए आपको अगली {needed} कक्षाओं में उपस्थित होना होगा।"
            elif lang == "hi-Latn":
                resp_text = f"Aapki current attendance {cur_pct}% hai. 75% target reach karne ke liye aapko aage aane wali {needed} consecutive classes attend karni padengi." if needed > 0 else f"Badhiya! Aapki attendance {cur_pct}% hai. Aap abhi bhi {can_miss} classes miss kar sakte hain aur aapka attendance 75% ke upar hi safe rahega."
            else:
                resp_text = f"Your current attendance is **{cur_pct}%**. {tool_res.get('message', '')}"

        else:
            tool_res = execute_tool("get_my_attendance", {}, user, db)
            tools_executed.append({
                "tool_name": "get_my_attendance",
                "tool_input": {},
                "tool_output": tool_res,
                "status": "success",
                "execution_time_ms": round((time.time() - t_start) * 1000, 2)
            })
            overall_pct = tool_res.get("overall_percentage", 0.0)
            eligible = tool_res.get("overall_eligible", True)
            elig_str = "Eligible for Exams" if eligible else "Condonation Required (Below 75%)"

            if lang == "te":
                resp_text = f"మీ మొత్తం అటెండెన్స్ **{overall_pct}%** ({elig_str}). సబ్జెక్ట్ వారీ వివరాలు:\n"
            elif lang == "te-Latn":
                resp_text = f"Mee overall attendance **{overall_pct}%** undi ({elig_str}). Subject-wise details kinda unnayi:\n"
            elif lang == "hi":
                resp_text = f"आपकी कुल उपस्थिति **{overall_pct}%** है ({elig_str})। विषयवार विवरण निम्नलिखित है:\n"
            elif lang == "hi-Latn":
                resp_text = f"Aapka official attendance status yeh raha:\n- **Overall Attendance**: **{overall_pct}%** ({elig_str})\n\n### Subject-wise Details:\n"
            else:
                resp_text = f"Here is your official attendance status:\n- **Overall Attendance**: **{overall_pct}%** ({elig_str})\n\n### Subject-wise Breakdown:\n"

            for s in tool_res.get("subjects", []):
                resp_text += f"- **{s.get('subject_name')}** ({s.get('subject_code')}): {s.get('attended_classes')}/{s.get('total_classes')} classes ({s.get('percentage')}%) - Status: `{s.get('status_indicator')}`\n"

        return {
            "message": resp_text,
            "detected_language": lang,
            "language_confidence": 0.95,
            "tools_executed": tools_executed,
            "citations": citations
        }

    # 2. Timetable Query
    elif any(k in q for k in ["timetable", "schedule", "class", "today", "room", "timing"]):
        t_start = time.time()
        tool_res = execute_tool("get_my_timetable", {}, user, db)
        tools_executed.append({
            "tool_name": "get_my_timetable",
            "tool_input": {},
            "tool_output": tool_res,
            "status": "success",
            "execution_time_ms": round((time.time() - t_start) * 1000, 2)
        })
        entries = tool_res.get("timetable", [])
        if lang in ["te", "te-Latn"]:
            resp_text = "Mee timetable schedule kinda ichina vidhamga undi:\n\n"
        elif lang == "hi":
            resp_text = "आपकी कक्षा समय-सारिणी निम्नलिखित है:\n\n"
        elif lang == "hi-Latn":
            resp_text = "Yeh raha aapka timetable schedule:\n\n"
        else:
            resp_text = "Here is your academic timetable schedule:\n\n"

        resp_text += "| Day | Time | Subject | Faculty | Room |\n|---|---|---|---|---|\n"
        for e in entries[:6]:
            resp_text += f"| {e.get('day_of_week')} | {e.get('start_time')}-{e.get('end_time')} | {e.get('subject_name')} | {e.get('faculty_name')} | {e.get('room_number')} |\n"

        return {
            "message": resp_text,
            "detected_language": lang,
            "language_confidence": 0.95,
            "tools_executed": tools_executed,
            "citations": citations
        }

    # 3. Exam Results & CGPA
    elif any(k in q for k in ["marks", "result", "sgpa", "cgpa", "grade", "gpa"]):
        t_start = time.time()
        tool_res = execute_tool("get_my_exam_results", {}, user, db)
        tools_executed.append({
            "tool_name": "get_my_exam_results",
            "tool_input": {},
            "tool_output": tool_res,
            "status": "success",
            "execution_time_ms": round((time.time() - t_start) * 1000, 2)
        })
        cgpa = tool_res.get("cgpa", 0.0)
        roll = tool_res.get("student_roll", "")
        if lang == "hi-Latn":
            resp_text = f"Roll No: **{roll}** ke Exam Results aur Academic Performance:\n- **Cumulative CGPA**: **{cgpa} / 10.0** (Great Job!)\n\n"
        elif lang == "hi":
            resp_text = f"अनुक्रमांक: **{roll}** के परीक्षा परिणाम और अकादमिक प्रदर्शन:\n- **संचयी CGPA**: **{cgpa} / 10.0**\n\n"
        elif lang in ["te", "te-Latn"]:
            resp_text = f"Roll No: **{roll}** Exam Results mariyu Academic Performance:\n- **Cumulative CGPA**: **{cgpa} / 10.0**\n\n"
        else:
            resp_text = f"Academic Performance for Roll No: **{roll}**\n- **Cumulative CGPA**: **{cgpa} / 10.0**\n\n"

        for sem in tool_res.get("semesters", []):
            resp_text += f"**Semester {sem.get('semester')}** — SGPA: **{sem.get('sgpa')}** (Credits: {sem.get('total_credits')})\n"
            for r in sem.get("results", []):
                resp_text += f"  - {r.get('subject_name')}: Grade `{r.get('grade')}` ({r.get('total_marks')} marks)\n"

        return {
            "message": resp_text,
            "detected_language": lang,
            "language_confidence": 0.95,
            "tools_executed": tools_executed,
            "citations": citations
        }

    # 4. Fees
    elif any(k in q for k in ["fee", "dues", "challan", "payment", "tuition"]):
        t_start = time.time()
        tool_res = execute_tool("get_pending_fees", {}, user, db)
        tools_executed.append({
            "tool_name": "get_pending_fees",
            "tool_input": {},
            "tool_output": tool_res,
            "status": "success",
            "execution_time_ms": round((time.time() - t_start) * 1000, 2)
        })
        due = tool_res.get("total_pending_due", 0.0)
        if lang == "hi-Latn":
            resp_text = f"ERP Fee Account Overview:\n- **Total Pending Balance**: **₹{due:,.2f}**\n\n"
        elif lang == "hi":
            resp_text = f"ईआरपी शुल्क खाता विवरण:\n- **कुल बकाया राशि**: **₹{due:,.2f}**\n\n"
        elif lang in ["te", "te-Latn"]:
            resp_text = f"ERP Fee Account Details:\n- **Total Pending Balance**: **₹{due:,.2f}**\n\n"
        else:
            resp_text = f"ERP Fee Account Overview:\n- **Total Pending Balance**: **₹{due:,.2f}**\n\n"

        for f in tool_res.get("records", []):
            resp_text += f"- **{f.get('fee_type')}**: Total ₹{f.get('total_amount'):,.2f} | Paid ₹{f.get('paid_amount'):,.2f} | Due: ₹{f.get('due_amount'):,.2f} (Status: `{f.get('status')}`)\n"

        return {
            "message": resp_text,
            "detected_language": lang,
            "language_confidence": 0.95,
            "tools_executed": tools_executed,
            "citations": citations
        }

    # 5. RAG Document Search / Syllabus / Policy
    elif any(k in q for k in ["syllabus", "unit", "regulation", "rule", "policy", "exam schedule", "notes"]):
        t_start = time.time()
        tool_res = execute_tool("search_academic_documents", {"query": query}, user, db)
        tools_executed.append({
            "tool_name": "search_academic_documents",
            "tool_input": {"query": query},
            "tool_output": tool_res,
            "status": "success",
            "execution_time_ms": round((time.time() - t_start) * 1000, 2)
        })
        results = tool_res.get("results", [])
        if results:
            if lang == "hi-Latn":
                resp_text = "Official CBIT academic documents ke anusaar, yeh details hain:\n\n"
            elif lang == "hi":
                resp_text = "आधिकारिक सीबीईटी शैक्षणिक दस्तावेजों के अनुसार, विवरण निम्नलिखित हैं:\n\n"
            elif lang in ["te", "te-Latn"]:
                resp_text = "Official CBIT academic documents prakaaram, details kinda unnaayi:\n\n"
            else:
                resp_text = "Based on official CBIT academic documents, here are the retrieved details:\n\n"

            for item in results:
                resp_text += f"> {item.get('content')}\n\n"
                citations.append({
                    "document_title": item.get("document_title"),
                    "page_number": item.get("page_number"),
                    "snippet": item.get("content")[:120] + "...",
                    "similarity_score": item.get("score")
                })
            resp_text += "\n*Citations provided below from verified college regulations.*"
        else:
            if lang == "hi-Latn":
                resp_text = f"Maine academic repository me '{query}' search kiya, par koi matching syllabus topic nahi mila. Kripya syllabus PDF upload karein."
            else:
                resp_text = f"I searched the academic repository for '{query}', but found no matching syllabus sections. Please ensure the syllabus PDF has been uploaded to the repository."

        return {
            "message": resp_text,
            "detected_language": lang,
            "language_confidence": 0.95,
            "tools_executed": tools_executed,
            "citations": citations
        }

    # Default Academic Greeting & Help
    else:
        if lang == "te":
            msg = f"నమస్కారం {user.full_name}! నేను మీ CampusAI అసిస్టెంట్‌ని. మీ అటెండెన్స్, టైమ్‌టేబుల్, ఎగ్జామ్ ఫలితాలు లేదా ఫీజు వివరాల గురించి నన్ను అడగవచ్చు."
        elif lang == "te-Latn":
            msg = f"Namaskaram {user.full_name}! Nenu mee CampusAI assistant ni. Mee attendance, timetable, results leda syllabus gurinchi emaina adagavachu."
        elif lang == "hi":
            msg = f"नमस्ते {user.full_name}! मैं आपका CampusAI सहायक हूँ। आप अपनी उपस्थिति, समय सारिणी, परीक्षा परिणाम या शुल्क के बारे में पूछ सकते हैं।"
        elif lang == "hi-Latn":
            msg = f"Namaste {user.full_name}! Main CampusAI hoon, aapka college assistant. Main aapki attendance calculation, timetable, semester results, fees status aur syllabus lookup me madad kar sakta hoon. Aaj aapko kya check karna hai?"
        else:
            msg = f"Hello {user.full_name}! I am CampusAI, your academic assistant. I can help you with:\n- Attendance summary and 75% target calculator\n- Daily and weekly timetable schedule\n- Semester grades, SGPA, and CGPA\n- Syllabus breakdown and AI study plans\n- Raising attendance correction requests\n- College fee balance check"

        return {
            "message": msg,
            "detected_language": lang,
            "language_confidence": 0.98,
            "tools_executed": [],
            "citations": []
        }
