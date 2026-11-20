import re
from typing import Tuple

# Common markers for Romanized Telugu (Tenglish)
ROMANIZED_TELUGU_KEYWORDS = {
    "naku", "undha", "undhi", "undi", "cheppandi", "enti", "ledu", "epudu",
    "eppudu", "chudandi", "chaduvukovali", "telusukovali", "kavalenu", "yela", "ela",
    "unayi", "unnaayi", "classlu", "examlu", "marks", "attendance", "ivvandi"
}

# Common markers for Romanized Hindi (Hinglish)
ROMANIZED_HINDI_KEYWORDS = {
    "mera", "meri", "kitna", "kitni", "batao", "batayein", "kab", "kya", "hai", "hain",
    "nahi", "aaj", "kal", "chahiye", "dekho", "kitne"
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

    # Check Romanized Telugu
    telugu_matches = clean_words.intersection(ROMANIZED_TELUGU_KEYWORDS)
    if len(telugu_matches) >= 1:
        return "te-Latn", 0.85, "Romanized Telugu (Tenglish)"

    # Check Romanized Hindi
    hindi_matches = clean_words.intersection(ROMANIZED_HINDI_KEYWORDS)
    if len(hindi_matches) >= 1:
        return "hi-Latn", 0.85, "Romanized Hindi (Hinglish)"

    return "en", 0.99, "English"


def build_multilingual_system_prompt(language_code: str, user_role: str, user_name: str) -> str:
    """Constructs academic system instructions for Bedrock Converse API with language guidance."""
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
        lang_directive = "- The user is writing in Hindi. Respond in polite, accurate Hindi (Devanagari), retaining official academic acronyms (SGPA, CGPA, Hall Ticket)."
    elif language_code == "hi-Latn":
        lang_directive = "- The user is writing in Hinglish. Respond in friendly, clear Romanized Hindi."
    else:
        lang_directive = "- Respond in professional, concise, and helpful English with structured bullet points and tables where appropriate."

    return base_instructions + "\n" + lang_directive
