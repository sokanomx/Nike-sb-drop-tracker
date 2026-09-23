import unittest
from decimal import Decimal

from tracker.config import Config
from tracker.filters import category, target_variants
from tracker.models import Product, Variant


CONFIG = Config(8, 4, 250, 5, ("11",), ("L", "Large", "LT", "Large Tall"), ("33", "34", "33W", "34W"), "America/Los_Angeles", 0, 9)


def product(title, product_type, variants, vendor="Nike SB"):
    return Product("1", title, "https://example.com/products/one", None, product_type, vendor, (), tuple(variants))


def variant(identifier, title, available=True):
    return Variant(identifier, title, available, Decimal("125.00"))


class FilterTests(unittest.TestCase):
    def test_matches_sb_dunk_low_size_11(self):
        item = product("Nike SB Dunk Low Pro", "Shoes", [variant("v1", "11"), variant("v2", "10")])
        self.assertEqual(category(item), "shoe")
        self.assertEqual([value.id for value in target_variants(item, "shoe", CONFIG)], ["v1"])

    def test_rejects_non_dunk_sb_shoe(self):
        item = product("Nike SB Blazer Mid", "Shoes", [variant("v1", "11")])
        self.assertIsNone(category(item))

    def test_matches_large_nike_sb_top(self):
        item = product("Nike SB Logo Tee", "T-Shirts", [variant("v1", "Large"), variant("v2", "Medium")])
        self.assertEqual(category(item), "top")
        self.assertEqual([value.id for value in target_variants(item, "top", CONFIG)], ["v1"])

    def test_matches_waist_34_bottom(self):
        item = product("Nike SB Kearny Cargo Pants", "Pants", [variant("v1", "34W"), variant("v2", "36W")])
        self.assertEqual(category(item), "bottom")
        self.assertEqual([value.id for value in target_variants(item, "bottom", CONFIG)], ["v1"])

    def test_does_not_treat_accessory_as_apparel(self):
        item = product("Nike SB Club Cap", "Accessories", [variant("v1", "Large")])
        self.assertIsNone(category(item))


if __name__ == "__main__":
    unittest.main()

