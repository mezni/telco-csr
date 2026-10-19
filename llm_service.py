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
from execution_budget import BudgetExceededError, ExecutionBudget

TRANSIENT_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


def run_inference(
    ticket: str,
    model: str | None = None,
    system_prompt: str = "",
    budget: ExecutionBudget | None = None,
) -> dict[str, Any]:
    """Run inference within a shared request and time budget."""
    settings = load_settings()

    if budget is None:
        budget = ExecutionBudget(
            max_requests=settings.max_attempts,
            deadline_seconds=settings.deadline_seconds,
        )

    selected_model = model or settings.model
    last_error: Exception | None = None

    while True:
        try:
            remaining_time = budget.reserve_request()
        except BudgetExceededError as exc:
            raise InferenceError(
                str(exc),
                retryable=True,
                attempts=budget.requests_used,
            ) from exc

        request_timeout = min(
            settings.timeout_seconds,
            remaining_time,
        )

        client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=request_timeout,
            max_retries=0,
        )

        try:
            started = time.monotonic()

            response = client.responses.create(
                model=selected_model,
                instructions=system_prompt,
                input=ticket,
            )

            latency_ms = round(
                (time.monotonic() - started) * 1000,
                2,
            )
            usage = response.usage

            return {
                "response": response.output_text,
                "model": selected_model,
                "latency_ms": latency_ms,
                "input_tokens": (usage.input_tokens if usage else None),
                "output_tokens": (usage.output_tokens if usage else None),
                "provider_attempts": budget.requests_used,
            }

        except (APIConnectionError, APITimeoutError) as exc:
            last_error = exc

        except APIStatusError as exc:
            if exc.status_code not in TRANSIENT_STATUS_CODES:
                raise InferenceError(
                    "The model provider rejected the request.",
                    retryable=False,
                    attempts=budget.requests_used,
                    status_code=exc.status_code,
                ) from exc

            last_error = exc

        try:
            remaining_time = budget.remaining_seconds

            if remaining_time <= 0:
                raise BudgetExceededError("Execution deadline exceeded.")

            if budget.requests_remaining <= 0:
                raise BudgetExceededError("Provider request budget exhausted.")

            delay = min(
                2 ** (budget.requests_used - 1),
                4,
                remaining_time,
            )
            time.sleep(delay)

        except BudgetExceededError as exc:
            raise InferenceError(
                str(exc),
                retryable=True,
                attempts=budget.requests_used,
            ) from last_error
