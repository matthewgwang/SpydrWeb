"""Account augmentation — maps PaySim account IDs to Canadian personas.

Given a set of PaySim account IDs (C-prefix strings), generates
realistic demographic metadata so the detection pipeline has rich
profiles to work with.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

_FIRST_NAMES_FEMALE = [
    "Margaret", "Helen", "Dorothy", "Linda", "Susan", "Karen", "Nancy",
    "Sarah", "Emily", "Jessica", "Priya", "Mei", "Fatima", "Anika",
    "Olivia", "Sophia", "Chloe", "Ava", "Isabella", "Mia",
]
_FIRST_NAMES_MALE = [
    "Robert", "James", "David", "Michael", "William", "Richard", "Thomas",
    "Daniel", "Joseph", "George", "Wei", "Raj", "Mohammed", "Carlos",
    "Noah", "Liam", "Ethan", "Lucas", "Mason", "Logan",
]
_LAST_NAMES = [
    "Chen", "Williams", "Park", "Liu", "Sharma", "Kowalski", "Singh",
    "Nguyen", "Kim", "Patel", "Brown", "Taylor", "Anderson", "Thomas",
    "Jackson", "White", "Martin", "Thompson", "Garcia", "Martinez",
    "Robinson", "Clark", "Lewis", "Lee", "Walker", "Hall", "Young",
]
_LOCATIONS = [
    "Toronto, ON", "Mississauga, ON", "Scarborough, ON", "Etobicoke, ON",
    "Richmond Hill, ON", "Markham, ON", "Brampton, ON", "Hamilton, ON",
    "Waterloo, ON", "Ottawa, ON", "London, ON", "Kitchener, ON",
    "Oakville, ON", "Burlington, ON", "Vaughan, ON",
]

_AGE_BRACKETS = [
    (18, 25, 0.15),
    (26, 35, 0.25),
    (36, 50, 0.25),
    (51, 65, 0.20),
    (66, 85, 0.15),
]

_DEVICES_TEMPLATES = [
    ["dev_{id}_iphone"],
    ["dev_{id}_android"],
    ["dev_{id}_laptop", "dev_{id}_phone"],
    ["dev_{id}_ipad"],
    ["dev_{id}_macbook", "dev_{id}_iphone"],
]

_CHANNELS_TEMPLATES = [
    {"mobile": 80, "online": 20},
    {"online": 60, "mobile": 30, "branch": 10},
    {"mobile": 50, "online": 50},
    {"branch": 30, "mobile": 50, "online": 20},
    {"mobile": 90, "online": 10},
]


def augment_accounts(
    account_ids: list[str],
    seed: int = 42,
) -> list[dict]:
    """Generate persona metadata for a list of PaySim account IDs.

    Returns a list of dicts compatible with the persona format used
    in profiles.py (account_id, name, age, location, behavior, etc.).
    """
    rng = random.Random(seed)
    bracket_ages, bracket_weights = [], []
    for lo, hi, w in _AGE_BRACKETS:
        bracket_ages.append((lo, hi))
        bracket_weights.append(w)

    personas: list[dict] = []
    for account_id in account_ids:
        is_female = rng.random() < 0.5
        first = rng.choice(_FIRST_NAMES_FEMALE if is_female else _FIRST_NAMES_MALE)
        last = rng.choice(_LAST_NAMES)
        name = f"{first} {last}"

        lo, hi = rng.choices(bracket_ages, weights=bracket_weights, k=1)[0]
        age = rng.randint(lo, hi)

        location = rng.choice(_LOCATIONS)
        created_days_ago = rng.randint(180, 2500)
        created = datetime.now(UTC) - timedelta(days=created_days_ago)

        avg_amount = round(rng.uniform(20, 500), 2)
        std_amount = round(avg_amount * rng.uniform(0.3, 1.5), 2)
        daily_freq = round(rng.uniform(0.3, 5.0), 1)

        hour_start = rng.randint(6, 12)
        hour_end = rng.randint(hour_start + 4, 23)
        typical_hours = list(range(hour_start, hour_end + 1))

        short_id = account_id[-6:]
        devices = [d.format(id=short_id) for d in rng.choice(_DEVICES_TEMPLATES)]
        channels = rng.choice(_CHANNELS_TEMPLATES)

        persona: dict = {
            "account_id": account_id,
            "name": name,
            "age": age,
            "location": location,
            "account_created": created.strftime("%Y-%m-%d"),
            "account_type": "small_business" if rng.random() < 0.1 else "retail",
            "behavior": {
                "avg_amount": avg_amount,
                "std_amount": std_amount,
                "daily_frequency": daily_freq,
                "typical_hours": typical_hours,
                "typical_merchants": _pick_merchants(rng, age),
                "typical_channels": channels,
                "devices": devices,
                "balance_check_frequency": round(rng.uniform(0.0, 2.0), 1),
                "transfer_method": rng.choice(["online", "branch_only", "online"]),
                "known_payees": _pick_payees(rng),
                "support_interaction_frequency": round(rng.uniform(0.02, 0.3), 2),
            },
        }

        if age >= 65:
            persona["vulnerability_factors"] = _pick_vulnerability_factors(rng, age)
            persona["communication_style"] = {
                "vocabulary": rng.choice(["simple", "moderate"]),
                "tone": rng.choice(["polite, unhurried", "formal, brief", "friendly, chatty"]),
            }

        personas.append(persona)

    return personas


def _pick_merchants(rng: random.Random, age: int) -> list[str]:
    common = ["Tim Hortons", "Amazon", "Walmart"]
    if age < 30:
        pool = common + ["Uber Eats", "Steam", "Apple", "Spotify"]
    elif age < 50:
        pool = common + ["Costco", "Canadian Tire", "Home Depot"]
    else:
        pool = common + ["Metro Grocery", "Shoppers Drug Mart", "Rexall Pharmacy"]
    return rng.sample(pool, min(len(pool), rng.randint(2, 5)))


def _pick_payees(rng: random.Random) -> list[str]:
    pool = [
        "Rent e-Transfer", "Hydro One", "Bell Canada", "Rogers",
        "Landlord", "Family e-Transfer", "Netflix", "CRA",
    ]
    return rng.sample(pool, rng.randint(1, 4))


def _pick_vulnerability_factors(rng: random.Random, age: int) -> list[str]:
    possible = ["low_digital_literacy", "rigid_routine"]
    if age >= 75:
        possible.extend(["declining_social_spending", "interaction_isolation"])
    if rng.random() < 0.3:
        possible.append("recent_life_disruption")
    return rng.sample(possible, rng.randint(1, min(3, len(possible))))
