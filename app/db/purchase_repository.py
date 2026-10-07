from app.db.connection import DatabaseConnection


class PurchaseRepository:
    """Data access layer for purchase-related database operations."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()
        self._owns_connection = db is None

    def create_purchase(self, supplier_id, purchase_date, total_amount, status="COMPLETED"):
        """Create a purchase record and return the new purchase ID."""
        query = """
            INSERT INTO purchases (
                supplier_id,
                purchase_date,
                total_amount,
                status
            )
            VALUES (%s, %s, %s, %s)
        """

        cursor = self.db.execute(
            query,
            (supplier_id, purchase_date, total_amount, status),
        )

        purchase_id = cursor.lastrowid
        cursor.close()

        return purchase_id

    def create_purchase_item(
        self,
        purchase_id,
        product_id,
        quantity,
        unit_cost,
        subtotal,
    ):
        """Create a purchase item record and return its ID."""
        query = """
            INSERT INTO purchase_items (
                purchase_id,
                product_id,
                quantity,
                unit_cost,
                subtotal
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor = self.db.execute(
            query,
            (
                purchase_id,
                product_id,
                quantity,
                unit_cost,
                subtotal,
            ),
        )

        item_id = cursor.lastrowid
        cursor.close()

        return item_id

    def get_purchase(self, purchase_id):
        """Retrieve a purchase by ID."""
        query = """
            SELECT
                id,
                supplier_id,
                purchase_date,
                total_amount,
                status
            FROM purchases
            WHERE id = %s
        """

        cursor = self.db.execute(query, (purchase_id,))
        purchase = cursor.fetchone()
        cursor.close()

        return purchase

    def get_purchase_items(self, purchase_id):
        """Retrieve all items belonging to a purchase."""
        query = """
            SELECT
                pi.id,
                pi.purchase_id,
                pi.product_id,
                p.sku,
                p.name,
                pi.quantity,
                pi.unit_cost,
                pi.subtotal
            FROM purchase_items pi
            JOIN products p
                ON p.id = pi.product_id
            WHERE pi.purchase_id = %s
            ORDER BY pi.id
        """

        cursor = self.db.execute(query, (purchase_id,))
        items = cursor.fetchall()
        cursor.close()

        return items

    def get_purchase_history(self):
        """Retrieve purchase history with supplier information."""
        query = """
            SELECT
                pu.id,
                pu.purchase_date,
                pu.supplier_id,
                s.name AS supplier_name,
                pu.total_amount,
                pu.status
            FROM purchases pu
            JOIN suppliers s
                ON s.id = pu.supplier_id
            ORDER BY pu.purchase_date DESC, pu.id DESC
        """

        cursor = self.db.execute(query)
        purchases = cursor.fetchall()
        cursor.close()

        return purchases

    def get_products_by_purchase(self, purchase_id):
        """Retrieve products included in a purchase."""
        query = """
            SELECT
                p.id,
                p.sku,
                p.name,
                pi.quantity,
                pi.unit_cost,
                pi.subtotal
            FROM purchase_items pi
            JOIN products p
                ON p.id = pi.product_id
            WHERE pi.purchase_id = %s
            ORDER BY p.name
        """

        cursor = self.db.execute(query, (purchase_id,))
        products = cursor.fetchall()
        cursor.close()

        return products

    def close(self):
        """Close the database connection when owned by this repository."""
        if self._owns_connection:
            self.db.close()
