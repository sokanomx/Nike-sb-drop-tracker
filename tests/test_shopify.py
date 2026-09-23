import unittest

from tracker.models import Store
from tracker.shopify import _product_from_json


class ShopifyParsingTests(unittest.TestCase):
    def test_parses_product_and_variants(self):
        raw = {
            "id": 123,
            "title": "Nike SB Dunk Low Pro",
            "handle": "nike-sb-dunk-low-pro",
            "product_type": "Shoes",
            "vendor": "Nike SB",
            "tags": ["Nike", "SB"],
            "image": {"src": "https://cdn.example/image.jpg"},
            "variants": [{"id": 456, "title": "11", "available": True, "price": "125.00"}],
        }
        product = _product_from_json(Store("Example", "https://example.com"), raw)
        self.assertEqual(product.id, "123")
        self.assertEqual(product.url, "https://example.com/products/nike-sb-dunk-low-pro")
        self.assertEqual(product.variants[0].title, "11")
        self.assertTrue(product.variants[0].available)


if __name__ == "__main__":
    unittest.main()

