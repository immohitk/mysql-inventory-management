
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from database import reset_dev


class TestResetDev(unittest.TestCase):
    def run_main(self, *args):
        with patch("sys.argv", ["reset_dev.py", *args]):
            reset_dev.main()

    def valid_args(self, database="inventory_migration_test"):
        return (
            "--database", database,
            "--confirm-database", database,
            "--confirm-create",
        )

    @patch("database.reset_dev.run_mysql")
    def test_rejects_protected_database(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main(*self.valid_args("inventory_db"))
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch("database.reset_dev.run_mysql")
    def test_requires_explicit_confirmation(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main(
                "--database", "inventory_migration_test",
                "--confirm-database", "inventory_migration_test",
            )
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch("database.reset_dev.run_mysql")
    def test_rejects_invalid_database_name(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main(*self.valid_args("production"))
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch("database.reset_dev.run_mysql")
    @patch("database.reset_dev.MYSQL")
    def test_rejects_missing_mysql_client(self, mysql, run_mysql):
        mysql.is_file.return_value = False
        with patch.object(reset_dev, "LOGIN_PATH", "test-login"):
            with self.assertRaises(SystemExit) as error:
                self.run_main(*self.valid_args())
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch("database.reset_dev.run_mysql")
    @patch("database.reset_dev.MYSQL")
    def test_refuses_existing_database(self, mysql, run_mysql):
        mysql.is_file.return_value = True
        run_mysql.return_value = SimpleNamespace(
            returncode=0, stdout="1\n", stderr=""
        )
        with patch.object(reset_dev, "LOGIN_PATH", "test-login"):
            with self.assertRaises(SystemExit) as error:
                self.run_main(*self.valid_args())
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_called_once()
        self.assertNotIn("DROP DATABASE", str(run_mysql.call_args_list))

    @patch("database.reset_dev.run_mysql")
    @patch("database.reset_dev.MYSQL")
    def test_creates_only_after_empty_preflight(self, mysql, run_mysql):
        mysql.is_file.return_value = True
        run_mysql.side_effect = [
            SimpleNamespace(returncode=0, stdout="0\n", stderr=""),
            SimpleNamespace(returncode=0, stdout="", stderr=""),
        ]
        with patch.object(reset_dev, "LOGIN_PATH", "test-login"):
            self.run_main(*self.valid_args())

        self.assertEqual(run_mysql.call_count, 2)
        preflight_sql = run_mysql.call_args_list[0].args[0]
        create_sql = run_mysql.call_args_list[1].args[0]
        self.assertIn("INFORMATION_SCHEMA.SCHEMATA", preflight_sql)
        self.assertIn("CREATE DATABASE", create_sql)
        self.assertNotIn("DROP DATABASE", preflight_sql.upper())
        self.assertNotIn("DROP DATABASE", create_sql.upper())

    @patch("database.reset_dev.run_mysql")
    def test_rejects_mismatched_database_confirmation(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main(
                "--database", "inventory_migration_test",
                "--confirm-database", "inventory_migration_other",
                "--confirm-create",
            )
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch("database.reset_dev.run_mysql")
    def test_rejects_administrative_login_path(self, run_mysql):
        with patch.object(reset_dev, "LOGIN_PATH", "root"):
            with self.assertRaises(SystemExit) as error:
                self.run_main(*self.valid_args())
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch("database.reset_dev.run_mysql")
    def test_rejects_missing_login_path(self, run_mysql):
        with patch.object(reset_dev, "LOGIN_PATH", ""):
            with self.assertRaises(SystemExit) as error:
                self.run_main(*self.valid_args())
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()


if __name__ == "__main__":
    unittest.main()
