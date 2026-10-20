
"""Create a fresh inventory migration database without overwriting one."""

import argparse
import os
import re
import subprocess
from pathlib import Path

MYSQL = Path(
    os.environ.get(
        "MYSQL_CLIENT",
        r"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe",
    )
)
LOGIN_PATH = os.environ.get("MYSQL_LOGIN_PATH", "").strip()
DATABASE_PATTERN = re.compile(r"inventory_migration_[A-Za-z0-9_]+\Z")


def validate_database_name(database):
    """Restrict targets to the migration-test namespace."""
    if not DATABASE_PATTERN.fullmatch(database):
        raise ValueError(
            "Database must match inventory_migration_<test_name>."
        )
    return database



def run_mysql(sql):
    """Execute SQL using the explicitly configured login path."""
    command = [
        str(MYSQL),
        f"--login-path={LOGIN_PATH}",
        "--default-character-set=utf8mb4",
        "--batch",
        "--skip-column-names",
        "--execute",
        sql,
    ]
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(f"Could not launch MySQL: {exc}") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--confirm-create", action="store_true")
    parser.add_argument("--confirm-database")
    args = parser.parse_args()

    try:
        database = validate_database_name(args.database.strip())
    except ValueError as exc:
        parser.error(str(exc))

    if args.confirm_database != database:
        parser.error("Confirmation database must exactly match --database.")

    if not args.confirm_create:
        parser.error("Creation requires --confirm-create.")

    if not LOGIN_PATH:
        parser.error(
            "Set MYSQL_LOGIN_PATH to an explicitly configured, "
            "least-privileged database account. No default is permitted."
        )

    if LOGIN_PATH.casefold() in {
        "inventory-migrations",
        "root",
        "admin",
        "administrator",
    }:
        parser.error("Refusing a known administrative/default login path.")

    if not MYSQL.is_file():
        parser.error(f"MySQL client not found: {MYSQL}")

    # Read-only preflight: refuse to overwrite an existing database.
    result = run_mysql(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.SCHEMATA "
        f"WHERE SCHEMA_NAME = '{database}';"
    )

    if result.returncode != 0:
        parser.error(
            result.stderr.strip() or "Could not inspect database target."
        )

    if result.stdout.strip() != "0":
        parser.error(
            f"Refusing to overwrite existing database {database!r}. "
            "Choose a new, verified disposable database name."
        )

    result = run_mysql(f"CREATE DATABASE `{database}`;")

    if result.returncode != 0:
        parser.error(
            result.stderr.strip() or "Database creation failed."
        )

    print(f"Created fresh database {database}.")


if __name__ == "__main__":
    main()
