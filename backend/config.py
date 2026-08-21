"""Shared runtime configuration for the backend and AI integrations."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# The agentic module historically owned this file. Load it first so the
# backend uses the existing local credential without copying it into source.
load_dotenv(PROJECT_ROOT / "agentic_ai" / ".env")
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
