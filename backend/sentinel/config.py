"""SENTINEL configuration — pydantic-settings for env loading and validation."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env at project root (SpydrWeb/.env)
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """All config from environment. Matches wiring_guide and implementation_details."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    LLM_BASE_URL: str = "https://vjioo4r1vyvcozuj.us-east-2.aws.endpoints.huggingface.cloud/v1"
    LLM_API_KEY: str = "test"
    LLM_MODEL: str = "openai/gpt-oss-120b"

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGIN: str = "http://localhost:5173"

    # --- Demo ---
    DEMO_SPEED: float = 0.5
    CACHE_LLM_RESPONSES: bool = True
    DATA_MODE: str = "synthetic"  # "synthetic" | "paysim" | "both"

    # --- Detection / Baseline ---
    BASELINE_DECAY_FACTOR: float = 0.05
    VULNERABILITY_HIGH_THRESHOLD: float = 0.7
    VULNERABILITY_MEDIUM_THRESHOLD: float = 0.4

    # --- Score thresholds (Action: ALLOW < DELAY < HOLD < REFER) ---
    SCORE_THRESHOLD_ALLOW: float = 0.3
    SCORE_THRESHOLD_DELAY: float = 0.5
    SCORE_THRESHOLD_HOLD: float = 0.7
    SCORE_THRESHOLD_REFER: float = 0.85

    # --- Fast-path ---
    FAST_PATH_MAX_AMOUNT_STD: float = 2.0
    FAST_PATH_MIN_PROFILE_AGE_DAYS: int = 30

    # --- Scoring ---
    VELOCITY_MULTIPLIER_WEIGHT: float = 0.15
    CORROBORATION_BONUS: float = 0.1

    # --- Orchestrator ---
    DEFAULT_MODE: str = "pipeline"  # "pipeline" | "agentic"
    MAX_AGENT_ROUNDS: int = 12


settings = Settings()
