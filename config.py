# config.py

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    model: str
    timeout_seconds: float = 30.0
    max_attempts: int = 3
    deadline_seconds: float = 60.0


def load_settings() -> Settings:
    """Load and validate application settings."""
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    if not model:
        raise ValueError("OPENAI_MODEL is not configured.")

    try:
        timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        attempts = int(os.getenv("LLM_MAX_ATTEMPTS", "3"))
        deadline = float(os.getenv("LLM_DEADLINE_SECONDS", "60"))
    except ValueError as exc:
        raise ValueError(
            "Timeout, deadline, and retry settings must be numeric."
        ) from exc

    if not 0 < timeout < float("inf"):
        raise ValueError("LLM_TIMEOUT_SECONDS must be positive and finite.")

    if attempts < 1:
        raise ValueError("LLM_MAX_ATTEMPTS must be at least 1.")

    if not 0 < deadline < float("inf"):
        raise ValueError("LLM_DEADLINE_SECONDS must be positive and finite.")

    return Settings(
        openai_api_key=api_key,
        model=model,
        timeout_seconds=timeout,
        max_attempts=attempts,
        deadline_seconds=deadline,
    )
