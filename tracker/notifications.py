from __future__ import annotations

import html
import os
import smtplib
from email.message import EmailMessage

import requests

from .models import Match


def _post_json(url: str, payload: dict) -> None:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()


def _price_text(match: Match) -> str:
    prices = match.prices
    if not prices:
        return "Price unavailable"
    if len(prices) == 1:
        return f"${prices[0]:.2f}"
    return f"${prices[0]:.2f}–${prices[-1]:.2f}"


def send_discord(match: Match, webhook_url: str) -> None:
    local = "📍 LOCAL · " if match.store.local else ""
    sizes = ", ".join(match.available_sizes)
    embed = {
        "title": match.product.title[:256],
        "url": match.product.url,
        "description": f"{local}{match.reason.title()}",
        "color": 0xF97316 if match.store.local else 0x5865F2,
        "fields": [
            {"name": "Store", "value": match.store.name, "inline": True},
            {"name": "Price", "value": _price_text(match), "inline": True},
            {"name": "Target size in stock", "value": sizes or "Unknown", "inline": False},
        ],
    }
    if match.product.image_url:
        embed["thumbnail"] = {"url": match.product.image_url}
    _post_json(webhook_url, {"content": "New Nike SB match detected", "embeds": [embed]})


def send_discord_test(webhook_url: str) -> None:
    _post_json(
        webhook_url,
        {
            "content": "✅ **TEST ONLY — Nike SB Drop Tracker is connected.**",
            "allowed_mentions": {"parse": []},
        },
    )


def digest_html(matches: list[Match]) -> str:
    if not matches:
        return "<h1>Nike SB weekly recap</h1><p>No target-size inventory was available when this recap ran.</p>"
    rows = []
    for match in sorted(matches, key=lambda item: (not item.store.local, item.store.name, item.product.title)):
        local = "📍 LOCAL" if match.store.local else ""
        rows.append(
            "<tr>"
            f"<td>{html.escape(local)}</td>"
            f"<td>{html.escape(match.store.name)}</td>"
            f"<td><a href=\"{html.escape(match.product.url, quote=True)}\">{html.escape(match.product.title)}</a></td>"
            f"<td>{html.escape(', '.join(match.available_sizes))}</td>"
            f"<td>{html.escape(_price_text(match))}</td>"
            "</tr>"
        )
    return (
        "<h1>Nike SB weekly availability recap</h1>"
        "<p>Availability was checked when this message was generated and may change quickly.</p>"
        "<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">"
        "<thead><tr><th></th><th>Store</th><th>Product</th><th>Target size</th><th>Price</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def send_digest(matches: list[Match], *, sender: str, password: str, recipient: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Nike SB weekly size availability recap"
    message["From"] = sender
    message["To"] = recipient
    message.set_content("Your email client must support HTML to view this recap.")
    message.add_alternative(digest_html(matches), subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
        smtp.login(sender, password)
        smtp.send_message(message)


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
