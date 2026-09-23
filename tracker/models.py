from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Variant:
    id: str
    title: str
    available: bool
    price: Decimal


@dataclass(frozen=True)
class Product:
    id: str
    title: str
    url: str
    image_url: str | None
    product_type: str
    vendor: str
    tags: tuple[str, ...]
    variants: tuple[Variant, ...]


@dataclass(frozen=True)
class Store:
    name: str
    url: str
    local: bool = False


@dataclass(frozen=True)
class Match:
    store: Store
    product: Product
    category: str
    target_variants: tuple[Variant, ...]
    reason: str

    @property
    def prices(self) -> tuple[Decimal, ...]:
        return tuple(sorted({variant.price for variant in self.target_variants}))

    @property
    def available_sizes(self) -> tuple[str, ...]:
        return tuple(variant.title for variant in self.target_variants if variant.available)


@dataclass
class ScanResult:
    store: Store
    matches: list[Match] = field(default_factory=list)
    snapshot: dict[str, dict[str, bool]] = field(default_factory=dict)
    error: str | None = None

