
import unittest
from unittest.mock import MagicMock, patch

from database import seed_demo


class TestSeedDemo(unittest.TestCase):
    DATABASE = "inventory_migration_dev"

    def run_main(self, *extra_args, login_path="test-seed-user"):
        args = [
            "seed_demo.py",
            "--database",
            self.DATABASE,
            "--confirm-disposable",
            "--confirm-database",
            self.DATABASE,
            *extra_args,
        ]
        with (
            patch("sys.argv", args),
            patch.object(seed_demo, "LOGIN_PATH", login_path),
        ):
            return seed_demo.main()

    def test_rejects_production_database_name(self):
        with (
            patch("sys.argv", ["seed_demo.py", "--database", "inventory_db"]),
            patch.object(seed_demo, "LOGIN_PATH", "test-seed-user"),
        ):
            with self.assertRaises(SystemExit) as exc:
                seed_demo.main()
        self.assertEqual(exc.exception.code, 2)

    def test_rejects_database_name_with_sql_punctuation(self):
        with patch(
            "sys.argv",
            [
                "seed_demo.py",
                "--database",
                "inventory_migration_dev;DROP",
                "--confirm-disposable",
                "--confirm-database",
                "inventory_migration_dev;DROP",
            ],
        ):
            with self.assertRaises(SystemExit) as exc:
                seed_demo.main()
        self.assertEqual(exc.exception.code, 2)

    def test_rejects_missing_disposable_confirmation(self):
        with (
            patch(
                "sys.argv",
                [
                    "seed_demo.py",
                    "--database",
                    self.DATABASE,
                    "--confirm-database",
                    self.DATABASE,
                ],
            ),
            patch.object(seed_demo, "LOGIN_PATH", "test-seed-user"),
        ):
            with self.assertRaises(SystemExit) as exc:
                seed_demo.main()
        self.assertEqual(exc.exception.code, 2)

    def test_rejects_mismatched_database_confirmation(self):
        with (
            patch(
                "sys.argv",
                [
                    "seed_demo.py",
                    "--database",
                    self.DATABASE,
                    "--confirm-disposable",
                    "--confirm-database",
                    "inventory_migration_other",
                ],
            ),
            patch.object(seed_demo, "LOGIN_PATH", "test-seed-user"),
        ):
            with self.assertRaises(SystemExit) as exc:
                seed_demo.main()
        self.assertEqual(exc.exception.code, 2)

    def test_rejects_missing_login_path_before_mysql(self):
        with patch("database.seed_demo.subprocess.run") as run_mysql:
            with patch.object(seed_demo, "MYSQL") as mysql:
                mysql.is_file.return_value = True
                with self.assertRaises(SystemExit) as exc:
                    self.run_main(login_path="")
        self.assertEqual(exc.exception.code, 2)
        run_mysql.assert_not_called()

    def test_rejects_administrative_login_path_before_mysql(self):
        with patch("database.seed_demo.subprocess.run") as run_mysql:
            with self.assertRaises(SystemExit) as exc:
                self.run_main(login_path="inventory-migrations")
        self.assertEqual(exc.exception.code, 2)
        run_mysql.assert_not_called()

    def test_generated_sql_starts_transaction_and_commits(self):
        sql = seed_demo.build_seed_sql()
        self.assertTrue(sql.startswith("START TRANSACTION;"))
        self.assertIn("COMMIT;", sql)

    def test_generated_sql_contains_expected_demo_records(self):
        sql = seed_demo.build_seed_sql()
        for sku in (
            "ELEC-001", "ELEC-002", "COMP-001", "COMP-002",
            "OFF-001", "OFF-002", "HOME-001", "HOME-002",
        ):
            self.assertIn(sku, sql)

    def test_generated_sql_skips_existing_products(self):
        sql = seed_demo.build_seed_sql()
        self.assertIn("NOT EXISTS (SELECT 1 FROM products", sql)

    def test_generated_sql_does_not_select_legacy_database(self):
        sql = seed_demo.build_seed_sql()
        self.assertNotIn("USE inventory_db", sql)
        self.assertNotIn("DROP TABLE", sql)

    @patch("database.seed_demo.subprocess.run")
    @patch("database.seed_demo.MYSQL")
    def test_rejects_unexpected_connected_database(self, mysql, run_mysql):
        mysql.is_file.return_value = True
        run_mysql.return_value = MagicMock(
            returncode=0,
            stdout="inventory_migration_other\n",
            stderr="",
        )

        with patch.object(seed_demo, "LOGIN_PATH", "test-seed-user"):
            with patch(
                "sys.argv",
                [
                    "seed_demo.py",
                    "--database",
                    self.DATABASE,
                    "--confirm-disposable",
                    "--confirm-database",
                    self.DATABASE,
                ],
            ):
                result = seed_demo.main()

        self.assertEqual(result, 1)
        run_mysql.assert_called_once()
        self.assertIn("SELECT DATABASE()", run_mysql.call_args.args[0][-1])

    @patch("database.seed_demo.subprocess.run")
    @patch("database.seed_demo.MYSQL")
    def test_stops_when_connection_check_fails(self, mysql, run_mysql):
        mysql.is_file.return_value = True
        run_mysql.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="connection failed",
        )

        with patch.object(seed_demo, "LOGIN_PATH", "test-seed-user"):
            with patch(
                "sys.argv",
                [
                    "seed_demo.py",
                    "--database",
                    self.DATABASE,
                    "--confirm-disposable",
                    "--confirm-database",
                    self.DATABASE,
                ],
            ):
                result = seed_demo.main()

        self.assertEqual(result, 1)
        run_mysql.assert_called_once()

    @patch("database.seed_demo.subprocess.run")
    @patch("database.seed_demo.MYSQL")
    def test_seed_failure_returns_nonzero_without_success_message(
        self, mysql, run_mysql
    ):
        mysql.is_file.return_value = True
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout=f"{self.DATABASE}\n",
                stderr="",
            ),
            MagicMock(
                returncode=1,
                stdout="",
                stderr="seed SQL failed",
            ),
        ]

        with patch.object(seed_demo, "LOGIN_PATH", "test-seed-user"):
            with patch(
                "sys.argv",
                [
                    "seed_demo.py",
                    "--database",
                    self.DATABASE,
                    "--confirm-disposable",
                    "--confirm-database",
                    self.DATABASE,
                ],
            ):
                with patch("builtins.print") as mock_print:
                    result = seed_demo.main()

        self.assertEqual(result, 1)
        printed_messages = [
            str(call.args[0])
            for call in mock_print.call_args_list
            if call.args
        ]
        self.assertFalse(
            any("Demo seed completed" in message for message in printed_messages)
        )
        self.assertEqual(run_mysql.call_count, 2)


if __name__ == "__main__":
    unittest.main()
