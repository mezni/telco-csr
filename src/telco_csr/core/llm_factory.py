import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    """Returns a configured ChatOpenAI instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("DEFAULT_MODEL", "gpt-6-luna")

    return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)
