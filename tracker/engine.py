from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import Config
from .filters import category, target_variants
from .models import Match, ScanResult, Store
from .shopify import fetch_products


def _store_key(store: Store) -> str:
    return store.url.lower().removeprefix("https://").removeprefix("http://").rstrip("/")


def scan_store(store: Store, config: Config, previous: dict | None, *, seed: bool) -> ScanResult:
    result = ScanResult(store=store)
    try:
        products = fetch_products(
            store,
            timeout=config.request_timeout_seconds,
            page_size=config.shopify_page_size,
            max_pages=config.shopify_max_pages,
        )
        previous_products = (previous or {}).get("products", {})
        already_seeded = bool((previous or {}).get("seeded", False))

        for product in products:
            product_category = category(product)
            if product_category is None:
                continue
            targets = target_variants(product, product_category, config)
            if not targets:
                continue
            current = {variant.id: variant.available for variant in targets}
            result.snapshot[product.id] = current

            if seed or not already_seeded:
                continue
            available = tuple(variant for variant in targets if variant.available)
            if not available:
                continue
            prior = previous_products.get(product.id)
            if prior is None:
                result.matches.append(Match(store, product, product_category, available, "new listing"))
                continue
            restocked = tuple(
                variant for variant in available if not bool(prior.get(variant.id, False))
            )
            if restocked:
                result.matches.append(Match(store, product, product_category, restocked, "target-size restock"))
    except Exception as exc:  # One broken retailer must not stop the batch.
        result.error = f"{type(exc).__name__}: {exc}"
    return result


def scan_all(stores: list[Store], config: Config, state: dict, *, seed: bool = False) -> list[ScanResult]:
    results: list[ScanResult] = []
    with ThreadPoolExecutor(max_workers=config.max_workers) as pool:
        futures = {
            pool.submit(scan_store, store, config, state["stores"].get(_store_key(store)), seed=seed): store
            for store in stores
        }
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda item: item.store.name.casefold())


def update_state(state: dict, results: list[ScanResult]) -> None:
    for result in results:
        if result.error:
            continue
        state["stores"][_store_key(result.store)] = {
            "name": result.store.name,
            "seeded": True,
            "products": result.snapshot,
        }

