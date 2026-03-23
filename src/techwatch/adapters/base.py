"""Base adapter interface and shared infrastructure for source fetchers."""

from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import httpx

from techwatch.config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket rate limiter with burst support."""

    def __init__(self, max_qps: float = 5.0, burst: int = 10) -> None:
        self.max_qps = max_qps
        self.burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()

    def acquire(self) -> None:
        """Block until a token is available."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.burst, self._tokens + elapsed * self.max_qps)
        self._last_refill = now

        if self._tokens < 1.0:
            wait = (1.0 - self._tokens) / self.max_qps
            logger.debug("Rate limiter: sleeping %.2fs", wait)
            time.sleep(wait)
            self._tokens = 0.0
            self._last_refill = time.monotonic()
        else:
            self._tokens -= 1.0


class RetryPolicy:
    """Jittered exponential backoff retry configuration."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: float = 0.5,
        retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504),
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.retryable_status_codes = retryable_status_codes

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number (0-indexed)."""
        delay = min(self.base_delay * (2**attempt), self.max_delay)
        jitter_amount = delay * self.jitter * random.random()
        return delay + jitter_amount


class ResponseCache:
    """Simple file-based response cache."""

    def __init__(self, cache_dir: Path, ttl: int = 300) -> None:
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, url: str, params: dict[str, Any] | None = None) -> str:
        raw = url + json.dumps(params or {}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, url: str, params: dict[str, Any] | None = None) -> Optional[dict]:
        """Return cached response if fresh, else None."""
        key = self._key(url, params)
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            return None

        data = json.loads(path.read_text())
        cached_at = datetime.fromisoformat(data["_cached_at"])
        if datetime.utcnow() - cached_at > timedelta(seconds=self.ttl):
            path.unlink(missing_ok=True)
            return None

        return data.get("response")

    def put(
        self, url: str, params: dict[str, Any] | None, response: dict
    ) -> None:
        """Store a response in the cache."""
        key = self._key(url, params)
        path = self.cache_dir / f"{key}.json"
        data = {
            "_cached_at": datetime.utcnow().isoformat(),
            "_url": url,
            "response": response,
        }
        path.write_text(json.dumps(data))


# ── Domain allowlist ────────────────────────────────────────────────

ALLOWED_DOMAINS = frozenset({
    "api.bestbuy.com",
    "api.ebay.com",
    "api.sandbox.ebay.com",
    "open.er-api.com",
    "www.ecb.europa.eu",
    "sdw-wsrest.ecb.europa.eu",
})


def check_domain_allowlist(url: str) -> bool:
    """Verify that a URL targets an allowed domain."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return parsed.hostname in ALLOWED_DOMAINS


# ── Base adapter ────────────────────────────────────────────────────


class BaseAdapter(ABC):
    """Abstract base for all source adapters.

    Subclasses implement ``fetch_raw()`` to return source-native data.
    The base class provides rate limiting, retry, caching, and logging.
    """

    source_name: str = "unknown"
    max_qps: float = 5.0
    burst: int = 10
    cache_ttl: int = 300

    def __init__(self) -> None:
        settings = get_settings()
        self._rate_limiter = RateLimiter(self.max_qps, self.burst)
        self._retry_policy = RetryPolicy(max_retries=settings.default_max_retries)
        self._cache = ResponseCache(
            cache_dir=settings.get_cache_dir() / self.source_name,
            ttl=self.cache_ttl,
        )
        self._client = httpx.Client(
            timeout=httpx.Timeout(settings.default_timeout),
            follow_redirects=True,
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        use_cache: bool = True,
        check_allowlist: bool = True,
    ) -> dict[str, Any]:
        """Make an HTTP request with rate limiting, retry, and caching."""
        if check_allowlist and not check_domain_allowlist(url):
            raise ValueError(f"Domain not in allowlist: {url}")

        # Check cache
        if use_cache and method.upper() == "GET":
            cached = self._cache.get(url, params)
            if cached is not None:
                logger.debug("[%s] Cache hit: %s", self.source_name, url)
                return cached

        # Rate limit
        self._rate_limiter.acquire()

        # Retry loop
        last_error: Exception | None = None
        for attempt in range(self._retry_policy.max_retries + 1):
            try:
                response = self._client.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    json=json_body,
                )

                if response.status_code in self._retry_policy.retryable_status_codes:
                    delay = self._retry_policy.get_delay(attempt)
                    logger.warning(
                        "[%s] Retryable %d from %s (attempt %d, wait %.1fs)",
                        self.source_name,
                        response.status_code,
                        url,
                        attempt + 1,
                        delay,
                    )
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                data = response.json()

                # Cache successful GET responses
                if use_cache and method.upper() == "GET":
                    self._cache.put(url, params, data)

                return data

            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code not in self._retry_policy.retryable_status_codes:
                    raise
            except httpx.TransportError as exc:
                last_error = exc
                if attempt < self._retry_policy.max_retries:
                    delay = self._retry_policy.get_delay(attempt)
                    logger.warning(
                        "[%s] Transport error: %s (attempt %d, wait %.1fs)",
                        self.source_name,
                        exc,
                        attempt + 1,
                        delay,
                    )
                    time.sleep(delay)

        raise RuntimeError(
            f"[{self.source_name}] Exhausted {self._retry_policy.max_retries} retries for {url}"
        ) from last_error

    @abstractmethod
    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch raw source data. Subclasses must implement."""
        ...

    def close(self) -> None:
        """Clean up HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
