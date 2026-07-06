import json
import logging
import re
from typing import Any

from huggingface_hub import InferenceClient

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_CV_CHARS = 14_000

EXTRACTION_SCHEMA = """{
  "first_name": "string (required)",
  "last_name": "string (required)",
  "email": "string email (required)",
  "nationality": "string or null",
  "date_of_birth": "YYYY-MM-DD or null",
  "languages_known": "comma-separated string or null",
  "phone": "string or null",
  "visa_status": "string or null",
  "linkedin_url": "string URL or null",
  "current_location": "string or null",
  "preferred_location": "string or null",
  "total_experience_years": "number or null",
  "uae_experience_years": "number or null (years worked in UAE, infer from UAE employers if possible)",
  "industry": "string or null (e.g. IT, Finance, Healthcare)",
  "current_company": "string or null",
  "current_designation": "string or null",
  "current_ctc": "number or null",
  "expected_ctc": "number or null",
  "notice_period": "string or null",
  "skills": [{"name": "string", "years_experience": "number or null", "proficiency_level": "string or null"}],
  "education": [{"degree": "string", "specialization": "string or null", "institution": "string or null", "start_year": "integer or null", "end_year": "integer or null", "percentage": "number or null"}],
  "work_experience": [{"company_name": "string", "designation": "string or null", "start_date": "YYYY-MM-DD or null", "end_date": "YYYY-MM-DD or null", "currently_working": "boolean", "job_description": "string or null"}]
}"""


def _build_prompt(cv_text: str) -> str:
    truncated = cv_text[:MAX_CV_CHARS]
    return f"""You are an expert CV parser. Extract candidate information from the CV text below.

Return ONLY valid JSON matching this schema (no markdown, no explanation):
{EXTRACTION_SCHEMA}

Rules:
- Use null for unknown fields, never invent data.
- Split full name into first_name and last_name.
- Normalize email to lowercase.
- Dates as YYYY-MM-DD. Years as integers for education.
- Include all skills, education entries, and work experiences found.
- candidate_status is not needed in output.

CV TEXT:
{truncated}
"""


def _extract_json_block(text: str) -> dict[str, Any]:
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    return json.loads(text)



def parse_candidate_with_llm(raw_text: str, storage_uri: str, source: str) -> dict[str, Any]:
    if not settings.HF_API_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not configured")

    client = InferenceClient(token=settings.HF_API_TOKEN)

    # Build chat prompt/messages
    system = "You are a helpful assistant that extracts structured JSON from a CV. Only output JSON."
    user = _build_prompt(raw_text)

    response = client.chat.completions.create(
        model=settings.HF_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=settings.HF_MAX_TOKENS,
        temperature=0.1,
    )

    # Get the assistant reply
    content = response.choices[0].message["content"]

    if not content:
        raise RuntimeError("Empty response from LLM")

    parsed = _extract_json_block(content)
    parsed["resume_url"] = storage_uri
    parsed["source"] = source
    parsed["candidate_status"] = "pending_approval"

    return parsed