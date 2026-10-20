"""Safely seed repeatable demo data into an isolated migration database."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

MYSQL = Path(os.environ.get("MYSQL_CLIENT", r"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe"))
LOGIN_PATH = os.environ.get("MYSQL_LOGIN_PATH", "").strip()

ADMIN_LOGIN_PATHS = {
    "inventory-migrations",
    "root",
    "admin",
    "administrator",
}
DEMO_PREFIX = "inventory_migration_"

CATEGORIES = [
    ("Electronics", "Electronic devices and components"),
    ("Office Supplies", "Office and stationery supplies"),
    ("Home Appliances", "Household electrical appliances"),
    ("Computer Accessories", "Accessories for computers"),
]

SUPPLIERS = [
    ("TechSource Supplies", "techsource@example.test"),
    ("OfficeMart Distributors", "officemart@example.test"),
    ("HomeTech Wholesale", "hometech@example.test"),
]

PRODUCTS = [
    ("ELEC-001", "Wireless Mouse", "Electronics", "TechSource Supplies", 350, 599, 40, 5),
    ("ELEC-002", "USB Keyboard", "Electronics", "TechSource Supplies", 500, 799, 30, 5),
    ("COMP-001", "USB-C Hub", "Computer Accessories", "TechSource Supplies", 900, 1499, 20, 3),
    ("COMP-002", "Laptop Stand", "Computer Accessories", "TechSource Supplies", 650, 1099, 15, 3),
    ("OFF-001", "A4 Paper Ream", "Office Supplies", "OfficeMart Distributors", 220, 299, 50, 10),
    ("OFF-002", "Ballpoint Pens Pack", "Office Supplies", "OfficeMart Distributors", 60, 99, 60, 10),
    ("HOME-001", "Electric Kettle", "Home Appliances", "HomeTech Wholesale", 750, 1199, 12, 3),
    ("HOME-002", "Desk Fan", "Home Appliances", "HomeTech Wholesale", 900, 1399, 10, 2),
]


def sql_string(value):
    """Quote a fixed demo value as a MySQL string literal."""
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def build_seed_sql():
    statements = ["START TRANSACTION;"]

    for name, description in CATEGORIES:
        statements.append(
            "INSERT INTO categories (name, description) "
            f"SELECT {sql_string(name)}, {sql_string(description)} "
            "FROM DUAL WHERE NOT EXISTS ("
            f"SELECT 1 FROM categories WHERE name = {sql_string(name)});"
        )

    for name, email in SUPPLIERS:
        statements.append(
            "INSERT INTO suppliers (name, email) "
            f"SELECT {sql_string(name)}, {sql_string(email)} "
            "FROM DUAL WHERE NOT EXISTS ("
            f"SELECT 1 FROM suppliers WHERE name = {sql_string(name)});"
        )

    for sku, name, category, supplier, cost, price, quantity, reorder in PRODUCTS:
        statements.append(
            "INSERT INTO products "
            "(category_id, supplier_id, sku, name, description, cost_price, "
            "selling_price, quantity, reorder_level) "
            "SELECT c.id, s.id, "
            f"{sql_string(sku)}, {sql_string(name)}, {sql_string('Demo product')}, "
            f"{cost}, {price}, {quantity}, {reorder} "
            "FROM categories c CROSS JOIN suppliers s "
            f"WHERE c.name = {sql_string(category)} "
            f"AND s.name = {sql_string(supplier)} "
            "AND NOT EXISTS (SELECT 1 FROM products "
            f"WHERE sku = {sql_string(sku)});"
        )

    statements.extend([
        "COMMIT;",
        "SELECT 'categories' AS entity, COUNT(*) AS total FROM categories "
        "UNION ALL SELECT 'suppliers', COUNT(*) FROM suppliers "
        "UNION ALL SELECT 'products', COUNT(*) FROM products;",
    ])
    return "\n".join(statements)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        required=True,
        help="Target isolated migration database, e.g. inventory_migration_dev",
    )
    parser.add_argument("--confirm-disposable", action="store_true")
    parser.add_argument("--confirm-database")
    args = parser.parse_args()

    database = args.database.strip()
    if (
        not database.startswith(DEMO_PREFIX)
        or len(database) <= len(DEMO_PREFIX)
        or not all(
            char.isascii() and (char.isalnum() or char == "_")
            for char in database
        )
    ):
        parser.error(
            f"database must be a valid name starting with {DEMO_PREFIX!r}"
        )

    if args.confirm_database != database:
        parser.error("Confirmation database must exactly match --database.")

    if not args.confirm_disposable:
        parser.error(
            "Seeding requires --confirm-disposable for a verified disposable database."
        )

    if not LOGIN_PATH:
        parser.error(
            "Set MYSQL_LOGIN_PATH to an explicitly configured, "
            "least-privileged database account. No default is permitted."
        )

    if LOGIN_PATH.casefold() in ADMIN_LOGIN_PATHS:
        parser.error("Refusing a known administrative/default login path.")

    if not MYSQL.is_file():
        print(f"MySQL client not found: {MYSQL}", file=sys.stderr)
        return 1

    try:
        connection_check = subprocess.run(
            [
                str(MYSQL),
                f"--login-path={LOGIN_PATH}",
                f"--database={database}",
                "--batch",
                "--skip-column-names",
                "--execute",
                "SELECT DATABASE()",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(f"Could not launch MySQL: {exc}", file=sys.stderr)
        return 1

    if connection_check.returncode != 0:
        print(
            connection_check.stderr.strip() or "MySQL connection failed.",
            file=sys.stderr,
        )
        return 1

    connected_database = connection_check.stdout.strip()
    if connected_database != database:
        print(
            f"Connected to unexpected database {connected_database!r}; "
            f"expected {database!r}.",
            file=sys.stderr,
        )
        return 1

    try:
        result = subprocess.run(
            [
                str(MYSQL),
                f"--login-path={LOGIN_PATH}",
                f"--database={database}",
                "--batch",
                "--skip-column-names",
                "--execute",
                build_seed_sql(),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(f"Could not launch MySQL: {exc}", file=sys.stderr)
        return 1

    if result.returncode != 0:
        print(result.stderr.strip() or "MySQL seed failed.", file=sys.stderr)
        print(
            "If the transaction was interrupted, verify the database before retrying.",
            file=sys.stderr,
        )
        return 1

    print(f"Demo seed completed for {database}.")
    print(result.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
