from __future__ import annotations

import time
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode, urljoin

import requests

from .models import Product, Store, Variant


# A normal browser signature avoids Shopify storefront bot filters that reject
# custom/non-browser agents even though the product feed itself is public.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _money(value: object) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return Decimal("0")


def _product_from_json(store: Store, raw: dict) -> Product:
    handle = str(raw.get("handle", "")).strip()
    product_url = urljoin(store.url.rstrip("/") + "/", f"products/{handle}")
    image = raw.get("image") or {}
    image_url = image.get("src") if isinstance(image, dict) else None
    variants = tuple(
        Variant(
            id=str(item.get("id", item.get("title", "unknown"))),
            title=str(item.get("title", "")).strip(),
            available=bool(item.get("available", False)),
            price=_money(item.get("price", "0")),
        )
        for item in raw.get("variants", [])
    )
    tags_value = raw.get("tags", [])
    if isinstance(tags_value, str):
        tags = tuple(part.strip() for part in tags_value.split(",") if part.strip())
    else:
        tags = tuple(str(part) for part in tags_value)
    return Product(
        id=str(raw.get("id", product_url)),
        title=str(raw.get("title", "Untitled product")).strip(),
        url=product_url,
        image_url=image_url,
        product_type=str(raw.get("product_type", "")).strip(),
        vendor=str(raw.get("vendor", "")).strip(),
        tags=tags,
        variants=variants,
    )


def _retry_delay(response: requests.Response, attempt: int) -> float:
    value = response.headers.get("Retry-After", "")
    if value.isdigit():
        return min(float(value), 8.0)
    if value:
        try:
            return max(0.5, min((parsedate_to_datetime(value).timestamp() - time.time()), 8.0))
        except (TypeError, ValueError, OverflowError):
            pass
    return 1.5 * (attempt + 1)


def _load_json(session: requests.Session, url: str, timeout: float) -> dict:
    for attempt in range(3):
        response = session.get(url, timeout=timeout)
        if response.status_code != 429:
            response.raise_for_status()
            return response.json()
        if attempt == 2:
            response.raise_for_status()
        time.sleep(_retry_delay(response, attempt))
    raise RuntimeError("Unreachable retry state")


def fetch_products(store: Store, *, timeout: float, page_size: int, max_pages: int) -> list[Product]:
    products: list[Product] = []
    endpoint = urljoin(store.url.rstrip("/") + "/", "products.json")
    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
        for page in range(1, max_pages + 1):
            url = f"{endpoint}?{urlencode({'limit': page_size, 'page': page})}"
            payload = _load_json(session, url, timeout)
            batch = payload.get("products")
            if not isinstance(batch, list):
                raise ValueError("Shopify response did not contain a products list")
            products.extend(_product_from_json(store, item) for item in batch)
            if len(batch) < page_size:
                break
            time.sleep(0.2)
    return products
