
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-6-luna"

DEFAULT_SYSTEM_PROMPT = """
You are a telecom customer support assistant.
Classify the customer's message into one category:
- order_status
- billing
- technical_support
- other

Return the category and a brief explanation.
Do not invent customer or account information.
"""


def run_inference(
    ticket: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Run one real LLM request and return its response and metrics."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing from .env")

    client = OpenAI()
    start = time.perf_counter()

    response = client.responses.create(
        model=model,
        instructions=system_prompt,
        input=ticket,
    )

    latency_ms = (time.perf_counter() - start) * 1000
    usage = response.usage

    return {
        "model": model,
        "response": response.output_text,
        "latency_ms": round(latency_ms, 2),
        "input_tokens": usage.input_tokens if usage else None,
        "output_tokens": usage.output_tokens if usage else None,
        "total_tokens": usage.total_tokens if usage else None,
    }

