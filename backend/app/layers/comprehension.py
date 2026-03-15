"""Layer 4 — AI Comprehension (Coaching / Coercion Detection).

Uses the LLM to analyse support chat interactions against the sender's
established communication fingerprint. Detects vocabulary shifts, coached
patterns, third-party indicators, urgency, coercion, and isolation signals.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from app.ai.prompts import COACHING_DETECTION_PROMPT
from app.layers.base import DetectionLayer
from app.models.events import EventType
from app.models.layers import LayerSignal

if TYPE_CHECKING:
    from app.ai.cache import ResponseCache
    from app.ai.provider import LLMProvider
    from app.brain.graph import BrainGraph
    from app.core.event_stream import EventStream
    from app.models.account import AccountProfile
    from app.models.transaction import Transaction


class ComprehensionLayer(DetectionLayer):
    layer_id = 4
    layer_name = "comprehension"

    def __init__(self, llm_provider: LLMProvider, cache: ResponseCache | None = None, event_stream=None) -> None:
        self.llm = llm_provider
        self.cache = cache
        self.event_stream = event_stream

    async def analyze(
        self,
        transaction: Transaction,
        sender: AccountProfile,
        receiver: AccountProfile,
        event_stream: EventStream,
        graph: BrainGraph,
    ) -> LayerSignal:
        recent_chats = event_stream.query(
            account_id=transaction.sender_id,
            event_type=EventType.SUPPORT_CHAT,
            since=transaction.timestamp - timedelta(days=7),
            until=transaction.timestamp,
        )

        if not recent_chats:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=False,
                confidence=0.0,
                explanation="No recent support interactions to analyse",
            )

        fingerprint_text = "No established fingerprint"
        if sender.communication_fingerprint:
            fp = sender.communication_fingerprint
            fingerprint_text = (
                f"Vocabulary level: {fp.typical_vocabulary_level}. "
                f"Tone: {fp.typical_tone}. "
                f"Topics: {', '.join(fp.typical_topics) if fp.typical_topics else 'general banking'}. "
                f"Uses technical terms: {fp.uses_technical_banking_terms}. "
                f"Sentiment: {fp.baseline_sentiment}. "
                f"Sample phrases: {'; '.join(fp.sample_phrases) if fp.sample_phrases else 'N/A'}"
            )

        interaction_text = "\n\n".join(
            f"[{chat.timestamp.isoformat()}] {chat.payload.get('content', '(no content)')}"
            for chat in recent_chats
        )

        prompt = COACHING_DETECTION_PROMPT.format(
            name=sender.name,
            age=sender.age or "unknown",
            communication_fingerprint=fingerprint_text,
            interaction_text=interaction_text,
        )

        system = "You are a communication analysis specialist detecting third-party influence."
        result = await self.llm.complete_json(system, prompt, cache=self.cache)

        if "error" in result:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=False,
                confidence=0.0,
                explanation=f"LLM analysis failed: {result.get('error', 'unknown')}",
            )

        return self._parse_coaching_result(result)

    def _parse_coaching_result(self, result: dict) -> LayerSignal:
        indicators = [
            "vocabulary_shift",
            "coached_patterns",
            "third_party_indicators",
            "urgency_signals",
            "coercion_indicators",
            "isolation_signals",
        ]

        detected_indicators: list[str] = []
        total_confidence = 0.0
        evidence: dict = {}

        for indicator in indicators:
            data = result.get(indicator, {})
            if isinstance(data, dict) and data.get("detected"):
                detected_indicators.append(indicator)
                conf = float(data.get("confidence", 0.5))
                total_confidence += conf
                evidence[indicator] = {
                    "evidence": data.get("evidence", ""),
                    "deviation": data.get("deviation", ""),
                    "confidence": conf,
                }

        if not detected_indicators:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=False,
                confidence=0.0,
                explanation="No coaching or coercion indicators detected in recent communications",
            )

        avg_confidence = total_confidence / len(detected_indicators)
        combined_confidence = min(avg_confidence + 0.1 * (len(detected_indicators) - 1), 1.0)

        severity = "low"
        if len(detected_indicators) >= 4 or combined_confidence > 0.8:
            severity = "critical"
        elif len(detected_indicators) >= 2 or combined_confidence > 0.6:
            severity = "high"
        elif combined_confidence > 0.4:
            severity = "medium"

        explanation_parts = [f"{ind.replace('_', ' ')}" for ind in detected_indicators]

        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=True,
            confidence=round(combined_confidence, 3),
            explanation=(
                f"Detected {len(detected_indicators)} coaching/coercion indicator(s): "
                f"{', '.join(explanation_parts)}"
            ),
            evidence=evidence,
            severity=severity,
        )
