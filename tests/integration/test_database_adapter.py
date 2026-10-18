
import unittest
from unittest.mock import MagicMock


from tests.integration.test_database import DatabaseAdapter


class TestDatabaseAdapter(unittest.TestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.adapter = DatabaseAdapter(self.connection)

    def test_execute_passes_query_and_parameters(self):
        cursor = self.connection.cursor.return_value

        result = self.adapter.execute(
            "SELECT id FROM suppliers WHERE id = %s",
            (7,),
        )

        self.connection.cursor.assert_called_once_with()
        cursor.execute.assert_called_once_with(
            "SELECT id FROM suppliers WHERE id = %s",
            (7,),
        )
        self.assertIs(result, cursor)

    def test_execute_uses_empty_parameters_when_omitted(self):
        cursor = self.connection.cursor.return_value

        self.adapter.execute("SELECT 1")

        cursor.execute.assert_called_once_with("SELECT 1", ())

    def test_execute_closes_cursor_if_execution_fails(self):
        cursor = self.connection.cursor.return_value
        cursor.execute.side_effect = RuntimeError("query failed")

        with self.assertRaisesRegex(RuntimeError, "query failed"):
            self.adapter.execute("SELECT 1")

        cursor.close.assert_called_once_with()

    def test_commit_delegates(self):
        self.adapter.commit()
        self.connection.commit.assert_called_once_with()

    def test_rollback_delegates(self):
        self.adapter.rollback()
        self.connection.rollback.assert_called_once_with()

    def test_close_delegates(self):
        self.adapter.close()
        self.connection.close.assert_called_once_with()

    def test_rejects_none_connection(self):
        with self.assertRaisesRegex(ValueError, "approved test connection"):
            DatabaseAdapter(None)


if __name__ == "__main__":
    unittest.main()
