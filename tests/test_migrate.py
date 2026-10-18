
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from database import migrate


class TestMigrationRunner(unittest.TestCase):
    def run_main(self, database="inventory_migration_test", mysql_exists=True):
        with patch("sys.argv", ["migrate.py", "--database", database]):
            if mysql_exists:
                with patch("database.migrate.MYSQL") as mysql:
                    mysql.is_file.return_value = True
                    migrate.main()
            else:
                migrate.main()

    def successful_schema_inspection(self):
        return MagicMock(
            returncode=0,
            stdout=(
                "categories\n"
                "products\n"
                "purchase_items\n"
                "purchases\n"
                "sale_items\n"
                "sales\n"
                "suppliers\n"
            ),
            stderr="",
        )

    @patch("database.migrate.run_mysql")
    def test_rejects_protected_database_before_sql(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main("inventory_db")

        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch("database.migrate.run_mysql")
    def test_rejects_invalid_database_name_before_sql(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main("production")

        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch("database.migrate.MYSQL")
    @patch("database.migrate.run_mysql")
    def test_rejects_missing_mysql_client(self, run_mysql, mysql):
        mysql.is_file.return_value = False

        with self.assertRaises(SystemExit) as error:
            self.run_main(mysql_exists=False)

        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    
    @patch("database.migrate.run_mysql")
    def test_reports_connection_failure(self, run_mysql):
        run_mysql.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="connection failed",
        )

        with patch("database.migrate.MYSQL") as mysql:
            mysql.is_file.return_value = True

            with self.assertRaises(SystemExit) as error:
                with patch("sys.stderr") as stderr:
                    self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertIn("connection failed", str(stderr.write.call_args_list))



    @patch("database.migrate.run_mysql")
    def test_rejects_unexpected_connected_database(self, run_mysql):
        run_mysql.return_value = MagicMock(
            returncode=0,
            stdout="inventory_migration_other",
            stderr="",
        )

        with patch("database.migrate.MYSQL") as mysql:
            mysql.is_file.return_value = True

            with self.assertRaises(SystemExit) as error:
                self.run_main("inventory_migration_test")

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 1)

    
    @patch("database.migrate.run_mysql")
    def test_rejects_schema_inspection_failure_before_writes(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test",
                stderr="",
            ),
            MagicMock(
                returncode=1,
                stdout="",
                stderr="schema inspection failed",
            ),
        ]

        with patch("database.migrate.MYSQL") as mysql:
            mysql.is_file.return_value = True

            with self.assertRaises(SystemExit) as error:
                with patch("sys.stderr"):
                    self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 2)


    @patch("database.migrate.run_mysql")
    def test_rejects_missing_base_tables_before_writes(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test",
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout="categories\nproducts\n",
                stderr="",
            ),
        ]

        with patch("database.migrate.MYSQL") as mysql:
            mysql.is_file.return_value = True

            with self.assertRaises(SystemExit) as error:
                with patch("sys.stderr"):
                    self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 2)


    @patch("database.migrate.run_mysql")
    def test_applies_migrations_in_order_and_skips_recorded_files(
        self, run_mysql
    ):
        run_mysql.side_effect = [
            MagicMock(returncode=0, stdout="inventory_migration_test", stderr=""),
            self.successful_schema_inspection(),
            MagicMock(returncode=0, stdout="", stderr=""),  # History table
            MagicMock(returncode=0, stdout="1", stderr=""),  # 001 recorded
            MagicMock(returncode=0, stdout="0", stderr=""),  # 002 not recorded
            MagicMock(returncode=0, stdout="", stderr=""),  # Apply 002
            MagicMock(returncode=0, stdout="", stderr=""),  # Record 002
            MagicMock(returncode=0, stdout="0", stderr=""),  # 003 not recorded
            MagicMock(returncode=0, stdout="", stderr=""),  # Apply 003
            MagicMock(returncode=0, stdout="", stderr=""),  # Record 003
            MagicMock(returncode=0, stdout="0", stderr=""),  # 004 not recorded
            MagicMock(returncode=0, stdout="", stderr=""),  # Apply 004
            MagicMock(returncode=0, stdout="", stderr=""),  # Record 004
        ]

        with patch(
            "database.migrate.MIGRATIONS_DIR",
            Path("database/migrations"),
        ):
            self.run_main()

        applied_files = [
            invocation.kwargs["file"].name
            for invocation in run_mysql.call_args_list
            if invocation.kwargs.get("file") is not None
        ]

        self.assertEqual(
            applied_files,
            [
                "002_create_package_and_supplier_tables.sql",
                "003_create_legacy_product_mapping.sql",
                "004_supplier_offer_evidence.sql",
            ],
        )

    @patch("database.migrate.run_mysql")
    def test_does_not_record_failed_migration(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(returncode=0, stdout="inventory_migration_test", stderr=""),
            self.successful_schema_inspection(),
            MagicMock(returncode=0, stdout="", stderr=""),  # History table
            MagicMock(returncode=0, stdout="0", stderr=""),  # Not recorded
            MagicMock(returncode=1, stdout="", stderr="simulated SQL failure"),
        ]

        with patch(
            "database.migrate.MIGRATIONS_DIR",
            Path("database/migrations"),
        ):
            with self.assertRaisesRegex(
                RuntimeError, "may retain partial DDL"
            ):
                self.run_main()

        self.assertEqual(run_mysql.call_count, 5)

    @patch("database.migrate.run_mysql")
    def test_reports_migration_tracking_failure(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(returncode=0, stdout="inventory_migration_test", stderr=""),
            self.successful_schema_inspection(),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="0", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=1, stdout="", stderr="tracking insert failed"),
        ]
        with patch("database.migrate.MIGRATIONS_DIR", Path("database/migrations")):
            with self.assertRaisesRegex(RuntimeError, "executed but tracking failed"):
                self.run_main()
        self.assertEqual(run_mysql.call_count, 6)

    @patch("database.migrate.run_mysql")
    def test_reports_empty_migrations_directory(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(returncode=0, stdout="inventory_migration_test", stderr=""),
            self.successful_schema_inspection(),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        with patch("database.migrate.MIGRATIONS_DIR", Path("missing_migrations")):
            with self.assertRaisesRegex(RuntimeError, "No migration files"):
                self.run_main()

    @patch("database.migrate.run_mysql")
    def test_rejects_partial_first_migration_before_writes(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test",
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout=(
                    "categories\n"
                    "products\n"
                    "purchase_items\n"
                    "purchases\n"
                    "sale_items\n"
                    "sales\n"
                    "suppliers\n"
                    "units\n"
                ),
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout="",
                stderr="",
            ),
        ]

        with patch("database.migrate.MYSQL") as mysql:
            mysql.is_file.return_value = True

            with self.assertRaises(SystemExit) as error:
                with patch("sys.stderr"):
                    self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 2)


    
    @patch("database.migrate.run_mysql")
    def test_rejects_recorded_migration_with_missing_tables(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test",
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout=(
                    "categories\n"
                    "products\n"
                    "purchase_items\n"
                    "purchases\n"
                    "sale_items\n"
                    "sales\n"
                    "schema_migrations\n"
                    "suppliers\n"
                ),
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout="001_create_base_procurement_tables.sql\n",
                stderr="",
            ),
        ]

        with patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 3)


    @patch("database.migrate.run_mysql")
    def test_rejects_migration_tables_without_history(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test",
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout=(
                    "categories\n"
                    "package_forms\n"
                    "products\n"
                    "purchase_items\n"
                    "purchases\n"
                    "sale_items\n"
                    "sales\n"
                    "suppliers\n"
                    "unit_conversions\n"
                    "units\n"
                ),
                stderr="",
            ),
        ]

        with patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 2)


    
    @patch("database.migrate.run_mysql")
    def test_rejects_unknown_recorded_migration(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test",
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout=(
                    "categories\n"
                    "products\n"
                    "purchase_items\n"
                    "purchases\n"
                    "sale_items\n"
                    "sales\n"
                    "schema_migrations\n"
                    "suppliers\n"
                ),
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout="999_unknown_migration.sql\n",
                stderr="",
            ),
        ]

        with patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 3)


if __name__ == "__main__":
    unittest.main()
