import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.unit_service import UnitService


class TestUnitService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.service = UnitService(self.db)

    def test_create_unit_normalizes_dimension(self):
        self.service.create_unit("Kilogram", "kg", "mass")

        self.db.execute.assert_called_once()
        self.assertEqual(
            self.db.execute.call_args.args[1],
            ("Kilogram", "kg", "MASS"),
        )
        self.db.commit.assert_called_once()

    def test_create_unit_rejects_unknown_dimension(self):
        with self.assertRaisesRegex(ValueError, "COUNT, MASS, or VOLUME"):
            self.service.create_unit("Liter", "L", "LENGTH")

        self.db.execute.assert_not_called()

    def test_create_unit_rejects_blank_name(self):
        with self.assertRaisesRegex(ValueError, "Unit name is required"):
            self.service.create_unit(" ", "kg", "MASS")

        self.db.execute.assert_not_called()

    def test_conversion_accepts_matching_dimensions(self):
        self.db.execute.return_value.fetchall.return_value = [
            (1, "MASS"),
            (2, "MASS"),
        ]
        self.db.execute.return_value.lastrowid = 10

        result = self.service.create_conversion(1, 2, Decimal("1000"))

        self.assertEqual(result, 10)
        self.db.commit.assert_called_once()

    def test_conversion_rejects_incompatible_dimensions(self):
        self.db.execute.return_value.fetchall.return_value = [
            (1, "MASS"),
            (2, "VOLUME"),
        ]

        with self.assertRaisesRegex(ValueError, "incompatible"):
            self.service.create_conversion(1, 2, 1000)

        # Dimension validation happens before any write transaction.
        self.db.execute.assert_called_once()
        self.db.commit.assert_not_called()
        self.db.rollback.assert_not_called()

    def test_conversion_rejects_missing_unit(self):
        self.db.execute.return_value.fetchall.return_value = [(1, "MASS")]

        with self.assertRaisesRegex(ValueError, "Both conversion units"):
            self.service.create_conversion(1, 2, 1000)

        self.db.commit.assert_not_called()

    def test_conversion_rejects_zero_factor(self):
        with self.assertRaisesRegex(ValueError, "positive number"):
            self.service.create_conversion(1, 2, 0)

        self.db.execute.assert_not_called()

    def test_conversion_rejects_negative_factor(self):
        with self.assertRaises(ValueError):
            self.service.create_conversion(1, 2, -1)

        self.db.execute.assert_not_called()

    def test_conversion_rejects_boolean_factor(self):
        with self.assertRaises(ValueError):
            self.service.create_conversion(1, 2, True)

        self.db.execute.assert_not_called()

    def test_conversion_rejects_nan(self):
        with self.assertRaises(ValueError):
            self.service.create_conversion(1, 2, Decimal("NaN"))

        self.db.execute.assert_not_called()

    def test_conversion_rejects_boolean_unit_ids(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            self.service.create_conversion(True, 2, 1000)

        self.db.execute.assert_not_called()

    def test_conversion_rejects_excessive_decimal_places(self):
        with self.assertRaisesRegex(ValueError, "8 decimal places"):
            self.service.create_conversion(1, 2, Decimal("1.123456789"))

        self.db.execute.assert_not_called()

    def test_conversion_rejects_infinite_factor(self):
        with self.assertRaises(ValueError):
            self.service.create_conversion(1, 2, Decimal("Infinity"))

        self.db.execute.assert_not_called()

    def test_list_units_closes_cursor(self):
        cursor = self.db.execute.return_value
        cursor.fetchall.return_value = [(1, "Kilogram", "kg", "MASS")]

        result = self.service.list_units()

        self.assertEqual(result, [(1, "Kilogram", "kg", "MASS")])
        cursor.close.assert_called_once()

    def test_create_unit_rolls_back_on_database_error(self):
        self.db.execute.side_effect = RuntimeError("database failure")

        with self.assertRaisesRegex(RuntimeError, "database failure"):
            self.service.create_unit("Kilogram", "kg", "MASS")

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_create_unit_closes_cursor_after_insert(self):
        cursor = self.db.execute.return_value
        cursor.lastrowid = 7

        result = self.service.create_unit("Kilogram", "kg", "MASS")

        self.assertEqual(result, 7)
        cursor.close.assert_called_once()
        self.db.commit.assert_called_once()

    def test_invalid_conversion_ids_do_not_start_transaction(self):
        for from_id, to_id in [(0, 2), (True, 2), (1, False)]:
            with self.subTest(from_id=from_id, to_id=to_id):
                self.db.reset_mock()

                with self.assertRaises(ValueError):
                    self.service.create_conversion(
                        from_id, to_id, Decimal("1000")
                    )

                self.db.execute.assert_not_called()
                self.db.commit.assert_not_called()
                self.db.rollback.assert_not_called()

    def test_conversion_insert_sql_has_valid_column_list(self):
        self.db.execute.return_value.fetchall.return_value = [
            (1, "MASS"),
            (2, "MASS"),
        ]
        self.db.execute.return_value.lastrowid = 10

        self.service.create_conversion(1, 2, Decimal("1000"))

        insert_sql = self.db.execute.call_args_list[1].args[0]
        normalized_sql = " ".join(insert_sql.split()).upper()
        normalized_sql = normalized_sql.replace("( ", "(").replace(" )", ")")

        self.assertIn(
            "FROM_UNIT_ID, FROM_UNIT_TYPE, TO_UNIT_ID, "
            "TO_UNIT_TYPE, CONVERSION_FACTOR) VALUES",
            normalized_sql,
        )


if __name__ == "__main__":
    unittest.main()
