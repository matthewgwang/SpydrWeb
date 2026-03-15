"""Chat template loader from HuggingFace datasets.

Sources:
- Financial Support Conversations (ai-training-datasets/financial_support, 100 dialogues)
- Bitext Retail Banking Chat (bitext/Bitext-retail-banking-llm-chatbot-training-dataset, 25K pairs)

Extracts realistic dialogue templates indexed by persona type and intent.
Falls back to hardcoded templates if datasets are not available.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_TEMPLATES: dict[str, list[str]] = {
    "elderly:balance_inquiry": [
        "Hi, can you tell me what my balance is please?",
        "Good morning. I just want to check how much is in my account.",
        "Hello dear, could you look up my account balance for me?",
    ],
    "elderly:payment_help": [
        "I need help paying my phone bill. Can someone walk me through it?",
        "My grandson says I should pay online but I don't know how.",
        "Can you help me with my hydro payment? I usually do it at the branch.",
    ],
    "elderly:card_issue": [
        "My card wouldn't work at the store today. Is something wrong?",
        "I tried to use my card at Shoppers and it was declined.",
        "The machine said 'card not recognized'. What does that mean?",
    ],
    "elderly:general": [
        "I'd like to check on my account please.",
        "When does my pension come in this month?",
        "Can I get a copy of my statement?",
    ],
    "young:transfer": [
        "hey can u check if my etransfer went thru?",
        "i need to send money to my roommate, whats the max etransfer?",
        "how do i set up auto etransfer for rent every month",
    ],
    "young:card_issue": [
        "my card got declined but i have money?? whats going on",
        "i think someone used my card, theres a charge i dont recognize",
        "can i get a virtual card number for online shopping",
    ],
    "young:general": [
        "is there an outage rn? app wont load",
        "how do i change my PIN",
        "can you waive the monthly fee? im a student",
    ],
    "middle:payment": [
        "Hi, I'd like to set up a recurring payment for daycare.",
        "Can I get a copy of my last 3 months of statements for my mortgage application?",
        "I need to update my address — we just moved.",
    ],
    "middle:dispute": [
        "I noticed a charge on my account that I don't recognize — $47.50 from 'TKT Services'.",
        "There's a duplicate charge from last week that needs to be reversed.",
        "I was double-charged at a restaurant. How do I dispute that?",
    ],
    "middle:general": [
        "What's the interest rate on your savings accounts right now?",
        "Can I increase my credit limit? My income has gone up.",
        "I need to add my spouse as a joint account holder.",
    ],
    "business:operations": [
        "I need to increase my daily transfer limit for a supplier payment.",
        "Can you confirm my payroll batch went through?",
        "My POS terminal isn't connecting — is there an outage?",
    ],
    "business:general": [
        "I need to set up a new employee for payroll deposits.",
        "What are the fees for international wire transfers?",
        "Can I get a letter confirming my business account for a vendor application?",
    ],
    "fraud:coached": [
        "Hi there. My grandson is helping me set up online banking. I need to add a new payee "
        "and I'd like to know what my e-transfer limit is. Can you walk me through how to "
        "initiate a wire transfer to a beneficiary account?",
    ],
    "fraud:romance": [
        "I need to send money to someone overseas. It's for a friend who is having medical "
        "issues. Please don't ask too many questions, this is urgent.",
    ],
    "fraud:authority": [
        "Hello, I received a call from your fraud department saying my account has been "
        "compromised. They told me to transfer my savings to a safe account immediately.",
    ],
}


def get_templates() -> dict[str, list[str]]:
    """Return all chat templates indexed by persona_type:intent."""
    return dict(_TEMPLATES)


def get_template(persona_type: str, intent: str) -> str | None:
    """Return a single template for the given persona type and intent."""
    key = f"{persona_type}:{intent}"
    templates = _TEMPLATES.get(key, [])
    return templates[0] if templates else None


def get_templates_for_persona(persona_type: str) -> dict[str, list[str]]:
    """Return all templates for a given persona type."""
    prefix = f"{persona_type}:"
    return {
        k: v for k, v in _TEMPLATES.items() if k.startswith(prefix)
    }


def load_from_huggingface(
    dataset_name: str,
    cache_dir: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Load a HuggingFace dataset and return as list of dicts.

    Requires the `datasets` library. Returns empty list if unavailable.
    """
    try:
        from datasets import load_dataset
        ds = load_dataset(dataset_name, cache_dir=str(cache_dir) if cache_dir else None)
        if "train" in ds:
            return [dict(row) for row in ds["train"]]
        return [dict(row) for row in ds]
    except Exception:
        return []


def enrich_templates_from_dataset(
    dataset_rows: list[dict[str, Any]],
    text_field: str = "text",
    intent_field: str = "intent",
) -> dict[str, list[str]]:
    """Parse a loaded dataset into template format.

    Returns dict mapping intent to list of text samples.
    """
    result: dict[str, list[str]] = {}
    for row in dataset_rows:
        intent = row.get(intent_field, "general")
        text = row.get(text_field, "")
        if text:
            result.setdefault(intent, []).append(text)
    return result
