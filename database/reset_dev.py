"""Explicitly reset a disposable inventory migration database."""

import argparse
import os
import re
import subprocess
from pathlib import Path

MYSQL = Path(os.environ.get("MYSQL_CLIENT", r"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe"))
LOGIN_PATH = os.environ.get("MYSQL_LOGIN_PATH", "inventory-migrations")
DATABASE_PATTERN = re.compile(r"inventory_migration_[A-Za-z0-9_]+\Z")

def validate_database_name(database):
    """Reject targets outside the disposable migration database namespace."""
    if not DATABASE_PATTERN.fullmatch(database):
        raise ValueError("Database must match inventory_migration_<test_name>.")
    return database

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--confirm-reset", action="store_true")
    parser.add_argument('--confirm-database')
    args = parser.parse_args()

    try:
        database = validate_database_name(args.database.strip())
    except ValueError as exc:
        parser.error(str(exc))

    if args.confirm_database != database:
        parser.error("Confirmation database must exactly match --database.")

    if not args.confirm_reset:
        parser.error("Reset requires the explicit --confirm-reset flag.")

    if not MYSQL.is_file():
        parser.error(f"MySQL client not found: {MYSQL}")

    quoted_database = chr(96) + database + chr(96)
    sql = f"DROP DATABASE IF EXISTS {quoted_database}; CREATE DATABASE {quoted_database};"
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
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:
        parser.error(f"Could not launch MySQL: {exc}")
    if result.returncode != 0:
        parser.error(result.stderr.strip() or "Database reset failed.")
    print(f"Reset completed for {database}.")

if __name__ == "__main__":
    main()
