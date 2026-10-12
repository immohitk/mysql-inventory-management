
"""Validate evidence and explicit decisions for supplier offers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SupplierOfferEvidence:
    package_evidence: str | None
    price_evidence: str | None
    moq_evidence: str | None


@dataclass(frozen=True)
class SupplierOfferReview:
    evidence: SupplierOfferEvidence
    decision: str
    reviewer: str | None
    review_notes: str | None = None


def missing_evidence(evidence: SupplierOfferEvidence) -> list[str]:
    """Return evidence fields that are missing or blank."""
    fields = {
        "package_evidence": evidence.package_evidence,
        "price_evidence": evidence.price_evidence,
        "moq_evidence": evidence.moq_evidence,
    }

    return [
        name
        for name, value in fields.items()
        if value is None or not value.strip()
    ]


def approval_status(evidence: SupplierOfferEvidence) -> str:
    """Evidence completion allows review, not automatic approval."""
    return (
        "READY_FOR_REVIEW"
        if not missing_evidence(evidence)
        else "PENDING"
    )


def validate_review(review: SupplierOfferReview) -> list[str]:
    """Return review errors without changing or approving database records."""
    errors = []

    if review.decision not in {"APPROVED", "REJECTED", "PENDING"}:
        errors.append("invalid_decision")

    if review.decision == "APPROVED":
        errors.extend(missing_evidence(review.evidence))

        if review.reviewer is None or not review.reviewer.strip():
            errors.append("reviewer")

    return errors
