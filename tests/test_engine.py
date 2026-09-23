import unittest
from decimal import Decimal
from unittest.mock import patch

from tracker.config import Config
from tracker.engine import scan_store, update_state
from tracker.models import Product, Store, Variant


CONFIG = Config(8, 4, 250, 5, ("11",), ("L",), ("33", "34"), "America/Los_Angeles", 0, 9)
STORE = Store("Example", "https://example.com", True)


def item(available=True):
    return Product("p1", "Nike SB Dunk Low Pro", "https://example.com/products/p1", None, "Shoes", "Nike SB", (), (Variant("v11", "11", available, Decimal("125.00")),))


class EngineTests(unittest.TestCase):
    @patch("tracker.engine.fetch_products", return_value=[item(True)])
    def test_first_scan_silently_seeds(self, _fetch):
        result = scan_store(STORE, CONFIG, None, seed=False)
        self.assertEqual(result.matches, [])
        self.assertEqual(result.snapshot, {"p1": {"v11": True}})

    @patch("tracker.engine.fetch_products", return_value=[item(True)])
    def test_new_listing_alerts_after_seed(self, _fetch):
        result = scan_store(STORE, CONFIG, {"seeded": True, "products": {}}, seed=False)
        self.assertEqual([match.reason for match in result.matches], ["new listing"])

    @patch("tracker.engine.fetch_products", return_value=[item(True)])
    def test_size_restock_alerts(self, _fetch):
        previous = {"seeded": True, "products": {"p1": {"v11": False}}}
        result = scan_store(STORE, CONFIG, previous, seed=False)
        self.assertEqual([match.reason for match in result.matches], ["target-size restock"])

    @patch("tracker.engine.fetch_products", return_value=[item(True)])
    def test_no_repeat_alert_while_size_stays_available(self, _fetch):
        previous = {"seeded": True, "products": {"p1": {"v11": True}}}
        result = scan_store(STORE, CONFIG, previous, seed=False)
        self.assertEqual(result.matches, [])

    @patch("tracker.engine.fetch_products", side_effect=TimeoutError("slow"))
    def test_failed_store_does_not_replace_snapshot(self, _fetch):
        state = {"stores": {"example.com": {"seeded": True, "products": {"old": {"v": True}}}}}
        result = scan_store(STORE, CONFIG, state["stores"]["example.com"], seed=False)
        update_state(state, [result])
        self.assertIn("old", state["stores"]["example.com"]["products"])


if __name__ == "__main__":
    unittest.main()

