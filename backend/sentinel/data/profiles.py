"""Persona definitions for SENTINEL synthetic data.

These define the 4 demo accounts with their behavioural characteristics.
"""

MARGARET_CHEN = {
    "account_id": "C1231006815",
    "name": "Margaret Chen",
    "age": 74,
    "location": "Scarborough, ON",
    "account_created": "2019-03-15",
    "account_type": "retail",
    "behavior": {
        "avg_amount": 62.50,
        "std_amount": 35.00,
        "daily_frequency": 0.8,
        "typical_hours": [9, 10, 11, 14, 15],
        "typical_merchants": ["Metro Grocery", "Shoppers Drug Mart", "Bell Canada"],
        "typical_channels": {"branch": 15, "mobile": 85},
        "devices": ["dev_margaret_iphone"],
        "balance_check_frequency": 1.0,
        "login_pattern": "daily 8-9am",
        "transfer_method": "branch_only",
        "known_payees": ["Bell Canada Auto-Pay"],
        "support_interaction_frequency": 0.15,
    },
    "communication_style": {
        "vocabulary": "simple",
        "tone": "polite, unhurried",
        "typical_messages": [
            "Hi, what's my balance please?",
            "I think my card isn't working",
            "Can you help me with my phone bill payment?",
        ],
        "never_uses": [
            "wire transfer",
            "beneficiary",
            "initiate",
            "e-transfer limit",
            "payee management",
        ],
    },
    "vulnerability_factors": [
        "low_digital_literacy",
        "rigid_routine",
        "declining_social_spending",
    ],
}

ROBERT_WILLIAMS = {
    "account_id": "C1666544295",
    "name": "Robert Williams",
    "age": 81,
    "location": "Etobicoke, ON",
    "account_created": "2015-06-01",
    "account_type": "retail",
    "behavior": {
        "avg_amount": 85.00,
        "std_amount": 45.00,
        "daily_frequency": 0.5,
        "typical_hours": [10, 11, 14],
        "typical_merchants": ["Loblaws", "Rexall Pharmacy", "St. James Church"],
        "typical_channels": {"branch": 60, "mobile": 40},
        "devices": ["dev_robert_tablet"],
        "balance_check_frequency": 0.3,
        "transfer_method": "branch_only",
        "known_payees": ["Condo Corp Auto-Pay", "Bell Canada"],
        "support_interaction_frequency": 0.08,
    },
    "communication_style": {
        "vocabulary": "moderate",
        "tone": "formal, brief",
        "typical_messages": [
            "I'd like to check on my account",
            "When does my pension come in?",
        ],
    },
    "vulnerability_factors": [
        "recent_life_disruption",
        "interaction_isolation",
        "declining_social_spending",
    ],
}

DAVID_PARK = {
    "account_id": "C2048537720",
    "name": "David Park",
    "age": 28,
    "location": "Toronto, ON",
    "account_created": "2022-11-01",
    "account_type": "retail",
    "behavior": {
        "avg_amount": 125.00,
        "std_amount": 200.00,
        "daily_frequency": 2.5,
        "typical_hours": list(range(8, 24)),
        "typical_merchants": ["Uber Eats", "Amazon", "Steam", "TTC", "Shopify"],
        "typical_channels": {"online": 70, "mobile": 30},
        "devices": ["dev_david_macbook", "dev_david_pixel", "dev_david_ipad"],
        "balance_check_frequency": 0.1,
        "transfer_method": "online",
        "known_payees": ["Landlord e-Transfer", "Mom e-Transfer", "Netflix", "Spotify"],
    },
}

SARAH_WILLIAMS = {
    "account_id": "C90045638",
    "name": "Sarah Williams",
    "age": 35,
    "location": "Mississauga, ON",
    "account_created": "2020-05-15",
    "account_type": "retail",
    "behavior": {
        "avg_amount": 95.00,
        "std_amount": 80.00,
        "daily_frequency": 1.8,
        "typical_hours": [7, 8, 12, 17, 18, 19, 20],
        "typical_merchants": ["Daycare Center", "Walmart", "Amazon", "Tim Hortons"],
        "typical_channels": {"mobile": 60, "online": 30, "branch": 10},
        "devices": ["dev_sarah_iphone", "dev_sarah_laptop"],
        "balance_check_frequency": 0.5,
        "transfer_method": "online",
        "known_payees": ["Daycare Monthly", "Husband e-Transfer", "Hydro One"],
    },
}

ALL_PERSONAS = [MARGARET_CHEN, ROBERT_WILLIAMS, DAVID_PARK, SARAH_WILLIAMS]
