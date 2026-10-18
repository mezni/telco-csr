import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is missing. Add it to your .env file.")

client = OpenAI()

MODEL = "gpt-6-luna"

SYSTEM_PROMPT = """
You are a telecom customer support assistant.
Classify the customer's message into one category:
- order_status
- billing
- technical_support
- other

Return the category and a brief explanation.
Do not invent customer or account information.
"""

ticket = "My order #4821 has not arrived."

start = time.perf_counter()

response = client.responses.create(
    model=MODEL,
    instructions=SYSTEM_PROMPT,
    input=ticket,
)

latency_ms = (time.perf_counter() - start) * 1000
usage = response.usage

metrics = {
    "model": MODEL,
    "latency_ms": round(latency_ms, 2),
    "input_tokens": usage.input_tokens if usage else None,
    "output_tokens": usage.output_tokens if usage else None,
    "total_tokens": usage.total_tokens if usage else None,
}

print("\n=== LLM RESPONSE ===")
print(response.output_text)

print("\n=== RUN METRICS ===")
for name, value in metrics.items():
    print(f"{name}: {value}")
