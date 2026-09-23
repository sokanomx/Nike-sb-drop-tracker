from __future__ import annotations

import csv
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracker.config import load_config
from tracker.filters import category
from tracker.models import Store
from tracker.shopify import fetch_products


INPUT = ROOT / "source-audit" / "classified.csv"
OUTPUT = ROOT / "source-audit" / "coverage.csv"
NIKE_SB = re.compile(r"\bnike\s*(?:sb|skateboarding)\b", re.IGNORECASE)


def inspect(row: dict[str, str], config) -> dict[str, str]:
    result = dict(row)
    if row["platform"] != "shopify":
        result.update(catalog_products="", nike_sb_products="", target_products="", coverage_status="not_applicable")
        return result
    try:
        store = Store(row["name"], row["canonical_url"] or row["url"])
        products = fetch_products(
            store,
            timeout=config.request_timeout_seconds,
            page_size=config.shopify_page_size,
            max_pages=config.shopify_max_pages,
        )
        nike_sb_count = sum(
            bool(NIKE_SB.search(" ".join((item.title, item.vendor, item.product_type, *item.tags))))
            for item in products
        )
        target_count = sum(category(item) is not None for item in products)
        if target_count:
            coverage = "target_products_found"
        elif nike_sb_count:
            coverage = "nike_sb_found_no_current_targets"
        elif row["official_nike_2026_match"].lower() == "true":
            coverage = "official_shop_no_current_nike_sb_catalog"
        else:
            coverage = "no_nike_sb_evidence_manual_review"
        result.update(
            catalog_products=str(len(products)),
            nike_sb_products=str(nike_sb_count),
            target_products=str(target_count),
            coverage_status=coverage,
        )
    except Exception as exc:
        result.update(
            catalog_products="",
            nike_sb_products="",
            target_products="",
            coverage_status=f"scan_error:{type(exc).__name__}",
        )
    return result


def main() -> None:
    config = load_config()
    with INPUT.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    output: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(inspect, row, config): row for row in rows}
        for future in as_completed(futures):
            output.append(future.result())
    output.sort(key=lambda row: (row["coverage_status"], row["state"], row["name"].casefold()))
    fields = list(rows[0]) + ["catalog_products", "nike_sb_products", "target_products", "coverage_status"]
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    counts: dict[str, int] = {}
    for row in output:
        counts[row["coverage_status"]] = counts.get(row["coverage_status"], 0) + 1
    for key, value in sorted(counts.items()):
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
