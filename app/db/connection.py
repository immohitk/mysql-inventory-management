import mysql.connector

from app.config import DATABASE_CONFIG


class DatabaseConnection:
    """Manage the MySQL database connection lifecycle."""

    def __init__(self):
        self.connection = None

    def connect(self):
        """Open a MySQL connection."""
        if self.connection is None or not self.connection.is_connected():
            self.connection = mysql.connector.connect(**DATABASE_CONFIG)

        return self.connection

    def execute(self, query, params=None):
        """Execute a SQL query and return the cursor."""
        connection = self.connect()
        cursor = connection.cursor()

        cursor.execute(query, params or ())

        return cursor

    def commit(self):
        """Commit the current transaction."""
        if self.connection is not None:
            self.connection.commit()

    def rollback(self):
        """Rollback the current transaction."""
        if self.connection is not None:
            self.connection.rollback()

    def close(self):
        """Close the database connection."""
        if self.connection is not None and self.connection.is_connected():
            self.connection.close()

        self.connection = None