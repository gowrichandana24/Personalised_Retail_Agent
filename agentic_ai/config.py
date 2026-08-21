import os

from backend.config import GEMINI_API_KEY, GEMINI_MODEL


MAX_RECOMMENDATIONS = int(
    os.getenv(
        "MAX_RECOMMENDATIONS",
        "5"
    )
)

DEFAULT_BUDGET = float(
    os.getenv(
        "DEFAULT_BUDGET",
        "5000"
    )
)

DISCOVERY_THRESHOLD = float(
    os.getenv(
        "DISCOVERY_THRESHOLD",
        "0.6"
    )
)