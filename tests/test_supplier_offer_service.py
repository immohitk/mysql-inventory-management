
import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from mysql.connector import Error

from app.services.supplier_offer_service import SupplierOfferService


class TestSupplierOfferService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = SupplierOfferService(self.db)

    def test_create_offer_uses_decimal_values_and_commits(self):
        self.db.execute.return_value.lastrowid = 7

        result = self.service.create_offer(
            1, 2, 3, Decimal("2.5000"), Decimal("19.99")
        )

        self.assertEqual(result, 7)
        params = self.db.execute.call_args.args[1]
        self.assertEqual(params[3], Decimal("2.5000"))
        self.assertEqual(params[4], Decimal("19.99"))
        self.db.commit.assert_called_once()

    def test_create_offer_rejects_invalid_ids(self):
        for value in (0, -1, True, "1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.service.create_offer(
                        value, 2, 3, Decimal("1"), Decimal("10")
                    )

        self.db.execute.assert_not_called()

    def test_create_offer_requires_price(self):
        with self.assertRaisesRegex(ValueError, "Purchase price is required"):
            self.service.create_offer(1, 2, 3)

        self.db.execute.assert_not_called()

    def test_create_offer_rejects_zero_or_negative_moq(self):
        for value in (0, -1, Decimal("0.0000")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.service.create_offer(1, 2, 3, value, 10)

        self.db.execute.assert_not_called()

    def test_create_offer_rejects_negative_price(self):
        with self.assertRaises(ValueError):
            self.service.create_offer(1, 2, 3, 1, -0.01)

        self.db.execute.assert_not_called()

    def test_create_offer_rejects_boolean_decimals(self):
        for value in (True, False):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.service.create_offer(1, 2, 3, value, 10)
                with self.assertRaises(ValueError):
                    self.service.create_offer(1, 2, 3, 1, value)

        self.db.execute.assert_not_called()

    def test_create_offer_rejects_non_finite_values(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.service.create_offer(1, 2, 3, value, 10)
                with self.assertRaises(ValueError):
                    self.service.create_offer(1, 2, 3, 1, value)

        self.db.execute.assert_not_called()

    def test_create_offer_rejects_excess_decimal_places(self):
        with self.assertRaisesRegex(ValueError, "4 decimal places"):
            self.service.create_offer(1, 2, 3, "1.00001", 10)

        with self.assertRaisesRegex(ValueError, "2 decimal places"):
            self.service.create_offer(1, 2, 3, 1, "10.001")

        self.db.execute.assert_not_called()

    def test_create_offer_rejects_oversized_values(self):
        with self.assertRaisesRegex(ValueError, "supported range"):
            self.service.create_offer(1, 2, 3, "100000000", 10)

        with self.assertRaisesRegex(ValueError, "supported range"):
            self.service.create_offer(1, 2, 3, 1, "10000000000.00")

        self.db.execute.assert_not_called()

    def test_create_offer_rejects_non_boolean_active_flag(self):
        with self.assertRaisesRegex(ValueError, "is_active"):
            self.service.create_offer(1, 2, 3, 1, 10, is_active=1)

        self.db.execute.assert_not_called()

    def test_duplicate_offer_error_rolls_back(self):
        self.db.execute.side_effect = Error(
            errno=1062, msg="duplicate entry"
        )

        with self.assertRaisesRegex(ValueError, "offer already exists"):
            self.service.create_offer(1, 2, 3, 1, 10)

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_missing_foreign_key_error_rolls_back(self):
        self.db.execute.side_effect = Error(
            errno=1452, msg="foreign key failure"
        )

        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.service.create_offer(1, 2, 3, 1, 10)

        self.db.rollback.assert_called_once()

    def test_get_offer_delegates_to_repository(self):
        expected_offer = (7, 1, 2, 3)
        self.service.repository.get_by_id = MagicMock(
            return_value=expected_offer
        )

        result = self.service.get_offer(7)

        self.assertEqual(result, expected_offer)
        self.service.repository.get_by_id.assert_called_once_with(7)
        self.db.execute.assert_not_called()

    def test_get_offer_rejects_invalid_id_before_repository_call(self):
        self.service.repository.get_by_id = MagicMock()

        for value in (0, -1, True, "1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.service.get_offer(value)

        self.service.repository.get_by_id.assert_not_called()
        self.db.execute.assert_not_called()

    def test_get_all_offers_rejects_non_boolean_filter(self):
        self.service.repository.list_all = MagicMock()

        with self.assertRaises(ValueError):
            self.service.get_all_offers(active_only=1)

        self.service.repository.list_all.assert_not_called()
        self.db.execute.assert_not_called()


    def test_get_all_offers_delegates_active_filter_to_repository(self):
        expected_offers = [(7,)]
        self.service.repository.list_all = MagicMock(
            return_value=expected_offers
        )

        result = self.service.get_all_offers(active_only=True)

        self.assertEqual(result, expected_offers)
        self.service.repository.list_all.assert_called_once_with(
            active_only=True
        )
        self.db.execute.assert_not_called()

    def test_deactivate_offer_uses_soft_deactivation(self):
        self.db.execute.return_value.rowcount = 1

        result = self.service.deactivate_offer(7)

        self.assertEqual(result, 1)
        query, params = self.db.execute.call_args.args
        self.assertIn("SET is_active = %s", query)
        self.assertEqual(params, (False, 7))
        self.db.commit.assert_called_once()

    def test_activate_offer_uses_active_update(self):
        self.db.execute.return_value.rowcount = 1

        result = self.service.activate_offer(7)

        self.assertEqual(result, 1)
        query, params = self.db.execute.call_args.args
        self.assertIn("SET is_active = %s", query)
        self.assertEqual(params, (True, 7))
        self.db.commit.assert_called_once()
        self.db.rollback.assert_not_called()

    def test_deactivate_missing_offer_raises_and_rolls_back(self):
        update_cursor = MagicMock()
        update_cursor.rowcount = 0
        check_cursor = MagicMock()
        check_cursor.fetchone.return_value = None
        self.db.execute.side_effect = [update_cursor, check_cursor]

        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.service.deactivate_offer(99)

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()
        update_cursor.close.assert_called_once()
        check_cursor.close.assert_called_once()

    def test_activate_missing_offer_raises_and_rolls_back(self):
        update_cursor = MagicMock()
        update_cursor.rowcount = 0
        check_cursor = MagicMock()
        check_cursor.fetchone.return_value = None
        self.db.execute.side_effect = [update_cursor, check_cursor]

        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.service.activate_offer(99)

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()
        update_cursor.close.assert_called_once()
        check_cursor.close.assert_called_once()

    def test_activate_database_error_rolls_back(self):
        self.db.execute.side_effect = Error(
            errno=2000, msg="simulated database failure"
        )

        with self.assertRaises(Error):
            self.service.activate_offer(7)

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_update_missing_offer_raises_and_rolls_back(self):
        self.db.execute.return_value.rowcount = 0
        self.db.execute.return_value.fetchone.return_value = None

        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.service.update_offer(99, 1, 2, 3, 1, 10)

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_update_missing_foreign_key_error_rolls_back(self):
        self.db.execute.side_effect = Error(
            errno=1452, msg="foreign key failure"
        )

        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.service.update_offer(7, 99, 2, 3, 1, 10)

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_close_only_closes_owned_connection(self):
        self.service.close()
        self.db.close.assert_not_called()

        owned_db = MagicMock()
        owned_service = SupplierOfferService()
        owned_service.db = owned_db
        owned_service._owns_connection = True

        owned_service.close()
        owned_db.close.assert_called_once()


    def test_update_database_error_rolls_back(self):
        self.db.execute.side_effect = Error(
            errno=1062, msg="duplicate entry"
        )

        with self.assertRaisesRegex(ValueError, "offer already exists"):
            self.service.update_offer(7, 1, 2, 3, 1, 10)

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_deactivate_database_error_rolls_back(self):
        self.db.execute.side_effect = Error(
            errno=2000, msg="simulated database failure"
        )

        with self.assertRaises(Error):
            self.service.deactivate_offer(7)

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_get_offer_closes_cursor_when_fetch_fails(self):
        cursor = self.db.execute.return_value
        cursor.fetchone.side_effect = Error(
            errno=2000, msg="simulated fetch failure"
        )

        with self.assertRaises(Error):
            self.service.get_offer(7)

        cursor.close.assert_called_once()

    def test_update_existing_unchanged_offer_commits(self):
        self.db.execute.return_value.rowcount = 0
        self.db.execute.return_value.fetchone.return_value = (7,)

        result = self.service.update_offer(7, 1, 2, 3, 1, 10)

        self.assertEqual(result, 0)
        self.assertEqual(self.db.execute.call_count, 2)
        self.db.commit.assert_called_once()
        self.db.rollback.assert_not_called()

    def test_get_offers_by_supplier_delegates_to_repository(self):
        expected = [(7,)]
        self.service.repository.list_by_supplier = MagicMock(
            return_value=expected
        )

        result = self.service.get_offers_by_supplier(12, active_only=True)

        self.assertEqual(result, expected)
        self.service.repository.list_by_supplier.assert_called_once_with(
            12, active_only=True
        )
        self.db.execute.assert_not_called()

    def test_get_offers_by_supplier_rejects_invalid_id(self):
        self.service.repository.list_by_supplier = MagicMock()

        for value in (0, -1, True, "12"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.service.get_offers_by_supplier(value)

        self.service.repository.list_by_supplier.assert_not_called()
        self.db.execute.assert_not_called()

    def test_get_offers_by_product_delegates_to_repository(self):
        expected = [(8,)]
        self.service.repository.list_by_product = MagicMock(
            return_value=expected
        )

        result = self.service.get_offers_by_product(23, active_only=True)

        self.assertEqual(result, expected)
        self.service.repository.list_by_product.assert_called_once_with(
            23, active_only=True
        )
        self.db.execute.assert_not_called()

    def test_get_offers_by_product_rejects_invalid_id(self):
        self.service.repository.list_by_product = MagicMock()

        for value in (0, -1, True, "23"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.service.get_offers_by_product(value)

        self.service.repository.list_by_product.assert_not_called()
        self.db.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
