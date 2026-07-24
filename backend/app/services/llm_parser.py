import json
import logging
import re
from typing import Any

from huggingface_hub import InferenceClient

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_CV_CHARS = 14_000

# Models verified against Inference Providers chat_completion for typical HF tokens.
DEFAULT_MODEL_CANDIDATES = (
    "meta-llama/Llama-3.1-8B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "meta-llama/Meta-Llama-3-8B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
)

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


def _message_content(message: Any) -> str:
    if message is None:
        return ""
    if isinstance(message, dict):
        content = message.get("content")
    else:
        content = getattr(message, "content", None)
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(str(part.get("text") or ""))
            elif isinstance(part, str):
                parts.append(part)
            else:
                text = getattr(part, "text", None)
                if text:
                    parts.append(str(text))
        return "".join(parts).strip()
    return str(content or "").strip()


def _is_model_unavailable(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        token in text
        for token in (
            "model_not_supported",
            "not supported by any provider",
            "model is not supported",
            "is not a chat model",
            "not supported for task",
            "supported task:",
            "does not exist",
            "404",
            "not found",
            "no provider",
            "forbidden",
            "401",
            "403",
        )
    )


def _model_candidates() -> list[str]:
    primary = (settings.HF_MODEL or "").strip().strip('"')
    extras = [
        m.strip().strip('"')
        for m in (settings.HF_MODEL_FALLBACKS or "").split(",")
        if m.strip()
    ]
    ordered: list[str] = []
    for model in [primary, *extras, *DEFAULT_MODEL_CANDIDATES]:
        if model and model not in ordered:
            ordered.append(model)
    return ordered


def _create_client() -> InferenceClient:
    kwargs: dict[str, Any] = {
        "token": (settings.HF_API_TOKEN or "").strip().strip('"'),
        "timeout": settings.HF_TIMEOUT_SECONDS,
    }
    provider = (settings.HF_PROVIDER or "").strip().lower()
    # "auto" lets the hub pick a provider; passing it as a literal can mis-route.
    if provider and provider not in {"auto", "none", "default"}:
        kwargs["provider"] = provider
    return InferenceClient(**kwargs)


def _chat_complete(client: InferenceClient, model: str, system: str, user: str) -> str:
    """Call chat completion (correct task for instruct/chat models)."""
    response = client.chat_completion(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=settings.HF_MAX_TOKENS,
        temperature=0.1,
    )
    if not response.choices:
        raise RuntimeError(f"Empty choices from LLM model {model}")
    content = _message_content(response.choices[0].message)
    if not content:
        raise RuntimeError(f"Empty response from LLM model {model}")
    return content


def parse_candidate_with_llm(raw_text: str, storage_uri: str, source: str) -> dict[str, Any]:
    if not settings.HF_API_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not configured")

    client = _create_client()
    system = "You are a helpful assistant that extracts structured JSON from a CV. Only output JSON."
    user = _build_prompt(raw_text)

    last_error: Exception | None = None
    used_model: str | None = None
    content = ""

    for model in _model_candidates():
        try:
            logger.info("Calling HF chat model: %s", model)
            content = _chat_complete(client, model, system, user)
            used_model = model
            break
        except Exception as exc:
            last_error = exc
            if _is_model_unavailable(exc):
                logger.warning("HF model unavailable (%s): %s", model, exc)
                continue
            raise RuntimeError(f"HF LLM call failed for model {model}: {exc}") from exc

    if not used_model or not content:
        raise RuntimeError(
            "No supported Hugging Face chat model is available for this token. "
            f"Tried: {', '.join(_model_candidates())}. Last error: {last_error}"
        )

    try:
        parsed = _extract_json_block(content)
    except json.JSONDecodeError as exc:
        logger.error("LLM returned non-JSON content from %s: %s", used_model, content[:500])
        raise RuntimeError(f"LLM returned invalid JSON from {used_model}") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("LLM JSON payload must be an object")

    parsed["resume_url"] = storage_uri
    parsed["source"] = source
    parsed["candidate_status"] = "pending_approval"
    parsed["_llm_model"] = used_model
    return parsed
