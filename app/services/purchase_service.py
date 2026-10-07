from decimal import Decimal

from app.db.purchase_repository import PurchaseRepository
from app.db.connection import DatabaseConnection


class PurchaseService:
    """Business logic for purchase creation and calculation."""

    def __init__(self):
        self.repository = PurchaseRepository()
        self.db = DatabaseConnection()

    def _validate_supplier(self, supplier_id):
        """Validate that the supplier exists."""
        if not isinstance(supplier_id, int) or supplier_id <= 0:
            raise ValueError("Supplier ID must be a positive integer.")

        cursor = self.db.execute(
            "SELECT id FROM suppliers WHERE id = %s",
            (supplier_id,),
        )
        supplier = cursor.fetchone()
        cursor.close()

        if supplier is None:
            raise ValueError("Supplier does not exist.")

    def _validate_product(self, product_id):
        """Validate that the product exists."""
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValueError("Product ID must be a positive integer.")

        cursor = self.db.execute(
            "SELECT id FROM products WHERE id = %s",
            (product_id,),
        )
        product = cursor.fetchone()
        cursor.close()

        if product is None:
            raise ValueError("Product does not exist.")

    def _validate_quantity(self, quantity):
        """Validate purchase quantity."""
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

    def _validate_unit_cost(self, unit_cost):
        """Validate purchase unit cost."""
        try:
            cost = Decimal(str(unit_cost))
        except (ValueError, TypeError):
            raise ValueError("Unit cost must be a valid number.")

        if cost < 0:
            raise ValueError("Unit cost cannot be negative.")

        return cost

    def calculate_item_subtotal(self, quantity, unit_cost):
        """Calculate subtotal for one purchase item."""
        self._validate_quantity(quantity)
        cost = self._validate_unit_cost(unit_cost)

        return Decimal(quantity) * cost

    def calculate_total(self, items):
        """Calculate total purchase amount from item data."""
        if not items:
            raise ValueError("Purchase must contain at least one item.")

        total = Decimal("0.00")

        for item in items:
            quantity = item["quantity"]
            unit_cost = item["unit_cost"]

            subtotal = self.calculate_item_subtotal(
                quantity,
                unit_cost,
            )

            total += subtotal

        return total

    def prepare_purchase_items(self, items):
        """Validate items and calculate their subtotals."""
        if not items:
            raise ValueError("Purchase must contain at least one item.")

        prepared_items = []

        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            unit_cost = item["unit_cost"]

            self._validate_product(product_id)
            self._validate_quantity(quantity)

            cost = self._validate_unit_cost(unit_cost)

            subtotal = self.calculate_item_subtotal(
                quantity,
                cost,
            )

            prepared_items.append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_cost": cost,
                    "subtotal": subtotal,
                }
            )

        return prepared_items

    def create_purchase(self, supplier_id, purchase_date, items):
        """Prepare a purchase and calculate its total."""
        self._validate_supplier(supplier_id)

        prepared_items = self.prepare_purchase_items(items)

        total_amount = self.calculate_total(prepared_items)

        return {
            "supplier_id": supplier_id,
            "purchase_date": purchase_date,
            "items": prepared_items,
            "total_amount": total_amount,
        }

    def close(self):
        """Close database connections."""
        self.repository.close()
        self.db.close()