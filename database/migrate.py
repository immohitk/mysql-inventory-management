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


    # Existing migration records have no verified checksums.
    # Do not backfill them without validating the applied SQL.
    # Create the migration history table if needed.
    history_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """
    result = run_mysql(database, history_sql)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migrations:
        raise RuntimeError(
            f"No migration files found in {MIGRATIONS_DIR}"
        )

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
