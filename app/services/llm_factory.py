import os
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

def get_llm(model_name: str = "groq/llama-3.3-70b-versatile") -> LLM:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")

    return LLM(
        model=model_name,
        api_key=api_key,
        temperature=0.7,
    )
