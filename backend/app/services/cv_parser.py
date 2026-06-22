import re
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict


EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(
    r"(\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}"
)
LINKEDIN_REGEX = re.compile(
    r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+"
)


def extract_email(text: str) -> Optional[str]:
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = PHONE_REGEX.search(text)
    return match.group(0) if match else None


def extract_linkedin(text: str) -> Optional[str]:
    match = LINKEDIN_REGEX.search(text)
    return match.group(0) if match else None


def extract_name(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Heuristic:
    - First non-empty line
    - Capitalized words
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return None, None

    parts = lines[0].split()
    if len(parts) >= 2:
        return parts[0], parts[-1]

    return None, None


def extract_total_experience(text: str) -> Optional[Decimal]:
    """
    Matches:
    - "5 years experience"
    - "3.5 yrs"
    """
    match = re.search(r"(\d+(\.\d+)?)\s*(years|yrs)", text, re.I)
    if match:
        return Decimal(match.group(1))
    return None


def extract_location(text: str) -> Optional[str]:
    """
    Simple heuristic — expand later
    """
    match = re.search(r"Location[:\-]\s*(.+)", text, re.I)
    return match.group(1).strip() if match else None


def extract_languages(text: str) -> Optional[str]:
    match = re.search(r"Languages?[:\-]\s*(.+)", text, re.I)
    return match.group(1).strip() if match else None


def parse_candidate_from_text(
    text: str,
    *,
    source: str = "cv_upload",
    created_by: str = "system"
) -> Dict:
    first_name, last_name = extract_name(text)

    payload = {
        "first_name": first_name or "Unknown",
        "last_name": last_name or "Unknown",
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin_url": extract_linkedin(text),
        "current_location": extract_location(text),
        "languages_known": extract_languages(text),
        "total_experience_years": extract_total_experience(text),
        "source": source,
        "created_by": created_by,
    }

    # Remove None values (important for Pydantic)
    return {k: v for k, v in payload.items() if v is not None}