import tkinter as tk
from tkinter import messagebox, ttk

from app.services.category_service import CategoryService


class CategoryFrame(ttk.Frame):
    """Display the category management screen."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)

        self.service = CategoryService()

        self._build_ui()
        self.refresh_categories()

    def _build_ui(self):
        title = ttk.Label(
            self,
            text="Categories",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w", pady=(0, 15))

        form_frame = ttk.LabelFrame(
            self,
            text="Category Details",
            padding=10,
        )
        form_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            form_frame,
            text="Name:",
        ).grid(
            row=0,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.name_entry = ttk.Entry(
            form_frame,
            width=40,
        )
        self.name_entry.grid(
            row=0,
            column=1,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        ttk.Label(
            form_frame,
            text="Description:",
        ).grid(
            row=1,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.description_entry = ttk.Entry(
            form_frame,
            width=40,
        )
        self.description_entry.grid(
            row=1,
            column=1,
            padx=(0, 10),
            pady=5,
            sticky="ew",
        )

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            pady=(10, 0),
            sticky="w",
        )

        ttk.Button(
            button_frame,
            text="Add",
            command=self.add_category,
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Edit",
            command=self.edit_category,
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Delete",
            command=self.delete_category,
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh_categories,
        ).pack(side="left", padx=5)

        form_frame.columnconfigure(1, weight=1)

        table_frame = ttk.LabelFrame(
            self,
            text="Categories",
            padding=10,
        )
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "name", "description")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("description", text="Description")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("name", width=200, anchor="center")
        self.tree.column("description", width=400, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set,
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.on_category_select,
        )

    def clear_form(self):
        """Clear the category form."""
        self.name_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)

    def get_form_data(self):
        """Return category form values."""
        name = self.name_entry.get().strip()
        description = self.description_entry.get().strip()

        return name, description

    def get_selected_id(self):
        """Return the selected category ID."""
        selected = self.tree.selection()

        if not selected:
            return None

        values = self.tree.item(selected[0], "values")

        if not values:
            return None

        return int(values[0])

    def refresh_categories(self):
        """Reload categories from the database."""
        try:
            categories = self.service.get_all_categories()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for category in categories:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        category[0],
                        category[1],
                        category[2] or "",
                    ),
                )

            self.clear_form()

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error),
            )

    def on_category_select(self, event=None):
        """Load the selected category into the form."""
        selected = self.tree.selection()

        if not selected:
            return

        values = self.tree.item(
            selected[0],
            "values",
        )

        if not values:
            return

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[1])

        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, values[2])

    def add_category(self):
        """Create a new category."""
        name, description = self.get_form_data()

        try:
            self.service.create_category(
                name=name,
                description=description,
            )

            messagebox.showinfo(
                "Success",
                "Category added successfully.",
            )

            self.refresh_categories()

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error),
            )

    def edit_category(self):
        """Update the selected category."""
        category_id = self.get_selected_id()

        if category_id is None:
            messagebox.showwarning(
                "Select Category",
                "Please select a category first.",
            )
            return

        name, description = self.get_form_data()

        try:
            self.service.update_category(
                category_id=category_id,
                name=name,
                description=description,
            )

            messagebox.showinfo(
                "Success",
                "Category updated successfully.",
            )

            self.refresh_categories()

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error),
            )

    def delete_category(self):
        """Delete the selected category."""
        category_id = self.get_selected_id()

        if category_id is None:
            messagebox.showwarning(
                "Select Category",
                "Please select a category first.",
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this category?",
        )

        if not confirm:
            return

        try:
            self.service.delete_category(category_id)

            messagebox.showinfo(
                "Success",
                "Category deleted successfully.",
            )

            self.refresh_categories()

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error),
            )