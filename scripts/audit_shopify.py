from __future__ import annotations

import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "source-audit" / "candidates.csv"
OUTPUT = ROOT / "source-audit" / "classified.csv"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"


def hostname(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def inspect(row: dict[str, str], active_hosts: set[str]) -> dict[str, str]:
    result = dict(row)
    try:
        response = requests.get(
            row["url"].rstrip("/") + "/products.json?limit=1",
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=12,
            allow_redirects=True,
        )
        result["http_status"] = str(response.status_code)
        result["canonical_url"] = response.url.split("/products.json", 1)[0]
        payload = response.json() if response.ok else None
        shopify = isinstance(payload, dict) and isinstance(payload.get("products"), list)
        result["platform"] = "shopify" if shopify else "non_shopify_or_blocked"
        if shopify and hostname(result["canonical_url"]) in active_hosts:
            result["queue"] = "active"
        elif shopify:
            result["queue"] = "verified_shopify_ready"
        else:
            result["queue"] = "custom_adapter_review"
        result["note"] = ""
    except Exception as exc:
        result.update(
            http_status="",
            canonical_url=row["url"],
            platform="unknown",
            queue="manual_review",
            note=f"{type(exc).__name__}: {str(exc)[:160]}",
        )
    return result


def main() -> None:
    with INPUT.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    stores = json.loads((ROOT / "stores.json").read_text())["stores"]
    active_hosts = {hostname(item["url"]) for item in stores if item.get("enabled", True)}
    output: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(inspect, row, active_hosts): row for row in rows}
        for future in as_completed(futures):
            output.append(future.result())
    output.sort(key=lambda row: (row["queue"], row["state"], row["name"].casefold()))
    fields = list(rows[0]) + ["http_status", "canonical_url", "platform", "queue", "note"]
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    counts: dict[str, int] = {}
    for row in output:
        counts[row["queue"]] = counts.get(row["queue"], 0) + 1
    print(json.dumps({"total": len(output), "queues": counts}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
