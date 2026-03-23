"""ECB exchange rate adapter and currency converter."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Optional

from techwatch.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

ECB_DAILY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_NS = {"gesmes": "http://www.gesmes.org/xml/2002-08-01", "ecb": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}


class EcbRatesAdapter(BaseAdapter):
    """Fetch reference exchange rates from the European Central Bank."""

    source_name = "ecb_fx"
    max_qps = 1.0
    burst = 2
    cache_ttl = 3600  # Rates update once daily

    def _parse_rates(self, xml_text: str) -> dict[str, float]:
        """Parse ECB XML into currency -> EUR rate mapping."""
        root = ET.fromstring(xml_text)
        rates: dict[str, float] = {"EUR": 1.0}

        for cube in root.iter():
            if cube.tag.endswith("Cube") and "currency" in cube.attrib:
                currency = cube.attrib["currency"]
                rate = float(cube.attrib["rate"])
                rates[currency] = rate

        return rates

    def get_rates(self) -> dict[str, float]:
        """Fetch current ECB reference rates.

        Returns a dict mapping currency codes to their EUR exchange rate.
        """
        self._rate_limiter.acquire()
        response = self._client.get(ECB_DAILY_URL)
        response.raise_for_status()
        return self._parse_rates(response.text)

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch raw rate data."""
        rates = self.get_rates()
        return [{"rates": rates, "fetched_at": datetime.utcnow().isoformat()}]


class CurrencyConverter:
    """Convert between currencies using ECB reference rates.

    Conservative approach: preserve original amounts, provide converted
    convenience values, and clearly mark when conversion is unavailable.
    """

    def __init__(self, rates: dict[str, float] | None = None) -> None:
        self._rates = rates or {}
        self._fetched_at: Optional[datetime] = None

    def load_rates(self, adapter: EcbRatesAdapter) -> None:
        """Load fresh rates from the ECB adapter."""
        self._rates = adapter.get_rates()
        self._fetched_at = datetime.utcnow()

    @property
    def is_loaded(self) -> bool:
        return bool(self._rates)

    @property
    def fetched_at(self) -> Optional[datetime]:
        return self._fetched_at

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> Optional[float]:
        """Convert an amount between currencies.

        Returns None if conversion is not possible (missing rate).
        Never fabricates precision — returns None rather than guessing.
        """
        if from_currency == to_currency:
            return amount

        from_rate = self._rates.get(from_currency.upper())
        to_rate = self._rates.get(to_currency.upper())

        if from_rate is None or to_rate is None:
            logger.warning(
                "Cannot convert %s -> %s: missing rate(s)",
                from_currency,
                to_currency,
            )
            return None

        # Convert via EUR as base
        eur_amount = amount / from_rate
        return round(eur_amount * to_rate, 2)

    def get_supported_currencies(self) -> list[str]:
        """Return list of currencies with available rates."""
        return sorted(self._rates.keys())
