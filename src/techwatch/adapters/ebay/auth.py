"""eBay OAuth2 token management."""

from __future__ import annotations

import base64
import logging
import time
from typing import Optional

import httpx

from techwatch.config import get_settings

logger = logging.getLogger(__name__)

EBAY_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_AUTH_SANDBOX_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"


class EbayAuth:
    """Manages eBay OAuth2 client credentials flow.

    Caches the access token and automatically refreshes when expired.
    """

    def __init__(self, sandbox: bool = False) -> None:
        settings = get_settings()
        self._client_id = settings.ebay_client_id.get_secret_value()
        self._client_secret = settings.ebay_client_secret.get_secret_value()
        self._auth_url = EBAY_AUTH_SANDBOX_URL if sandbox else EBAY_AUTH_URL
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0
        self._client = httpx.Client(timeout=httpx.Timeout(30.0))

    def _get_basic_auth(self) -> str:
        credentials = f"{self._client_id}:{self._client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    def get_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        if self._access_token and time.time() < self._token_expiry - 60:
            return self._access_token

        logger.debug("Refreshing eBay OAuth token")
        response = self._client.post(
            self._auth_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {self._get_basic_auth()}",
            },
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
        )
        response.raise_for_status()
        data = response.json()

        self._access_token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 7200)
        logger.debug("eBay token refreshed, expires in %ds", data.get("expires_in", 0))
        return self._access_token

    def close(self) -> None:
        self._client.close()
