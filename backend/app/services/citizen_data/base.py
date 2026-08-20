from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DerivedCitizenAttributes:
    """Prefer derived attributes over raw identity documents — never store
    raw Aadhaar numbers, document images, etc. in the profile."""

    age_range: str | None = None
    income_range: str | None = None
    state: str | None = None
    occupation_category: str | None = None
    extra: dict | None = None


class CitizenDataProvider(ABC):
    @abstractmethod
    async def get_authorization_url(self, state: str) -> str: ...

    @abstractmethod
    async def exchange_code_for_profile(self, code: str) -> DerivedCitizenAttributes: ...
