import unittest
from unittest.mock import MagicMock, patch

from database import reset_dev


class TestResetDev(unittest.TestCase):
    def run_main(self, *args):
        if "--database" in args and "--confirm-database" not in args:
            index = args.index("--database") + 1
            args = (*args, "--confirm-database", args[index])
        with patch("sys.argv", ["reset_dev.py", *args]):
            reset_dev.main()

    @patch('database.reset_dev.subprocess.run')
    def test_rejects_protected_database(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main('--database', 'inventory_db', '--confirm-reset')
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch('database.reset_dev.subprocess.run')
    def test_requires_explicit_confirmation(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main('--database', 'inventory_migration_test')
        self.assertEqual(error.exception.code, 2)

        run_mysql.assert_not_called()

    @patch('database.reset_dev.subprocess.run')
    def test_rejects_invalid_database_name(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main('--database', 'production', '--confirm-reset')
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch('database.reset_dev.subprocess.run')
    @patch('database.reset_dev.MYSQL')
    def test_rejects_missing_mysql_client(self, mysql, run_mysql):
        mysql.is_file.return_value = False
        with self.assertRaises(SystemExit) as error:
            self.run_main('--database', 'inventory_migration_test', '--confirm-reset')
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()

    @patch('database.reset_dev.subprocess.run')
    @patch('database.reset_dev.MYSQL')
    def test_resets_only_requested_database(self, mysql, run_mysql):
        mysql.is_file.return_value = True
        run_mysql.return_value = MagicMock(returncode=0, stdout='', stderr='')
        self.run_main('--database', 'inventory_migration_test', '--confirm-reset')
        run_mysql.assert_called_once()
        self.assertIn("DROP DATABASE IF EXISTS " + chr(96) + "inventory_migration_test" + chr(96), run_mysql.call_args.args[0][-1])
        self.assertIn("CREATE DATABASE " + chr(96) + "inventory_migration_test" + chr(96), run_mysql.call_args.args[0][-1])

    @patch('database.reset_dev.subprocess.run')
    def test_rejects_mismatched_database_confirmation(self, run_mysql):
        with self.assertRaises(SystemExit) as error:
            self.run_main('--database', 'inventory_migration_test', '--confirm-reset', '--confirm-database', 'inventory_migration_other')
        self.assertEqual(error.exception.code, 2)
        run_mysql.assert_not_called()
