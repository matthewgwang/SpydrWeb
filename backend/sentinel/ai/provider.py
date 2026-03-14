"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Every LLM backend (GPT-OSS, mock, etc.) implements this."""

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        cache=None,
    ) -> str:
        ...

    @abstractmethod
    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        cache=None,
    ) -> dict:
        ...

    @abstractmethod
    async def complete_with_tools(
        self,
        messages: list,
        tools: list,
        temperature: float = 0.3,
    ) -> dict:
        ...
