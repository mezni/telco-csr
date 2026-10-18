
# llm_service.py

import time
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)

from config import load_settings
from errors import InferenceError


TRANSIENT_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


def run_inference(
    ticket: str,
    model: str | None = None,
    system_prompt: str = "",
) -> dict[str, Any]:
    """Call the model with bounded retries for transient failures."""
    settings = load_settings()

    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.timeout_seconds,
        max_retries=0,
    )

    selected_model = model or settings.model
    last_error: Exception | None = None

    for attempt in range(1, settings.max_attempts + 1):
        started = time.perf_counter()

        try:
            response = client.responses.create(
                model=selected_model,
                instructions=system_prompt,
                input=ticket,
            )

            latency_ms = round(
                (time.perf_counter() - started) * 1000,
                2,
            )

            usage = response.usage

            return {
                "response": response.output_text,
                "model": selected_model,
                "latency_ms": latency_ms,
                "input_tokens": (
                    usage.input_tokens if usage else None
                ),
                "output_tokens": (
                    usage.output_tokens if usage else None
                ),
                "provider_attempts": attempt,
            }

        except (APIConnectionError, APITimeoutError) as exc:
            last_error = exc

        except APIStatusError as exc:
            if exc.status_code not in TRANSIENT_STATUS_CODES:
                raise InferenceError(
                    "The model provider rejected the request.",
                    retryable=False,
                    attempts=attempt,
                    status_code=exc.status_code,
                ) from exc

            last_error = exc

        if attempt < settings.max_attempts:
            time.sleep(min(2 ** (attempt - 1), 4))

    raise InferenceError(
        "The model provider failed after exhausting its retry budget.",
        retryable=True,
        attempts=settings.max_attempts,
    ) from last_error

