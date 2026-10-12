import unittest
from types import SimpleNamespace
from unittest.mock import patch

from database import validate_mappings


def successful_result(value):
    return SimpleNamespace(
        returncode=0,
        stdout=f"{value}\n",
        stderr="",
    )


class TestValidateMappings(unittest.TestCase):
    @patch("database.validate_mappings.run_mysql")
    def test_pending_mappings_with_notes_are_allowed(self, run_mysql):
        run_mysql.side_effect = [
            successful_result(8),  # source_products
            successful_result(8),  # mappings
            successful_result(0),  # missing_product_mappings
            successful_result(0),  # missing_product_reference
            successful_result(0),  # invalid_status
            successful_result(0),  # pending_without_notes
            successful_result(0),  # approved_without_unit
        ]

        with patch(
            "sys.argv",
            [
                "validate_mappings.py",
                "--database",
                "inventory_migration_test",
            ],
        ):
            validate_mappings.main()

        self.assertEqual(run_mysql.call_count, 7)

    @patch("database.validate_mappings.run_mysql")
    def test_missing_product_mappings_are_blocked(self, run_mysql):
        run_mysql.side_effect = [
            successful_result(8),
            successful_result(7),
            successful_result(1),
            successful_result(0),
            successful_result(0),
            successful_result(0),
            successful_result(0),
        ]

        with patch(
            "sys.argv",
            [
                "validate_mappings.py",
                "--database",
                "inventory_migration_test",
            ],
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "missing_product_mappings",
            ):
                validate_mappings.main()

    @patch("database.validate_mappings.run_mysql")
    def test_approved_mapping_without_unit_is_blocked(self, run_mysql):
        run_mysql.side_effect = [
            successful_result(8),
            successful_result(8),
            successful_result(0),
            successful_result(0),
            successful_result(0),
            successful_result(0),
            successful_result(1),
        ]

        with patch(
            "sys.argv",
            [
                "validate_mappings.py",
                "--database",
                "inventory_migration_test",
            ],
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "approved_without_unit",
            ):
                validate_mappings.main()

    @patch("database.validate_mappings.run_mysql")
    def test_production_database_is_rejected(self, run_mysql):
        with patch(
            "sys.argv",
            [
                "validate_mappings.py",
                "--database",
                "inventory_db",
            ],
        ):
            with self.assertRaises(SystemExit):
                validate_mappings.main()

        run_mysql.assert_not_called()


if __name__ == "__main__":
    unittest.main()
