import customtkinter as ctk
from tkinter import ttk, messagebox
from database import Database      # Your existing Database class

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class USBRelayGUI(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("USB Relay Database")
        self.geometry("1250x700")

        # ---------------- Database ----------------
        self.db = Database()
        self.db.connect_database("product_db")

        # ---------------- Layout ----------------
        self.left_frame = ctk.CTkFrame(self, width=320)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.create_widgets()
        self.fetch_data()

    # ---------------------------------------------------
    # GUI Widgets
    # ---------------------------------------------------

    def create_widgets(self):

        ctk.CTkLabel(
            self.left_frame,
            text="USB Relay Database",
            font=("Arial", 22, "bold")
        ).pack(pady=20)

        # Product Serial
        ctk.CTkLabel(self.left_frame, text="Product Serial").pack(anchor="w", padx=10)

        self.serial_entry = ctk.CTkEntry(self.left_frame, width=250)
        self.serial_entry.pack(padx=10, pady=5)

        # Hardware Version
        ctk.CTkLabel(self.left_frame, text="Hardware Version").pack(anchor="w", padx=10)

        self.hw_entry = ctk.CTkEntry(self.left_frame)
        self.hw_entry.pack(padx=10, pady=5)

        # FTDI Serial
        ctk.CTkLabel(self.left_frame, text="FTDI Serial").pack(anchor="w", padx=10)

        self.ftdi_entry = ctk.CTkEntry(self.left_frame)
        self.ftdi_entry.pack(padx=10, pady=5)

        # Firmware Version
        ctk.CTkLabel(self.left_frame, text="Firmware Version").pack(anchor="w", padx=10)

        self.firmware_entry = ctk.CTkEntry(self.left_frame)
        self.firmware_entry.pack(padx=10, pady=5)

        # QA Date
        ctk.CTkLabel(self.left_frame, text="QA Performed On").pack(anchor="w", padx=10)

        self.date_entry = ctk.CTkEntry(self.left_frame)
        self.date_entry.pack(padx=10, pady=5)

        # QA By
        ctk.CTkLabel(self.left_frame, text="QA Performed By").pack(anchor="w", padx=10)

        self.qa_by_entry = ctk.CTkEntry(self.left_frame)
        self.qa_by_entry.pack(padx=10, pady=5)

        # QA Passed
        ctk.CTkLabel(self.left_frame, text="QA Passed").pack(anchor="w", padx=10)

        self.qa_passed = ctk.CTkComboBox(
            self.left_frame,
            values=["PASS", "FAIL"]
        )
        self.qa_passed.pack(padx=10, pady=5)

        # ---------------- Buttons ----------------

        ctk.CTkButton(
            self.left_frame,
            text="Fetch",
            command=self.fetch_data
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            self.left_frame,
            text="Insert",
            command=self.insert_record
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            self.left_frame,
            text="Update",
            command=self.update_record
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            self.left_frame,
            text="Delete",
            command=self.delete_record
        ).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            self.left_frame,
            text="Clear",
            command=self.clear_entries
        ).pack(fill="x", padx=10, pady=5)

        # ---------------- Treeview ----------------

        columns = (
            "Serial",
            "Hardware",
            "FTDI",
            "Firmware",
            "Date",
            "By",
            "Passed"
        )

        self.tree = ttk.Treeview(
            self.right_frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.load_selected_row)

    # ---------------------------------------------------
    # Fetch Records
    # ---------------------------------------------------

    def fetch_data(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = self.db.fetch_all_records()

        for row in rows:

            self.tree.insert(
                "",
                "end",
                values=(
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7]
                )
            )

    # ---------------------------------------------------
    # Load Selected Row
    # ---------------------------------------------------

    def load_selected_row(self, event):

        selected = self.tree.focus()

        if not selected:
            return

        values = self.tree.item(selected)["values"]

        self.clear_entries()

        self.serial_entry.insert(0, values[0])
        self.hw_entry.insert(0, values[1])
        self.ftdi_entry.insert(0, values[2])
        self.firmware_entry.insert(0, values[3])
        self.date_entry.insert(0, values[4])
        self.qa_by_entry.insert(0, values[5])
        self.qa_passed.set(values[6])

    # ---------------------------------------------------

    def clear_entries(self):

        self.serial_entry.delete(0, "end")
        self.hw_entry.delete(0, "end")
        self.ftdi_entry.delete(0, "end")
        self.firmware_entry.delete(0, "end")
        self.date_entry.delete(0, "end")
        self.qa_by_entry.delete(0, "end")
        self.qa_passed.set("PASS")

    # Empty methods (implemented in Part 2)

    def insert_record(self):
        pass

    def update_record(self):
        pass

    def delete_record(self):
        pass


if __name__ == "__main__":

    app = USBRelayGUI()
    app.mainloop()