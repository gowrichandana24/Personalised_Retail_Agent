"""
RetailMind Gemini Intelligence Layer
====================================

Responsibilities
----------------
Gemini is responsible for:

1. Understanding natural-language shopping requests
2. Extracting the shopping mission
3. Detecting shopping constraints
4. Detecting discovery intent
5. Understanding user preferences and exclusions
6. Producing structured JSON for the Supervisor

Gemini does NOT directly select products.

Product selection, ranking, bundling and quality checks
remain deterministic and are handled by tools.py.

This separation makes the system:
- Explainable
- Reliable
- Modular
- Resilient to temporary Gemini failures
"""

import time
from typing import Any, Dict

from google import genai
from pydantic import BaseModel, Field

try:
    from .config import GEMINI_API_KEY, GEMINI_MODEL
except ImportError:  # pragma: no cover - supports `python gemini_agent.py`.
    from config import GEMINI_API_KEY, GEMINI_MODEL


# ============================================================
# STRUCTURED SHOPPING MISSION
# ============================================================

class ShoppingMission(BaseModel):
    """
    Structured representation of the user's shopping intent.
    """

    category: str = Field(
        description=(
            "Main product category such as outfit, shirt, "
            "jeans, footwear, dress, accessories, or fashion."
        )
    )

    occasion: str = Field(
        description=(
            "Shopping occasion such as college, office, "
            "travel, party, wedding, date, gym, or general."
        )
    )

    style: str = Field(
        description=(
            "Desired style such as casual, formal, "
            "streetwear, minimal, sporty, trendy, "
            "comfortable, traditional, or mixed."
        )
    )

    budget: float = Field(
        description=(
            "Maximum shopping budget in Indian rupees. "
            "If the user does not specify a budget, use 5000."
        )
    )

    discovery: bool = Field(
        description=(
            "True when the user wants something new, "
            "different, unexpected, experimental, "
            "trendy, or outside their usual style."
        )
    )

    requires_bundle: bool = Field(
        description=(
            "True when the user wants a complete outfit, "
            "combination, kit, set, bundle, or multiple "
            "coordinated products."
        )
    )

    user_preferences: list[str] = Field(
        default_factory=list,
        description=(
            "Explicit preferences stated by the user."
        )
    )

    exclusions: list[str] = Field(
        default_factory=list,
        description=(
            "Products, styles, colours, materials, or "
            "other things the user explicitly does not want."
        )
    )

    reasoning: str = Field(
        description=(
            "Short explanation of how the shopping request "
            "was interpreted."
        )
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

_client = None


def get_gemini_client():
    """
    Create and cache the Gemini client.

    The API key is loaded through config.py.
    """

    global _client

    if _client is None:

        if not GEMINI_API_KEY:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Add it to your .env file."
            )

        _client = genai.Client(
            api_key=GEMINI_API_KEY
        )

    return _client


# ============================================================
# SHOPPING REQUEST UNDERSTANDING
# ============================================================

def understand_shopping_request(
    user_query: str,
) -> Dict[str, Any]:
    """
    Understand a natural-language shopping request
    using Gemini.

    Returns
    -------
    Dict[str, Any]
        Structured shopping mission.

    Gemini is retried automatically when temporary
    availability/rate-limit errors occur.

    Non-temporary errors are raised immediately.
    """

    client = get_gemini_client()

    # ========================================================
    # INTELLIGENCE PROMPT
    # ========================================================

    prompt = f"""
You are the intelligence layer of a personalized
retail recommendation agent.

Your job is to understand the user's shopping request
and convert it into a structured shopping mission.

You DO NOT select products.

You only understand the user's intent and constraints.

Extract:

1. Product category
2. Shopping occasion
3. Desired style
4. Maximum budget in Indian Rupees
5. Discovery intent
6. Whether a bundle is required
7. Explicit user preferences
8. Explicit exclusions
9. Short reasoning for your interpretation


IMPORTANT RULES
---------------

RULE 1:
Never invent a budget when the user explicitly provides one.

Example:
"I need something under ₹3000"

must produce:

budget = 3000


RULE 2:
If the user does not provide a budget:

budget = 5000


RULE 3:
Discovery intent should be TRUE when the user asks for
something:

- different
- new
- unexpected
- surprising
- experimental
- trendy
- outside their usual style
- something they have not tried before

Examples:

"Show me something different"
"Surprise me"
"I want a new style"
"I'm bored of my usual clothes"

should produce:

discovery = true


RULE 4:
Bundle intent should be TRUE when the user asks for:

- complete outfit
- complete look
- combination
- coordinated outfit
- travel kit
- set
- bundle
- multiple matching products

Example:

"Build me a complete college outfit"

should produce:

requires_bundle = true


RULE 5:
Preserve negative constraints.

Example:

"I don't want sneakers"

should produce:

exclusions = ["sneakers"]


RULE 6:
Preserve explicit preferences.

Example:

"I prefer oversized shirts"

should include:

user_preferences = ["oversized shirts"]


RULE 7:
Understand natural language.

Do not depend only on exact keywords.


RULE 8:
Do not select products.

Product selection is performed later by
the deterministic recommendation and ranking tools.


USER REQUEST
------------

{user_query}
"""

    # ========================================================
    # RETRY CONFIGURATION
    # ========================================================

    max_retries = 3

    # ========================================================
    # GEMINI REQUEST
    # ========================================================

    for attempt in range(max_retries):

        try:

            response = client.models.generate_content(

                model=GEMINI_MODEL,

                contents=prompt,

                config={
                    "response_mime_type": "application/json",
                    "response_schema": ShoppingMission,
                },
            )

            # =================================================
            # EMPTY RESPONSE CHECK
            # =================================================

            if not response.text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            # =================================================
            # STRUCTURED RESPONSE VALIDATION
            # =================================================

            mission = ShoppingMission.model_validate_json(
                response.text
            )

            # =================================================
            # SUCCESS
            # =================================================

            return mission.model_dump()

        # ====================================================
        # ERROR HANDLING
        # ====================================================

        except Exception as error:

            error_text = str(error).upper()

            # Temporary Gemini/API errors
            temporary_error = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
                or "DEADLINE" in error_text
                or "TIMEOUT" in error_text
            )

            # ------------------------------------------------
            # Permanent error
            # ------------------------------------------------

            if not temporary_error:

                raise

            # ------------------------------------------------
            # Last attempt
            # ------------------------------------------------

            if attempt == max_retries - 1:

                raise RuntimeError(
                    "Gemini is temporarily unavailable "
                    "after multiple retry attempts."
                ) from error

            # ------------------------------------------------
            # Exponential backoff
            # ------------------------------------------------

            wait_time = 2 ** attempt

            print(
                f"\n[Gemini Retry]"
            )

            print(
                f"Attempt {attempt + 1}/{max_retries} "
                f"failed."
            )

            print(
                f"Temporary Gemini error detected."
            )

            print(
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)

    # ========================================================
    # SAFETY FALLBACK
    # ========================================================

    raise RuntimeError(
        "Gemini request failed unexpectedly."
    )
