
"""Validate supplier offers in an isolated migration test database."""

import argparse
import re

try:
    from database.migrate import run_mysql
except ModuleNotFoundError:
    from migrate import run_mysql


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    args = parser.parse_args()

    database = args.database.strip()
    if not re.fullmatch(r"inventory_migration_[A-Za-z0-9_]+", database):
        parser.error("Use an isolated inventory_migration_<test_name> database.")

    checks = {
        "offers": "SELECT COUNT(*) FROM supplier_offers",
        "missing_review": """
            SELECT COUNT(*)
            FROM supplier_offers AS o
            LEFT JOIN supplier_offer_reviews AS r
                ON r.supplier_offer_id = o.id
            WHERE r.supplier_offer_id IS NULL
        """,
        "unapproved_or_incomplete": """
            SELECT COUNT(*)
            FROM supplier_offers AS o
            JOIN supplier_offer_reviews AS r
                ON r.supplier_offer_id = o.id
            WHERE r.review_status <> 'APPROVED'
               OR r.package_evidence IS NULL
               OR TRIM(r.package_evidence) = ''
               OR r.price_evidence IS NULL
               OR TRIM(r.price_evidence) = ''
               OR r.moq_evidence IS NULL
               OR TRIM(r.moq_evidence) = ''
               OR r.reviewer IS NULL
               OR TRIM(r.reviewer) = ''
               OR r.reviewed_at IS NULL
        """,
        "invalid_price_or_moq": """
            SELECT COUNT(*)
            FROM supplier_offers
            WHERE purchase_price < 0
               OR minimum_order_quantity <= 0
        """,
    }

    results = {}
    for name, sql in checks.items():
        result = run_mysql(database, sql)
        if result.returncode != 0:
            raise SystemExit(result.stderr.strip())
        results[name] = int(result.stdout.strip())


    for name, count in results.items():
        print(f"{name}: {count}")

    if results["offers"] == 0:
        raise SystemExit(
            "BLOCKED: no supplier offers exist; "
            "offer migration has not been demonstrated."
        )

    failures = [
        name
        for name, count in results.items()
        if name != "offers" and count > 0
    ]

    if failures:
        raise SystemExit(
            "BLOCKED: supplier-offer validation failed: "
            + ", ".join(failures)
        )

    print("PASSED: all supplier offers have complete approved reviews.")



if __name__ == "__main__":
    main()
