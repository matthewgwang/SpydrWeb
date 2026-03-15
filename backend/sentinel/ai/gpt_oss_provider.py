"""GPT-OSS 120B implementation — OpenAI-compatible client."""

from __future__ import annotations

import hashlib
import json

from openai import AsyncOpenAI

from sentinel.ai.cache import ResponseCache
from sentinel.ai.provider import LLMProvider
from sentinel.config import settings


class GPTOSSProvider(LLMProvider):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        cache: ResponseCache | None = None,
    ) -> str:
        if cache:
            cache_key = hashlib.md5(
                (system_prompt + user_prompt).encode()
            ).hexdigest()
            cached = cache.get(cache_key)
            if cached:
                return cached

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4096,
                temperature=temperature,
            )
            result = resp.choices[0].message.content

            if cache:
                cache.set(cache_key, result)

            return result

        except Exception as e:
            return f"[LLM unavailable: {e}. Using fallback response.]"

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        cache: ResponseCache | None = None,
    ) -> dict:
        result = await self.complete(system_prompt, user_prompt, cache=cache)

        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]

        try:
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response", "raw": result}

    async def complete_with_tools(
        self,
        messages: list,
        tools: list,
        temperature: float = 0.3,
    ) -> dict:
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=4096,
            )
            choice = resp.choices[0]
            return {
                "content": choice.message.content,
                "tool_calls": choice.message.tool_calls,
                "has_tool_calls": choice.message.tool_calls is not None,
            }
        except Exception as e:
            return {
                "content": f"[LLM unavailable: {e}]",
                "tool_calls": None,
                "has_tool_calls": False,
            }
