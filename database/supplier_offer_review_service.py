
"""Persist supplier-offer reviews in isolated migration test databases."""

import re

from database.migrate import run_mysql
from database.supplier_offer_approval import (
    SupplierOfferReview,
    validate_review,
)


def save_review(database: str, offer_id: int, review: SupplierOfferReview) -> None:
    """Save a validated review; never connect to the original inventory DB."""
    database = database.strip()

    if not re.fullmatch(r"inventory_migration_[A-Za-z0-9_]+", database):
        raise ValueError("Use an isolated inventory_migration_<test_name> database.")

    if isinstance(offer_id, bool) or not isinstance(offer_id, int) or offer_id <= 0:
        raise ValueError("offer_id must be a positive integer.")

    errors = validate_review(review)
    if errors:
        raise ValueError("Review validation failed: " + ", ".join(errors))

    # Escape SQL string literals before passing them to the MySQL client.
    def sql_value(value: str | None) -> str:
        if value is None:
            return "NULL"
        escaped = value.replace("\\", "\\\\").replace("'", "''")
        return f"'{escaped}'"

    evidence = review.evidence
    decision = review.decision
    reviewer = review.reviewer

    sql = f"""
        INSERT INTO supplier_offer_reviews (
            supplier_offer_id,
            package_evidence,
            price_evidence,
            moq_evidence,
            review_status,
            reviewer,
            reviewed_at,
            review_notes
        )
        SELECT
            o.id,
            {sql_value(evidence.package_evidence)},
            {sql_value(evidence.price_evidence)},
            {sql_value(evidence.moq_evidence)},
            {sql_value(decision)},
            {sql_value(reviewer)},
            CURRENT_TIMESTAMP,
            {sql_value(review.review_notes)}
        FROM supplier_offers AS o
        WHERE o.id = {offer_id}
        ON DUPLICATE KEY UPDATE
            package_evidence = VALUES(package_evidence),
            price_evidence = VALUES(price_evidence),
            moq_evidence = VALUES(moq_evidence),
            review_status = VALUES(review_status),
            reviewer = VALUES(reviewer),
            reviewed_at = VALUES(reviewed_at),
            review_notes = VALUES(review_notes)
    """

    result = run_mysql(database, sql)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    # A successful INSERT ... SELECT can affect zero rows if the offer ID
    # does not exist, so confirm the review record was persisted.
    check = run_mysql(
        database,
        "SELECT COUNT(*) FROM supplier_offer_reviews "
        f"WHERE supplier_offer_id = {offer_id}",
    )
    if check.returncode != 0:
        raise RuntimeError(check.stderr.strip())
    if check.stdout.strip() != "1":
        raise ValueError(f"Supplier offer {offer_id} does not exist.")
