import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def create_llm_client() -> OpenAI:
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL")

    if not api_key:
        raise ValueError("GROQ_API_KEY is missing from environment")

    if not model:
        raise ValueError("GROQ_MODEL is missing from environment")

    return OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
        timeout=60.0,
        max_retries=2,
    )


def get_model_name() -> str:
    model = os.getenv("GROQ_MODEL")

    if not model:
        raise ValueError("GROQ_MODEL is missing from environment")

    return model
