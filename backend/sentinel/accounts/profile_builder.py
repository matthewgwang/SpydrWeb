"""Profile builder — uses LLM to generate narrative profile summaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
        """Generate an LLM-written narrative summary for a profile."""
        prompt = (
            f"Write a 2-3 sentence summary of this banking customer:\n"
            f"Name: {profile.name}, Age: {profile.age}, "
            f"Location: {profile.location}, Type: {profile.account_type}"
        )
        return await self.llm.complete(
            "You are a banking analyst summarizing customer profiles.",
            prompt,
            cache=self.cache,
        )

    async def generate_fingerprint(
        self, profile: AccountProfile, support_events: list[Event]
    ) -> CommunicationFingerprint:
        """Generate communication fingerprint from support chat history.

        Placeholder — returns defaults. Will be fully implemented in Phase 1.
        """
        return CommunicationFingerprint()
