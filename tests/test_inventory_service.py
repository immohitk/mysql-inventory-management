import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.inventory_service import InventoryService


class TestInventoryService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = InventoryService(self.db)

    def test_stock_in_accepts_fractional_quantity(self):
        self.db.execute.return_value.fetchone.return_value = (
            Decimal("10.0000"),
        )
        self.db.execute.return_value.rowcount = 1

        result = self.service.stock_in(1, Decimal("1.2500"))

        self.assertEqual(result, Decimal("11.2500"))
        self.assertEqual(self.db.execute.call_count, 2)

    def test_stock_in_accepts_integer_quantity(self):
        self.db.execute.return_value.fetchone.return_value = (
            Decimal("10.0000"),
        )
        self.db.execute.return_value.rowcount = 1

        result = self.service.stock_in(1, 2)

        self.assertEqual(result, Decimal("12.0000"))

    def test_stock_in_rejects_zero_quantity(self):
        with self.assertRaises(ValueError):
            self.service.stock_in(1, 0)

    def test_stock_in_rejects_negative_quantity(self):
        with self.assertRaises(ValueError):
            self.service.stock_in(1, Decimal("-1.5"))

    def test_stock_in_rejects_boolean_quantity(self):
        with self.assertRaises(ValueError):
            self.service.stock_in(1, True)

    def test_stock_in_rejects_invalid_product_id(self):
        with self.assertRaises(ValueError):
            self.service.stock_in(0, 1)

    def test_get_product_stock_rejects_missing_product(self):
        self.db.execute.return_value.fetchone.return_value = None

        with self.assertRaisesRegex(ValueError, "Product does not exist"):
            self.service.get_product_stock(999)

    def test_stock_in_rejects_more_than_four_decimal_places(self):
        with self.assertRaisesRegex(ValueError, "4 decimal places"):
            self.service.stock_in(1, Decimal("1.12345"))

    def test_stock_in_rejects_nan(self):
        with self.assertRaises(ValueError):
            self.service.stock_in(1, Decimal("NaN"))

    def test_stock_in_rejects_infinity(self):
        with self.assertRaises(ValueError):
            self.service.stock_in(1, Decimal("Infinity"))

    def test_stock_in_rejects_oversized_quantity(self):
        with self.assertRaisesRegex(ValueError, "supported range"):
            self.service.stock_in(1, Decimal("10000000000"))

    def test_stock_in_rejects_boolean_product_id(self):
        with self.assertRaises(ValueError):
            self.service.stock_in(True, 1)


if __name__ == "__main__":
    unittest.main()
