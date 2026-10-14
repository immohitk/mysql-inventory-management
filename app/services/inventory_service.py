from decimal import Decimal, InvalidOperation

from app.db.connection import DatabaseConnection


class InventoryService:
    """Business logic for inventory stock operations."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()
        self._owns_connection = db is None

    def get_product_stock(self, product_id):
        """Return the current stock quantity for a product."""
        if (
            not isinstance(product_id, int)
            or isinstance(product_id, bool)
            or product_id <= 0
        ):
            raise ValueError("Product ID must be a positive integer.")

        cursor = self.db.execute(
            "SELECT quantity FROM products WHERE id = %s",
            (product_id,),
        )
        product = cursor.fetchone()
        cursor.close()

        if product is None:
            raise ValueError("Product does not exist.")

        return product[0]

    @staticmethod
    def _validate_quantity(quantity):
        """Convert a valid positive quantity to Decimal."""
        if isinstance(quantity, bool):
            raise ValueError("Stock-in quantity must be a positive number.")

        try:
            quantity = Decimal(str(quantity))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(
                "Stock-in quantity must be a valid number."
            ) from None

        if not quantity.is_finite() or quantity <= 0:
            raise ValueError(
                "Stock-in quantity must be a positive number."
            )

        if quantity.as_tuple().exponent < -4:
            raise ValueError(
                "Stock-in quantity must have at most 4 decimal places."
            )

        if quantity >= Decimal("10000000000"):
            raise ValueError(
                "Stock-in quantity exceeds the supported range."
            )

        return quantity

    def stock_in(self, product_id, quantity):
        """Increase product stock by a positive decimal quantity."""
        if (
            not isinstance(product_id, int)
            or isinstance(product_id, bool)
            or product_id <= 0
        ):
            raise ValueError("Product ID must be a positive integer.")

        quantity = self._validate_quantity(quantity)
        current_stock = self.get_product_stock(product_id)

        cursor = self.db.execute(
            """
            UPDATE products
            SET quantity = quantity + %s
            WHERE id = %s
            """,
            (quantity, product_id),
        )

        rows_affected = cursor.rowcount
        cursor.close()

        if rows_affected != 1:
            raise ValueError("Product stock could not be updated.")

        return Decimal(str(current_stock)) + quantity

    def close(self):
        """Close the database connection when owned by this service."""
        if self._owns_connection:
            self.db.close()
