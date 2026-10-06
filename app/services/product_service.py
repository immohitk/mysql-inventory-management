from decimal import Decimal

from mysql.connector import Error

from app.db.connection import DatabaseConnection


class ProductService:
    """Provide CRUD operations for products."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    def create_product(
        self,
        category_id,
        supplier_id,
        sku,
        name,
        description=None,
        cost_price=0,
        selling_price=0,
        quantity=0,
        reorder_level=0,
    ):
        """Create a new product."""
        category_id = self._validate_id(category_id, "Category ID")
        supplier_id = self._validate_id(supplier_id, "Supplier ID")
        sku = self._validate_sku(sku)
        name = self._validate_name(name)
        description = self._validate_description(description)
        cost_price = self._validate_price(cost_price, "Cost price")
        selling_price = self._validate_price(selling_price, "Selling price")
        quantity = self._validate_quantity(quantity, "Quantity")
        reorder_level = self._validate_quantity(reorder_level, "Reorder level")

        if selling_price < cost_price:
            raise ValueError("Selling price cannot be lower than cost price.")

        try:
            cursor = self.db.execute(
                """
                INSERT INTO products (
                    category_id,
                    supplier_id,
                    sku,
                    name,
                    description,
                    cost_price,
                    selling_price,
                    quantity,
                    reorder_level
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    category_id,
                    supplier_id,
                    sku,
                    name,
                    description,
                    cost_price,
                    selling_price,
                    quantity,
                    reorder_level,
                ),
            )

            product_id = cursor.lastrowid
            cursor.close()
            self.db.commit()

            return product_id

        except Error as error:
            self.db.rollback()

            if error.errno == 1062:
                raise ValueError("Product SKU already exists.") from error

            if error.errno == 1452:
                raise ValueError(
                    "Category or supplier does not exist."
                ) from error

            raise

    def get_product(self, product_id):
        """Return a product by ID."""
        product_id = self._validate_id(product_id, "Product ID")

        cursor = self.db.execute(
            """
            SELECT
                id,
                category_id,
                supplier_id,
                sku,
                name,
                description,
                cost_price,
                selling_price,
                quantity,
                reorder_level
            FROM products
            WHERE id = %s
            """,
            (product_id,),
        )

        product = cursor.fetchone()
        cursor.close()

        return product

    def get_all_products(self):
        """Return all products."""
        cursor = self.db.execute(
            """
            SELECT
                id,
                category_id,
                supplier_id,
                sku,
                name,
                description,
                cost_price,
                selling_price,
                quantity,
                reorder_level
            FROM products
            ORDER BY id
            """
        )

        products = cursor.fetchall()
        cursor.close()

        return products

    def search_products(self, search_term):
        """Search products by SKU or name."""
        if not isinstance(search_term, str):
            raise ValueError("Search term must be a string.")

        search_term = search_term.strip()

        if not search_term:
            raise ValueError("Search term cannot be empty.")

        pattern = f"%{search_term}%"

        cursor = self.db.execute(
            """
            SELECT
                id,
                category_id,
                supplier_id,
                sku,
                name,
                description,
                cost_price,
                selling_price,
                quantity,
                reorder_level
            FROM products
            WHERE sku LIKE %s
               OR name LIKE %s
            ORDER BY name
            """,
            (pattern, pattern),
        )

        products = cursor.fetchall()
        cursor.close()

        return products

    def filter_by_category(self, category_id):
        """Return products belonging to a category."""
        category_id = self._validate_id(category_id, "Category ID")

        cursor = self.db.execute(
            """
            SELECT
                id,
                category_id,
                supplier_id,
                sku,
                name,
                description,
                cost_price,
                selling_price,
                quantity,
                reorder_level
            FROM products
            WHERE category_id = %s
            ORDER BY name
            """,
            (category_id,),
        )

        products = cursor.fetchall()
        cursor.close()

        return products

    def filter_by_supplier(self, supplier_id):
        """Return products belonging to a supplier."""
        supplier_id = self._validate_id(supplier_id, "Supplier ID")

        cursor = self.db.execute(
            """
            SELECT
                id,
                category_id,
                supplier_id,
                sku,
                name,
                description,
                cost_price,
                selling_price,
                quantity,
                reorder_level
            FROM products
            WHERE supplier_id = %s
            ORDER BY name
            """,
            (supplier_id,),
        )

        products = cursor.fetchall()
        cursor.close()

        return products

    def update_product(
        self,
        product_id,
        category_id,
        supplier_id,
        sku,
        name,
        description=None,
        cost_price=0,
        selling_price=0,
        quantity=0,
        reorder_level=0,
    ):
        """Update an existing product."""
        product_id = self._validate_id(product_id, "Product ID")
        category_id = self._validate_id(category_id, "Category ID")
        supplier_id = self._validate_id(supplier_id, "Supplier ID")
        sku = self._validate_sku(sku)
        name = self._validate_name(name)
        description = self._validate_description(description)
        cost_price = self._validate_price(cost_price, "Cost price")
        selling_price = self._validate_price(selling_price, "Selling price")
        quantity = self._validate_quantity(quantity, "Quantity")
        reorder_level = self._validate_quantity(reorder_level, "Reorder level")

        if selling_price < cost_price:
            raise ValueError("Selling price cannot be lower than cost price.")

        try:
            cursor = self.db.execute(
                """
                UPDATE products
                SET
                    category_id = %s,
                    supplier_id = %s,
                    sku = %s,
                    name = %s,
                    description = %s,
                    cost_price = %s,
                    selling_price = %s,
                    quantity = %s,
                    reorder_level = %s
                WHERE id = %s
                """,
                (
                    category_id,
                    supplier_id,
                    sku,
                    name,
                    description,
                    cost_price,
                    selling_price,
                    quantity,
                    reorder_level,
                    product_id,
                ),
            )

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected == 0:
                self.db.rollback()
                raise ValueError("Product not found.")

            self.db.commit()

            return rows_affected

        except Error as error:
            self.db.rollback()

            if error.errno == 1062:
                raise ValueError("Product SKU already exists.") from error

            if error.errno == 1452:
                raise ValueError(
                    "Category or supplier does not exist."
                ) from error

            raise

    def delete_product(self, product_id):
        """Delete an existing product."""
        product_id = self._validate_id(product_id, "Product ID")

        try:
            cursor = self.db.execute(
                """
                DELETE FROM products
                WHERE id = %s
                """,
                (product_id,),
            )

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected == 0:
                self.db.rollback()
                raise ValueError("Product not found.")

            self.db.commit()

            return rows_affected

        except Error as error:
            self.db.rollback()

            if error.errno == 1451:
                raise ValueError(
                    "Product cannot be deleted because it is used "
                    "in purchase or sale records."
                ) from error

            raise

    @staticmethod
    def _validate_id(value, field_name):
        """Validate a positive integer ID."""
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer.")

        return value

    @staticmethod
    def _validate_sku(sku):
        """Validate and normalize a product SKU."""
        if not isinstance(sku, str):
            raise ValueError("SKU must be a string.")

        sku = sku.strip()

        if not sku:
            raise ValueError("SKU cannot be empty.")

        if len(sku) > 50:
            raise ValueError("SKU must not exceed 50 characters.")

        return sku

    @staticmethod
    def _validate_name(name):
        """Validate and normalize a product name."""
        if not isinstance(name, str):
            raise ValueError("Product name must be a string.")

        name = name.strip()

        if not name:
            raise ValueError("Product name cannot be empty.")

        if len(name) > 150:
            raise ValueError("Product name must not exceed 150 characters.")

        return name

    @staticmethod
    def _validate_description(description):
        """Validate and normalize a product description."""
        if description is None:
            return None

        if not isinstance(description, str):
            raise ValueError("Product description must be a string.")

        description = description.strip()

        if not description:
            return None

        return description

    @staticmethod
    def _validate_price(value, field_name):
        """Validate a non-negative monetary value."""
        try:
            value = Decimal(str(value))
        except (TypeError, ValueError, ArithmeticError) as error:
            raise ValueError(f"{field_name} must be a valid number.") from error

        if value < 0:
            raise ValueError(f"{field_name} cannot be negative.")

        return value

    @staticmethod
    def _validate_quantity(value, field_name):
        """Validate a non-negative integer quantity."""
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{field_name} must be a non-negative integer.")

        return value