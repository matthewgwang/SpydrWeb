"""Profile builder — uses LLM to generate narrative profile summaries."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sentinel.ai.prompts import (
    COMMUNICATION_FINGERPRINT_PROMPT,
    PROFILE_GENERATION_PROMPT,
)
from sentinel.models.account import AccountProfile, CommunicationFingerprint

if TYPE_CHECKING:
    from sentinel.ai.cache import ResponseCache
    from sentinel.ai.provider import LLMProvider
    from sentinel.brain.graph import BrainGraph
    from sentinel.core.event_stream import EventStream
    from sentinel.models.events import Event


class ProfileBuilder:
    def __init__(self, llm_provider: LLMProvider, cache: ResponseCache) -> None:
        self.llm = llm_provider
        self.cache = cache

    async def build_profile(
        self, account_id: str, event_stream: EventStream, graph: BrainGraph
    ) -> AccountProfile:
        """Create a minimal profile for an unknown account."""
        return AccountProfile(account_id=account_id)

    async def generate_summary(self, profile: AccountProfile) -> str:
        """Generate an LLM-written narrative summary using the spec prompt."""
        baseline = profile.baseline

        prompt = PROFILE_GENERATION_PROMPT.format(
            account_id=profile.account_id,
            name=profile.name,
            age=profile.age or "unknown",
            location=profile.location or "unknown",
            account_created=profile.account_created or "unknown",
            avg_amount=baseline.avg_amount if baseline else 0.0,
            std_amount=baseline.std_amount if baseline else 0.0,
            avg_daily_frequency=baseline.avg_daily_frequency if baseline else 0.0,
            typical_hours=baseline.typical_hours if baseline else [],
            typical_merchants=(
                list(baseline.typical_merchants.keys())[:5] if baseline else []
            ),
            typical_channels=(
                list(baseline.typical_channels.keys()) if baseline else []
            ),
            devices=profile.devices,
            known_payees=profile.known_payees,
            balance_check_frequency_daily=(
                baseline.balance_check_frequency_daily if baseline else 0.0
            ),
        )

        system = "You are a banking analyst summarizing customer profiles."
        return await self.llm.complete(system, prompt, cache=self.cache)

    async def generate_fingerprint(
        self, profile: AccountProfile, support_events: list[Event]
    ) -> CommunicationFingerprint:
        """Generate communication fingerprint from support chat history."""
        if not support_events:
            return CommunicationFingerprint()

        interactions_text = "\n\n".join(
            f"[{e.timestamp.isoformat()}] {e.payload.get('content', '(no content)')}"
            for e in support_events
        )

        prompt = COMMUNICATION_FINGERPRINT_PROMPT.format(
            name=profile.name,
            age=profile.age or "unknown",
            interactions_text=interactions_text,
        )

        system = "You are a behavioral analyst creating communication profiles."
        result = await self.llm.complete(system, prompt, cache=self.cache)

        avg_words = 0
        if support_events:
            total_words = sum(
                len(e.payload.get("content", "").split())
                for e in support_events
            )
            avg_words = total_words // len(support_events)

        sample_phrases = []
        for e in support_events[:3]:
            content = e.payload.get("content", "")
            if content:
                sample_phrases.append(content[:100])

        channels_used = list({
            e.payload.get("channel", "chat") for e in support_events
        })

        return CommunicationFingerprint(
            typical_vocabulary_level=self._extract_field(result, "vocabulary", "simple"),
            typical_tone=self._extract_field(result, "tone", "polite"),
            typical_topics=self._extract_list(result, "topics"),
            avg_message_length_words=avg_words,
            uses_technical_banking_terms="technical" in result.lower(),
            typical_channels=channels_used,
            baseline_sentiment=self._extract_field(result, "sentiment", "neutral"),
            sample_phrases=sample_phrases,
        )

    @staticmethod
    def _extract_field(text: str, field: str, default: str) -> str:
        text_lower = text.lower()
        if field == "vocabulary":
            for level in ("technical", "moderate", "simple"):
                if level in text_lower:
                    return level
        elif field == "tone":
            for tone in ("formal", "terse", "anxious", "polite", "neutral"):
                if tone in text_lower:
                    return tone
        elif field == "sentiment":
            for s in ("positive", "anxious", "frustrated", "neutral"):
                if s in text_lower:
                    return s
        return default

    @staticmethod
    def _extract_list(text: str, field: str) -> list[str]:
        try:
            data = json.loads(text)
            if isinstance(data, dict) and field in data:
                return data[field]
        except (json.JSONDecodeError, TypeError):
            pass
        return []
