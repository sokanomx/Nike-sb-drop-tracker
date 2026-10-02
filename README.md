# Nike SB Drop Tracker

A notification-only tracker for Nike SB Dunk Low/High releases plus sale-priced
Nike SB apparel and accessories. It polls verified Shopify storefronts, sends
immediate size-11 Dunk Discord alerts, and emails a Monday sale recap.

The tracker never logs in to a store, adds products to a cart, or purchases
anything.

## What it watches

- Nike SB Dunk Low and Dunk High shoes in US men's size 11
- Nike SB apparel on sale in Large/Large Tall tops and waist 33–34 bottoms
- All available Nike SB accessories on sale
- Brand-new size-11 Dunk listings and size-specific restocks
- Nationwide shops, with Bay Area retailers marked `LOCAL`

Each newly configured store is silently seeded on its first successful scan.
Existing inventory is saved without generating alerts.

## Repository secrets

Add these at **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
| --- | --- |
| `DISCORD_WEBHOOK_URL` | Dedicated Discord alerts-channel webhook |
| `GMAIL_ADDRESS` | Gmail account that sends the weekly recap |
| `GMAIL_APP_PASSWORD` | Gmail App Password, not the normal password |
| `DIGEST_TO` | Recipient for the recap |

No secret belongs in `config.json`, `stores.json`, or any committed file.

## First-time setup

1. Create a public GitHub repository and copy this folder into it.
2. Add the four repository secrets above.
3. Keep the initial store list small until every feed is verified.
4. Run **Actions → Nike SB Tracker → Run workflow → seed**. This records the
   current inventory and sends nothing.
5. Run the workflow once more with **test-discord**. It sends one clearly
   labeled test message.
6. Run **poll** manually and inspect the log. No existing item should alert.
7. Leave the workflows enabled. Polling is scheduled about every five minutes;
   GitHub may occasionally start a scheduled run late.

Full-price shoes remain eligible for immediate Discord alerts. Apparel and
accessories never generate Discord alerts and appear only in the weekly email
when Shopify reports a genuine markdown (regular price above current price).

The Monday recap workflow evaluates Pacific time at runtime. It has two UTC
schedules so it continues to land near 9:00 AM through daylight-saving changes,
and a state guard prevents duplicate sends.

## Local commands

```bash
python -m pip install -r requirements.txt
python -m tracker.cli seed
python -m tracker.cli poll --dry-run
python -m tracker.cli digest --dry-run --force
python -m tracker.cli test-discord
python -m unittest discover -s tests
```

## Store-list rules

Only add a Shopify shop after confirming that
`https://STORE/products.json?limit=1` returns a valid product payload. Deduplicate
by normalized hostname. Set `local` to `true` for the agreed Bay Area region.
Non-Shopify sources and eBay are intentionally deferred; they will use separate
adapters and separate state.
