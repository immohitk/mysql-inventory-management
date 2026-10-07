from app.db.connection import DatabaseConnection


class InventoryService:
    """Business logic for inventory stock operations."""

    def __init__(self):
        self.db = DatabaseConnection()

    def get_product_stock(self, product_id):
        """Return the current stock quantity for a product."""
        if not isinstance(product_id, int) or product_id <= 0:
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

    def stock_in(self, product_id, quantity):
        """Increase product stock by the specified quantity."""
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValueError("Product ID must be a positive integer.")

        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Stock-in quantity must be a positive integer.")

        current_stock = self.get_product_stock(product_id)

        query = """
            UPDATE products
            SET quantity = quantity + %s
            WHERE id = %s
        """

        cursor = self.db.execute(
            query,
            (quantity, product_id),
        )

        rows_affected = cursor.rowcount
        cursor.close()

        if rows_affected != 1:
            raise ValueError("Product stock could not be updated.")

        return current_stock + quantity

    def close(self):
        """Close the database connection."""
        self.db.close()