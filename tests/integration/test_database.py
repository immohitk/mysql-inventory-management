"""Fail-closed helpers for opt-in MySQL integration tests."""

import os
import re

import mysql.connector


DATABASE_PATTERN = re.compile(r"inventory_migration_[A-Za-z0-9_]+\Z")

REQUIRED_MIGRATIONS = {
    "001_create_base_procurement_tables.sql",
    "002_create_package_and_supplier_tables.sql",
    "003_create_legacy_product_mapping.sql",
    "004_supplier_offer_evidence.sql",
}


REQUIRED_SCHEMA = {
    "categories": {
        "id",
        "name",
        "description",
    },
    "suppliers": {
        "id",
        "name",
    },
    "products": {
        "id",
        "category_id",
        "supplier_id",
        "sku",
        "name",
        "description",
        "cost_price",
        "selling_price",
        "quantity",
        "reorder_level",
    },
    "units": {
        "id",
        "name",
        "code",
        "unit_type",
    },
    "package_forms": {
        "id",
        "name",
    },
    "package_specifications": {
        "id",
        "package_form_id",
        "name",
    },
    "supplier_offers": {
        "id",
        "supplier_id",
        "product_id",
        "package_specification_id",
        "minimum_order_quantity",
        "purchase_price",
        "is_active",
    },
    "supplier_offer_reviews": {
        "supplier_offer_id",
    },
    "legacy_product_mapping": {
        "product_id",
    },
    "schema_migrations": {
        "version",
    },
}



def _validate_required_schema(cursor):
    """Fail if required integration-test tables or columns are missing."""
    for table, required_columns in REQUIRED_SCHEMA.items():
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
            """,
            (table,),
        )
        existing_columns = {row[0] for row in cursor.fetchall()}
        missing_columns = required_columns - existing_columns

        if missing_columns:
            raise RuntimeError(
                f"Required schema is missing for table {table!r}: "
                + ", ".join(sorted(missing_columns))
            )



def connect_test_database():
    """Connect only to an explicitly approved integration-test database."""
    if os.environ.get("RUN_MYSQL_INTEGRATION_TESTS") != "1":
        raise RuntimeError("MySQL integration tests are disabled.")

    database = os.environ.get("INVENTORY_TEST_DATABASE", "").strip()
    approved_database = os.environ.get(
        "INVENTORY_TEST_DATABASE_CONFIRM", ""
    ).strip()

    if not DATABASE_PATTERN.fullmatch(database):
        raise RuntimeError(
            "INVENTORY_TEST_DATABASE must use the "
            "inventory_migration_<test_name> namespace."
        )

    if approved_database != database:
        raise RuntimeError(
            "INVENTORY_TEST_DATABASE_CONFIRM must exactly match "
            "INVENTORY_TEST_DATABASE."
        )

    disposable_approval = os.environ.get(
        "INVENTORY_TEST_DATABASE_DISPOSABLE", ""
    ).strip()

    if disposable_approval != database:
        raise RuntimeError(
            "INVENTORY_TEST_DATABASE_DISPOSABLE must exactly match "
            "the explicitly approved disposable test database."
        )

    try:
        port = int(os.environ.get("INVENTORY_TEST_DB_PORT", "3306"))
    except ValueError as error:
        raise RuntimeError(
            "INVENTORY_TEST_DB_PORT must be an integer between 1 and 65535."
        ) from error

    if not 1 <= port <= 65535:
        raise RuntimeError(
            "INVENTORY_TEST_DB_PORT must be an integer between 1 and 65535."
        )

    config = {
        "host": os.environ.get("INVENTORY_TEST_DB_HOST", "localhost").strip(),
        "port": port,
        "user": os.environ.get("INVENTORY_TEST_DB_USER", "").strip(),
        "password": os.environ.get("INVENTORY_TEST_DB_PASSWORD", ""),
        "database": database,
    }

    if not config["user"]:
        raise RuntimeError(
            "INVENTORY_TEST_DB_USER must be configured."
        )

    if config["user"].casefold() in {
        "root",
        "admin",
        "administrator",
        "mysql.session",
        "mysql.sys",
    }:
        raise RuntimeError(
            "INVENTORY_TEST_DB_USER must be a dedicated "
            "non-administrative test account."
        )

    connection = mysql.connector.connect(**config)

    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT DATABASE()")
            row = cursor.fetchone()
            actual_database = row[0] if row else None

            if actual_database != database:
                raise RuntimeError(
                    f"Connected to {actual_database!r}; "
                    f"expected {database!r}."
                )

            cursor.execute("SELECT version FROM schema_migrations")
            applied_migrations = {row[0] for row in cursor.fetchall()}

            missing = REQUIRED_MIGRATIONS - applied_migrations
            if missing:
                raise RuntimeError(
                    "Required migrations are missing: "
                    + ", ".join(sorted(missing))
                )

            _validate_required_schema(cursor)
        finally:
            cursor.close()

        return connection
    except Exception:
        connection.close()
        raise


class DatabaseAdapter:
    """Adapt an approved raw MySQL connection to the application's DB API."""

    def __init__(self, connection):
        if connection is None:
            raise ValueError("An approved test connection is required.")
        self.connection = connection

    def execute(self, query, params=None):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
        except Exception:
            cursor.close()
            raise
        return cursor

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()
