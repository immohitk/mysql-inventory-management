import tkinter as tk
from tkinter import ttk, messagebox

from app.services.product_service import ProductService


class ProductFrame(ttk.Frame):
    """Display the product management screen."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)

        self.service = ProductService()

        self._build_ui()

    def _build_ui(self):
        title = ttk.Label(
            self,
            text="Products",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w", pady=(0, 15))

        form_frame = ttk.LabelFrame(
            self,
            text="Product Details",
            padding=10,
        )
        form_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(form_frame, text="SKU:").grid(
            row=0,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.sku_entry = ttk.Entry(form_frame, width=30)
        self.sku_entry.grid(
            row=0,
            column=1,
            padx=(0, 15),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Name:").grid(
            row=0,
            column=2,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.name_entry = ttk.Entry(form_frame, width=30)
        self.name_entry.grid(
            row=0,
            column=3,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Category ID:").grid(
            row=1,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.category_id_entry = ttk.Entry(form_frame, width=30)
        self.category_id_entry.grid(
            row=1,
            column=1,
            padx=(0, 15),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Supplier ID:").grid(
            row=1,
            column=2,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.supplier_id_entry = ttk.Entry(form_frame, width=30)
        self.supplier_id_entry.grid(
            row=1,
            column=3,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Cost Price:").grid(
            row=2,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.cost_price_entry = ttk.Entry(form_frame, width=30)
        self.cost_price_entry.grid(
            row=2,
            column=1,
            padx=(0, 15),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Selling Price:").grid(
            row=2,
            column=2,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.selling_price_entry = ttk.Entry(form_frame, width=30)
        self.selling_price_entry.grid(
            row=2,
            column=3,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Quantity:").grid(
            row=3,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.quantity_entry = ttk.Entry(form_frame, width=30)
        self.quantity_entry.grid(
            row=3,
            column=1,
            padx=(0, 15),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Reorder Level:").grid(
            row=3,
            column=2,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.reorder_level_entry = ttk.Entry(form_frame, width=30)
        self.reorder_level_entry.grid(
            row=3,
            column=3,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Description:").grid(
            row=4,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.description_entry = ttk.Entry(form_frame, width=30)
        self.description_entry.grid(
            row=4,
            column=1,
            columnspan=3,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(
            row=5,
            column=0,
            columnspan=4,
            pady=(10, 0),
            sticky="w",
        )

        ttk.Button(
            button_frame,
            text="Add",
            command=self.add_product,
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Edit",
            command=self.edit_product,
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Delete",
            command=self.delete_product,
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh_products,
        ).pack(side="left", padx=5)

        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        table_frame = ttk.LabelFrame(
            self,
            text="Products",
            padding=10,
        )
        table_frame.pack(fill="both", expand=True)

        columns = (
            "id",
            "sku",
            "name",
            "category_id",
            "supplier_id",
            "cost_price",
            "selling_price",
            "quantity",
            "reorder_level",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.on_product_select,
        )

        headings = {
            "id": "ID",
            "sku": "SKU",
            "name": "Name",
            "category_id": "Category ID",
            "supplier_id": "Supplier ID",
            "cost_price": "Cost Price",
            "selling_price": "Selling Price",
            "quantity": "Quantity",
            "reorder_level": "Reorder Level",
        }

        for column, heading in headings.items():
            self.tree.heading(column, text=heading)

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("sku", width=100, anchor="center")
        self.tree.column("name", width=180, anchor="center")
        self.tree.column("category_id", width=100, anchor="center")
        self.tree.column("supplier_id", width=100, anchor="center")
        self.tree.column("cost_price", width=100, anchor="center")
        self.tree.column("selling_price", width=110, anchor="center")
        self.tree.column("quantity", width=80, anchor="center")
        self.tree.column("reorder_level", width=100, anchor="center")

        horizontal_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview,
        )

        vertical_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )

        self.tree.configure(
            xscrollcommand=horizontal_scrollbar.set,
            yscrollcommand=vertical_scrollbar.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.refresh_products()

    def add_product(self):
        """Add a new product."""
        try:
            sku = self.sku_entry.get().strip()
            name = self.name_entry.get().strip()
            category_id = int(self.category_id_entry.get().strip())
            supplier_id = int(self.supplier_id_entry.get().strip())
            cost_price = float(self.cost_price_entry.get().strip())
            selling_price = float(self.selling_price_entry.get().strip())
            quantity = int(self.quantity_entry.get().strip())
            reorder_level = int(self.reorder_level_entry.get().strip())
            description = self.description_entry.get().strip()

            self.service.create_product(
                category_id=category_id,
                supplier_id=supplier_id,
                sku=sku,
                name=name,
                description=description,
                cost_price=cost_price,
                selling_price=selling_price,
                quantity=quantity,
                reorder_level=reorder_level,
            )

            self.refresh_products()
            self.clear_form()

            messagebox.showinfo(
                "Success",
                "Product added successfully.",
            )

        except ValueError as error:
            messagebox.showerror(
                "Invalid Input",
                str(error),
            )

    def refresh_products(self):
        """Reload products from the database."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.service.db.rollback()

        products = self.service.get_all_products()

        for product in products:
            self.tree.insert(
                "",
                "end",
                values=(
                    product[0],
                    product[3],
                    product[4],
                    product[1],
                    product[2],
                    product[6],
                    product[7],
                    product[8],
                    product[9],
                ),
            )

        self.tree.selection_remove(self.tree.selection())
        self.clear_form()

    def on_product_select(self, event):
        """Load the selected product into the form."""
        selected = self.tree.selection()

        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        product_id = int(values[0])

        product = self.service.get_product(product_id)

        if product is None:
            return

        self.sku_entry.delete(0, tk.END)
        self.sku_entry.insert(0, product[3])

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, product[4])

        self.category_id_entry.delete(0, tk.END)
        self.category_id_entry.insert(0, product[1])

        self.supplier_id_entry.delete(0, tk.END)
        self.supplier_id_entry.insert(0, product[2])

        self.cost_price_entry.delete(0, tk.END)
        self.cost_price_entry.insert(0, product[6])

        self.selling_price_entry.delete(0, tk.END)
        self.selling_price_entry.insert(0, product[7])

        self.quantity_entry.delete(0, tk.END)
        self.quantity_entry.insert(0, product[8])

        self.reorder_level_entry.delete(0, tk.END)
        self.reorder_level_entry.insert(0, product[9])

        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, product[5])

    def edit_product(self):
        """Update the selected product."""
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Please select a product to edit.",
            )
            return

        values = self.tree.item(selected[0], "values")
        product_id = int(values[0])

        try:
            sku = self.sku_entry.get().strip()
            name = self.name_entry.get().strip()
            category_id = int(self.category_id_entry.get().strip())
            supplier_id = int(self.supplier_id_entry.get().strip())
            cost_price = float(self.cost_price_entry.get().strip())
            selling_price = float(self.selling_price_entry.get().strip())
            quantity = int(self.quantity_entry.get().strip())
            reorder_level = int(self.reorder_level_entry.get().strip())
            description = self.description_entry.get().strip()

            self.service.update_product(
                product_id=product_id,
                category_id=category_id,
                supplier_id=supplier_id,
                sku=sku,
                name=name,
                description=description,
                cost_price=cost_price,
                selling_price=selling_price,
                quantity=quantity,
                reorder_level=reorder_level,
            )

            self.refresh_products()
            self.clear_form()

            messagebox.showinfo(
                "Success",
                "Product updated successfully.",
            )

        except ValueError as error:
            messagebox.showerror(
                "Invalid Input",
                str(error),
            )

    def delete_product(self):
        """Delete the selected product."""
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Please select a product to delete.",
            )
            return

        values = self.tree.item(selected[0], "values")
        product_id = int(values[0])
        product_name = values[2]

        confirm = messagebox.askyesno(
            "Delete Product",
            f"Are you sure you want to delete '{product_name}'?",
        )

        if not confirm:
            return

        try:
            self.service.delete_product(product_id)

            self.refresh_products()
            self.clear_form()

            messagebox.showinfo(
                "Success",
                "Product deleted successfully.",
            )

        except ValueError as error:
            messagebox.showerror(
                "Delete Failed",
                str(error),
            )

    def clear_form(self):
        """Clear all product form fields."""
        self.sku_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.category_id_entry.delete(0, tk.END)
        self.supplier_id_entry.delete(0, tk.END)
        self.cost_price_entry.delete(0, tk.END)
        self.selling_price_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.reorder_level_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)