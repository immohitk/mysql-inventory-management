import unittest
from types import SimpleNamespace
from unittest.mock import patch

from database import validate_supplier_offers


class TestValidateSupplierOffers(unittest.TestCase):
    @patch("database.validate_supplier_offers.run_mysql")
    def test_empty_offers_are_blocked(self, run_mysql):
        run_mysql.return_value = SimpleNamespace(
            returncode=0,
            stdout="0\n",
            stderr="",
        )

        with patch(
            "sys.argv",
            [
                "validate_supplier_offers.py",
                "--database",
                "inventory_migration_test",
            ],
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "no supplier offers exist",
            ):
                validate_supplier_offers.main()

        self.assertEqual(run_mysql.call_count, 4)

    @patch("database.validate_supplier_offers.run_mysql")
    def test_invalid_database_is_rejected_before_queries(self, run_mysql):
        with patch(
            "sys.argv",
            [
                "validate_supplier_offers.py",
                "--database",
                "inventory_db",
            ],
        ):
            with self.assertRaises(SystemExit):
                validate_supplier_offers.main()

        run_mysql.assert_not_called()

    @patch("database.validate_supplier_offers.run_mysql")
    def test_database_error_stops_validation(self, run_mysql):
        run_mysql.return_value = SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="simulated SQL failure",
        )

        with patch(
            "sys.argv",
            [
                "validate_supplier_offers.py",
                "--database",
                "inventory_migration_test",
            ],
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "simulated SQL failure",
            ):
                validate_supplier_offers.main()

        run_mysql.assert_called_once()


if __name__ == "__main__":
    unittest.main()