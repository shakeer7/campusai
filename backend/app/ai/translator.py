import logging
import re
from typing import Tuple, Optional
import boto3
from botocore.config import Config
from app.core.config import settings

logger = logging.getLogger(__name__)

# ISO 639-1 language code mapping for AWS Translate
AWS_TRANSLATE_CODE_MAP = {
    "en": "en",
    "hi": "hi",
    "te": "te",
    "hi-Latn": "hi",    # Base Indic translation via AWS Translate
    "te-Latn": "te",    # Base Indic translation via AWS Translate
}

# Common transliteration mappings for Hinglish
DEVANAGARI_TO_HINGLISH_RULES = [
    ("नमस्ते", "Namaste"),
    ("उपस्थिति", "Attendance"),
    ("कक्षा", "Class"),
    ("कक्षाएं", "Classes"),
    ("कक्षाओं", "Classes"),
    ("समय सारिणी", "Timetable"),
    ("समय-सारिणी", "Timetable"),
    ("परीक्षा", "Exam"),
    ("परिणाम", "Result"),
    ("अंक", "Marks"),
    ("शुल्क", "Fees"),
    ("छात्र", "Student"),
    ("शिक्षक", "Faculty"),
    ("विभाग", "Department"),
    ("है", "hai"),
    ("हैं", "hain"),
    ("नहीं", "nahi"),
    ("आपकी", "Aapki"),
    ("आपका", "Aapka"),
    ("कुल", "Overall"),
    ("विवरण", "Details"),
    ("निम्नलिखित", "neeche diye gaye"),
]


def get_translate_client():
    """Initializes AWS Translate client with timeouts and retries."""
    boto_config = Config(
        retries={"max_attempts": 3, "mode": "standard"},
        connect_timeout=4,
        read_timeout=15
    )
    return boto3.client(
        "translate",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        aws_session_token=settings.AWS_SESSION_TOKEN or None,
        config=boto_config
    )


def translate_with_aws(
    text: str,
    target_lang: str,
    source_lang: str = "auto"
) -> Tuple[str, str]:
    """
    Translates text using Amazon Translate neural translation service.
    Returns: (translated_text, target_language_code)
    """
    if not text or not text.strip():
        return text, target_lang

    aws_target = AWS_TRANSLATE_CODE_MAP.get(target_lang, target_lang)
    aws_source = AWS_TRANSLATE_CODE_MAP.get(source_lang, source_lang) if source_lang != "auto" else "auto"

    # Avoid redundant translation if source and target are the same
    if aws_source != "auto" and aws_source == aws_target:
        return text, target_lang

    has_creds = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
    can_call_aws = has_creds and not settings.AWS_BEDROCK_MOCK_FALLBACK

    if can_call_aws:
        try:
            client = get_translate_client()
            logger.info(f"Calling AWS Translate: '{aws_source}' -> '{aws_target}' (chars={len(text)})")
            response = client.translate_text(
                Text=text,
                SourceLanguageCode=aws_source,
                TargetLanguageCode=aws_target
            )
            result_text = response.get("TranslatedText", text)

            # If user wanted Hinglish and target was translated to Hindi, adapt to Romanized Hinglish
            if target_lang == "hi-Latn":
                result_text = convert_hindi_to_hinglish(result_text)

            return result_text, target_lang
        except Exception as e:
            logger.warning(f"AWS Translate API call failed: {e}. Falling back to internal translation.")

    # Graceful Fallback Translation
    fallback_text = _fallback_translate(text, target_lang)
    return fallback_text, target_lang


def convert_hindi_to_hinglish(devanagari_text: str) -> str:
    """Helper to convert key Devanagari words to natural Hinglish for comfortable reading."""
    res = devanagari_text
    for dev, hing in DEVANAGARI_TO_HINGLISH_RULES:
        res = res.replace(dev, hing)
    return res


def _fallback_translate(text: str, target_lang: str) -> str:
    """Deterministic fallback for local, CI/CD, and offline testing environments."""
    if target_lang == "hi-Latn":
        return convert_hindi_to_hinglish(text)
    return text
