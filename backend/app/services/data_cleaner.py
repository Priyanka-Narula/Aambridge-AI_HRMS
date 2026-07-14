from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


def _strip_or_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _parse_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def clean_candidate_data(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize and clean parsed candidate fields before validation."""
    cleaned: dict[str, Any] = {}

    string_fields = [
        "first_name",
        "last_name",
        "email",
        "nationality",
        "languages_known",
        "phone",
        "visa_status",
        "linkedin_url",
        "current_location",
        "preferred_location",
        "current_company",
        "current_designation",
        "industry",
        "notice_period",
        "resume_url",
        "source",
        "candidate_status",
    ]
    for field in string_fields:
        if field in data:
            cleaned[field] = _strip_or_none(data.get(field))

    if cleaned.get("email"):
        cleaned["email"] = cleaned["email"].lower()

    if cleaned.get("linkedin_url") and not cleaned["linkedin_url"].startswith("http"):
        cleaned["linkedin_url"] = f"https://{cleaned['linkedin_url']}"

    cleaned["date_of_birth"] = _parse_date(data.get("date_of_birth"))
    cleaned["total_experience_years"] = _parse_decimal(data.get("total_experience_years"))
    cleaned["uae_experience_years"] = _parse_decimal(data.get("uae_experience_years"))
    cleaned["current_ctc"] = _parse_decimal(data.get("current_ctc"))
    cleaned["expected_ctc"] = _parse_decimal(data.get("expected_ctc"))

    cleaned["skills"] = []
    for skill in data.get("skills") or []:
        if not isinstance(skill, dict):
            continue
        name = _strip_or_none(skill.get("name"))
        if not name:
            continue
        cleaned["skills"].append(
            {
                "name": name,
                "years_experience": _parse_decimal(skill.get("years_experience")),
                "proficiency_level": _strip_or_none(skill.get("proficiency_level")),
            }
        )

    cleaned["education"] = []
    for edu in data.get("education") or []:
        if not isinstance(edu, dict):
            continue
        degree = _strip_or_none(edu.get("degree"))
        if not degree:
            continue
        cleaned["education"].append(
            {
                "degree": degree,
                "specialization": _strip_or_none(edu.get("specialization")),
                "institution": _strip_or_none(edu.get("institution")),
                "start_year": _parse_int(edu.get("start_year")),
                "end_year": _parse_int(edu.get("end_year")),
                "percentage": _parse_decimal(edu.get("percentage")),
            }
        )

    cleaned["work_experience"] = []
    for exp in data.get("work_experience") or []:
        if not isinstance(exp, dict):
            continue
        company = _strip_or_none(exp.get("company_name"))
        if not company:
            continue
        cleaned["work_experience"].append(
            {
                "company_name": company,
                "designation": _strip_or_none(exp.get("designation")),
                "start_date": _parse_date(exp.get("start_date")),
                "end_date": _parse_date(exp.get("end_date")),
                "currently_working": bool(exp.get("currently_working", False)),
                "job_description": _strip_or_none(exp.get("job_description")),
            }
        )

    return cleaned
