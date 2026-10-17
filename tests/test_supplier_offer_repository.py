
import unittest
from unittest.mock import MagicMock

from app.repositories.supplier_offer_repository import (
    SupplierOfferRepository,
)


class TestSupplierOfferRepository(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.repository = SupplierOfferRepository(self.db)
        self.cursor = self.db.execute.return_value

    def test_get_by_id_uses_parameterized_query(self):
        self.cursor.fetchone.return_value = (7, 1, 2, 3)

        result = self.repository.get_by_id(7)

        self.assertEqual(result, (7, 1, 2, 3))
        query, params = self.db.execute.call_args.args
        self.assertIn("WHERE id = %s", query)
        self.assertEqual(params, (7,))
        self.cursor.close.assert_called_once()

    def test_get_by_id_returns_none_when_missing(self):
        self.cursor.fetchone.return_value = None

        self.assertIsNone(self.repository.get_by_id(99))
        self.cursor.close.assert_called_once()

    def test_list_all_orders_by_id(self):
        self.cursor.fetchall.return_value = [(7,), (8,)]

        result = self.repository.list_all()

        self.assertEqual(result, [(7,), (8,)])
        query = self.db.execute.call_args.args[0]
        self.assertIn("ORDER BY id", query)
        self.assertNotIn("WHERE is_active = TRUE", query)
        self.cursor.close.assert_called_once()

    def test_list_all_filters_active_offers(self):
        self.repository.list_all(active_only=True)
        self.cursor.close.assert_called_once()

        query = self.db.execute.call_args.args[0]
        self.assertIn("WHERE is_active = TRUE", query)

    def test_list_by_supplier_uses_parameterized_query(self):
        self.repository.list_by_supplier(12, active_only=True)
        self.cursor.close.assert_called_once()

        query, params = self.db.execute.call_args.args
        self.assertIn("WHERE supplier_id = %s", query)
        self.assertIn("AND is_active = TRUE", query)
        self.assertEqual(params, (12,))

    def test_list_by_product_uses_parameterized_query(self):
        self.repository.list_by_product(23, active_only=True)
        self.cursor.close.assert_called_once()

        query, params = self.db.execute.call_args.args
        self.assertIn("WHERE product_id = %s", query)
        self.assertIn("AND is_active = TRUE", query)
        self.assertEqual(params, (23,))


    def test_cursor_closes_when_fetch_fails(self):
        self.cursor.fetchall.side_effect = RuntimeError("fetch failed")

        with self.assertRaisesRegex(RuntimeError, "fetch failed"):
            self.repository.list_all()

        self.cursor.close.assert_called_once()

    def test_constructor_requires_database_wrapper(self):
        with self.assertRaisesRegex(ValueError, "required"):
            SupplierOfferRepository(None)

    def test_cursor_closes_when_fetchone_fails(self):
        self.cursor.fetchone.side_effect = RuntimeError("fetch failed")

        with self.assertRaisesRegex(RuntimeError, "fetch failed"):
            self.repository.get_by_id(7)

        self.cursor.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()
