from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import Store


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Config:
    request_timeout_seconds: float
    max_workers: int
    shopify_page_size: int
    shopify_max_pages: int
    shoe_sizes: tuple[str, ...]
    top_sizes: tuple[str, ...]
    bottom_sizes: tuple[str, ...]
    timezone: str
    weekly_digest_weekday: int
    weekly_digest_hour: int


def load_config(path: Path = ROOT / "config.json") -> Config:
    data = json.loads(path.read_text())
    return Config(
        request_timeout_seconds=float(data["request_timeout_seconds"]),
        max_workers=int(data["max_workers"]),
        shopify_page_size=int(data["shopify_page_size"]),
        shopify_max_pages=int(data["shopify_max_pages"]),
        shoe_sizes=tuple(data["shoe_sizes"]),
        top_sizes=tuple(data["top_sizes"]),
        bottom_sizes=tuple(data["bottom_sizes"]),
        timezone=data["timezone"],
        weekly_digest_weekday=int(data["weekly_digest_weekday"]),
        weekly_digest_hour=int(data["weekly_digest_hour"]),
    )


def load_stores(path: Path = ROOT / "stores.json") -> list[Store]:
    data = json.loads(path.read_text())
    stores = [
        Store(name=item["name"], url=item["url"], local=bool(item.get("local", False)))
        for item in data["stores"]
        if item.get("enabled", True)
    ]
    hosts: set[str] = set()
    for store in stores:
        host = store.url.lower().removeprefix("https://").removeprefix("http://").rstrip("/")
        if host in hosts:
            raise ValueError(f"Duplicate store hostname: {host}")
        hosts.add(host)
    return stores
