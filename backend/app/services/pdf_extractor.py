import fitz


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Read PDF bytes from memory and concatenate text from every page."""
    text_parts: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        for page in document:
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def build_text_preview(raw_text: str, max_length: int = 500) -> str:
    preview = raw_text[:max_length]
    if len(raw_text) > max_length:
        preview += "…"
    return preview
