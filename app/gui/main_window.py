import tkinter as tk
from tkinter import ttk

from app.gui.categories import CategoryFrame
from app.gui.products import ProductFrame
from app.gui.suppliers import SupplierFrame


class MainWindow(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("MySQL Inventory Management")
        self.geometry("1200x700")
        self.minsize(1000, 600)

        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(
            self,
            text="Inventory Management System",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(anchor="w", padx=20, pady=(20, 10))

        notebook = ttk.Notebook(self)
        notebook.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20),
        )

        categories_tab = CategoryFrame(notebook)
        products_tab = ProductFrame(notebook)
        suppliers_tab = SupplierFrame(notebook)

        notebook.add(
            categories_tab,
            text="Categories",
        )

        notebook.add(
            products_tab,
            text="Products",
        )

        notebook.add(
            suppliers_tab,
            text="Suppliers",
        )


def run_app():
    """Start the application."""
    app = MainWindow()
    app.mainloop()