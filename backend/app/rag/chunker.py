import re
from typing import List, Dict, Any


def split_text_into_chunks(
    pages_data: List[Dict[str, Any]],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Chunks document page text while retaining page numbers, document hierarchy,
    and token/character boundaries.
    """
    chunks = []
    chunk_index = 0

    for page_entry in pages_data:
        page_num = page_entry["page_number"]
        text = page_entry["text"]

        # Clean excess whitespaces
        text = re.sub(r'\s+', ' ', text).strip()

        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_slice = text[start:end].strip()

            if chunk_slice:
                chunks.append({
                    "chunk_index": chunk_index,
                    "page_number": page_num,
                    "content": chunk_slice,
                    "token_count": len(chunk_slice.split())
                })
                chunk_index += 1

            if end == len(text):
                break
            start += chunk_size - chunk_overlap

    return chunks
