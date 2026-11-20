import pytest
from app.models.user import User
from app.ai.multilingual import detect_language, build_multilingual_system_prompt
from app.ai.ollama_client import get_ollama_tool_definitions, run_ollama_orchestration
from app.ai.bedrock_client import _generate_local_academic_response, run_bedrock_orchestration
from app.ai.translator import translate_with_aws, convert_hindi_to_hinglish


def test_detect_hinglish_queries():
    cases = [
        "meri attendance kitni hai",
        "aaj ka timetable dikhao",
        "exam results kab aayenge",
        "kya mai safe hu ya detain ho jaunga",
        "fee kitni baki hai bhai",
        "mujhe apna schedule dekhna hai",
    ]
    for q in cases:
        code, conf, name = detect_language(q)
        assert code == "hi-Latn", f"Failed for '{q}': got {code} ({name})"
        assert conf >= 0.85


def test_detect_tenglish_queries():
    cases = [
        "naku attendance undha",
        "mee timetable cheppandi",
        "repu classlu unnaya",
    ]
    for q in cases:
        code, conf, name = detect_language(q)
        assert code == "te-Latn", f"Failed for '{q}': got {code} ({name})"


def test_detect_native_scripts():
    code_te, _, _ = detect_language("నా అటెండెన్స్ ఎంత?")
    assert code_te == "te"

    code_hi, _, _ = detect_language("मेरी कुल उपस्थिति क्या है?")
    assert code_hi == "hi"


def test_detect_english_standard():
    code_en, _, _ = detect_language("What is my current attendance percentage in CSE?")
    assert code_en == "en"


def test_hinglish_system_prompt():
    prompt = build_multilingual_system_prompt("hi-Latn", "student", "Rohan Reddy")
    assert "Hinglish" in prompt
    assert "Rohan Reddy" in prompt
    assert "STUDENT" in prompt


def test_ollama_tool_definitions():
    tools = get_ollama_tool_definitions()
    assert len(tools) >= 5
    tool_names = [t["function"]["name"] for t in tools]
    assert "get_my_attendance" in tool_names
    assert "calculate_attendance_target" in tool_names
    assert "get_my_timetable" in tool_names
    assert "get_my_exam_results" in tool_names
    for t in tools:
        assert t["type"] == "function"
        assert "parameters" in t["function"]


def test_hinglish_academic_response(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    res = _generate_local_academic_response("meri attendance kitni hai", "hi-Latn", u, db_session)
    assert res["detected_language"] == "hi-Latn"
    assert "Aapka official attendance status" in res["message"] or "Aapki" in res["message"]
    assert len(res["tools_executed"]) >= 1


def test_hinglish_target_calculation(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    res = _generate_local_academic_response("meri attendance target 75% ke liye kitni classes chahiye", "hi-Latn", u, db_session)
    assert res["detected_language"] == "hi-Latn"
    assert "attendance" in res["message"].lower()
    assert len(res["tools_executed"]) >= 1


def test_aws_translate_helper():
    translated, target = translate_with_aws("Hello Student", target_lang="hi-Latn")
    assert target == "hi-Latn"
    assert translated is not None

    hinglish = convert_hindi_to_hinglish("आपकी कुल उपस्थिति अच्छी है")
    assert "Attendance" in hinglish


def test_ollama_orchestration_fallback(db_session):
    u = db_session.query(User).filter(User.email == "rohan@test.ac.in").first()
    res = run_ollama_orchestration(
        user_message="meri attendance kitni hai",
        conversation_history=[],
        current_user=u,
        db=db_session
    )
    assert res["detected_language"] == "hi-Latn"
    assert "tools_executed" in res
    assert res["llm_provider"].startswith("ollama")
