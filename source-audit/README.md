# Retailer source audit

This folder is a staging area, not the live tracker configuration. Nothing here
generates alerts until a reviewed retailer is deliberately copied to
`stores.json` and silently seeded.

Start with `SUMMARY.md` for the current audit totals. `official-name-backlog.csv`
is the broader name-discovery queue derived from Nike's regional publications.

## Sources and scope

`candidates.csv` begins with a public 2024 list of US Shopify skate shops and
cross-references shop names against Nike's 2026 regional Nike SB launch lists.
It is an expansion seed, not yet a claim that every current Nike SB locator entry
has been captured. The interactive locator could not be exported during this
audit, so the official regional lists are being used as the traceable first-party
baseline while remaining names and websites are researched.

The classifier verifies the live `/products.json?limit=1` response on every URL.
Its generated `classified.csv` uses these queues:

- `active`: already enabled in the tracker;
- `verified_shopify_ready`: live Shopify feed, ready for product-quality review;
- `custom_adapter_review`: not currently exposing a usable Shopify feed;
- `manual_review`: network, certificate, redirect, or parsing issue;
- `unsuitable`: reserved for confirmed closures, duplicates, in-person-only
  stores, or sites with no trackable catalog.

Run the audit with:

```bash
python scripts/audit_shopify.py
python scripts/audit_product_coverage.py
```

`coverage.csv` then scans the full available catalog (up to the configured page
limit) and counts Nike SB products plus products matching the tracker's exact
shoe/apparel scope. A valid Shopify endpoint alone is not enough to activate a
store; product coverage is the second review gate.

Never bulk-copy the ready queue into `stores.json`. Review Nike SB product
coverage first, then add in small batches; per-source silent seeding remains the
final safety boundary.
