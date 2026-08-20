import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(ENV_PATH)


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


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