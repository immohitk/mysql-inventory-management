import tkinter as tk
from datetime import date
from decimal import Decimal
from tkinter import messagebox, ttk

from app.db.connection import DatabaseConnection
from app.db.purchase_repository import PurchaseRepository
from app.services.purchase_service import PurchaseService


class PurchaseFrame(ttk.Frame):
    """GUI for creating purchases and updating stock."""

    def __init__(self, parent, on_purchase_saved=None):
        super().__init__(parent)

        self.service = PurchaseService()
        self.lookup_db = DatabaseConnection()
        self.history_repository = PurchaseRepository(
            self.lookup_db
        )

        self.suppliers = []
        self.products = []
        self.items = []
        self.on_purchase_saved = on_purchase_saved

        self._build_ui()
        self._load_suppliers()
        self._load_products()
        self._load_purchase_history()

    def _build_ui(self):
        """Build the purchase form and item list."""

        title = ttk.Label(
            self,
            text="Purchases",
            font=("Arial", 16, "bold"),
        )
        title.pack(pady=10)

        form = ttk.Frame(self)
        form.pack(
            fill="x",
            padx=10,
            pady=5,
        )

        ttk.Label(
            form,
            text="Supplier",
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.supplier_var = tk.StringVar(
            value="Select Supplier"
        )

        self.supplier_combo = ttk.Combobox(
            form,
            textvariable=self.supplier_var,
            state="readonly",
            width=40,
        )
        self.supplier_combo.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="w",
        )

        ttk.Label(
            form,
            text="Product",
        ).grid(
            row=1,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.product_var = tk.StringVar(
            value="Select Product"
        )

        self.product_combo = ttk.Combobox(
            form,
            textvariable=self.product_var,
            state="readonly",
            width=40,
        )
        self.product_combo.grid(
            row=1,
            column=1,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.product_combo.bind(
            "<<ComboboxSelected>>",
            self._on_product_selected,
        )

        ttk.Label(
            form,
            text="Quantity",
        ).grid(
            row=2,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.quantity_var = tk.StringVar()

        ttk.Entry(
            form,
            textvariable=self.quantity_var,
            width=20,
        ).grid(
            row=2,
            column=1,
            padx=5,
            pady=5,
            sticky="w",
        )

        ttk.Label(
            form,
            text="Unit Cost",
        ).grid(
            row=3,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.unit_cost_var = tk.StringVar()

        ttk.Entry(
            form,
            textvariable=self.unit_cost_var,
            width=20,
        ).grid(
            row=3,
            column=1,
            padx=5,
            pady=5,
            sticky="w",
        )

        button_frame = ttk.Frame(form)
        button_frame.grid(
            row=4,
            column=0,
            columnspan=2,
            pady=5,
        )

        ttk.Button(
            button_frame,
            text="Add Item",
            command=self.add_item,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            button_frame,
            text="Delete Selected Item",
            command=self.delete_selected_item,
        ).pack(
            side="left",
            padx=5,
        )

        ttk.Button(
            button_frame,
            text="Reset Purchase",
            command=self.reset_purchase,
        ).pack(
            side="left",
            padx=5,
        )

        columns = (
            "product_id",
            "product",
            "quantity",
            "unit_cost",
            "subtotal",
        )

        items_frame = ttk.Frame(self)
        items_frame.pack(
            fill="both",
            expand=False,
            padx=10,
            pady=5,
        )

        self.items_tree = ttk.Treeview(
            items_frame,
            columns=columns,
            show="headings",
            height=4,
        )

        items_scrollbar = ttk.Scrollbar(
            items_frame,
            orient="vertical",
            command=self.items_tree.yview,
        )

        self.items_tree.configure(
            yscrollcommand=items_scrollbar.set,
        )

        self.items_tree.heading(
            "product_id",
            text="Product ID",
            anchor="center",
        )
        self.items_tree.heading(
            "product",
            text="Product",
            anchor="center",
        )
        self.items_tree.heading(
            "quantity",
            text="Quantity",
            anchor="center",
        )
        self.items_tree.heading(
            "unit_cost",
            text="Unit Cost",
            anchor="center",
        )
        self.items_tree.heading(
            "subtotal",
            text="Subtotal",
            anchor="center",
        )

        self.items_tree.column(
            "product_id",
            width=90,
            anchor="center",
        )
        self.items_tree.column(
            "product",
            width=250,
            anchor="center",
        )
        self.items_tree.column(
            "quantity",
            width=100,
            anchor="center",
        )
        self.items_tree.column(
            "unit_cost",
            width=120,
            anchor="center",
        )
        self.items_tree.column(
            "subtotal",
            width=120,
            anchor="center",
        )

        self.items_tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        items_scrollbar.pack(
            side="right",
            fill="y",
        )

        self.total_label = ttk.Label(
            self,
            text="Total: ₹0.00",
            font=("Arial", 12, "bold"),
        )
        self.total_label.pack(
            anchor="e",
            padx=10,
            pady=2,
        )

        ttk.Button(
            self,
            text="Save Purchase",
            command=self.save_purchase,
        ).pack(pady=5)

        history_title = ttk.Label(
            self,
            text="Purchase History",
            font=("Arial", 12, "bold"),
        )
        history_title.pack(
            anchor="w",
            padx=10,
            pady=(5, 3),
        )

        history_columns = (
            "purchase_id",
            "purchase_date",
            "supplier",
            "total_amount",
            "status",
        )

        history_frame = ttk.Frame(self)
        history_frame.pack(
            fill="both",
            expand=False,
            padx=10,
            pady=(0, 5),
        )

        self.history_tree = ttk.Treeview(
            history_frame,
            columns=history_columns,
            show="headings",
            height=5,
        )

        history_scrollbar = ttk.Scrollbar(
            history_frame,
            orient="vertical",
            command=self.history_tree.yview,
        )

        self.history_tree.configure(
            yscrollcommand=history_scrollbar.set,
        )

        self.history_tree.heading(
            "purchase_id",
            text="ID",
            anchor="center",
        )
        self.history_tree.heading(
            "purchase_date",
            text="Date",
            anchor="center",
        )
        self.history_tree.heading(
            "supplier",
            text="Supplier",
            anchor="center",
        )
        self.history_tree.heading(
            "total_amount",
            text="Total Amount",
            anchor="center",
        )
        self.history_tree.heading(
            "status",
            text="Status",
            anchor="center",
        )

        self.history_tree.column(
            "purchase_id",
            width=70,
            anchor="center",
        )
        self.history_tree.column(
            "purchase_date",
            width=160,
            anchor="center",
        )
        self.history_tree.column(
            "supplier",
            width=220,
            anchor="center",
        )
        self.history_tree.column(
            "total_amount",
            width=140,
            anchor="center",
        )
        self.history_tree.column(
            "status",
            width=120,
            anchor="center",
        )

        self.history_tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        history_scrollbar.pack(
            side="right",
            fill="y",
        )

        self.history_tree.bind(
            "<Double-1>",
            self._on_purchase_selected,
        )

    def _load_suppliers(self):
        """Load suppliers into the supplier dropdown."""

        query = """
            SELECT
                id,
                name
            FROM suppliers
            ORDER BY id
        """

        cursor = self.lookup_db.execute(query)
        self.suppliers = cursor.fetchall()
        cursor.close()

        supplier_values = [
            f"{supplier_id} - {name}"
            for supplier_id, name in self.suppliers
        ]

        self.supplier_combo["values"] = supplier_values
        self.supplier_var.set("Select Supplier")

    def _load_products(self):
        """Load products into the product dropdown."""

        query = """
            SELECT
                id,
                sku,
                name,
                cost_price
            FROM products
            ORDER BY id
        """

        cursor = self.lookup_db.execute(query)
        self.products = cursor.fetchall()
        cursor.close()

        product_values = [
            f"{product_id} - {sku} - {name}"
            for product_id, sku, name, cost_price in self.products
        ]

        self.product_combo["values"] = product_values
        self.product_var.set("Select Product")

    def _load_purchase_history(self):
        """Load purchase history into the history table."""

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # The history repository uses a persistent connection.
        # Roll back any previous read transaction so the next SELECT
        # sees purchases committed by the PurchaseService connection.
        self.history_repository.db.rollback()

        purchases = self.history_repository.get_purchase_history()

        for purchase in purchases:
            (
                purchase_id,
                purchase_date,
                supplier_id,
                supplier_name,
                total_amount,
                status,
            ) = purchase

            self.history_tree.insert(
                "",
                "end",
                values=(
                    purchase_id,
                    purchase_date,
                    supplier_name,
                    f"₹{Decimal(str(total_amount)):.2f}",
                    status,
                ),
            )

    def _on_purchase_selected(self, event=None):
        """Open purchase details for the selected purchase."""

        selected_items = self.history_tree.selection()

        if not selected_items:
            return

        selected_item = selected_items[0]

        values = self.history_tree.item(
            selected_item,
            "values",
        )

        purchase_id = int(values[0])

        self._show_purchase_details(purchase_id)

    def _show_purchase_details(self, purchase_id):
        """Show selected purchase details in a popup."""

        purchase_items = self.history_repository.get_purchase_items(
            purchase_id
        )

        popup = tk.Toplevel(self)
        popup.title(
            f"Purchase Details - #{purchase_id}"
        )
        popup.geometry("850x350")
        popup.transient(
            self.winfo_toplevel()
        )
        popup.grab_set()

        title = ttk.Label(
            popup,
            text=f"Purchase Details - #{purchase_id}",
            font=("Arial", 14, "bold"),
        )
        title.pack(pady=10)

        columns = (
            "product_id",
            "sku",
            "product",
            "quantity",
            "unit_cost",
            "subtotal",
        )

        details_tree = ttk.Treeview(
            popup,
            columns=columns,
            show="headings",
            height=8,
        )

        details_tree.heading(
            "product_id",
            text="Product ID",
            anchor="center",
        )
        details_tree.heading(
            "sku",
            text="SKU",
            anchor="center",
        )
        details_tree.heading(
            "product",
            text="Product",
            anchor="center",
        )
        details_tree.heading(
            "quantity",
            text="Quantity",
            anchor="center",
        )
        details_tree.heading(
            "unit_cost",
            text="Unit Cost",
            anchor="center",
        )
        details_tree.heading(
            "subtotal",
            text="Subtotal",
            anchor="center",
        )

        details_tree.column(
            "product_id",
            width=90,
            anchor="center",
        )
        details_tree.column(
            "sku",
            width=120,
            anchor="center",
        )
        details_tree.column(
            "product",
            width=220,
            anchor="center",
        )
        details_tree.column(
            "quantity",
            width=100,
            anchor="center",
        )
        details_tree.column(
            "unit_cost",
            width=120,
            anchor="center",
        )
        details_tree.column(
            "subtotal",
            width=120,
            anchor="center",
        )

        details_tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        for item in purchase_items:
            (
                item_id,
                purchase_id,
                product_id,
                sku,
                name,
                quantity,
                unit_cost,
                subtotal,
            ) = item

            details_tree.insert(
                "",
                "end",
                values=(
                    product_id,
                    sku,
                    name,
                    quantity,
                    f"₹{Decimal(str(unit_cost)):.2f}",
                    f"₹{Decimal(str(subtotal)):.2f}",
                ),
            )

        ttk.Button(
            popup,
            text="Close",
            command=popup.destroy,
        ).pack(pady=10)

    def _on_product_selected(self, event=None):
        """Populate unit cost when a product is selected."""

        selected_index = self.product_combo.current()

        if selected_index < 0:
            return

        product_id, sku, name, cost_price = self.products[
            selected_index
        ]

        self.unit_cost_var.set(
            f"{Decimal(str(cost_price)):.2f}"
        )

    def _get_selected_supplier_id(self):
        """Return the selected supplier ID."""

        selected_index = self.supplier_combo.current()

        if selected_index < 0:
            raise ValueError(
                "Please select a supplier."
            )

        supplier_id = self.suppliers[selected_index][0]

        return supplier_id

    def _get_selected_product(self):
        """Return the selected product information."""

        selected_index = self.product_combo.current()

        if selected_index < 0:
            raise ValueError(
                "Please select a product."
            )

        return self.products[selected_index]

    def add_item(self):
        """Add the selected product to the current purchase."""

        try:
            product_id, sku, name, cost_price = (
                self._get_selected_product()
            )

            quantity = int(
                self.quantity_var.get()
            )

            unit_cost = Decimal(
                self.unit_cost_var.get()
            )

            subtotal = self.service.calculate_item_subtotal(
                quantity,
                unit_cost,
            )

            item = {
                "product_id": product_id,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "subtotal": subtotal,
            }

            self.items.append(item)

            # A purchase belongs to one supplier.
            # Lock the supplier after the first item is added
            # so items cannot be saved under different suppliers
            # within the same purchase.
            self.supplier_combo.configure(
                state="disabled"
            )

            self.items_tree.insert(
                "",
                "end",
                values=(
                    product_id,
                    f"{sku} - {name}",
                    quantity,
                    f"₹{unit_cost:.2f}",
                    f"₹{subtotal:.2f}",
                ),
            )

            total = self.service.calculate_total(
                self.items
            )

            self.total_label.config(
                text=f"Total: ₹{total:.2f}"
            )

            self.product_combo.set(
                "Select Product"
            )
            self.quantity_var.set("")
            self.unit_cost_var.set("")

        except (ValueError, TypeError) as error:
            messagebox.showerror(
                "Invalid Item",
                str(error),
            )

    def delete_selected_item(self):
        """Remove the selected item from the current purchase."""

        selected_items = self.items_tree.selection()

        if not selected_items:
            messagebox.showwarning(
                "No Item Selected",
                "Please select an item to delete.",
            )
            return

        selected_item = selected_items[0]
        selected_index = self.items_tree.index(
            selected_item
        )

        del self.items[selected_index]
        self.items_tree.delete(selected_item)

        total = self.service.calculate_total(
            self.items
        )

        self.total_label.config(
            text=f"Total: ₹{total:.2f}"
        )

        # If no items remain, allow a different supplier to be selected.
        if not self.items:
            self.supplier_combo.configure(
                state="readonly"
            )

    def reset_purchase(self):
        """Clear the entire current purchase form."""

        if self.items:
            confirm = messagebox.askyesno(
                "Reset Purchase",
                "Remove all items from the current purchase?",
            )

            if not confirm:
                return

        self._reset_form()

    def save_purchase(self):
        """Save the current purchase."""

        try:
            supplier_id = (
                self._get_selected_supplier_id()
            )

            if not self.items:
                raise ValueError(
                    "Purchase must contain at least one item."
                )

            purchase_id = self.service.save_purchase(
                supplier_id=supplier_id,
                purchase_date=date.today(),
                items=self.items,
            )

            messagebox.showinfo(
                "Purchase Saved",
                f"Purchase #{purchase_id} saved successfully.",
            )

            self._reset_form()
            self._load_purchase_history()

            if self.on_purchase_saved:
                self.on_purchase_saved()

        except (ValueError, TypeError) as error:
            messagebox.showerror(
                "Purchase Error",
                str(error),
            )

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                str(error),
            )

    def _reset_form(self):
        """Reset the purchase form after a successful save."""

        self.items.clear()

        self.items_tree.delete(
            *self.items_tree.get_children()
        )

        self.total_label.config(
            text="Total: ₹0.00"
        )

        self.supplier_combo.configure(
            state="readonly"
        )
        self.supplier_combo.set(
            "Select Supplier"
        )
        self.product_combo.set(
            "Select Product"
        )
        self.quantity_var.set("")
        self.unit_cost_var.set("")

    def destroy(self):
        """Close database connections before destroying the frame."""

        self.service.close()
        self.lookup_db.close()

        super().destroy()
