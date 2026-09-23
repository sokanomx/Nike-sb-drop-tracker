from __future__ import annotations

import argparse
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import load_config, load_stores
from .engine import scan_all, update_state
from .notifications import required_env, send_digest, send_discord, send_discord_test
from .state import load_state, save_state


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Nike SB notification-only tracker")
    value.add_argument("command", choices=("seed", "poll", "digest", "test-discord"))
    value.add_argument("--dry-run", action="store_true", help="Fetch and report without notifications or state changes")
    value.add_argument("--force", action="store_true", help="Bypass the weekly digest time guard")
    return value


def _log_results(results) -> None:
    for result in results:
        if result.error:
            print(f"ERROR {result.store.name}: {result.error}")
        else:
            print(f"OK {result.store.name}: {len(result.snapshot)} tracked products, {len(result.matches)} alerts")


def _current_inventory(config, stores):
    # An intentionally empty, already-seeded snapshot makes every currently
    # available target product appear as a match without changing real state.
    inventory_state = {
        "stores": {
            store.url.lower().removeprefix("https://").removeprefix("http://").rstrip("/"): {
                "seeded": True,
                "products": {},
            }
            for store in stores
        }
    }
    results = scan_all(stores, config, inventory_state)
    for result in results:
        if result.error:
            print(f"ERROR {result.store.name}: {result.error}")
    return (
        [match for result in results if not result.error for match in result.matches],
        sum(1 for result in results if result.error),
    )


def main() -> int:
    args = parser().parse_args()
    if args.command == "test-discord":
        if args.dry_run:
            print("DRY RUN: Discord test suppressed")
            return 0
        send_discord_test(required_env("DISCORD_WEBHOOK_URL"))
        print("Discord test sent")
        return 0

    config = load_config()
    stores = load_stores()
    if not stores:
        print("No enabled stores are configured", file=sys.stderr)
        return 2
    state = load_state()

    if args.command in ("seed", "poll"):
        results = scan_all(stores, config, state, seed=args.command == "seed")
        _log_results(results)
        successful = [result for result in results if not result.error]
        if not successful:
            print("Every store failed; state was not changed", file=sys.stderr)
            return 1
        if args.command == "poll" and not args.dry_run:
            webhook = required_env("DISCORD_WEBHOOK_URL")
            delivery_failed_for: set[str] = set()
            for result in successful:
                for match in result.matches:
                    try:
                        send_discord(match, webhook)
                    except Exception as exc:
                        print(f"ALERT ERROR {match.store.name} {match.product.title}: {exc}", file=sys.stderr)
                        delivery_failed_for.add(result.store.url)
            successful = [result for result in successful if result.store.url not in delivery_failed_for]
            if delivery_failed_for:
                print("State was preserved for stores with failed alerts so delivery can retry", file=sys.stderr)
        if not args.dry_run:
            update_state(state, successful)
            save_state(state)
        return 1 if args.command == "poll" and not args.dry_run and delivery_failed_for else 0

    now = datetime.now(ZoneInfo(config.timezone))
    due = now.weekday() == config.weekly_digest_weekday and now.hour == config.weekly_digest_hour
    if not args.force and not due:
        print(f"Digest guard: not due at {now.isoformat()}")
        return 0
    local_date = now.date().isoformat()
    if not args.force and state.get("last_digest_local_date") == local_date:
        print("Digest guard: already sent today")
        return 0
    matches, failures = _current_inventory(config, stores)
    if failures == len(stores):
        print("Every store failed; digest was not sent", file=sys.stderr)
        return 1
    print(f"Digest contains {len(matches)} currently available products; {failures} stores failed")
    if not args.dry_run:
        send_digest(
            matches,
            sender=required_env("GMAIL_ADDRESS"),
            password=required_env("GMAIL_APP_PASSWORD"),
            recipient=required_env("DIGEST_TO"),
        )
        state["last_digest_local_date"] = local_date
        save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
