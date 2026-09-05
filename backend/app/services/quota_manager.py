from __future__ import annotations
from dataclasses import dataclass, asdict
from threading import Lock
from time import time

from app.config import settings

@dataclass
class ProviderUsage:
    requests: int = 0
    failures: int = 0
    fallback_requests: int = 0
    tokens_estimated: int = 0
    last_error: str | None = None
    window_started: float = 0.0

class QuotaManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._usage = {
            "gemini": ProviderUsage(window_started=time()),
            "openai": ProviderUsage(window_started=time()),
            "anthropic": ProviderUsage(window_started=time()),
        }

    def limit(self, provider: str) -> int:
        return int(getattr(settings, f"{provider}_soft_request_limit", 0))

    def can_use(self, provider: str) -> bool:
        with self._lock:
            limit = self.limit(provider)
            return limit <= 0 or self._usage[provider].requests < limit

    def record(self, provider: str, *, success: bool, tokens: int = 0, fallback: bool = False, error: str | None = None) -> None:
        with self._lock:
            usage = self._usage[provider]
            usage.requests += 1
            usage.tokens_estimated += max(0, tokens)
            if not success:
                usage.failures += 1
                usage.last_error = error
            if fallback:
                usage.fallback_requests += 1

    def snapshot(self) -> dict:
        with self._lock:
            result = {}
            for provider, usage in self._usage.items():
                limit = self.limit(provider)
                result[provider] = {
                    **asdict(usage),
                    "soft_limit": limit,
                    "remaining": None if limit <= 0 else max(0, limit - usage.requests),
                }
            return result

quota_manager = QuotaManager()
