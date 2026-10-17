
class SupplierOfferRepository:
    """Read supplier offers using parameterized SQL."""

    _SELECT_COLUMNS = """
        id, supplier_id, product_id, package_specification_id,
        minimum_order_quantity, purchase_price, is_active,
        created_at, updated_at
    """

    def __init__(self, db):
        if db is None:
            raise ValueError("A database connection wrapper is required.")
        self.db = db

    def get_by_id(self, offer_id):
        """Return one offer by ID, or None if it does not exist."""
        cursor = self.db.execute(
            f"""
            SELECT {self._SELECT_COLUMNS}
            FROM supplier_offers
            WHERE id = %s
            """,
            (offer_id,),
        )
        try:
            return cursor.fetchone()
        finally:
            cursor.close()

    def list_all(self, active_only=False):
        """List offers by ID, optionally filtering to active offers."""
        query = f"""
            SELECT {self._SELECT_COLUMNS}
            FROM supplier_offers
        """
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY id"

        cursor = self.db.execute(query)
        try:
            return cursor.fetchall()
        finally:
            cursor.close()

    def list_by_supplier(self, supplier_id, active_only=False):
        """List offers for a supplier, optionally filtering active offers."""
        query = f"""
            SELECT {self._SELECT_COLUMNS}
            FROM supplier_offers
            WHERE supplier_id = %s
        """
        params = [supplier_id]
        if active_only:
            query += " AND is_active = TRUE"
        query += " ORDER BY id"

        cursor = self.db.execute(query, tuple(params))
        try:
            return cursor.fetchall()
        finally:
            cursor.close()

    def list_by_product(self, product_id, active_only=False):
        """List offers for a product, optionally filtering active offers."""
        query = f"""
            SELECT {self._SELECT_COLUMNS}
            FROM supplier_offers
            WHERE product_id = %s
        """
        params = [product_id]
        if active_only:
            query += " AND is_active = TRUE"
        query += " ORDER BY id"

        cursor = self.db.execute(query, tuple(params))
        try:
            return cursor.fetchall()
        finally:
            cursor.close()
