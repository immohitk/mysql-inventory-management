import os
import unittest
from unittest.mock import MagicMock, patch

from tests.integration.test_database import (
    _validate_required_schema,
    connect_test_database,
)


class TestIntegrationDatabaseSafety(unittest.TestCase):
    def test_disabled_without_explicit_opt_in(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                connect_test_database()

    def test_rejects_missing_database_name(self):
        with patch.dict(
            os.environ,
            {"RUN_MYSQL_INTEGRATION_TESTS": "1"},
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "INVENTORY_TEST_DATABASE"):
                connect_test_database()

    def test_rejects_protected_database_name(self):
        with patch.dict(
            os.environ,
            {
                "RUN_MYSQL_INTEGRATION_TESTS": "1",
                "INVENTORY_TEST_DATABASE": "inventory_db",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "INVENTORY_TEST_DATABASE"):
                connect_test_database()

    def test_rejects_database_outside_test_namespace(self):
        with patch.dict(
            os.environ,
            {
                "RUN_MYSQL_INTEGRATION_TESTS": "1",
                "INVENTORY_TEST_DATABASE": "production",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "INVENTORY_TEST_DATABASE"):
                connect_test_database()

    def test_rejects_missing_exact_name_confirmation(self):
        with patch.dict(
            os.environ,
            {
                "RUN_MYSQL_INTEGRATION_TESTS": "1",
                "INVENTORY_TEST_DATABASE": "inventory_migration_test",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "INVENTORY_TEST_DATABASE_CONFIRM"
            ):
                connect_test_database()

    def test_rejects_mismatched_name_confirmation(self):
        with patch.dict(
            os.environ,
            {
                "RUN_MYSQL_INTEGRATION_TESTS": "1",
                "INVENTORY_TEST_DATABASE": "inventory_migration_test",
                "INVENTORY_TEST_DATABASE_CONFIRM": "inventory_migration_other",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "INVENTORY_TEST_DATABASE_CONFIRM"
            ):
                connect_test_database()

    @patch("tests.integration.test_database.mysql.connector.connect")
    def test_rejects_missing_test_user_without_connecting(self, mock_connect):
        with patch.dict(
            os.environ,
            {
                "RUN_MYSQL_INTEGRATION_TESTS": "1",
                "INVENTORY_TEST_DATABASE": "inventory_migration_test",
                "INVENTORY_TEST_DATABASE_CONFIRM": "inventory_migration_test",
                "INVENTORY_TEST_DATABASE_DISPOSABLE": "inventory_migration_test",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(
                RuntimeError, "INVENTORY_TEST_DB_USER"
            ):
                connect_test_database()

        mock_connect.assert_not_called()

    
    def test_schema_validator_rejects_missing_table_columns(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = []

        with self.assertRaisesRegex(RuntimeError, "categories"):
            _validate_required_schema(cursor)

    def test_schema_validator_accepts_required_columns(self):
        from tests.integration.test_database import REQUIRED_SCHEMA

        cursor = MagicMock()
        cursor.fetchall.side_effect = [
            [(column,) for column in columns]
            for columns in REQUIRED_SCHEMA.values()
        ]

        _validate_required_schema(cursor)
        self.assertEqual(
            cursor.execute.call_count,
            len(REQUIRED_SCHEMA),
        )


    @patch("tests.integration.test_database.mysql.connector.connect")
    def test_rejects_non_integer_port_without_connecting(self, mock_connect):
        with patch.dict(
            os.environ,
            {
                "RUN_MYSQL_INTEGRATION_TESTS": "1",
                "INVENTORY_TEST_DATABASE": "inventory_migration_test",
                "INVENTORY_TEST_DATABASE_CONFIRM": "inventory_migration_test",
                "INVENTORY_TEST_DATABASE_DISPOSABLE": "inventory_migration_test",
                "INVENTORY_TEST_DB_USER": "test_user",
                "INVENTORY_TEST_DB_PORT": "not-a-port",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "INVENTORY_TEST_DB_PORT"):
                connect_test_database()

        mock_connect.assert_not_called()

    @patch("tests.integration.test_database.mysql.connector.connect")
    def test_rejects_out_of_range_port_without_connecting(self, mock_connect):
        for port in ("0", "65536", "-1"):
            with self.subTest(port=port):
                with patch.dict(
                    os.environ,
                    {
                        "RUN_MYSQL_INTEGRATION_TESTS": "1",
                        "INVENTORY_TEST_DATABASE": "inventory_migration_test",
                        "INVENTORY_TEST_DATABASE_CONFIRM": "inventory_migration_test",
                        "INVENTORY_TEST_DATABASE_DISPOSABLE": "inventory_migration_test",
                        "INVENTORY_TEST_DB_USER": "test_user",
                        "INVENTORY_TEST_DB_PORT": port,
                    },
                    clear=True,
                ):
                    with self.assertRaisesRegex(
                        RuntimeError, "INVENTORY_TEST_DB_PORT"
                    ):
                        connect_test_database()

                mock_connect.assert_not_called()

    def test_rejects_missing_disposable_database_approval(self):
        with patch.dict(
            os.environ,
            {
                "RUN_MYSQL_INTEGRATION_TESTS": "1",
                "INVENTORY_TEST_DATABASE": "inventory_migration_test",
                "INVENTORY_TEST_DATABASE_CONFIRM": "inventory_migration_test",
                "INVENTORY_TEST_DB_USER": "inventory_test_user",
            },
            clear=True,
        ):
            with patch(
                "tests.integration.test_database.mysql.connector.connect"
            ) as mock_connect:
                with self.assertRaisesRegex(
                    RuntimeError, "INVENTORY_TEST_DATABASE_DISPOSABLE"
                ):
                    connect_test_database()

                mock_connect.assert_not_called()

    def test_rejects_mismatched_disposable_database_approval(self):
        with patch.dict(
            os.environ,
            {
                "RUN_MYSQL_INTEGRATION_TESTS": "1",
                "INVENTORY_TEST_DATABASE": "inventory_migration_test",
                "INVENTORY_TEST_DATABASE_CONFIRM": "inventory_migration_test",
                "INVENTORY_TEST_DATABASE_DISPOSABLE": "inventory_migration_other",
                "INVENTORY_TEST_DB_USER": "inventory_test_user",
            },
            clear=True,
        ):
            with patch(
                "tests.integration.test_database.mysql.connector.connect"
            ) as mock_connect:
                with self.assertRaisesRegex(
                    RuntimeError, "INVENTORY_TEST_DATABASE_DISPOSABLE"
                ):
                    connect_test_database()

                mock_connect.assert_not_called()

    def test_rejects_administrative_test_user_without_connecting(self):
        for username in (
            "root",
            "ROOT",
            "admin",
            "administrator",
            "mysql.session",
            "mysql.sys",
        ):
            with self.subTest(username=username):
                with patch.dict(
                    os.environ,
                    {
                        "RUN_MYSQL_INTEGRATION_TESTS": "1",
                        "INVENTORY_TEST_DATABASE": (
                            "inventory_migration_test"
                        ),
                        "INVENTORY_TEST_DATABASE_CONFIRM": (
                            "inventory_migration_test"
                        ),
                        "INVENTORY_TEST_DATABASE_DISPOSABLE": (
                            "inventory_migration_test"
                        ),
                        "INVENTORY_TEST_DB_USER": username,
                    },
                    clear=True,
                ):
                    with patch(
                        "tests.integration.test_database.mysql.connector.connect"
                    ) as mock_connect:
                        with self.assertRaisesRegex(
                            RuntimeError,
                            "non-administrative",
                        ):
                            connect_test_database()

                        mock_connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
