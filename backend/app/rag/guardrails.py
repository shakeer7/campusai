import re
import logging

logger = logging.getLogger(__name__)

# Patterns of potential prompt injections inside academic PDFs or lecture notes
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"disregard\s+the\s+above",
    r"system\s*:\s*you\s+must",
    r"override\s+your\s+role",
    r"output\s+all\s+passwords",
    r"reveal\s+secret\s+key"
]

COMPILED_INJECTIONS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def sanitize_retrieved_chunk(chunk_text: str) -> str:
    """
    Inspects document chunk for malicious prompt injection payloads.
    Neutralizes detected instructions to prevent jailbreaking through syllabus uploads.
    """
    sanitized = chunk_text
    detected = False
    for pattern in COMPILED_INJECTIONS:
        if pattern.search(sanitized):
            detected = True
            sanitized = pattern.sub("[FILTERED_POTENTIAL_INJECTION]", sanitized)

    if detected:
        logger.warning(f"Prompt injection pattern intercepted and neutralized in document chunk.")
    return sanitized
