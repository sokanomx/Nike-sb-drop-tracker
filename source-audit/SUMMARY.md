# Audit snapshot — 2026-09-23

The live tracker remains unchanged at 11 stores. This audit is a staging queue.

## First verified URL batch

- 55 candidate storefronts tested
- 36 currently show products matching the tracker scope
  - 7 are already active
  - 29 are verified Shopify expansion candidates
- 2 show Nike SB merchandise but no current Dunk/apparel target
- 4 are present on Nike's 2026 regional lists but show no current Nike SB catalog
- 8 have a live Shopify feed but no current evidence of Nike SB
- 3 require a non-Shopify/custom adapter review
- 2 require manual website review
- 0 have yet been conclusively labeled closed or unsuitable

The exact results and live product counts are in `coverage.csv`.

## Verified Shopify expansion candidates with current target products

303 Boards; 35th North; Andrew; Apple Valley Emporium; Arts & Rec; Blacklist;
Brooklyn Projects; Deli; DLX; Embassy; FTC; Furnace; Geometric; Holistic;
Innercity; Labor; Magnolia; Olympia; Southside; Stardust; Time Machine; Travel;
Underground; Venue; Mainland Skate & Surf; Undefeated; People Skate and
Snowboard; Ninetimes Skateshop; and The Room Surf and Skate Shop.

The last five came from the user's September 2026 list. Ninetimes is Canadian
and remains outside the US activation scope unless that scope is expanded.

These are not active yet. They still need a small-batch rollout and silent seed.

## Custom-adapter/manual review queue

- By and By — storefront feed returned HTTP 401
- Crushed — no Shopify feed at the tested endpoint
- Slappy's Garage — no Shopify feed at the tested endpoint
- Filter — hostname did not resolve during the audit
- Lead — endpoint did not return usable JSON

## Official-name discovery backlog

`official-name-backlog.csv` contains 183 regional entries transcribed from Nike's
2026 East, Central, and West launch lists. Branch locations are intentionally
preserved. The next pass resolves official websites, normalizes multi-location
retailers to hostnames, and removes overlaps with the 50-site verified batch.
