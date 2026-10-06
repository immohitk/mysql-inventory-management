from mysql.connector import Error

from app.db.connection import DatabaseConnection


class CategoryService:
    """Provide CRUD operations for product categories."""

    def __init__(self, db=None):
        self.db = db or DatabaseConnection()

    def create_category(self, name, description=None):
        """Create a new category."""
        name = self._validate_name(name)
        description = self._validate_description(description)

        try:
            cursor = self.db.execute(
                """
                INSERT INTO categories (name, description)
                VALUES (%s, %s)
                """,
                (name, description),
            )
            category_id = cursor.lastrowid
            cursor.close()
            self.db.commit()

            return category_id

        except Error as error:
            self.db.rollback()

            if error.errno == 1062:
                raise ValueError("Category name already exists.") from error

            raise

    def get_category(self, category_id):
        """Return a category by ID."""
        if not isinstance(category_id, int) or category_id <= 0:
            raise ValueError("Category ID must be a positive integer.")

        cursor = self.db.execute(
            """
            SELECT id, name, description
            FROM categories
            WHERE id = %s
            """,
            (category_id,),
        )

        category = cursor.fetchone()
        cursor.close()

        return category

    def get_all_categories(self):
        """Return all categories."""
        cursor = self.db.execute(
            """
            SELECT id, name, description
            FROM categories
            ORDER BY id
            """
        )

        categories = cursor.fetchall()
        cursor.close()

        return categories

    def search_categories(self, search_term):
        """Search categories by name."""
        if not isinstance(search_term, str):
            raise ValueError("Search term must be a string.")

        search_term = search_term.strip()

        if not search_term:
            raise ValueError("Search term cannot be empty.")

        cursor = self.db.execute(
            """
            SELECT id, name, description
            FROM categories
            WHERE name LIKE %s
            ORDER BY name
            """,
            (f"%{search_term}%",),
        )

        categories = cursor.fetchall()
        cursor.close()

        return categories

    def update_category(self, category_id, name, description=None):
        """Update an existing category."""
        if not isinstance(category_id, int) or category_id <= 0:
            raise ValueError("Category ID must be a positive integer.")

        name = self._validate_name(name)
        description = self._validate_description(description)

        try:
            cursor = self.db.execute(
                """
                UPDATE categories
                SET name = %s, description = %s
                WHERE id = %s
                """,
                (name, description, category_id),
            )

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected == 0:
                self.db.rollback()
                raise ValueError("Category not found.")

            self.db.commit()

            return rows_affected

        except Error as error:
            self.db.rollback()

            if error.errno == 1062:
                raise ValueError("Category name already exists.") from error

            raise

    def delete_category(self, category_id):
        """Delete an existing category."""
        if not isinstance(category_id, int) or category_id <= 0:
            raise ValueError("Category ID must be a positive integer.")

        try:
            cursor = self.db.execute(
                """
                DELETE FROM categories
                WHERE id = %s
                """,
                (category_id,),
            )

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected == 0:
                self.db.rollback()
                raise ValueError("Category not found.")

            self.db.commit()

            return rows_affected

        except Error as error:
            self.db.rollback()

            if error.errno == 1451:
                raise ValueError(
                    "Category cannot be deleted because products use it."
                ) from error

            raise

    @staticmethod
    def _validate_name(name):
        """Validate and normalize a category name."""
        if not isinstance(name, str):
            raise ValueError("Category name must be a string.")

        name = name.strip()

        if not name:
            raise ValueError("Category name cannot be empty.")

        if len(name) > 100:
            raise ValueError("Category name must not exceed 100 characters.")

        return name

    @staticmethod
    def _validate_description(description):
        """Validate and normalize a category description."""
        if description is None:
            return None

        if not isinstance(description, str):
            raise ValueError("Category description must be a string.")

        description = description.strip()

        if not description:
            return None

        return description