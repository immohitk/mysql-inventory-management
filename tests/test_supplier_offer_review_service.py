
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


if __name__ == "__main__":
    unittest.main()
