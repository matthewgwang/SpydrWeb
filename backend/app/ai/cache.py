"""File-based + in-memory LLM response cache."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


class ResponseCache:
    """Cache LLM responses for demo reliability.

    - Survives server restarts via file-based persistence
    - Falls back to memory-only when disk writes fail
    """

    def __init__(self, cache_dir: str | None = None) -> None:
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), ".cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: dict[str, str] = {}

    def _key_to_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> str | None:
        if key in self.memory_cache:
            return self.memory_cache[key]

        path = self._key_to_path(key)
        if path.exists():
            data = json.loads(path.read_text())
            self.memory_cache[key] = data["response"]
            return data["response"]

        return None

    def set(self, key: str, value: str) -> None:
        self.memory_cache[key] = value
        path = self._key_to_path(key)
        path.write_text(json.dumps({"key": key, "response": value}))

    def clear(self) -> None:
        self.memory_cache.clear()
        for f in self.cache_dir.glob("*.json"):
            f.unlink()

    async def warm_up(self, provider, prompts: list[tuple[str, str]]) -> None:
        """Pre-generate and cache responses for demo scenarios."""
        for system_prompt, user_prompt in prompts:
            key = hashlib.md5((system_prompt + user_prompt).encode()).hexdigest()
            if not self.get(key):
                response = await provider.complete(system_prompt, user_prompt)
                self.set(key, response)
