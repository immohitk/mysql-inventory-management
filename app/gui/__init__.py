import tkinter as tk
from tkinter import ttk


class CategoryFrame(ttk.Frame):
    """Display the category management screen."""

    def __init__(self, parent):
        super().__init__(parent, padding=15)

        self._build_ui()

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

        ttk.Label(form_frame, text="Description:").grid(
            row=1,
            column=0,
            padx=(0, 10),
            pady=5,
            sticky="w",
        )

        self.description_entry = ttk.Entry(form_frame, width=40)
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
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Edit",
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Delete",
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Refresh",
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
        self.tree.column("name", width=200)
        self.tree.column("description", width=400)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )

        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )