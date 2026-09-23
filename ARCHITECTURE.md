# Architecture

## Data flow

1. GitHub Actions starts the poller about every five minutes.
2. Store scans run concurrently, with short timeouts and bounded retries.
3. Each Shopify `/products.json` catalog is normalized into products and variants.
4. Independent filters classify Nike SB Dunk Low/High shoes and Nike SB apparel.
5. Only target variants are compared with the committed `state/seen.json` snapshot.
6. A new in-stock target listing or unavailable-to-available size transition becomes
   a Discord alert.
7. Updated state is committed only after processing. If an alert delivery fails,
   that store's prior state is preserved so the alert can retry.

## Silent seeding

Seeding is per hostname. A store with no successful prior snapshot records its
current target inventory without alerting. Consequently, adding a new retailer
later cannot turn its historical catalog into an alert flood.

## State model

The state file stores only:

- whether each normalized store hostname has been seeded;
- target product IDs;
- target variant IDs and their last known availability; and
- the local date of the last weekly recap.

Unavailable products remain represented while they are still returned by the
store. If a product disappears and later returns, it is treated as a new listing.
Failed store scans never replace a previously good snapshot.

## Alert channels

Discord is immediate. Each message includes retailer, local status, reason, link,
image when present, target size, and price.

The email job performs a fresh inventory scan on Monday around 9:00 AM Pacific.
It lists only target sizes available at that moment. Two UTC schedules account
for daylight-saving time; a local-time and last-sent guard prevent duplicates.

## Source strategy

Version 1 uses individually verified Shopify feeds. Non-Shopify retailers require
site-specific adapters and are deferred. eBay will be a separate future adapter
with its own saved searches and state, supporting model, size, price, condition,
and Authenticity Guarantee criteria.

## Failure containment

- A slow or broken retailer cannot stop other retailers.
- HTTP 429 responses get short bounded retries; no endless retry loop is used.
- A failed Discord delivery preserves that retailer's old snapshot.
- A digest is not marked sent unless SMTP succeeds.
- Workflows share one concurrency group to avoid state-write races.
- Credentials exist only as encrypted GitHub Actions secrets.

