from tkinter import ttk, messagebox

from app.services.supplier_service import SupplierService


class SupplierFrame(ttk.Frame):
    """Supplier management screen."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)

        self.service = SupplierService()

        self._build_ui()
        self.refresh_suppliers()

    def _build_ui(self):
        title = ttk.Label(
            self,
            text="Suppliers",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w", pady=(0, 15))

        form_frame = ttk.LabelFrame(
            self,
            text="Supplier Details",
            padding=10,
        )
        form_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(form_frame, text="Name:").grid(
            row=0,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.name_entry = ttk.Entry(form_frame, width=40)
        self.name_entry.grid(
            row=0,
            column=1,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Phone:").grid(
            row=1,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.phone_entry = ttk.Entry(form_frame, width=40)
        self.phone_entry.grid(
            row=1,
            column=1,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Email:").grid(
            row=2,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.email_entry = ttk.Entry(form_frame, width=40)
        self.email_entry.grid(
            row=2,
            column=1,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        ttk.Label(form_frame, text="Address:").grid(
            row=3,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.address_entry = ttk.Entry(form_frame, width=40)
        self.address_entry.grid(
            row=3,
            column=1,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(
            row=4,
            column=0,
            columnspan=2,
            pady=(10, 0),
            sticky="w",
        )

        ttk.Button(
            button_frame,
            text="Add",
            command=self.add_supplier,
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Edit",
            command=self.edit_supplier,
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Delete",
            command=self.delete_supplier,
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh_suppliers,
        ).pack(side="left", padx=5)

        form_frame.columnconfigure(1, weight=1)

        table_frame = ttk.LabelFrame(
            self,
            text="Suppliers",
            padding=10,
        )
        table_frame.pack(fill="both", expand=True)

        columns = (
            "id",
            "name",
            "phone",
            "email",
            "address",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
        )

        headings = {
            "id": "ID",
            "name": "Name",
            "phone": "Phone",
            "email": "Email",
            "address": "Address",
        }

        for column, heading in headings.items():
            self.tree.heading(column, text=heading)

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("phone", width=150)
        self.tree.column("email", width=250)
        self.tree.column("address", width=300)

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

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.on_supplier_select,
        )

    def get_selected_id(self):
        selection = self.tree.selection()

        if not selection:
            return None

        values = self.tree.item(selection[0], "values")
        return int(values[0])

    def on_supplier_select(self, event=None):
        supplier_id = self.get_selected_id()

        if supplier_id is None:
            return

        supplier = self.service.get_supplier(supplier_id)

        if supplier is None:
            return

        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, supplier[1] or "")

        self.phone_entry.delete(0, "end")
        self.phone_entry.insert(0, supplier[2] or "")

        self.email_entry.delete(0, "end")
        self.email_entry.insert(0, supplier[3] or "")

        self.address_entry.delete(0, "end")
        self.address_entry.insert(0, supplier[4] or "")

    def add_supplier(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        address = self.address_entry.get().strip()

        try:
            self.service.create_supplier(
                name=name,
                phone=phone,
                email=email,
                address=address,
            )

            self.refresh_suppliers()
            self.clear_form()

            messagebox.showinfo(
                "Success",
                "Supplier added successfully.",
            )

        except ValueError as error:
            messagebox.showerror(
                "Invalid Input",
                str(error),
            )

    def edit_supplier(self):
        supplier_id = self.get_selected_id()

        if supplier_id is None:
            messagebox.showwarning(
                "No Selection",
                "Please select a supplier to edit.",
            )
            return

        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        address = self.address_entry.get().strip()

        try:
            self.service.update_supplier(
                supplier_id=supplier_id,
                name=name,
                phone=phone,
                email=email,
                address=address,
            )

            self.refresh_suppliers()
            self.clear_form()

            messagebox.showinfo(
                "Success",
                "Supplier updated successfully.",
            )

        except ValueError as error:
            messagebox.showerror(
                "Invalid Input",
                str(error),
            )

    def delete_supplier(self):
        supplier_id = self.get_selected_id()

        if supplier_id is None:
            messagebox.showwarning(
                "No Selection",
                "Please select a supplier to delete.",
            )
            return

        supplier_name = self.name_entry.get().strip()

        confirm = messagebox.askyesno(
            "Delete Supplier",
            f"Are you sure you want to delete '{supplier_name}'?",
        )

        if not confirm:
            return

        try:
            self.service.delete_supplier(supplier_id)

            self.refresh_suppliers()
            self.clear_form()

            messagebox.showinfo(
                "Success",
                "Supplier deleted successfully.",
            )

        except ValueError as error:
            messagebox.showerror(
                "Delete Failed",
                str(error),
            )

    def refresh_suppliers(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        suppliers = self.service.get_all_suppliers()

        for supplier in suppliers:
            self.tree.insert(
                "",
                "end",
                values=(
                    supplier[0],
                    supplier[1],
                    supplier[2],
                    supplier[3],
                    supplier[4],
                ),
            )

        self.tree.selection_remove(self.tree.selection())
        self.clear_form()

    def clear_form(self):
        self.name_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.email_entry.delete(0, "end")
        self.address_entry.delete(0, "end")