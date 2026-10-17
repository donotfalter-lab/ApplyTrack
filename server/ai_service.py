"""AI draft generation for application screening questions, backed by Google Gemini."""

import os

import httpx
from google import genai
from google.genai import errors, types

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_OUTPUT_TOKENS = 500
TIMEOUT_MS = 30_000

SYSTEM_INSTRUCTION = (
    "You help job seekers write concise, professional, first-person answers to "
    "application screening questions. Tailor the answer to the company, role, and "
    "job description provided. Keep it to one or two short paragraphs. Do not invent "
    "specific employers, metrics, or experience; instead use bracketed placeholders "
    "like [your experience with X] wherever the applicant should fill in personal details."
)

BLOCKED_FINISH_REASONS = {
    "SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "LANGUAGE",
}


class AIServiceError(Exception):
    """A failure the user should see, with the HTTP status the API should return."""

    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _settings():
    return {
        "api_key": os.environ.get("GEMINI_API_KEY", "").strip(),
        "model": os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL,
        "mock": os.environ.get("AI_MOCK", "").strip().lower() in ("1", "true", "yes"),
    }


def is_mock_mode():
    settings = _settings()
    return settings["mock"] or not settings["api_key"]


def _build_prompt(question, company, role, job_description):
    return (
        f"Company: {company}\n"
        f"Role: {role}\n"
        f"Job description:\n{job_description or '(not provided)'}\n\n"
        f"Screening question:\n{question}\n\n"
        "Write the applicant's answer."
    )


def _mock_response(question, company, role):
    return (
        f"I'm excited about the {role} position at {company} because it lines up closely "
        f"with [your relevant experience or skills]. In my work on [a project or role you've "
        f"had], I focused on [the kind of problem you solved], which taught me how to "
        f"[a skill that matters for this role]. I'd bring that same approach to {company}'s "
        f"team.\n\n"
        f"More broadly, I'm drawn to {company} because of [something specific you admire "
        f"about the company or its product]. I'm looking for a role where I can keep growing "
        f"in [an area you want to develop] while contributing from day one, and this "
        f"opportunity feels like a strong fit."
    )


def _thinking_config(model):
    # "Thinking" tokens count against max_output_tokens, which can leave little or
    # nothing for the actual answer. Short drafts don't need much of it.
    if model.startswith("gemini-2.5-flash"):
        return types.ThinkingConfig(thinking_budget=0)
    if model.startswith(("gemini-3", "gemini-4")):
        return types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)
    return None


def _available_models(client):
    try:
        return sorted(
            m.name.removeprefix("models/")
            for m in client.models.list()
            if "generateContent" in (m.supported_actions or [])
        )
    except Exception:
        return []


def _translate_api_error(e, client, model):
    message = (e.message or "").lower()
    status = (e.status or "").upper()

    if e.code == 429 or status == "RESOURCE_EXHAUSTED":
        return AIServiceError(
            "The AI service is rate limited or out of quota. Wait a minute and try again "
            "(free-tier keys have low per-minute and daily limits).",
            429,
        )
    if e.code in (401, 403) or "api key" in message or status in ("UNAUTHENTICATED", "PERMISSION_DENIED"):
        return AIServiceError(
            "The AI service rejected the API key. Check GEMINI_API_KEY in server/.env."
        )
    if e.code == 404 or (status == "NOT_FOUND" and "model" in message):
        available = _available_models(client)
        hint = f" Available models: {', '.join(available)}." if available else ""
        reason = f" Google says: {e.message}" if e.message else ""
        return AIServiceError(
            f"The AI model '{model}' can't be used with this API key. "
            f"Set GEMINI_MODEL in server/.env to a valid model.{reason}{hint}"
        )
    if e.code == 504 or status == "DEADLINE_EXCEEDED":
        return AIServiceError("The AI service took too long to respond. Please try again.", 504)
    if isinstance(e, errors.ServerError):
        return AIServiceError("The AI service is having problems right now. Please try again shortly.")
    return AIServiceError(f"The AI service returned an error: {e.message or e.status or e.code}")


def generate_response(question, company, role, job_description):
    """Return a drafted answer to a screening question, or raise AIServiceError."""
    settings = _settings()
    if settings["mock"] or not settings["api_key"]:
        return _mock_response(question, company, role)

    model = settings["model"]
    client = genai.Client(
        api_key=settings["api_key"],
        http_options=types.HttpOptions(timeout=TIMEOUT_MS),
    )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        thinking_config=_thinking_config(model),
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=_build_prompt(question, company, role, job_description),
            config=config,
        )
    except httpx.TimeoutException:
        raise AIServiceError("The AI service took too long to respond. Please try again.", 504)
    except httpx.TransportError:
        raise AIServiceError(
            "Couldn't connect to the AI service. Check your internet connection and try again."
        )
    except errors.APIError as e:
        raise _translate_api_error(e, client, model)

    feedback = response.prompt_feedback
    if feedback and feedback.block_reason:
        raise AIServiceError(
            "The AI service declined to answer this question. Try rephrasing it."
        )

    candidate = response.candidates[0] if response.candidates else None
    finish = candidate.finish_reason.name if candidate and candidate.finish_reason else None
    if finish in BLOCKED_FINISH_REASONS:
        raise AIServiceError(
            "The AI service declined to answer this question. Try rephrasing it."
        )

    text = (response.text or "").strip()
    if not text and finish == "MAX_TOKENS":
        raise AIServiceError(
            "The AI service used up its output limit before writing an answer. Please try again."
        )
    if not text:
        raise AIServiceError("The AI service returned an empty response. Please try again.")
    return text
