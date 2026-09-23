from __future__ import annotations

import re

from .config import Config
from .models import Product, Variant


NIKE_SB_RE = re.compile(r"\bnike\s*(?:sb|skateboarding)\b", re.IGNORECASE)
DUNK_RE = re.compile(r"\bdunk\b", re.IGNORECASE)
LOW_HIGH_RE = re.compile(r"\b(?:low|high)(?:\s+pro)?\b", re.IGNORECASE)
TOP_RE = re.compile(r"\b(?:tee|t-shirt|shirt|hoodie|sweatshirt|crewneck|jacket|top|jersey|flannel)\b", re.IGNORECASE)
BOTTOM_RE = re.compile(r"\b(?:pant|pants|trouser|chino|jean|short|shorts)\b", re.IGNORECASE)
APPAREL_RE = re.compile(r"\b(?:apparel|clothing|tee|t-shirt|shirt|hoodie|sweatshirt|crewneck|jacket|pant|pants|trouser|chino|jean|short|shorts)\b", re.IGNORECASE)


def _haystack(product: Product) -> str:
    return " ".join((product.title, product.product_type, product.vendor, *product.tags))


def category(product: Product) -> str | None:
    text = _haystack(product)
    is_nike_sb = bool(NIKE_SB_RE.search(text)) or (
        re.search(r"\bnike\b", product.vendor, re.IGNORECASE)
        and re.search(r"\bsb\b", text, re.IGNORECASE)
    )
    if not is_nike_sb:
        return None
    if DUNK_RE.search(text) and LOW_HIGH_RE.search(text) and not APPAREL_RE.search(product.product_type):
        return "shoe"
    if APPAREL_RE.search(text):
        if BOTTOM_RE.search(text):
            return "bottom"
        return "top"
    return None


def _normalized_size(value: str) -> str:
    value = value.upper().strip()
    value = re.sub(r"\b(?:US|MEN'?S|MENS|SIZE)\b", "", value)
    return re.sub(r"[^A-Z0-9.]", "", value)


def target_variants(product: Product, product_category: str, config: Config) -> tuple[Variant, ...]:
    wanted = {
        "shoe": config.shoe_sizes,
        "top": config.top_sizes,
        "bottom": config.bottom_sizes,
    }[product_category]
    normalized_wanted = {_normalized_size(value) for value in wanted}
    return tuple(
        variant
        for variant in product.variants
        if _normalized_size(variant.title) in normalized_wanted
    )

