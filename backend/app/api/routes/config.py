from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/")
async def get_config():
    """Return system configuration for the Config display page."""
    return {
        "llm": {
            "model": settings.LLM_MODEL,
            "base_url": settings.LLM_BASE_URL,
            "cache_responses": settings.CACHE_LLM_RESPONSES,
        },
        "pipeline": {
            "mode": settings.DEFAULT_MODE,
            "max_agent_rounds": settings.MAX_AGENT_ROUNDS,
            "layers": [
                {
                    "id": 1,
                    "name": "Rules Engine",
                    "type": "deterministic",
                    "description": "8 hard-coded rules: velocity, amount threshold, geo-impossibility, new payee large, blacklist, device+sensitive, balance drain, layering pattern",
                },
                {
                    "id": 2,
                    "name": "Behavioral Profiling",
                    "type": "deterministic",
                    "description": "Compares transaction against sender baseline for amount deviation, frequency anomaly, timing anomaly, channel shift, and social spending disruption",
                },
                {
                    "id": 3,
                    "name": "Graph Topology",
                    "type": "deterministic",
                    "description": "NetworkX-based analysis: hub detection, fan-in/out patterns, shared identity signals, velocity spikes, and community structure",
                },
                {
                    "id": 4,
                    "name": "Communication Comprehension",
                    "type": "llm",
                    "description": "LLM analyzes support chat transcripts for coaching markers, vocabulary shifts, urgency patterns, and coercion indicators",
                },
                {
                    "id": 5,
                    "name": "Cross-Signal Synthesis",
                    "type": "llm",
                    "description": "LLM synthesizes all layer evidence into a narrative, exploitation pattern classification, and intervention recommendations",
                },
            ],
        },
        "scoring": {
            "thresholds": {
                "allow": settings.SCORE_THRESHOLD_ALLOW,
                "delay": settings.SCORE_THRESHOLD_DELAY,
                "hold": settings.SCORE_THRESHOLD_HOLD,
                "refer": settings.SCORE_THRESHOLD_REFER,
            },
            "velocity_multiplier_weight": settings.VELOCITY_MULTIPLIER_WEIGHT,
            "corroboration_bonus": settings.CORROBORATION_BONUS,
        },
        "fast_path": {
            "max_amount_std": settings.FAST_PATH_MAX_AMOUNT_STD,
            "min_profile_age_days": settings.FAST_PATH_MIN_PROFILE_AGE_DAYS,
        },
        "vulnerability": {
            "high_threshold": settings.VULNERABILITY_HIGH_THRESHOLD,
            "medium_threshold": settings.VULNERABILITY_MEDIUM_THRESHOLD,
        },
        "data": {
            "mode": settings.DATA_MODE,
            "demo_speed": settings.DEMO_SPEED,
            "baseline_decay_factor": settings.BASELINE_DECAY_FACTOR,
        },
    }
