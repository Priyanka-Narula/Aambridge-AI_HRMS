import re
from decimal import Decimal
from typing import Any


EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?:\+?\d[\d\-\s]{8,}\d)")
LINKEDIN_PATTERN = re.compile(r"https?://(?:[\w]+\.)?linkedin\.com/[^\s]+", re.IGNORECASE)
EXPERIENCE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)


def parse_candidate_from_text(raw_text: str, storage_uri: str, source: str) -> dict[str, Any]:
    """Regex-based fallback parser when LLM is unavailable."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    email_match = EMAIL_PATTERN.search(raw_text)
    email = email_match.group(0).lower() if email_match else None

    name_candidate = ""
    for line in lines[:12]:
        if "@" in line or len(line.split()) < 2:
            continue
        if any(token in line.lower() for token in ("resume", "curriculum", "cv", "profile", "experience")):
            continue
        name_candidate = line
        break

    if not name_candidate and email:
        local = re.sub(r"[^a-zA-Z ]", " ", email.split("@")[0]).strip()
        name_candidate = local.title()

    name_parts = [part for part in re.split(r"\s+", name_candidate) if part]
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "Unknown"

    phone_match = PHONE_PATTERN.search(raw_text)
    linkedin_match = LINKEDIN_PATTERN.search(raw_text)
    experience_match = EXPERIENCE_PATTERN.search(raw_text)

    location_candidate = None
    for line in lines[1:10]:
        lower = line.lower()
        if "@" in line or "linkedin.com" in lower:
            continue
        if PHONE_PATTERN.search(line):
            continue
        if len(line) <= 80:
            location_candidate = line
            break

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "linkedin_url": linkedin_match.group(0).strip() if linkedin_match else None,
        "current_location": location_candidate,
        "total_experience_years": Decimal(experience_match.group(1)) if experience_match else None,
        "resume_url": storage_uri,
        "source": source,
        "candidate_status": "pending_approval",
        "skills": [],
        "education": [],
        "work_experience": [],
    }
