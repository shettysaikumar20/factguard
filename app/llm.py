"""Small Gemini boundary; imports do not require credentials."""
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


class ModelUnavailable(RuntimeError):
    pass


def complete(instruction: str, payload: str, schema=None) -> str:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ModelUnavailable("GEMINI_API_KEY is not configured.")
    config = types.GenerateContentConfig(
        system_instruction=instruction, temperature=0,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        response_mime_type="application/json" if schema else "text/plain",
        response_json_schema=schema.model_json_schema() if schema else None,
    )
    try:
        with genai.Client(api_key=key, http_options=types.HttpOptions(
            timeout=30000, retry_options=types.HttpRetryOptions(attempts=1)
        )) as client:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                contents=payload, config=config,
            )
        if not response.text or not response.text.strip():
            raise ModelUnavailable("The model returned no answer.")
        return response.text.strip()
    except ModelUnavailable:
        raise
    except Exception as error:
        raise ModelUnavailable("Model request failed; check credentials, quota and connectivity.") from error
