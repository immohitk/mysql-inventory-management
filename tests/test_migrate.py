import os
import tempfile
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from database import migrate


class TestRunMysql(unittest.TestCase):
    def test_rejects_missing_or_conflicting_sql_arguments(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            migrate.run_mysql("inventory_migration_test")

        with self.assertRaisesRegex(ValueError, "exactly one"):
            migrate.run_mysql(
                "inventory_migration_test",
                sql="SELECT 1",
                file=Path("example.sql"),
            )

    @patch("database.migrate.subprocess.run")
    @patch("database.migrate.tempfile.NamedTemporaryFile")
    def test_rejects_missing_credentials_before_creating_file(
        self, temporary_file, subprocess_run
    ):
        with patch.dict(
            os.environ,
            {
                "INVENTORY_TEST_DB_USER": "",
                "INVENTORY_TEST_DB_PASSWORD": "",
            },
        ):
            with self.assertRaisesRegex(RuntimeError, "INVENTORY_TEST_DB_USER"):
                migrate.run_mysql(
                    "inventory_migration_test", sql="SELECT 1"
                )

        temporary_file.assert_not_called()
        subprocess_run.assert_not_called()

    @patch("database.migrate.subprocess.run")
    def test_executes_sql_file_through_stdin_and_cleans_up(self, subprocess_run):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            with patch("database.migrate.tempfile.tempdir", directory):
                sql_file = Path(directory) / "example.sql"
                sql_file.write_text("SELECT 1;\n", encoding="utf-8")

                subprocess_run.side_effect = [
                    MagicMock(returncode=0, stdout="TEST\\user\n", stderr=""),
                    MagicMock(returncode=0, stdout="", stderr=""),
                    MagicMock(returncode=0, stdout="1\n", stderr=""),
                ]

                with patch.dict(
                    os.environ,
                    {
                        "INVENTORY_TEST_DB_USER": "inventory_test_v043",
                        "INVENTORY_TEST_DB_PASSWORD": "unit-test-secret",
                        "INVENTORY_TEST_DB_HOST": "localhost",
                        "INVENTORY_TEST_DB_PORT": "",
                    },
                ):
                    result = migrate.run_mysql(
                        "inventory_migration_test", file=sql_file
                    )

                self.assertEqual(result.returncode, 0)
                self.assertEqual(subprocess_run.call_count, 3)

                mysql_call = subprocess_run.call_args
                command = mysql_call.args[0]

                self.assertIn("--database", command)
                self.assertIn("--no-login-paths", command)

                # MySQL requires --defaults-extra-file before other client options.
                self.assertTrue(command[1].startswith("--defaults-extra-file="))
                self.assertLess(
                    command.index("--no-login-paths"),
                    command.index("--default-character-set=utf8mb4"),
                )
                self.assertIn("inventory_migration_test", command)
                self.assertNotIn("--execute", command)
                self.assertIsNotNone(mysql_call.kwargs.get("stdin"))
                self.assertTrue(mysql_call.kwargs["stdin"].closed)
                self.assertNotIn(
                    "unit-test-secret",
                    " ".join(str(argument) for argument in command),
                )
                self.assertEqual(list(Path(directory).glob("inventory-migration-*.cnf")), [])

    @patch("database.migrate.subprocess.run")
    def test_rejects_control_characters_in_credentials(self, subprocess_run):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            with patch("database.migrate.tempfile.tempdir", directory):
                for invalid_password in ("line1\nline2", "line1\rline2"):
                    with self.subTest(password=repr(invalid_password)):
                        subprocess_run.reset_mock()

                        with patch.dict(
                            os.environ,
                            {
                                "INVENTORY_TEST_DB_USER": "inventory_test_v043",
                                "INVENTORY_TEST_DB_PASSWORD": invalid_password,
                                "INVENTORY_TEST_DB_HOST": "localhost",
                                "INVENTORY_TEST_DB_PORT": "",
                            },
                        ):
                            with self.assertRaisesRegex(
                                RuntimeError, "control characters"
                            ):
                                migrate.run_mysql(
                                    "inventory_migration_test", sql="SELECT 1"
                                )

                        self.assertEqual(list(Path(directory).iterdir()), [])
                        subprocess_run.assert_not_called()

    @patch("database.migrate.subprocess.run")
    def test_cleans_up_credentials_file_when_whoami_fails(self, subprocess_run):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            with patch("database.migrate.tempfile.tempdir", directory):
                subprocess_run.return_value = MagicMock(
                    returncode=1, stdout="", stderr="whoami failed"
                )

                with patch.dict(
                    os.environ,
                    {
                        "INVENTORY_TEST_DB_USER": "inventory_test_v043",
                        "INVENTORY_TEST_DB_PASSWORD": "unit-test-secret",
                        "INVENTORY_TEST_DB_HOST": "localhost",
                        "INVENTORY_TEST_DB_PORT": "",
                    },
                ):
                    with self.assertRaisesRegex(RuntimeError, "Windows account"):
                        migrate.run_mysql(
                            "inventory_migration_test", sql="SELECT 1"
                        )

                self.assertEqual(subprocess_run.call_count, 1)
                self.assertEqual(list(Path(directory).iterdir()), [])

    @patch("database.migrate.Path.write_text", side_effect=OSError("write failed"))
    @patch("database.migrate.subprocess.run")
    def test_cleans_up_credentials_file_when_write_fails(
        self, subprocess_run, write_text
    ):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            with patch("database.migrate.tempfile.tempdir", directory):
                subprocess_run.side_effect = [
                    MagicMock(returncode=0, stdout="TEST\\\\user\n", stderr=""),
                    MagicMock(returncode=0, stdout="", stderr=""),
                ]

                with patch.dict(
                    os.environ,
                    {
                        "INVENTORY_TEST_DB_USER": "inventory_test_v043",
                        "INVENTORY_TEST_DB_PASSWORD": "unit-test-secret",
                        "INVENTORY_TEST_DB_HOST": "localhost",
                        "INVENTORY_TEST_DB_PORT": "",
                    },
                ):
                    with self.assertRaisesRegex(OSError, "write failed"):
                        migrate.run_mysql(
                            "inventory_migration_test", sql="SELECT 1"
                        )

                write_text.assert_called_once()
                self.assertEqual(subprocess_run.call_count, 2)
                self.assertEqual(list(Path(directory).iterdir()), [])

    @patch("database.migrate.Path.unlink", side_effect=OSError("cleanup failed"))
    @patch("database.migrate.subprocess.run")
    def test_warns_when_credentials_file_cleanup_fails(
        self, subprocess_run, unlink
    ):
        with tempfile.TemporaryDirectory() as directory:
            with patch("database.migrate.tempfile.tempdir", directory):
                with patch.dict(
                    os.environ,
                    {
                        "INVENTORY_TEST_DB_USER": "inventory_test_v043",
                        "INVENTORY_TEST_DB_PASSWORD": "unit-test-secret",
                        "INVENTORY_TEST_DB_HOST": "localhost",
                        "INVENTORY_TEST_DB_PORT": "",
                    },
                ):
                    subprocess_run.side_effect = [
                        MagicMock(
                            returncode=0, stdout="TEST\\\\user\n", stderr=""
                        ),
                        MagicMock(returncode=0, stdout="", stderr=""),
                        MagicMock(returncode=0, stdout="1\n", stderr=""),
                    ]

                    with self.assertWarnsRegex(
                        RuntimeWarning,
                        "Could not remove the temporary MySQL credentials file",
                    ) as warning:
                        result = migrate.run_mysql(
                            "inventory_migration_test", sql="SELECT 1"
                        )

                self.assertEqual(result.returncode, 0)
                self.assertEqual(subprocess_run.call_count, 3)
                unlink.assert_called_once_with(missing_ok=True)
                self.assertNotIn(
                    "unit-test-secret", str(warning.warning)
                )

    @patch("database.migrate.subprocess.run")
    @patch("database.migrate.tempfile.NamedTemporaryFile")
    def test_rejects_administrative_account_before_side_effects(
        self, temporary_file, subprocess_run
    ):
        for username in ("root", "admin", "administrator", "ROOT"):
            with self.subTest(username=username):
                with patch.dict(
                    os.environ,
                    {
                        "INVENTORY_TEST_DB_USER": username,
                        "INVENTORY_TEST_DB_PASSWORD": "unit-test-password",
                    },
                ):
                    with self.assertRaisesRegex(
                        RuntimeError, "administrative database account"
                    ):
                        migrate.run_mysql(
                            "inventory_migration_test",
                            sql="SELECT 1",
                        )

                temporary_file.assert_not_called()
                subprocess_run.assert_not_called()

class TestMigrationRunner(unittest.TestCase):

    def setUp(self):
        self.credentials_patcher = patch.dict(
            os.environ,
            {
                "INVENTORY_TEST_DB_USER": "inventory_test_v043",
                "INVENTORY_TEST_DB_PASSWORD": "unit-test-only-password",
            },
        )
        self.credentials_patcher.start()

    def tearDown(self):
        self.credentials_patcher.stop()


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
            stdout="inventory_migration_other\tinventory_test_v043@localhost",
            stderr="",
        )

        with patch("database.migrate.MYSQL") as mysql:
            mysql.is_file.return_value = True

            with self.assertRaises(SystemExit) as error:
                self.run_main("inventory_migration_test")

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 1)

    @patch("database.migrate.run_mysql")
    def test_rejects_unexpected_connected_account(self, run_mysql):
        run_mysql.return_value = MagicMock(
            returncode=0,
            stdout=(
                "inventory_migration_test\t"
                "unexpected_user@localhost"
            ),
            stderr="",
        )

        with patch("database.migrate.MYSQL") as mysql:
            mysql.is_file.return_value = True

            with self.assertRaises(SystemExit) as error:
                with patch("sys.stderr"):
                    self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 1)

    @patch("database.migrate.run_mysql")
    def test_rejects_schema_inspection_failure_before_writes(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
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
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
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
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
                stderr="",
            ),
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
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
                stderr="",
            ),
            self.successful_schema_inspection(),
            MagicMock(returncode=0, stdout="", stderr=""),  # History table
            MagicMock(returncode=0, stdout="0", stderr=""),  # Not recorded
            MagicMock(
                returncode=1,
                stdout="",
                stderr="simulated SQL failure",
            ),
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
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
                stderr="",
            ),
            self.successful_schema_inspection(),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="0", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(
                returncode=1,
                stdout="",
                stderr="tracking insert failed",
            ),
        ]

        with patch("database.migrate.MIGRATIONS_DIR", Path("database/migrations")):
            with self.assertRaisesRegex(
                RuntimeError, "executed but tracking failed"
            ):
                self.run_main()

        self.assertEqual(run_mysql.call_count, 6)

    @patch("database.migrate.run_mysql")
    def test_reports_empty_migrations_directory(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
                stderr="",
            ),
            self.successful_schema_inspection(),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]

        with patch("database.migrate.MIGRATIONS_DIR", Path("missing_migrations")):
            with self.assertRaisesRegex(RuntimeError, "No migration files"):
                self.run_main()

    @patch("database.migrate.run_mysql")
    def test_rejects_migration_without_expected_table_mapping(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
                stderr="",
            ),
            self.successful_schema_inspection(),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            migration_dir = Path(temp_dir)
            (migration_dir / "999_unmapped_migration.sql").write_text(
                "SELECT 1;",
                encoding="utf-8",
            )

            with patch("database.migrate.MIGRATIONS_DIR", migration_dir):
                with self.assertRaises(SystemExit) as error:
                    with patch("sys.stderr"):
                        self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 2)

    @patch("database.migrate.run_mysql")
    def test_rejects_partial_first_migration_before_writes(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
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
            MagicMock(returncode=0, stdout="", stderr=""),
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
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
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
            MagicMock(
                returncode=0,
                stdout=(
                    "version\tvarchar\t255\tNO\tPRI\t\n"
                    "applied_at\ttimestamp\tNULL\tNO\tCURRENT_TIMESTAMP\n"
                ),
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
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
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
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
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
            MagicMock(
                returncode=0,
                stdout=(
                    "version\tvarchar\t255\tNO\tPRI\t\n"
                    "applied_at\ttimestamp\tNULL\tNO\tCURRENT_TIMESTAMP\n"
                ),
                stderr="",
            ),
        ]

        with patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 3)

    @patch("database.migrate.run_mysql")
    def test_rejects_history_version_without_primary_key(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
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
                stdout=(
                    "version\tvarchar\t255\tNO\t\t\n"
                    "applied_at\ttimestamp\tNULL\tNO\tCURRENT_TIMESTAMP\n"
                ),
                stderr="",
            ),
        ]

        with patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 3)

    @patch("database.migrate.run_mysql")
    def test_rejects_history_version_with_wrong_type(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
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
                stdout=(
                    "version\ttext\tNULL\tNO\tPRI\t\n"
                    "applied_at\ttimestamp\tNULL\tNO\tCURRENT_TIMESTAMP\n"
                ),
                stderr="",
            ),
        ]

        with patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 3)

    @patch("database.migrate.run_mysql")
    def test_rejects_history_applied_at_without_default(self, run_mysql):
        run_mysql.side_effect = [
            MagicMock(
                returncode=0,
                stdout="inventory_migration_test\tinventory_test_v043@localhost",
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
                stdout=(
                    "version\tvarchar\t255\tNO\tPRI\t\n"
                    "applied_at\ttimestamp\tNULL\tNO\t\t\n"
                ),
                stderr="",
            ),
        ]

        with patch("sys.stderr"):
            with self.assertRaises(SystemExit) as error:
                self.run_main()

        self.assertEqual(error.exception.code, 2)
        self.assertEqual(run_mysql.call_count, 3)

    @patch("database.migrate.subprocess.run")
    def test_does_not_write_credentials_when_acl_fails(self, subprocess_run):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            with patch("database.migrate.tempfile.tempdir", directory):

                subprocess_run.side_effect = [
                    MagicMock(returncode=0, stdout="TEST\\user\n", stderr=""),
                    MagicMock(
                        returncode=1,
                        stdout="",
                        stderr="Access is denied",
                    ),
                ]

                with patch.dict(
                    os.environ,
                    {
                        "INVENTORY_TEST_DB_USER": "inventory_test_v043",
                        "INVENTORY_TEST_DB_PASSWORD": "unit-test-secret",
                        "INVENTORY_TEST_DB_HOST": "localhost",
                        "INVENTORY_TEST_DB_PORT": "",
                    },
                ):
                    with self.assertRaisesRegex(RuntimeError, "permissions"):
                        migrate.run_mysql(
                            "inventory_migration_test", sql="SELECT 1"
                        )

                self.assertEqual(
                    list(Path(directory).iterdir()), []
                )
                self.assertEqual(subprocess_run.call_count, 2)

    @patch("database.migrate.subprocess.run")
    def test_executes_sql_and_cleans_up_credentials_file(self, subprocess_run):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            with patch("database.migrate.tempfile.tempdir", directory):

                subprocess_run.side_effect = [
                    MagicMock(returncode=0, stdout="TEST\\user\n", stderr=""),
                    MagicMock(returncode=0, stdout="", stderr=""),
                    MagicMock(returncode=0, stdout="1\n", stderr=""),
                ]

                with patch.dict(
                    os.environ,
                    {
                        "INVENTORY_TEST_DB_USER": "inventory_test_v043",
                        "INVENTORY_TEST_DB_PASSWORD": "unit-test-secret",
                        "INVENTORY_TEST_DB_HOST": "localhost",
                        "INVENTORY_TEST_DB_PORT": "",
                    },
                ):
                    result = migrate.run_mysql(
                        "inventory_migration_test", sql="SELECT 1"
                    )

                self.assertEqual(result.returncode, 0)
                self.assertEqual(subprocess_run.call_count, 3)

                mysql_command = subprocess_run.call_args.args[0]
                self.assertIn("--database", mysql_command)
                self.assertIn("inventory_migration_test", mysql_command)
                self.assertIn("--execute", mysql_command)
                self.assertIn("SELECT 1", mysql_command)
                self.assertEqual(list(Path(directory).iterdir()), [])

    @patch("database.migrate.subprocess.run")
    def test_cleans_up_credentials_file_when_mysql_fails(self, subprocess_run):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            with patch("database.migrate.tempfile.tempdir", directory):

                subprocess_run.side_effect = [
                    MagicMock(returncode=0, stdout="TEST\\user\n", stderr=""),
                    MagicMock(returncode=0, stdout="", stderr=""),
                    MagicMock(
                        returncode=1,
                        stdout="",
                        stderr="simulated MySQL failure",
                    ),
                ]

                with patch.dict(
                    os.environ,
                    {
                        "INVENTORY_TEST_DB_USER": "inventory_test_v043",
                        "INVENTORY_TEST_DB_PASSWORD": "unit-test-secret",
                        "INVENTORY_TEST_DB_HOST": "localhost",
                        "INVENTORY_TEST_DB_PORT": "",
                    },
                ):
                    result = migrate.run_mysql(
                        "inventory_migration_test", sql="SELECT 1"
                    )

                self.assertEqual(result.returncode, 1)
                self.assertEqual(list(Path(directory).iterdir()), [])

class TestRunMysqlDatabaseGuard(unittest.TestCase):
    @patch("database.migrate.subprocess.run")
    @patch("database.migrate.tempfile.NamedTemporaryFile")
    def test_rejects_original_database_before_side_effects(
        self, temporary_file, subprocess_run
    ):
        with self.assertRaisesRegex(ValueError, "isolated"):
            migrate.run_mysql("inventory_db", sql="SELECT 1")

        temporary_file.assert_not_called()
        subprocess_run.assert_not_called()

    @patch("database.migrate.subprocess.run")
    @patch("database.migrate.tempfile.NamedTemporaryFile")
    def test_rejects_invalid_database_name_before_side_effects(
        self, temporary_file, subprocess_run
    ):
        with self.assertRaisesRegex(ValueError, "isolated"):
            migrate.run_mysql("unsafe-db", sql="SELECT 1")

        temporary_file.assert_not_called()
        subprocess_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
