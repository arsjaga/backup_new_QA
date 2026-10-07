import tkinter as tk
from tkinter import ttk, messagebox

from database import Database

db = Database()
db.connect_database("product_db")


root = tk.Tk()
root.title("USB Relay Database")
root.geometry("900x500")

tree = ttk.Treeview(root)

tree["columns"] = (
    "Serial",
    "HW",
    "FTDI",
    "FW",
    "Date",
    "By",
    "Passed"
)

tree.column("#0", width=0)

for col in tree["columns"]:
    tree.heading(col, text=col)

tree.pack(fill="both", expand=True)


def fetch():

    tree.delete(*tree.get_children())

    rows = db.fetch_all_records()

    for row in rows:

        tree.insert(
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


def delete():

    selected = tree.focus()

    if not selected:
        return

    values = tree.item(selected)["values"]

    serial = values[0]

    db.delete_record(serial)

    fetch()


frame = tk.Frame(root)
frame.pack(pady=10)

tk.Button(frame, text="Delete", width=15, command=delete).grid(row=0, column=2, padx=5)

fetch()

root.mainloop()