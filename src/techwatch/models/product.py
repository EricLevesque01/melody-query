"""Product domain model — the *what* that is being sold."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class Specs(BaseModel):
    """Hardware / product specifications.

    Uses a flexible dict plus well-known typed fields so adapters can
    pass through arbitrary specs while scoring can access common ones.
    """

    model_config = ConfigDict(extra="allow")

    cpu: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    screen_in: Optional[float] = None
    gpu: Optional[str] = None
    battery_wh: Optional[float] = None
    weight_kg: Optional[float] = None
    resolution: Optional[str] = None
    refresh_rate_hz: Optional[int] = None
    ports: Optional[list[str]] = None


class Product(BaseModel):
    """Canonical product representation.

    ``canonical_product_id`` follows the pattern ``source:marketplace:item_id``
    so every record is traceable back to its origin.
    """

    model_config = ConfigDict(strict=True)

    canonical_product_id: str
    title: str
    brand: Optional[str] = None
    model: Optional[str] = None
    upc_gtin: Optional[str] = None
    canonical_category: str
    source_category_path: list[str] = []
    specs: Specs = Specs()
    images: list[str] = []
    url: Optional[str] = None
    raw_extras: dict[str, Any] = {}
