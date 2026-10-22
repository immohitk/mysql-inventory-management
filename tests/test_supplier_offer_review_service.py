
import unittest
from unittest.mock import patch

from database.supplier_offer_approval import (
    SupplierOfferEvidence,
    SupplierOfferReview,
)
from database.supplier_offer_review_service import save_review


class TestSupplierOfferReviewService(unittest.TestCase):
    def make_review(self, decision="APPROVED", reviewer="Reviewer 1"):
        return SupplierOfferReview(
            evidence=SupplierOfferEvidence(
                "Packaging specification",
                "Supplier quotation",
                "MOQ confirmation",
            ),
            decision=decision,
            reviewer=reviewer,
            review_notes="Test review",
        )

    def test_rejects_non_test_database(self):
        with self.assertRaises(ValueError):
            save_review("inventory_db", 1, self.make_review())

    def test_rejects_invalid_offer_id(self):
        with self.assertRaises(ValueError):
            save_review(
                "inventory_migration_snapshot_v043",
                0,
                self.make_review(),
            )

    def test_rejects_approval_without_reviewer(self):
        with self.assertRaisesRegex(ValueError, "reviewer"):
            save_review(
                "inventory_migration_snapshot_v043",
                1,
                self.make_review(reviewer=" "),
            )

    @patch("database.supplier_offer_review_service.run_mysql")
    def test_reports_database_error(self, run_mysql):
        run_mysql.return_value.returncode = 1
        run_mysql.return_value.stderr = "simulated SQL failure"

        with self.assertRaisesRegex(RuntimeError, "simulated SQL failure"):
            save_review(
                "inventory_migration_snapshot_v043",
                1,
                self.make_review(),
            )

        run_mysql.assert_called_once()


    @patch("database.supplier_offer_review_service.run_mysql")
    def test_does_not_overwrite_existing_review(self, run_mysql):
        run_mysql.return_value.returncode = 0
        run_mysql.return_value.stdout = "1\n"
        run_mysql.return_value.stderr = ""

        with self.assertRaisesRegex(ValueError, "already exists"):
            save_review(
                "inventory_migration_snapshot_v043",
                1,
                self.make_review(),
            )

        run_mysql.assert_called_once()

    @patch("database.supplier_offer_review_service.run_mysql")
    def test_verifies_review_using_selected_database(self, run_mysql):
        run_mysql.side_effect = [
            type("Result", (), {
                "returncode": 0,
                "stdout": "0\n",
                "stderr": "",
            })(),
            type("Result", (), {
                "returncode": 0,
                "stdout": "",
                "stderr": "",
            })(),
            type("Result", (), {
                "returncode": 0,
                "stdout": "1\n",
                "stderr": "",
            })(),
        ]

        save_review(
            "inventory_migration_snapshot_v043",
            1,
            self.make_review(),
        )

        self.assertEqual(run_mysql.call_count, 3)
        self.assertEqual(
            run_mysql.call_args_list[2].args[0],
            "inventory_migration_snapshot_v043",
        )
        self.assertIn(
            "SELECT COUNT(*) FROM supplier_offer_reviews",
            run_mysql.call_args_list[2].args[1],
        )

    @patch("database.supplier_offer_review_service.run_mysql")
    def test_rejects_offer_that_does_not_exist(self, run_mysql):
        def result(returncode=0, stdout="", stderr=""):
            return type(
                "Result",
                (),
                {
                    "returncode": returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                },
            )()

        run_mysql.side_effect = [
            result(stdout="0\n"),  # No existing review
            result(),              # INSERT ... SELECT inserts no row
            result(stdout="0\n"),  # Verification finds no review
        ]

        with self.assertRaisesRegex(ValueError, "does not exist"):
            save_review(
                "inventory_migration_snapshot_v043",
                999999,
                self.make_review(),
            )

        self.assertEqual(run_mysql.call_count, 3)
        self.assertEqual(
            run_mysql.call_args_list[2].args[0],
            "inventory_migration_snapshot_v043",
        )

    @patch("database.supplier_offer_review_service.run_mysql")
    def test_reports_post_insert_verification_error(self, run_mysql):
        def result(returncode=0, stdout="", stderr=""):
            return type(
                "Result",
                (),
                {
                    "returncode": returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                },
            )()

        run_mysql.side_effect = [
            result(stdout="0\n"),  # No existing review
            result(),              # INSERT succeeds
            result(returncode=1, stderr="verification failed"),
        ]

        with self.assertRaisesRegex(RuntimeError, "verification failed"):
            save_review(
                "inventory_migration_snapshot_v043",
                1,
                self.make_review(),
            )

        self.assertEqual(run_mysql.call_count, 3)

    @patch("database.supplier_offer_review_service.run_mysql")
    def test_rejects_malformed_existing_review_count(self, run_mysql):
        run_mysql.return_value.returncode = 0
        run_mysql.return_value.stdout = "not-a-count\n"
        run_mysql.return_value.stderr = ""

        with self.assertRaisesRegex(
            RuntimeError, "existing supplier offer review count"
        ):
            save_review(
                "inventory_migration_snapshot_v043",
                1,
                self.make_review(),
            )

        run_mysql.assert_called_once()

    @patch("database.supplier_offer_review_service.run_mysql")
    def test_rejects_malformed_persisted_review_count(self, run_mysql):
        def result(returncode=0, stdout="", stderr=""):
            return type(
                "Result",
                (),
                {
                    "returncode": returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                },
            )()

        run_mysql.side_effect = [
            result(stdout="0\n"),
            result(),
            result(stdout="unknown\n"),
        ]

        with self.assertRaisesRegex(
            RuntimeError, "persisted supplier offer review"
        ):
            save_review(
                "inventory_migration_snapshot_v043",
                1,
                self.make_review(),
            )

        self.assertEqual(run_mysql.call_count, 3)

    @patch("database.supplier_offer_review_service.run_mysql")
    def test_reports_multiple_persisted_reviews(self, run_mysql):
        def result(returncode=0, stdout="", stderr=""):
            return type(
                "Result",
                (),
                {
                    "returncode": returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                },
            )()

        run_mysql.side_effect = [
            result(stdout="0\n"),
            result(),
            result(stdout="2\n"),
        ]

        with self.assertRaisesRegex(
            RuntimeError, "Expected exactly one review"
        ):
            save_review(
                "inventory_migration_snapshot_v043",
                1,
                self.make_review(),
            )

        self.assertEqual(run_mysql.call_count, 3)

    @patch("database.supplier_offer_review_service.run_mysql")
    def test_rejects_multiple_existing_reviews(self, run_mysql):
        run_mysql.return_value.returncode = 0
        run_mysql.return_value.stdout = "2\n"
        run_mysql.return_value.stderr = ""

        with self.assertRaisesRegex(ValueError, "already exists"):
            save_review(
                "inventory_migration_snapshot_v043",
                1,
                self.make_review(),
            )

        run_mysql.assert_called_once()

if __name__ == "__main__":
    unittest.main()
