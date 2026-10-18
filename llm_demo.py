
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError(
        "OPENAI_API_KEY is missing. Add it to your .env file."
    )

client = OpenAI()

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
    model="gpt-6-luna",
    instructions=SYSTEM_PROMPT,
    input=ticket,
)

elapsed_ms = (time.perf_counter() - start) * 1000

print("Input:", ticket)
print("\nModel response:")
print(response.output_text)
print(f"\nLatency: {elapsed_ms:.2f} ms")

