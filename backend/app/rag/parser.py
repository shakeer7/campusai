import io
import logging
from typing import List, Dict, Any
import pypdf

logger = logging.getLogger(__name__)


def extract_text_by_pages(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Extracts text per page from PDF bytes.
    Preserves page number (1-indexed) and handles scanned/empty pages gracefully.
    """
    pages_data = []
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages_data.append({
                    "page_number": page_num,
                    "text": text
                })
            else:
                logger.warning(f"Page {page_num} contains no extractable text (might be scanned image).")
    except Exception as e:
        logger.error(f"Failed to parse PDF bytes: {e}")
        raise ValueError(f"Error extracting PDF text: {e}")

    return pages_data
