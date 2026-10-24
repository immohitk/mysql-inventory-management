
from decimal import Decimal, InvalidOperation

from app.db.connection import DatabaseConnection


class UnitService:
    """Manage units and dimension-safe unit conversions."""

    UNIT_TYPES = frozenset({"COUNT", "MASS", "VOLUME"})

    def __init__(self, db=None):
        self.db = db if db is not None else DatabaseConnection()
        self._owns_connection = db is None

    @staticmethod
    def _validate_id(value, field_name):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(f"{field_name} must be a positive integer.")
        return value

    @classmethod
    def _validate_unit_type(cls, unit_type):
        if not isinstance(unit_type, str):
            raise ValueError("Unit type must be COUNT, MASS, or VOLUME.")

        unit_type = unit_type.strip().upper()
        if unit_type not in cls.UNIT_TYPES:
            raise ValueError("Unit type must be COUNT, MASS, or VOLUME.")
        return unit_type

    @staticmethod
    def _validate_text(value, field_name, max_length):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required.")

        value = value.strip()
        if len(value) > max_length:
            raise ValueError(
                f"{field_name} must be at most {max_length} characters."
            )
        return value

    @staticmethod
    def _validate_factor(value):
        if isinstance(value, bool):
            raise ValueError("Conversion factor must be a positive number.")

        try:
            factor = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(
                "Conversion factor must be a valid number."
            ) from None

        if not factor.is_finite() or factor <= 0:
            raise ValueError("Conversion factor must be a positive number.")

        if factor.as_tuple().exponent < -8:
            raise ValueError(
                "Conversion factor must have at most 8 decimal places."
            )

        if factor >= Decimal("10000000000"):
            raise ValueError("Conversion factor exceeds the supported range.")

        return factor

    def _execute_write(self, query, params):
        """Execute a write, committing on success and rolling back on failure."""
        cursor = None
        try:
            cursor = self.db.execute(query, params)
            result = cursor.lastrowid
            cursor.close()
            cursor = None
            self.db.commit()
            return result
        except Exception:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
            self.db.rollback()
            raise

    def create_unit(self, name, code, unit_type):
        name = self._validate_text(name, "Unit name", 100)
        code = self._validate_text(code, "Unit code", 30)
        unit_type = self._validate_unit_type(unit_type)

        return self._execute_write(
            """
            INSERT INTO units (name, code, unit_type)
            VALUES (%s, %s, %s)
            """,
            (name, code, unit_type),
        )

    def list_units(self):
        cursor = self.db.execute(
            "SELECT id, name, code, unit_type FROM units ORDER BY id"
        )
        try:
            return cursor.fetchall()
        finally:
            cursor.close()

    def create_conversion(self, from_unit_id, to_unit_id, factor):
        from_unit_id = self._validate_id(from_unit_id, "From unit ID")
        to_unit_id = self._validate_id(to_unit_id, "To unit ID")
        factor = self._validate_factor(factor)

        cursor = self.db.execute(
            """
            SELECT id, unit_type
            FROM units
            WHERE id IN (%s, %s)
            ORDER BY id
            """,
            (from_unit_id, to_unit_id),
        )
        try:
            units = cursor.fetchall()
        finally:
            cursor.close()

        by_id = {row[0]: row[1] for row in units}

        if from_unit_id not in by_id or to_unit_id not in by_id:
            raise ValueError("Both conversion units must exist.")

        if by_id[from_unit_id] != by_id[to_unit_id]:
            raise ValueError(
                "Cannot convert between incompatible unit dimensions."
            )

        return self._execute_write(
            """
            INSERT INTO unit_conversions (
                from_unit_id,
                from_unit_type,
                to_unit_id,
                to_unit_type,
                conversion_factor
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                from_unit_id,
                by_id[from_unit_id],
                to_unit_id,
                by_id[to_unit_id],
                factor,
            ),
        )

    def close(self):
        if self._owns_connection:
            self.db.close()
