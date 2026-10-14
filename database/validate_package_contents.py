"""Validate package-content mappings in an isolated migration database."""

import argparse
import re

try:
    from database.migrate import run_mysql
except ModuleNotFoundError:
    from migrate import run_mysql


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate package-content mappings in an isolated "
            "migration test database."
        )
    )
    parser.add_argument("--database", required=True)
    args = parser.parse_args()

    database = args.database.strip()

    if not re.fullmatch(r"inventory_migration_[A-Za-z0-9_]+", database):
        parser.error(
            "Use an isolated inventory_migration_<test_name> database."
        )

    checks = {
        "package_specifications": """
            SELECT COUNT(*)
            FROM package_specifications
        """,
        
        "package_contents": """
            SELECT COUNT(*)
            FROM package_contents
        """,
        
        "specifications_without_contents": """
            SELECT COUNT(*)
            FROM package_specifications AS ps
            WHERE NOT EXISTS (
                SELECT 1
                FROM package_contents AS pc
                WHERE pc.package_specification_id = ps.id
            )
        """,
        
        "contents_without_specification": """
            SELECT COUNT(*)
            FROM package_contents AS pc
            LEFT JOIN package_specifications AS ps
                ON ps.id = pc.package_specification_id
            WHERE ps.id IS NULL
        """,
        
        "contents_without_valid_unit": """
            SELECT COUNT(*)
            FROM package_contents AS pc
            LEFT JOIN units AS u ON u.id = pc.unit_id
            WHERE u.id IS NULL
        """,
        
        "contents_with_invalid_quantity": """
            SELECT COUNT(*)
            FROM package_contents
            WHERE quantity <= 0
        """,
        
        "contents_with_invalid_form": """
            SELECT COUNT(*)
            FROM package_contents AS pc
            LEFT JOIN package_forms AS pf
                ON pf.id = pc.package_form_id
            WHERE pc.package_form_id IS NOT NULL
              AND pf.id IS NULL
        """,
        
        "contents_with_invalid_parent": """
            SELECT COUNT(*)
            FROM package_contents AS child
            LEFT JOIN package_contents AS parent
                ON parent.id = child.parent_content_id
               AND parent.package_specification_id =
                   child.package_specification_id
            WHERE child.parent_content_id IS NOT NULL
              AND parent.id IS NULL
        """,

        "parent_chains_with_cycles": """
            WITH RECURSIVE parent_walk
                (start_id, current_id, path, has_cycle) AS (
                SELECT
                    id,
                    id,
                    CAST(CONCAT(',', id, ',') AS CHAR(4000)),
                    0
                FROM package_contents

                UNION ALL

                SELECT
                    pw.start_id,
                    pc.parent_content_id,
                    CONCAT(pw.path, pc.parent_content_id, ','),
                    LOCATE(
                        CONCAT(',', pc.parent_content_id, ','),
                        pw.path
                    ) > 0
                FROM parent_walk AS pw
                JOIN package_contents AS pc
                    ON pc.id = pw.current_id
                WHERE pc.parent_content_id IS NOT NULL
                  AND pw.has_cycle = 0
            )
            SELECT COUNT(DISTINCT start_id)
            FROM parent_walk
            WHERE has_cycle = 1
        """,

        "offers_without_package_contents": """
            SELECT COUNT(*)
            FROM supplier_offers AS so
            WHERE NOT EXISTS (
                SELECT 1
                FROM package_contents AS pc
                WHERE pc.package_specification_id =
                      so.package_specification_id
            )
        """,
    }

    results = {}

    for name, sql in checks.items():
        result = run_mysql(database, sql)

        if result.returncode != 0:
            raise SystemExit(
                f"BLOCKED: could not run {name}: {result.stderr.strip()}"
            )

        try:
            results[name] = int(result.stdout.strip())
        except ValueError:
            raise SystemExit(
                f"BLOCKED: invalid count returned for {name}."
            ) from None

    for name, count in results.items():
        print(f"{name}: {count}")

    if results["package_specifications"] == 0:
        raise SystemExit(
            "BLOCKED: no package specifications exist; "
            "package-content migration has not been demonstrated."
        )

    if results["package_contents"] == 0:
        raise SystemExit(
            "BLOCKED: no package contents exist; "
            "package-content migration has not been demonstrated."
        )

    failures = [
        name
        for name, count in results.items()
        if name not in {"package_specifications", "package_contents"}
        and count > 0
    ]

    if failures:
        raise SystemExit(
            "BLOCKED: package-content validation failed: "
            + ", ".join(failures)
        )

    print(
        "STRUCTURAL CHECKS PASSED: package references and quantities "
        "are structurally valid. This does not prove that real-world "
        "package contents or quantities have been verified."
    )


if __name__ == "__main__":
    main()
