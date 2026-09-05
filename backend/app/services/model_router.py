from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
import asyncio
import json
import re

import httpx

from app.config import settings
from app.services.quota_manager import quota_manager


@dataclass
class Route:
    task: str
    tier: str
    provider: str
    model: str
    reason: str


@dataclass
class AIResult:
    provider: str
    model: str
    task: str
    tier: str
    text: str
    structured: dict
    latency_ms: float
    fallback_used: bool
    live: bool
    error: str | None = None


PROVIDERS = {
    "gemini": {
        "key": "gemini_api_key",
        "model": lambda: settings.gemini_model,
    },
    "openai": {
        "key": "openai_api_key",
        "model": lambda: settings.openai_model,
    },
    "anthropic": {
        "key": "anthropic_api_key",
        "model": lambda: settings.anthropic_model,
    },
}


def route(
    task: str,
    complexity: int,
    uncertainty: float,
    high_value: bool = False,
) -> Route:

    score = (
        max(0, min(150, complexity))
        + int(max(0, min(1, uncertainty)) * 30)
        + (20 if high_value else 0)
    )

    if task == "communication":
        tier = "fast" if score <= 60 else "standard"
    elif score <= 35:
        tier = "fast"
    elif score <= 70:
        tier = "standard"
    else:
        tier = "premium"

    if tier == "fast":
        provider = "gemini"
        reason = "Low-cost, low-latency path"
    elif tier == "standard":
        provider = "openai"
        reason = "Balanced reasoning path"
    else:
        provider = "anthropic"
        reason = "High-complexity or high-value path"

    return Route(
        task=task,
        tier=tier,
        provider=provider,
        model=PROVIDERS[provider]["model"](),
        reason=reason,
    )


def _extract_json(text: str) -> dict:
    text = text.strip()

    try:
        parsed = json.loads(text)

        if isinstance(parsed, dict):
            return parsed

    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.S)

    if match:
        try:
            parsed = json.loads(match.group(0))

            if isinstance(parsed, dict):
                return parsed

        except Exception:
            pass

    return {
        "raw": text,
        "parse_error": True,
    }


def _prompt(task: str, case: dict) -> str:

    base = json.dumps(
        case,
        ensure_ascii=False,
    )

    if task == "diagnosis":
        return f"""
You are the Investigator Agent in a revenue recovery system.

Analyze the revenue recovery case below.

Your job is to identify why the revenue is at risk and provide useful
context for the downstream Strategy Agent.

Do not execute any action.
Do not contact the customer.
Do not invent facts.
Use only information contained in the case.

Return ONLY valid JSON.

Required schema:

{{
  "root_cause": "string",
  "confidence": 0.0,
  "customer_context": "string",
  "recovery_context": "string"
}}

Rules:

- confidence must be between 0 and 1
- root_cause must be based on the supplied event and failure information
- customer_context should summarize relevant customer behavior
- recovery_context should summarize useful recovery signals
- do not recommend an action yet

Case:

{base}
""".strip()

    if task == "strategy":
        return f"""
You are the Strategy Agent in a revenue recovery system.

Choose the safest and most economically sensible recovery strategy
for the supplied case.

Do not execute anything.
Do not contact the customer.
Do not invent customer information.
Do not invent discounts.

Available actions:

PAYMENT_LINK
RETRY
ALTERNATIVE_METHOD
REMINDER
WAIT
INCENTIVE
STOP

Return ONLY valid JSON.

Required schema:

{{
  "action": "PAYMENT_LINK | RETRY | ALTERNATIVE_METHOD | REMINDER | WAIT | INCENTIVE | STOP",
  "rationale": "string",
  "confidence": 0.0,
  "risks": ["string"]
}}

Rules:

- confidence must be between 0 and 1
- action must be exactly one of the allowed actions
- STOP must be selected when recovery should not be attempted
- do not execute the action
- do not create a payment link
- do not promise a successful payment

Case:

{base}
""".strip()

    return f"""
You are the Communication Agent in a revenue recovery system.

Create a concise and professional customer recovery message for the
ALREADY-APPROVED action contained in this case.

Do not choose a new action.
Do not invent discounts.
Do not invent promises.
Do not claim that payment succeeded.
Do not execute any action.

Return ONLY valid JSON.

Required schema:

{{
  "message": "string",
  "tone": "string"
}}

Case:

{base}
""".strip()


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).upper()
    return "RESOURCE_EXHAUSTED" in text or "429" in text or "QUOTA" in text


def _should_retry(exc: Exception) -> bool:

    if isinstance(exc, httpx.TimeoutException):
        return True

    if isinstance(exc, httpx.NetworkError):
        return True

    if isinstance(exc, httpx.HTTPStatusError):

        status_code = exc.response.status_code

        if status_code == 429:
            return True

        if 500 <= status_code <= 599:
            return True

    return False


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: dict | None = None,
    params: dict | None = None,
    json_payload: dict | None = None,
) -> httpx.Response:

    retries = max(
        0,
        settings.ai_max_retries,
    )

    last_exception: Exception | None = None

    for attempt in range(retries + 1):

        try:

            response = await client.post(
                url,
                headers=headers,
                params=params,
                json=json_payload,
            )

            response.raise_for_status()

            return response

        except Exception as exc:

            last_exception = exc

            if attempt >= retries:
                raise

            if not _should_retry(exc):
                raise

            delay = min(
                2 ** attempt,
                8,
            )

            await asyncio.sleep(delay)

    if last_exception:
        raise last_exception

    raise RuntimeError("Request failed without an exception")


async def _gemini(prompt: str) -> str:

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not configured"
        )

    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=settings.gemini_api_key
    )

    def generate():

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=700,
                response_mime_type="application/json",
            ),
        )

        text = response.text

        if not text or not text.strip():
            raise RuntimeError(
                "Gemini returned empty content"
            )

        return text

    last_error: Exception | None = None

    for attempt in range(
        settings.ai_max_retries + 1
    ):

        try:

            return await asyncio.to_thread(
                generate
            )

        except Exception as exc:

            last_error = exc

            if _is_quota_error(exc) or attempt >= settings.ai_max_retries:
                raise

            await asyncio.sleep(
                min(2 ** attempt, 8)
            )

    if last_error:
        raise last_error

    raise RuntimeError(
        "Gemini request failed"
    )


async def _openai(prompt: str) -> str:

    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not configured"
        )

    headers = {
        "Authorization": (
            f"Bearer {settings.openai_api_key}"
        ),
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.openai_model,
        "input": prompt,
        "max_output_tokens": 700,
    }

    timeout = httpx.Timeout(
        connect=15.0,
        read=settings.ai_timeout_seconds,
        write=15.0,
        pool=15.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout
    ) as client:

        response = await _post_with_retry(
            client,
            "https://api.openai.com/v1/responses",
            headers=headers,
            json_payload=payload,
        )

        data = response.json()

    if data.get("output_text"):
        return data["output_text"]

    chunks = []

    for item in data.get(
        "output",
        [],
    ):

        for content in item.get(
            "content",
            [],
        ):

            if content.get("type") in (
                "output_text",
                "text",
            ):
                chunks.append(
                    content.get(
                        "text",
                        "",
                    )
                )

    text = "".join(chunks)

    if not text.strip():
        raise RuntimeError(
            "OpenAI returned empty content"
        )

    return text


async def _anthropic(prompt: str) -> str:

    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not configured"
        )

    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 700,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    timeout = httpx.Timeout(
        connect=15.0,
        read=settings.ai_timeout_seconds,
        write=15.0,
        pool=15.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout
    ) as client:

        response = await _post_with_retry(
            client,
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json_payload=payload,
        )

        data = response.json()

    text = "".join(
        item.get(
            "text",
            "",
        )
        for item in data.get(
            "content",
            [],
        )
        if item.get("type") == "text"
    )

    if not text.strip():
        raise RuntimeError(
            "Anthropic returned empty content"
        )

    return text


CALLERS = {
    "gemini": _gemini,
    "openai": _openai,
    "anthropic": _anthropic,
}


def available(provider: str) -> bool:

    return bool(
        getattr(
            settings,
            PROVIDERS[provider]["key"],
        )
    )


def _fallback_chain(
    primary: str,
) -> list[str]:

    order = [
        primary,
        "gemini",
        "openai",
        "anthropic",
    ]

    return list(
        dict.fromkeys(order)
    )


async def run_ai(
    task: str,
    case: dict,
    complexity: int,
    uncertainty: float,
    high_value: bool = False,
    force_provider: str | None = None,
) -> AIResult:

    selected = (
        force_provider
        if force_provider in PROVIDERS
        else route(
            task,
            complexity,
            uncertainty,
            high_value,
        ).provider
    )

    selected_route = route(
        task,
        complexity,
        uncertainty,
        high_value,
    )

    prompt = _prompt(
        task,
        case,
    )

    errors: list[str] = []

    for provider in _fallback_chain(
        selected
    ):

        if not available(provider):

            error = (
                f"{provider}: "
                "API key not configured"
            )

            errors.append(error)

            continue

        if not quota_manager.can_use(
            provider
        ):

            error = (
                f"{provider}: "
                "soft request limit reached"
            )

            errors.append(error)

            continue

        start = perf_counter()

        try:

            text = await CALLERS[
                provider
            ](prompt)

            tokens = max(
                1,
                len(prompt + text) // 4,
            )

            is_fallback = (
                provider != selected
            )

            quota_manager.record(
                provider,
                success=True,
                tokens=tokens,
                fallback=is_fallback,
            )

            return AIResult(
                provider=provider,
                model=PROVIDERS[
                    provider
                ]["model"](),
                task=task,
                tier=selected_route.tier,
                text=text,
                structured=_extract_json(
                    text
                ),
                latency_ms=(
                    perf_counter() - start
                ) * 1000,
                fallback_used=is_fallback,
                live=True,
                error=None,
            )

        except Exception as exc:

            error = (
                f"{provider}: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            errors.append(error)

            quota_manager.record(
                provider,
                success=False,
                fallback=(
                    provider != selected
                ),
                error=error,
            )

    return AIResult(
        provider=selected,
        model=PROVIDERS[
            selected
        ]["model"](),
        task=task,
        tier=selected_route.tier,
        text="DRY_RUN: no provider available",
        structured={
            "status": "dry_run",
            "message": (
                "No configured provider "
                "completed the request"
            ),
            "errors": errors,
        },
        latency_ms=0.0,
        fallback_used=len(errors) > 1,
        live=False,
        error=" | ".join(errors),
    )


def router_status() -> dict:

    return {
        provider: {
            "configured": available(
                provider
            ),
            "model": PROVIDERS[
                provider
            ]["model"](),
        }
        for provider in PROVIDERS
    }