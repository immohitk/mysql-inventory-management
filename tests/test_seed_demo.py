import unittest
from unittest.mock import patch

from database import seed_demo


class TestSeedDemo(unittest.TestCase):
    def test_rejects_production_database_name(self):
        with patch.object(seed_demo, "MYSQL") as mysql_path:
            mysql_path.is_file.return_value = True
            with patch("sys.argv", ["seed_demo.py", "--database", "inventory_db"]):
                with self.assertRaises(SystemExit) as exc:
                    seed_demo.main()
        self.assertEqual(exc.exception.code, 2)

    def test_rejects_database_name_with_sql_punctuation(self):
        with patch("sys.argv", ["seed_demo.py", "--database", "inventory_migration_dev;DROP"]):
            with self.assertRaises(SystemExit) as exc:
                seed_demo.main()
        self.assertEqual(exc.exception.code, 2)

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
        run_mysql.return_value = unittest.mock.MagicMock(
            returncode=0,
            stdout="inventory_migration_other\n",
            stderr="",
        )

        with patch(
            "sys.argv",
            ["seed_demo.py", "--database", "inventory_migration_dev"],
        ):
            result = seed_demo.main()

        self.assertEqual(result, 1)
        run_mysql.assert_called_once()
        self.assertIn("SELECT DATABASE()", run_mysql.call_args.args[0][-1])

    @patch("database.seed_demo.subprocess.run")
    @patch("database.seed_demo.MYSQL")
    def test_stops_when_connection_check_fails(self, mysql, run_mysql):
        mysql.is_file.return_value = True
        run_mysql.return_value = unittest.mock.MagicMock(
            returncode=1,
            stdout="",
            stderr="connection failed",
        )

        with patch(
            "sys.argv",
            ["seed_demo.py", "--database", "inventory_migration_dev"],
        ):
            result = seed_demo.main()

        self.assertEqual(result, 1)
        run_mysql.assert_called_once()


if __name__ == "__main__":
    unittest.main()
