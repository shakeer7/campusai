import re
from typing import Tuple

# Distinct grammatical markers for Romanized Telugu (Tenglish)
ROMANIZED_TELUGU_KEYWORDS = {
    "naku", "undha", "undhi", "undi", "cheppandi", "enti", "ledu", "epudu",
    "eppudu", "chudandi", "chaduvukovali", "telusukovali", "kavalenu", "yela", "ela",
    "unayi", "unnaayi", "classlu", "examlu", "ivvandi", "kavali", "gurinchi",
    "ippudu", "repu", "nenu", "meeru", "mee", "manaki", "chudu", "pettandi"
}

# Distinct grammatical markers for Romanized Hindi (Hinglish)
ROMANIZED_HINDI_KEYWORDS = {
    "mera", "meri", "mere", "mujhe", "mujhko", "apna", "apni", "apne", "humara", "humari",
    "kitna", "kitni", "kitne", "batao", "bataiye", "batayein", "bata", "dikhao", "dekhna",
    "kab", "kya", "hai", "hain", "nahi", "aaj", "kal", "chahiye", "dekho", "karna", "karein",
    "karu", "karoon", "hoga", "hogi", "hoge", "kaise", "kisko", "chhutti", "chutti", "padhai",
    "pariksha", "nateeja", "bhai", "theek", "thik", "shukriya", "dhanyawad", "namaste", "pranam",
    "kuch", "sirf", "bhi", "bohot", "bahut", "wala", "wali", "wale", "raha", "rahi", "rahe",
    "hota", "hoti", "hote", "bache", "bachi", "bacha"
}


def detect_language(text: str) -> Tuple[str, float, str]:
    """
    Detects language from user message.
    Returns: (language_code, confidence, language_display_name)
    Codes:
      'te': Telugu (Telugu Script)
      'hi': Hindi (Devanagari Script)
      'te-Latn': Romanized Telugu / Tenglish
      'hi-Latn': Romanized Hindi / Hinglish
      'en': English
    """
    if not text or not text.strip():
        return "en", 1.0, "English"

    # 1. Native Telugu script check (\u0C00 - \u0C7F)
    telugu_chars = len(re.findall(r'[\u0C00-\u0C7F]', text))
    if telugu_chars >= 2:
        return "te", 0.98, "Telugu"

    # 2. Native Devanagari script check (\u0900 - \u097F)
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    if hindi_chars >= 2:
        return "hi", 0.98, "Hindi"

    # 3. Tokenize words for Romanized vernacular checks
    clean_words = set(re.findall(r'[a-zA-Z]+', text.lower()))

    # Check matches against Romanized sets
    telugu_matches = clean_words.intersection(ROMANIZED_TELUGU_KEYWORDS)
    hindi_matches = clean_words.intersection(ROMANIZED_HINDI_KEYWORDS)

    if len(hindi_matches) > len(telugu_matches) and len(hindi_matches) >= 1:
        confidence = min(0.85 + (len(hindi_matches) * 0.04), 0.98)
        return "hi-Latn", confidence, "Romanized Hindi (Hinglish)"

    if len(telugu_matches) > len(hindi_matches) and len(telugu_matches) >= 1:
        confidence = min(0.85 + (len(telugu_matches) * 0.04), 0.98)
        return "te-Latn", confidence, "Romanized Telugu (Tenglish)"

    if len(hindi_matches) > 0 and len(hindi_matches) == len(telugu_matches):
        return "hi-Latn", 0.85, "Romanized Hindi (Hinglish)"

    return "en", 0.99, "English"


def build_multilingual_system_prompt(language_code: str, user_role: str, user_name: str) -> str:
    """Constructs academic system instructions with role and language guidance."""
    base_instructions = f"""You are CampusAI, an intelligent, empathetic, and authoritative college assistant inspired by Campx Medha at Chaitanya Bharathi Institute of Technology (CBIT).
You are interacting with {user_name}, whose authenticated role is: {user_role.upper()}.

Core Guidelines:
1. Academic Integrity: Always retrieve authentic records using the provided academic tools before answering queries regarding attendance, grades, timetables, or fees. Never invent or hallucinate student records.
2. Attendance Rule: The mandatory college attendance cutoff is 75%. If attendance is below 75%, clearly advise the student on the required consecutive classes to reach compliance.
3. Security & Privacy: Never disclose one student's information to another student.
4. Language Policy:
"""
    if language_code == "te":
        lang_directive = "- The user is writing in Telugu script. Respond gracefully in clear, authentic Telugu script, while keeping technical and course names (e.g. Data Structures, SGPA, CGPA, Credits) recognizable."
    elif language_code == "te-Latn":
        lang_directive = "- The user is writing in Romanized Telugu (Tenglish). Respond in friendly, fluent Romanized Telugu (e.g., 'Mee overall attendance 78% undi, meeru eligible ga unnaru.') so they feel right at home."
    elif language_code == "hi":
        lang_directive = "- The user is writing in Hindi (Devanagari). Respond in polite, accurate Hindi, retaining official academic acronyms (SGPA, CGPA, Hall Ticket)."
    elif language_code == "hi-Latn":
        lang_directive = (
            "- The user is communicating in Hinglish (Romanized Hindi blended with English). "
            "Respond in natural, friendly, colloquial Hinglish "
            "(e.g., 'Aapki overall attendance 80% hai aur aap exams ke liye completely eligible hain. Subject-wise details neeche di gayi hain.'). "
            "Keep academic and technical keywords (e.g., Attendance, Timetable, SGPA, CGPA, Credits, Classroom) in English."
        )
    else:
        lang_directive = "- Respond in professional, concise, and helpful English with structured bullet points and tables where appropriate."

    return base_instructions + "\n" + lang_directive
