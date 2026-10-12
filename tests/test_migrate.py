
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from database import migrate


class TestMigrationRunner(unittest.TestCase):
    def run_main(self, database="inventory_migration_test"):
        with patch("sys.argv", ["migrate.py", "--database", database]):
            migrate.main()

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
            self.run_main()

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
    def test_applies_migrations_in_order_and_skips_recorded_files(
        self, run_mysql
    ):
        run_mysql.side_effect = [
            MagicMock(returncode=0, stdout="inventory_migration_test", stderr=""),
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

        self.assertEqual(run_mysql.call_count, 4)

    @patch("database.migrate.run_mysql")
    def test_reports_empty_migrations_directory(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(returncode=0, stdout="inventory_migration_test", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        with patch("database.migrate.MIGRATIONS_DIR", Path("missing_migrations")):
            with self.assertRaisesRegex(RuntimeError, "No migration files"):
                self.run_main()


if __name__ == "__main__":
    unittest.main()
