"""Tests for isolated package-content migration validation."""

import unittest
from unittest.mock import patch

from database.validate_package_contents import main


class TestValidatePackageContents(unittest.TestCase):
    def run_validator(self, database="inventory_migration_test"):
        with patch(
            "database.validate_package_contents.argparse.ArgumentParser.parse_args"
        ) as parse_args:
            parse_args.return_value.database = database
            with patch(
                "database.validate_package_contents.run_mysql"
            ) as run_mysql:
                return main(), run_mysql

    def setUp(self):
        self.valid_counts = {
            "package_specifications": 2,
            "package_contents": 2,
            "specifications_without_contents": 0,
            "contents_without_specification": 0,
            "contents_without_valid_unit": 0,
            "contents_with_invalid_quantity": 0,
            "contents_with_invalid_form": 0,
            "contents_with_invalid_parent": 0,
            "offers_without_package_contents": 0,
        }

    @patch("database.validate_package_contents.run_mysql")
    def test_empty_specifications_are_blocked(self, run_mysql):
        run_mysql.return_value.returncode = 0
        run_mysql.return_value.stderr = ""
        run_mysql.return_value.stdout = "0"

        with patch(
            "database.validate_package_contents.argparse.ArgumentParser.parse_args"
        ) as parse_args:
            parse_args.return_value.database = "inventory_migration_test"

            with self.assertRaisesRegex(
                SystemExit, "no package specifications exist"
            ):
                main()

        self.assertEqual(run_mysql.call_count, 9)

    @patch("database.validate_package_contents.run_mysql")
    def test_empty_contents_are_blocked(self, run_mysql):
        def query_result(database, sql):
            result = type("Result", (), {})()
            result.returncode = 0
            result.stderr = ""
            result.stdout = "2" if "package_specifications" in sql else "0"
            return result

        run_mysql.side_effect = query_result

        with patch(
            "database.validate_package_contents.argparse.ArgumentParser.parse_args"
        ) as parse_args:
            parse_args.return_value.database = "inventory_migration_test"

            with self.assertRaisesRegex(
                SystemExit, "no package contents exist"
            ):
                main()

    @patch("database.validate_package_contents.run_mysql")
    def test_invalid_database_name_is_rejected_before_sql(self, run_mysql):
        with patch(
            "database.validate_package_contents.argparse.ArgumentParser.parse_args"
        ) as parse_args:
            parse_args.return_value.database = "inventory_db"

            with self.assertRaises(SystemExit):
                main()

        run_mysql.assert_not_called()

    @patch("database.validate_package_contents.run_mysql")
    def test_database_query_failure_stops_validation(self, run_mysql):
        run_mysql.return_value.returncode = 1
        run_mysql.return_value.stderr = "simulated database error"

        with patch(
            "database.validate_package_contents.argparse.ArgumentParser.parse_args"
        ) as parse_args:
            parse_args.return_value.database = "inventory_migration_test"

            with self.assertRaisesRegex(
                SystemExit, "simulated database error"
            ):
                main()

    @patch("database.validate_package_contents.run_mysql")
    def test_valid_structure_passes_with_factual_verification_caveat(
        self, run_mysql
    ):
        counts = iter(self.valid_counts.values())

        def query_result(database, sql):
            result = type("Result", (), {})()
            result.returncode = 0
            result.stderr = ""
            result.stdout = str(next(counts))
            return result

        run_mysql.side_effect = query_result

        with patch(
            "database.validate_package_contents.argparse.ArgumentParser.parse_args"
        ) as parse_args:
            parse_args.return_value.database = "inventory_migration_test"

            with patch("builtins.print") as printed:
                main()

        output = " ".join(
            str(call.args[0]) for call in printed.call_args_list
        )
        self.assertIn("STRUCTURAL CHECKS PASSED", output)
        self.assertIn("does not prove", output)


if __name__ == "__main__":
    unittest.main()
