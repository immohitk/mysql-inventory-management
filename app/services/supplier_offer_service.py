
from decimal import Decimal, InvalidOperation

from mysql.connector import Error

from app.db.connection import DatabaseConnection

from app.repositories.supplier_offer_repository import SupplierOfferRepository


class SupplierOfferService:
    """Manage supplier offers without mixing offer CRUD with review approval."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()
        self._owns_connection = db is None
        self.repository = SupplierOfferRepository(self.db)

    @staticmethod
    def _validate_id(value, field_name):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(f"{field_name} must be a positive integer.")
        return value

    @staticmethod
    def _validate_decimal(value, field_name, scale, minimum):
        if isinstance(value, bool):
            raise ValueError(f"{field_name} must be a valid number.")

        try:
            number = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f"{field_name} must be a valid number.") from None

        if not number.is_finite():
            raise ValueError(f"{field_name} must be a finite number.")

        if number < minimum:
            raise ValueError(f"{field_name} must be at least {minimum}.")

        if number.as_tuple().exponent < -scale:
            raise ValueError(
                f"{field_name} must have at most {scale} decimal places."
            )

        # DECIMAL(12, 4) or DECIMAL(12, 2) allows 8 or 10
        # integer digits respectively.
        max_value = Decimal(10) ** (12 - scale)
        if number >= max_value:
            raise ValueError(f"{field_name} exceeds the supported range.")

        return number

    @classmethod
    def _validate_moq(cls, value):
        return cls._validate_decimal(
            value,
            "Minimum order quantity",
            scale=4,
            minimum=Decimal("0.0001"),
        )

    @classmethod
    def _validate_price(cls, value):
        return cls._validate_decimal(
            value,
            "Purchase price",
            scale=2,
            minimum=Decimal("0"),
        )

    @staticmethod
    def _validate_active(value):
        if not isinstance(value, bool):
            raise ValueError("is_active must be a boolean.")
        return value

    def create_offer(
        self,
        supplier_id,
        product_id,
        package_specification_id,
        minimum_order_quantity=Decimal("1.0000"),
        purchase_price=None,
        is_active=True,
    ):
        """Create an offer and return its new ID."""
        supplier_id = self._validate_id(supplier_id, "Supplier ID")
        product_id = self._validate_id(product_id, "Product ID")
        package_specification_id = self._validate_id(
            package_specification_id,
            "Package specification ID",
        )
        minimum_order_quantity = self._validate_moq(minimum_order_quantity)

        if purchase_price is None:
            raise ValueError("Purchase price is required.")
        purchase_price = self._validate_price(purchase_price)
        is_active = self._validate_active(is_active)

        cursor = None
        try:
            cursor = self.db.execute(
                """
                INSERT INTO supplier_offers (
                    supplier_id,
                    product_id,
                    package_specification_id,
                    minimum_order_quantity,
                    purchase_price,
                    is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    supplier_id,
                    product_id,
                    package_specification_id,
                    minimum_order_quantity,
                    purchase_price,
                    is_active,
                ),
            )
            offer_id = cursor.lastrowid
            cursor.close()
            cursor = None
            self.db.commit()
            return offer_id

        except Error as error:
            if cursor is not None:
                cursor.close()
            self.db.rollback()

            if error.errno == 1062:
                raise ValueError(
                    "An offer already exists for this supplier, product, "
                    "and package specification."
                ) from error
            if error.errno == 1452:
                raise ValueError(
                    "Supplier, product, or package specification does not exist."
                ) from error
            raise

    def get_offer(self, offer_id):
        """Return one offer, or None if it does not exist."""
        offer_id = self._validate_id(offer_id, "Offer ID")
        return self.repository.get_by_id(offer_id)

    def get_all_offers(self, active_only=False):
        """Return offers ordered by ID, optionally excluding inactive offers."""
        if not isinstance(active_only, bool):
            raise ValueError("active_only must be a boolean.")
        return self.repository.list_all(active_only=active_only)

    def get_offers_by_supplier(self, supplier_id, active_only=False):
        """Return offers belonging to one supplier."""
        supplier_id = self._validate_id(supplier_id, "Supplier ID")
        if not isinstance(active_only, bool):
            raise ValueError("active_only must be a boolean.")
        return self.repository.list_by_supplier(
            supplier_id,
            active_only=active_only,
        )

    def get_offers_by_product(self, product_id, active_only=False):
        """Return offers for one product."""
        product_id = self._validate_id(product_id, "Product ID")
        if not isinstance(active_only, bool):
            raise ValueError("active_only must be a boolean.")
        return self.repository.list_by_product(
            product_id,
            active_only=active_only,
        )

    def update_offer(
        self,
        offer_id,
        supplier_id,
        product_id,
        package_specification_id,
        minimum_order_quantity,
        purchase_price,
        is_active=True,
    ):
        """Update offer details while preserving its separate review record."""
        offer_id = self._validate_id(offer_id, "Offer ID")
        supplier_id = self._validate_id(supplier_id, "Supplier ID")
        product_id = self._validate_id(product_id, "Product ID")
        package_specification_id = self._validate_id(
            package_specification_id,
            "Package specification ID",
        )
        minimum_order_quantity = self._validate_moq(minimum_order_quantity)
        purchase_price = self._validate_price(purchase_price)
        is_active = self._validate_active(is_active)

        cursor = None
        try:
            cursor = self.db.execute(
                """
                UPDATE supplier_offers
                SET supplier_id = %s,
                    product_id = %s,
                    package_specification_id = %s,
                    minimum_order_quantity = %s,
                    purchase_price = %s,
                    is_active = %s
                WHERE id = %s
                """,
                (
                    supplier_id,
                    product_id,
                    package_specification_id,
                    minimum_order_quantity,
                    purchase_price,
                    is_active,
                    offer_id,
                ),
            )
            rows_affected = cursor.rowcount
            cursor.close()
            cursor = None

            if rows_affected == 0:
                # A matching row with unchanged values can also report zero.
                check = self.db.execute(
                    "SELECT id FROM supplier_offers WHERE id = %s",
                    (offer_id,),
                )
                try:
                    exists = check.fetchone() is not None
                finally:
                    check.close()

                if not exists:
                    self.db.rollback()
                    raise ValueError("Supplier offer does not exist.")

            self.db.commit()
            return rows_affected

        except Error as error:
            if cursor is not None:
                cursor.close()
            self.db.rollback()

            if error.errno == 1062:
                raise ValueError(
                    "An offer already exists for this supplier, product, "
                    "and package specification."
                ) from error
            if error.errno == 1452:
                raise ValueError(
                    "Supplier, product, or package specification does not exist."
                ) from error
            raise

    def deactivate_offer(self, offer_id):
        """Deactivate an offer without deleting its history."""
        return self._set_active(offer_id, False)

    def activate_offer(self, offer_id):
        """Reactivate an existing offer."""
        return self._set_active(offer_id, True)

    def _set_active(self, offer_id, is_active):
        offer_id = self._validate_id(offer_id, "Offer ID")
        cursor = None
        try:
            cursor = self.db.execute(
                """
                UPDATE supplier_offers
                SET is_active = %s
                WHERE id = %s
                """,
                (is_active, offer_id),
            )
            rows_affected = cursor.rowcount
            cursor.close()
            cursor = None

            if rows_affected == 0:
                check = self.db.execute(
                    "SELECT id FROM supplier_offers WHERE id = %s",
                    (offer_id,),
                )
                try:
                    exists = check.fetchone() is not None
                finally:
                    check.close()

                if not exists:
                    self.db.rollback()
                    raise ValueError("Supplier offer does not exist.")

            self.db.commit()
            return rows_affected

        except Error:
            if cursor is not None:
                cursor.close()
            self.db.rollback()
            raise

    def close(self):
        """Close the database connection only when this service owns it."""
        if self._owns_connection:
            self.db.close()
