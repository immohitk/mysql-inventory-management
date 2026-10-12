"""Validate legacy product mappings in an isolated migration test database."""

import argparse
import re

try:
    from database.migrate import run_mysql
except ModuleNotFoundError:
    from migrate import run_mysql


def main():
    parser = argparse.ArgumentParser(
        description="Validate legacy product mappings in an isolated test database."
    )
    parser.add_argument("--database", required=True)
    args = parser.parse_args()

    database = args.database.strip()
    if not re.fullmatch(r"inventory_migration_[A-Za-z0-9_]+", database):
        parser.error("Use an isolated inventory_migration_<test_name> database.")

    checks = {
        "source_products": "SELECT COUNT(1) FROM products",
        "mappings": "SELECT COUNT(1) FROM legacy_product_mapping",
        "missing_product_mappings": """
            SELECT COUNT(1)
            FROM products AS p
            LEFT JOIN legacy_product_mapping AS m ON m.product_id = p.id
            WHERE m.product_id IS NULL
        """,
        "missing_product_reference": """
            SELECT COUNT(1)
            FROM legacy_product_mapping AS m
            LEFT JOIN products AS p ON p.id = m.product_id
            WHERE p.id IS NULL
        """,
        "invalid_status": """
            SELECT COUNT(1)
            FROM legacy_product_mapping
            WHERE mapping_status NOT IN ('PENDING', 'APPROVED')
        """,
        "pending_without_notes": """
            SELECT COUNT(1)
            FROM legacy_product_mapping
            WHERE mapping_status = 'PENDING'
              AND (mapping_notes IS NULL OR TRIM(mapping_notes) = '')
        """,
        "approved_without_unit": """
            SELECT COUNT(1)
            FROM legacy_product_mapping AS m
            LEFT JOIN units AS u ON u.id = m.inventory_unit_id
            WHERE m.mapping_status = 'APPROVED'
              AND (m.inventory_unit_id IS NULL OR u.id IS NULL)
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

    if results["mappings"] == 0:
        raise SystemExit("BLOCKED: no legacy product mappings were found.")

    failures = [
        name
        for name, count in results.items()
        if name not in {"source_products", "mappings"} and count > 0
    ]

    if results["mappings"] != results["source_products"]:
        failures.append("mapping_count_does_not_match_source_count")

    if failures:
        raise SystemExit(
            "BLOCKED: legacy mapping validation failed: "
            + ", ".join(failures)
        )

    print(
        "PASSED: every source product has a mapping; "
        "unverified mappings are documented and approved mappings have valid units."
    )


if __name__ == "__main__":
    main()
