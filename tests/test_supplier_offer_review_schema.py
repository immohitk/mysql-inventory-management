"""Opt-in MySQL schema checks for supplier-offer reviews."""

import os
import unittest

from tests.integration.test_database import connect_test_database


class TestSupplierOfferReviewSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("RUN_MYSQL_INTEGRATION_TESTS") != "1":
            raise unittest.SkipTest("MySQL integration tests are disabled.")

        cls.connection = connect_test_database()

    @classmethod
    def tearDownClass(cls):
        connection = getattr(cls, "connection", None)
        if connection is not None:
            connection.close()

    def test_review_table_exists(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = 'supplier_offer_reviews'
                """
            )
            self.assertEqual(cursor.fetchone()[0], 1)
        finally:
            cursor.close()

    def test_review_table_has_required_fields(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
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
                """
            )
            self.assertEqual(cursor.fetchone()[0], 7)
        finally:
            cursor.close()


if __name__ == "__main__":
    unittest.main()
