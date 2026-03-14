"""All LLM prompt templates for SENTINEL.

Every module that calls the LLM imports its prompt from here.
"""

PROFILE_GENERATION_PROMPT = """Given the following account data, generate a concise behavioral profile summary in 3-5 sentences. Describe the customer's banking habits, typical patterns, and communication style as if you were writing a case file for a fraud analyst.

Account ID: {account_id}
Name: {name}, Age: {age}, Location: {location}
Account created: {account_created}
Transaction history summary:
- Average transaction: ${avg_amount:.2f} (std: ${std_amount:.2f})
- Typical frequency: {avg_daily_frequency:.1f} transactions/day
- Typical hours: {typical_hours}
- Typical merchants: {typical_merchants}
- Typical channels: {typical_channels}
- Devices: {devices}
- Known payees: {known_payees}
- Balance check frequency: {balance_check_frequency_daily:.1f}/day

Generate ONLY the profile summary text, no headers or labels."""

COMMUNICATION_FINGERPRINT_PROMPT = """Analyze these customer support interactions and generate a communication fingerprint — a description of how this customer typically communicates.

Customer: {name}, Age: {age}
Historical interactions:
{interactions_text}

Describe in 2-3 sentences:
1. Their typical vocabulary level (simple/moderate/technical)
2. Their typical tone and communication style
3. What topics they usually discuss
4. Any characteristic phrases or patterns

Generate ONLY the fingerprint description."""

COACHING_DETECTION_PROMPT = """Analyze this customer support interaction. Compare it against the customer's established communication fingerprint provided below.

Customer: {name}, Age: {age}
Established communication fingerprint:
{communication_fingerprint}

Current interaction:
{interaction_text}

You are looking for signs of third-party influence. Do NOT judge whether exploitation is occurring. Only annotate what you observe.

For each of the following indicators, respond with a JSON object:

{{
  "vocabulary_shift": {{
    "detected": true/false,
    "evidence": "quoted text showing unusual vocabulary",
    "deviation": "how this differs from the fingerprint",
    "confidence": 0.0-1.0
  }},
  "coached_patterns": {{
    "detected": true/false,
    "evidence": "quoted text that sounds rehearsed or scripted",
    "deviation": "how this differs from typical style",
    "confidence": 0.0-1.0
  }},
  "third_party_indicators": {{
    "detected": true/false,
    "evidence": "quoted references to someone helping or being present",
    "deviation": "why this is unusual for this customer",
    "confidence": 0.0-1.0
  }},
  "urgency_signals": {{
    "detected": true/false,
    "evidence": "quoted text showing time pressure or resistance to procedures",
    "deviation": "how this differs from typical calm communication",
    "confidence": 0.0-1.0
  }},
  "coercion_indicators": {{
    "detected": true/false,
    "evidence": "quoted text showing hesitation, confusion, or contradictions",
    "deviation": "behavioral inconsistency with profile",
    "confidence": 0.0-1.0
  }},
  "isolation_signals": {{
    "detected": true/false,
    "evidence": "quoted requests to change contact info or dismiss concerns",
    "deviation": "unusual for this customer",
    "confidence": 0.0-1.0
  }}
}}

Respond ONLY with the JSON object, no other text."""

EXPLOITATION_ASSESSMENT_PROMPT = """You are assessing whether a transaction warrants investigation for social engineering or elder exploitation. You do NOT determine whether fraud is occurring — you assess risk level only.

Sender profile:
{sender_profile}

Sender vulnerability score: {vulnerability_score} (factors: {vulnerability_factors})

Receiver profile:
{receiver_profile}

Transaction:
Amount: ${amount:.2f}
Type: {tx_type}
Channel: {channel}
Sender balance before: ${old_balance_sender:.2f}
Sender balance after: ${new_balance_sender:.2f}
Is first transaction to this payee: {is_new_payee}

Recent events for sender (last 7 days):
{recent_events}

Based on the sender's profile, vulnerability level, and this transaction's characteristics, rank the likelihood of each exploitation type and suggest which detection layers to prioritize.

Respond with JSON:
{{
  "exploitation_types": [
    {{"type": "family_coercion", "likelihood": 0.0-1.0, "reasoning": "..."}},
    {{"type": "romance_scam", "likelihood": 0.0-1.0, "reasoning": "..."}},
    {{"type": "authority_impersonation", "likelihood": 0.0-1.0, "reasoning": "..."}},
    {{"type": "phone_coaching", "likelihood": 0.0-1.0, "reasoning": "..."}}
  ],
  "priority_layers": [1, 2, 3, 4],
  "layer_weights": {{"1": 0.2, "2": 0.3, "3": 0.2, "4": 0.3}},
  "warrants_investigation": true/false,
  "reasoning": "..."
}}

Respond ONLY with the JSON object."""

SYNTHESIS_PROMPT = """You are a fraud intelligence analyst specializing in elder exploitation and social engineering. You do NOT make fraud/no-fraud determinations. You synthesize evidence and present it clearly so a human analyst can act quickly.

SENDER PROFILE:
{sender_profile}

SENDER VULNERABILITY: {vulnerability_score}/1.0
Factors: {vulnerability_factors}

SENDER COMMUNICATION FINGERPRINT:
{communication_fingerprint}

RECEIVER PROFILE:
{receiver_profile}

RECEIVER RISK:
{recipient_risk}

TRANSACTION:
{transaction_details}

LAYER SIGNALS:
{layer_signals_formatted}

GRAPH CONTEXT:
{graph_context}

RELATIONSHIP TIMELINE:
{relationship_timeline}

Based on all the above evidence, produce an evidence brief with the following structure:

1. NARRATIVE: A chronological story of what happened, written in plain language. Connect the signals together — show how events across different data sources relate to each other. Be specific about timing and sequence.

2. MANIPULATION INDICATORS: List the specific signs of third-party influence or manipulation found in the evidence.

3. EXPLOITATION PATTERN: Which exploitation tactic does this most resemble (family_coercion / romance_scam / authority_impersonation / phone_coaching) and why?

4. WHAT TRADITIONAL SYSTEMS MISSED: Explain specifically what a traditional transaction-monitoring system would NOT have caught and why cross-data synthesis was necessary.

5. INTERVENTION RECOMMENDATIONS: Based on the identified tactic, suggest 2-3 specific actions the analyst should take. Include sensitivity guidance for how to approach the customer.

Write the narrative as if you are briefing a human analyst who needs to act within minutes. Be direct, specific, and cite which data source each observation comes from.

Respond in plain text (not JSON) with clear section headers."""
