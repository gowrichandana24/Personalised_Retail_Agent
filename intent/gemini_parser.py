from google import genai

from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from .schemas import ShoppingIntent
from .prompts import INTENT_SYSTEM_PROMPT

class GeminiIntentParser:

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured in agentic_ai/.env or .env."
            )

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

    def parse(self, user_message: str, context: dict | None = None) -> ShoppingIntent:
        context_text = context or {}

        prompt = f"""
{INTENT_SYSTEM_PROMPT}

PREVIOUS CONVERSATION INTENT:

{context_text}

CUSTOMER MESSAGE:

{user_message}
"""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ShoppingIntent,
            },
        )

        return ShoppingIntent.model_validate_json(
            response.text
        )