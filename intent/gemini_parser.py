import os

from dotenv import load_dotenv
from google import genai

from .schemas import ShoppingIntent
from .prompts import INTENT_SYSTEM_PROMPT


load_dotenv()


class GeminiIntentParser:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

    def parse(self, user_message: str) -> ShoppingIntent:

        prompt = f"""
{INTENT_SYSTEM_PROMPT}

CUSTOMER MESSAGE:

{user_message}
"""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ShoppingIntent,
            },
        )

        return ShoppingIntent.model_validate_json(
            response.text
        )