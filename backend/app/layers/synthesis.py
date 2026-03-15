"""Layer 5 — Cross-Signal Synthesis.

Uses the LLM to synthesize evidence from all layers into an EvidenceBrief:
chronological narrative, manipulation indicators, exploitation pattern,
what traditional systems missed, and intervention recommendations.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.ai.prompts import SYNTHESIS_PROMPT
from app.models.layers import ExploitationTactic, LayerSignal
from app.models.report import EvidenceBrief, InterventionRecommendation

if TYPE_CHECKING:
    from app.ai.cache import ResponseCache
    from app.ai.provider import LLMProvider
    from app.models.account import AccountProfile, VulnerabilityScore
    from app.models.layers import TestPlan
    from app.models.transaction import Transaction


class SynthesisLayer:
    """Layer 5 — synthesizes all layer signals into an EvidenceBrief."""

    layer_id = 5
    layer_name = "synthesis"

    def __init__(
        self,
        llm_provider: LLMProvider,
        cache: ResponseCache | None = None,
    ) -> None:
        self.llm = llm_provider
        self.cache = cache

    async def synthesize(
        self,
        *,
        all_signals: list[LayerSignal],
        sender_profile: AccountProfile,
        receiver_profile: AccountProfile,
        transaction: Transaction,
        graph_context: dict,
        relationship_timeline: list | None,
        vulnerability: VulnerabilityScore | None,
        test_plan: TestPlan,
    ) -> EvidenceBrief:
        """Synthesize evidence into an EvidenceBrief for the analyst."""
        vuln_score = vulnerability.score if vulnerability else 0.0
        vuln_factors = (
            ", ".join(f.factor for f in vulnerability.factors)
            if vulnerability and vulnerability.factors
            else "none"
        )

        sender_text = sender_profile.summary_text or (
            f"{sender_profile.name}, age {sender_profile.age}, {sender_profile.location}. "
            f"Account {sender_profile.account_id}."
        )
        receiver_text = receiver_profile.summary_text or (
            f"{receiver_profile.name or receiver_profile.account_id}, "
            f"age {receiver_profile.age or 'unknown'}, {receiver_profile.location or 'unknown'}."
        )

        fp = sender_profile.communication_fingerprint
        fp_text = "No established fingerprint"
        if fp:
            fp_text = (
                f"Vocabulary: {fp.typical_vocabulary_level}. "
                f"Tone: {fp.typical_tone}. "
                f"Topics: {fp.typical_topics}. "
                f"Sample phrases: {'; '.join(fp.sample_phrases[:3]) if fp.sample_phrases else 'N/A'}"
            )

        rr = receiver_profile.recipient_risk
        rr_text = "No recipient risk data"
        if rr:
            rr_text = (
                f"First-time senders 7d: {rr.first_time_sender_count_7d}. "
                f"Inbound velocity 24h: {rr.inbound_velocity_24h}. "
                f"Receive-to-send ratio: {rr.receive_to_send_ratio}. "
                f"Is receive-only: {rr.is_receive_only}"
            )

        tx_details = (
            f"${transaction.amount:,.2f} {transaction.type.value} via {transaction.channel}. "
            f"Balance: ${transaction.old_balance_sender:,.0f} → ${transaction.new_balance_sender:,.0f}. "
            f"New payee: {transaction.receiver_id not in sender_profile.known_payees}"
        )

        signals_text = "\n".join(
            f"  [L{s.layer_id} {s.layer_name}] triggered={s.triggered} conf={s.confidence}: {s.explanation}"
            for s in all_signals
        )

        graph_text = str(graph_context) if graph_context else "No graph context"

        timeline_text = "No relationship history"
        if relationship_timeline:
            timeline_text = "\n".join(
                f"  {e.get('timestamp', '')} {e.get('type', '')}: {e.get('from', '')} → {e.get('to', '')}"
                for e in relationship_timeline[:10]
            )

        prompt = SYNTHESIS_PROMPT.format(
            sender_profile=sender_text,
            vulnerability_score=f"{vuln_score:.2f}",
            vulnerability_factors=vuln_factors,
            communication_fingerprint=fp_text,
            receiver_profile=receiver_text,
            recipient_risk=rr_text,
            transaction_details=tx_details,
            layer_signals_formatted=signals_text,
            graph_context=graph_text,
            relationship_timeline=timeline_text,
        )

        system = "You are a fraud intelligence analyst. Synthesize evidence clearly. Do NOT make fraud determinations."
        result = await self.llm.complete(system, prompt, cache=self.cache)

        return self._parse_synthesis_result(result, all_signals)

    def _parse_synthesis_result(self, text: str, all_signals: list[LayerSignal]) -> EvidenceBrief:
        """Parse LLM plain-text response into EvidenceBrief."""
        narrative = ""
        manipulation_indicators: list[str] = []
        exploitation_tactic = ExploitationTactic.UNKNOWN
        what_missed = ""
        interventions: list[InterventionRecommendation] = []

        # Flexible header: "NARRATIVE:", "1. NARRATIVE:", "### 1. NARRATIVE", "**NARRATIVE**:", etc.
        _H = r"(?:^|\n)\s*(?:#{1,4}\s+)?(?:\d+[\.\)]\s+)?(?:\*{2})?"
        _HE = r"(?:\*{2})?\s*:?\s*\n"
        _NX = r"(?:\n\s*(?:#{1,4}\s+)?(?:\d+[\.\)]\s+)?(?:\*{2})?(?:NARRATIVE|MANIPULATION|EXPLOITATION|WHAT|INTERVENTION))"

        patterns = [
            (rf"{_H}NARRATIVE{_HE}(.*?)(?={_NX}|\Z)", "narrative", str),
            (rf"{_H}MANIPULATION INDICATORS?{_HE}(.*?)(?={_NX}|\Z)", "manipulation", "lines"),
            (rf"{_H}EXPLOITATION PATTERN{_HE}(.*?)(?={_NX}|\Z)", "exploitation", str),
            (rf"{_H}WHAT TRADITIONAL SYSTEMS MISSED{_HE}(.*?)(?={_NX}|\Z)", "missed", str),
            (rf"{_H}INTERVENTION RECOMMENDATIONS?{_HE}(.*?)(?={_NX}|\Z)", "interventions", "lines"),
        ]

        for pattern, key, fmt in patterns:
            m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if m:
                content = m.group(1).strip()
                if key == "narrative":
                    narrative = content
                elif key == "manipulation":
                    manipulation_indicators = [
                        line.strip().lstrip("-•* ")
                        for line in content.split("\n")
                        if line.strip()
                    ]
                elif key == "exploitation":
                    content_lower = content.lower()
                    if any(k in content_lower for k in ("family_coercion", "family coercion", "family member", "relative")):
                        exploitation_tactic = ExploitationTactic.FAMILY_COERCION
                    elif any(k in content_lower for k in ("romance", "love", "dating", "relationship")):
                        exploitation_tactic = ExploitationTactic.ROMANCE_SCAM
                    elif any(k in content_lower for k in ("authority", "impersonat", "government", "irs", "police", "official")):
                        exploitation_tactic = ExploitationTactic.AUTHORITY_IMPERSONATION
                    elif any(k in content_lower for k in ("phone_coaching", "phone coaching", "coaching", "coached", "guided", "instructed")):
                        exploitation_tactic = ExploitationTactic.PHONE_COACHING
                elif key == "missed":
                    what_missed = content
                elif key == "interventions":
                    for line in content.split("\n"):
                        line = line.strip().lstrip("-•* ")
                        if line:
                            interventions.append(InterventionRecommendation(
                                action="recommend",
                                reason=line[:200],
                                urgency="MEDIUM",
                            ))

        # Fallback: use full text as narrative if parsing found nothing
        if not narrative and text:
            narrative = text[:2000]

        triggered = [s for s in all_signals if s.triggered]
        conf = max((s.confidence for s in triggered), default=0.0) if triggered else 0.0

        return EvidenceBrief(
            narrative=narrative,
            signals=all_signals,
            exploitation_tactic=exploitation_tactic,
            manipulation_indicators=manipulation_indicators,
            interventions=interventions,
            confidence_score=round(conf, 3),
            what_traditional_systems_missed=what_missed,
        )
