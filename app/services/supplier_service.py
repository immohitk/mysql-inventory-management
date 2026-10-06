from mysql.connector import Error

from app.db.connection import DatabaseConnection


class SupplierService:
    """Provide CRUD operations for suppliers."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    def create_supplier(self, name, phone=None, email=None, address=None):
        """Create a new supplier."""
        name = self._validate_name(name)
        phone = self._validate_optional_text(phone, "Phone", 30)
        email = self._validate_email(email)
        address = self._validate_optional_text(address, "Address", 255)

        try:
            cursor = self.db.execute(
                """
                INSERT INTO suppliers (name, phone, email, address)
                VALUES (%s, %s, %s, %s)
                """,
                (name, phone, email, address),
            )

            supplier_id = cursor.lastrowid
            cursor.close()
            self.db.commit()

            return supplier_id

        except Error as error:
            self.db.rollback()

            if error.errno == 1062:
                raise ValueError("Supplier name already exists.") from error

            raise

    def get_supplier(self, supplier_id):
        """Return a supplier by ID."""
        supplier_id = self._validate_id(supplier_id)

        cursor = self.db.execute(
            """
            SELECT id, name, phone, email, address
            FROM suppliers
            WHERE id = %s
            """,
            (supplier_id,),
        )

        supplier = cursor.fetchone()
        cursor.close()

        return supplier

    def get_all_suppliers(self):
        """Return all suppliers."""
        cursor = self.db.execute(
            """
            SELECT id, name, phone, email, address
            FROM suppliers
            ORDER BY id
            """
        )

        suppliers = cursor.fetchall()
        cursor.close()

        return suppliers

    def search_suppliers(self, search_term):
        """Search suppliers by name, phone, or email."""
        if not isinstance(search_term, str):
            raise ValueError("Search term must be a string.")

        search_term = search_term.strip()

        if not search_term:
            raise ValueError("Search term cannot be empty.")

        pattern = f"%{search_term}%"

        cursor = self.db.execute(
            """
            SELECT id, name, phone, email, address
            FROM suppliers
            WHERE name LIKE %s
               OR phone LIKE %s
               OR email LIKE %s
            ORDER BY name
            """,
            (pattern, pattern, pattern),
        )

        suppliers = cursor.fetchall()
        cursor.close()

        return suppliers

    def update_supplier(
        self,
        supplier_id,
        name,
        phone=None,
        email=None,
        address=None,
    ):
        """Update an existing supplier."""
        supplier_id = self._validate_id(supplier_id)
        name = self._validate_name(name)
        phone = self._validate_optional_text(phone, "Phone", 30)
        email = self._validate_email(email)
        address = self._validate_optional_text(address, "Address", 255)

        try:
            cursor = self.db.execute(
                """
                UPDATE suppliers
                SET
                    name = %s,
                    phone = %s,
                    email = %s,
                    address = %s
                WHERE id = %s
                """,
                (
                    name,
                    phone,
                    email,
                    address,
                    supplier_id,
                ),
            )

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected == 0:
                self.db.rollback()
                raise ValueError("Supplier not found.")

            self.db.commit()

            return rows_affected

        except Error as error:
            self.db.rollback()

            if error.errno == 1062:
                raise ValueError("Supplier name already exists.") from error

            raise

    def delete_supplier(self, supplier_id):
        """Delete an existing supplier."""
        supplier_id = self._validate_id(supplier_id)

        try:
            cursor = self.db.execute(
                """
                DELETE FROM suppliers
                WHERE id = %s
                """,
                (supplier_id,),
            )

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected == 0:
                self.db.rollback()
                raise ValueError("Supplier not found.")

            self.db.commit()

            return rows_affected

        except Error as error:
            self.db.rollback()

            if error.errno == 1451:
                raise ValueError(
                    "Supplier cannot be deleted because products "
                    "or purchases use it."
                ) from error

            raise

    @staticmethod
    def _validate_id(supplier_id):
        """Validate a positive integer supplier ID."""
        if (
            not isinstance(supplier_id, int)
            or isinstance(supplier_id, bool)
            or supplier_id <= 0
        ):
            raise ValueError("Supplier ID must be a positive integer.")

        return supplier_id

    @staticmethod
    def _validate_name(name):
        """Validate and normalize a supplier name."""
        if not isinstance(name, str):
            raise ValueError("Supplier name must be a string.")

        name = name.strip()

        if not name:
            raise ValueError("Supplier name cannot be empty.")

        if len(name) > 150:
            raise ValueError(
                "Supplier name must not exceed 150 characters."
            )

        return name

    @staticmethod
    def _validate_optional_text(value, field_name, max_length):
        """Validate an optional text field."""
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string.")

        value = value.strip()

        if not value:
            return None

        if len(value) > max_length:
            raise ValueError(
                f"{field_name} must not exceed {max_length} characters."
            )

        return value

    @staticmethod
    def _validate_email(email):
        """Validate an optional email address."""
        if email is None:
            return None

        if not isinstance(email, str):
            raise ValueError("Email must be a string.")

        email = email.strip()

        if not email:
            return None

        if len(email) > 150:
            raise ValueError("Email must not exceed 150 characters.")

        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("Email must be a valid email address.")

        return email