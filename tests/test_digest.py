import unittest
from decimal import Decimal

from tracker.cli import _weekly_sale_matches
from tracker.models import Match, Product, Store, Variant


STORE = Store("Example", "https://example.com")


def match(category, *, price="30", regular="45", available=True):
    variant = Variant(
        "v1",
        "Large",
        available,
        Decimal(price),
        Decimal(regular) if regular is not None else None,
    )
    product = Product(
        category,
        f"Nike SB {category}",
        f"https://example.com/{category}",
        None,
        category,
        "Nike SB",
        (),
        (variant,),
    )
    return Match(STORE, product, category, (variant,), "new listing")


class WeeklyDigestTests(unittest.TestCase):
    def test_includes_sale_apparel_and_accessories_only(self):
        matches = [
            match("shoe"),
            match("top"),
            match("bottom", price="45", regular="45"),
            match("accessory"),
        ]
        selected = _weekly_sale_matches(matches)
        self.assertEqual([item.category for item in selected], ["top", "accessory"])
        self.assertTrue(all(item.reason == "currently on sale" for item in selected))


if __name__ == "__main__":
    unittest.main()
