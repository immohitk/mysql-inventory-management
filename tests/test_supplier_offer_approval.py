
import unittest

from database.supplier_offer_approval import (
    SupplierOfferEvidence,
    SupplierOfferReview,
    approval_status,
    missing_evidence,
    validate_review,
)


class TestSupplierOfferApproval(unittest.TestCase):
    def test_all_evidence_missing(self):
        evidence = SupplierOfferEvidence(None, None, None)

        self.assertEqual(
            missing_evidence(evidence),
            ["package_evidence", "price_evidence", "moq_evidence"],
        )
        self.assertEqual(approval_status(evidence), "PENDING")

    def test_blank_evidence_is_missing(self):
        evidence = SupplierOfferEvidence("  ", "invoice", "")

        self.assertEqual(
            missing_evidence(evidence),
            ["package_evidence", "moq_evidence"],
        )
        self.assertEqual(approval_status(evidence), "PENDING")

    def test_complete_evidence_is_only_ready_for_review(self):
        evidence = SupplierOfferEvidence(
            "Supplier packaging specification",
            "Supplier quotation",
            "Supplier MOQ confirmation",
        )

        self.assertEqual(missing_evidence(evidence), [])
        self.assertEqual(approval_status(evidence), "READY_FOR_REVIEW")

    def test_evidence_does_not_mean_approved(self):
        evidence = SupplierOfferEvidence(
            "Packaging specification",
            "Supplier quotation",
            "MOQ confirmation",
        )

        status = approval_status(evidence)

        self.assertEqual(status, "READY_FOR_REVIEW")
        self.assertNotEqual(status, "APPROVED")


    def test_approval_requires_reviewer_and_complete_evidence(self):
        evidence = SupplierOfferEvidence(
            "Packaging specification",
            "Supplier quotation",
            "MOQ confirmation",
        )
        review = SupplierOfferReview(
            evidence=evidence,
            decision="APPROVED",
            reviewer=" ",
        )

        self.assertEqual(validate_review(review), ["reviewer"])

    def test_approval_rejects_missing_evidence(self):
        evidence = SupplierOfferEvidence(
            None,
            "Supplier quotation",
            "MOQ confirmation",
        )
        review = SupplierOfferReview(
            evidence=evidence,
            decision="APPROVED",
            reviewer="Reviewer 1",
        )

        self.assertEqual(
            validate_review(review),
            ["package_evidence"],
        )

    def test_invalid_decision_is_rejected(self):
        evidence = SupplierOfferEvidence(None, None, None)
        review = SupplierOfferReview(
            evidence=evidence,
            decision="AUTO_APPROVE",
            reviewer="Reviewer 1",
        )

        self.assertEqual(validate_review(review), ["invalid_decision"])


if __name__ == "__main__":
    unittest.main()
