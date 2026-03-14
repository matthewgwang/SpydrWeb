"""In-memory account profile store."""

from __future__ import annotations

from sentinel.models.account import AccountProfile


class AccountStore:
    """Simple dict-backed store. Replace with a DB adapter later if needed."""

    def __init__(self) -> None:
        self._profiles: dict[str, AccountProfile] = {}

    def get_profile(self, account_id: str) -> AccountProfile | None:
        return self._profiles.get(account_id)

    def save_profile(self, profile: AccountProfile) -> None:
        self._profiles[profile.account_id] = profile

    def get_all_profiles(self) -> list[AccountProfile]:
        return list(self._profiles.values())

    def create_from_persona(self, persona: dict) -> AccountProfile:
        profile = AccountProfile(
            account_id=persona["account_id"],
            name=persona.get("name", ""),
            age=persona.get("age"),
            location=persona.get("location"),
            account_type=persona.get("account_type", "retail"),
            devices=persona.get("behavior", {}).get("devices", []),
            known_payees=persona.get("behavior", {}).get("known_payees", []),
        )
        self.save_profile(profile)
        return profile
