
import unittest

from database.migrate import run_mysql


TEST_DATABASE = "inventory_migration_snapshot_v043"


class TestSupplierOfferReviewSchema(unittest.TestCase):
    def test_review_table_exists(self):
        result = run_mysql(
            TEST_DATABASE,
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = 'supplier_offer_reviews'
            """,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "1")

    def test_review_table_has_required_fields(self):
        result = run_mysql(
            TEST_DATABASE,
            """
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'supplier_offer_reviews'
              AND column_name IN (
                  'supplier_offer_id',
                  'package_evidence',
                  'price_evidence',
                  'moq_evidence',
                  'review_status',
                  'reviewer',
                  'reviewed_at'
              )
            """,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "7")


if __name__ == "__main__":
    unittest.main()
