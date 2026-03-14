from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (two levels up from this file)
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)


def _bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes")


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://vjioo4r1vyvcozuj.us-east-2.aws.endpoints.huggingface.cloud/v1")
LLM_API_KEY: str = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", "test")
LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
CORS_ORIGIN: str = os.getenv("CORS_ORIGIN", "http://localhost:5173")

# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
DEMO_SPEED: float = float(os.getenv("DEMO_SPEED", "0.5"))
CACHE_LLM_RESPONSES: bool = _bool(os.getenv("CACHE_LLM_RESPONSES"), default=True)
DATA_MODE: str = os.getenv("DATA_MODE", "synthetic")  # "synthetic" | "paysim" | "both"

# ---------------------------------------------------------------------------
# Detection thresholds
# ---------------------------------------------------------------------------
FAST_PATH_MAX_AMOUNT_STD: float = float(os.getenv("FAST_PATH_MAX_AMOUNT_STD", "2.0"))
FAST_PATH_MIN_PROFILE_AGE_DAYS: int = int(os.getenv("FAST_PATH_MIN_PROFILE_AGE_DAYS", "30"))

SCORE_THRESHOLD_ALLOW: float = float(os.getenv("SCORE_THRESHOLD_ALLOW", "0.3"))
SCORE_THRESHOLD_CHALLENGE: float = float(os.getenv("SCORE_THRESHOLD_CHALLENGE", "0.6"))
SCORE_THRESHOLD_BLOCK: float = float(os.getenv("SCORE_THRESHOLD_BLOCK", "0.85"))

VELOCITY_MULTIPLIER_WEIGHT: float = float(os.getenv("VELOCITY_MULTIPLIER_WEIGHT", "0.15"))
CORROBORATION_BONUS: float = float(os.getenv("CORROBORATION_BONUS", "0.1"))

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
DEFAULT_MODE: str = os.getenv("DEFAULT_MODE", "pipeline")  # "pipeline" | "agentic"
MAX_AGENT_ROUNDS: int = int(os.getenv("MAX_AGENT_ROUNDS", "12"))
