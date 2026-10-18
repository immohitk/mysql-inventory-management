"""Run SQL migrations against isolated test databases only."""

import argparse
import hashlib
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = ROOT / "database" / "migrations"

MYSQL = Path(
    os.environ.get(
        "MYSQL_CLIENT",
        r"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe",
    )
)
LOGIN_PATH = os.environ.get(
    "MYSQL_LOGIN_PATH",
    "inventory-migrations",
)

def run_mysql(database, sql=None, file=None):
    """Run SQL against the explicitly selected test database."""
    command = [
        str(MYSQL),
        f"--login-path={LOGIN_PATH}",
        "--default-character-set=utf8mb4",
        "--database",
        database,
        "--batch",
        "--skip-column-names",
    ]

    if file is not None:
        with file.open("r", encoding="utf-8") as sql_file:
            return subprocess.run(
                command,
                stdin=sql_file,
                text=True,
                capture_output=True,
                check=False,
            )

    command.extend(["--execute", sql])

    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Apply migrations to an isolated test database."
    )
    parser.add_argument("--database", required=True)
    args = parser.parse_args()

    database = args.database.strip()

    if not re.fullmatch(
        r"inventory_migration_[A-Za-z0-9_]+",
        database,
    ):
        parser.error(
            "Database must match inventory_migration_<test_name>."
        )

    if database.lower() == "inventory_db":
        parser.error(
            "Refusing to run migrations against the original inventory_db."
        )


    if not MYSQL.is_file():
        parser.error(f"MySQL client not found: {MYSQL}")


    # Confirm the selected database exists and is reachable.
    result = run_mysql(database, "SELECT DATABASE()")
    if result.returncode != 0:
        parser.error(
            "Cannot connect to the selected test database:\n"
            + result.stderr.strip()
        )

    connected_database = result.stdout.strip()
    if connected_database != database:
        parser.error(
            f"Connected to unexpected database {connected_database!r}; "
            f"expected {database!r}."
        )


    # Inspect existing tables before making any database changes.
    inspection_sql = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
        ORDER BY TABLE_NAME
    """
    result = run_mysql(database, inspection_sql)

    if result.returncode != 0:
        parser.error(
            "Cannot inspect the selected test database schema:\n"
            + result.stderr.strip()
        )

    existing_tables = {
        table.strip()
        for table in result.stdout.splitlines()
        if table.strip()
    }

    base_tables = {
        "categories",
        "suppliers",
        "products",
        "purchases",
        "purchase_items",
        "sales",
        "sale_items",
    }

    if not base_tables.issubset(existing_tables):
        missing_tables = sorted(base_tables - existing_tables)
        parser.error(
            "Database is missing required base tables: "
            + ", ".join(missing_tables)
        )

    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migrations:
        raise RuntimeError(
            f"No migration files found in {MIGRATIONS_DIR}"
        )

    migration_table_groups = {
        "001_create_base_procurement_tables.sql": {
            "units",
            "unit_conversions",
            "package_forms",
        },
        "002_create_package_and_supplier_tables.sql": {
            "package_specifications",
            "package_contents",
            "supplier_offers",
        },
        "003_create_legacy_product_mapping.sql": {
            "legacy_product_mapping",
        },
        "004_supplier_offer_evidence.sql": {
            "supplier_offer_reviews",
        },
    }

    migration_versions = {migration.name for migration in migrations}

    for migration_name, expected_tables in migration_table_groups.items():
        present_tables = expected_tables & existing_tables

        if present_tables and present_tables != expected_tables:
            missing_tables = sorted(expected_tables - present_tables)
            parser.error(
                f"Partial migration state detected for {migration_name}; "
                "missing tables: "
                + ", ".join(missing_tables)
            )

    history_table_exists = "schema_migrations" in existing_tables

    if history_table_exists:
        columns_sql = """
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_KEY,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'schema_migrations'
            ORDER BY ORDINAL_POSITION
        """
        result = run_mysql(database, columns_sql)

        if result.returncode != 0:
            parser.error(
                "Cannot inspect migration history columns:\n"
                + result.stderr.strip()
            )

        history_columns = {}

        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) != 6:
                parser.error(
                    "Migration history table has an invalid column definition."
                )

            (
                name,
                data_type,
                length,
                nullable,
                column_key,
                column_default,
            ) = parts
            history_columns[name.strip()] = {
                "data_type": data_type.strip().lower(),
                "length": length.strip(),
                "nullable": nullable.strip().upper(),
                "column_key": column_key.strip().upper(),
                "default": column_default.strip().lower(),
            }

        version_column = history_columns.get("version")
        applied_at_column = history_columns.get("applied_at")

        if version_column is None or applied_at_column is None:
            missing_columns = sorted(
                {"version", "applied_at"} - set(history_columns)
            )
            parser.error(
                "Migration history table is missing required columns: "
                + ", ".join(missing_columns)
            )

        if (
            version_column["data_type"] != "varchar"
            or version_column["length"] != "255"
            or version_column["nullable"] != "NO"
            or version_column["column_key"] != "PRI"
        ):
            parser.error(
                "Migration history column 'version' must be "
                "VARCHAR(255) NOT NULL PRIMARY KEY."
            )

        if (
            applied_at_column["data_type"] != "timestamp"
            or applied_at_column["nullable"] != "NO"
            or applied_at_column["default"].replace("()", "").strip()
            != "current_timestamp"
        ):
            parser.error(
                "Migration history column 'applied_at' must be "
                "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP."
            )

        result = run_mysql(
            database,
            "SELECT version FROM schema_migrations ORDER BY version",
        )

        if result.returncode != 0:
            parser.error(
                "Cannot inspect existing migration history:\n"
                + result.stderr.strip()
            )

        recorded_versions = {
            version.strip()
            for version in result.stdout.splitlines()
            if version.strip()
        }

        unknown_versions = recorded_versions - migration_versions
        if unknown_versions:
            parser.error(
                "Unknown migration versions recorded: "
                + ", ".join(sorted(unknown_versions))
            )

        for version in recorded_versions:
            expected_tables = migration_table_groups.get(version)

            if expected_tables is None:
                parser.error(
                    f"Migration {version} has no expected-table mapping."
                )

            if not expected_tables.issubset(existing_tables):
                missing_tables = sorted(
                    expected_tables - existing_tables
                )
                parser.error(
                    f"Migration {version} is recorded, but tables are missing: "
                    + ", ".join(missing_tables)
                )

        for version, expected_tables in migration_table_groups.items():
            if (
                expected_tables.issubset(existing_tables)
                and version not in recorded_versions
            ):
                parser.error(
                    f"Migration tables exist without a history record for {version}. "
                    "Inspect the database manually before retrying."
                )
    else:
        migration_tables = set().union(*migration_table_groups.values())
        present_migration_tables = existing_tables & migration_tables

        if present_migration_tables:
            parser.error(
                "Migration-created tables exist but schema_migrations is missing. "
                "Inspect the database manually before retrying."
            )


    # Create the migration history table only after consistency checks pass.
    history_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """
    result = run_mysql(database, history_sql)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    for migration in migrations:
        version = migration.name
        safe_version = version.replace("'", "''")

        result = run_mysql(
            database,
            "SELECT COUNT(*) FROM schema_migrations "
            f"WHERE version = '{safe_version}'",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        if result.stdout.strip() == "1":
            print(f"SKIP: {version} already recorded")
            continue

        print(f"Applying: {version}")
        result = run_mysql(database, file=migration)

        if result.returncode != 0:
            print(result.stderr.strip())
            raise RuntimeError(
                f"{version} failed. MySQL may retain partial DDL. "
                "Inspect the test database before retrying."
            )

        # Record success only after the complete SQL file succeeds.
        result = run_mysql(
            database,
            "INSERT INTO schema_migrations (version) "
            f"VALUES ('{safe_version}')",
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"{version} executed but tracking failed. "
                "Inspect the database before retrying.\n"
                + result.stderr.strip()
            )

        print(f"SUCCESS: {version}")

    print("Migration run finished.")


if __name__ == "__main__":
    main()
