import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import pymysql

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class DatabaseApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MySQL Manager")
        self.geometry("900x600")

        self.current_db = None
        self.current_table = None

        # Left panel for controls
        self.left_frame = ctk.CTkFrame(self, width=250)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.left_frame, text="Select Database:", font=("Arial", 14)).pack(anchor="w", pady=(0, 5))
        self.db_var = tk.StringVar()
        self.db_combo = ttk.Combobox(self.left_frame, state="readonly", font=("Arial", 14), textvariable=self.db_var)
        self.db_combo.pack(fill="x")
        self.db_combo.bind("<<ComboboxSelected>>", self.on_database_selected)

        ctk.CTkLabel(self.left_frame, text="Select Table:", font=("Arial", 14)).pack(anchor="w", pady=(15, 5))
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(self.left_frame, state="readonly", font=("Arial", 14), textvariable=self.table_var)
        self.table_combo.pack(fill="x")
        self.table_combo.bind("<<ComboboxSelected>>", self.on_table_selected)

        btns = [
            ("Insert Record", self.insert_record_form),
            ("Delete Record", self.delete_record_form),
            ("Edit Record", self.edit_record_form),
            ("View Table", self.view_table_data_right),
        ]
        for text, cmd in btns:
            btn = ctk.CTkButton(self.left_frame, text=text, command=cmd)
            btn.pack(fill="x", pady=8)

        self.status_label = ctk.CTkLabel(self.left_frame, text="", wraplength=220)
        self.status_label.pack(pady=20)

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.data_tree = None  # Will hold Treeview for right panel data

        self.load_databases()

    def set_status(self, msg):
        self.status_label.configure(text=msg)

    def load_databases(self):
        try:
            conn = pymysql.connect(host='localhost', user='root', passwd='')
            cursor = conn.cursor()
            cursor.execute("SHOW DATABASES")
            dbs = [row[0] for row in cursor.fetchall()]
            conn.close()

            self.db_combo['values'] = dbs
            if dbs:
                self.db_combo.current(0)
                self.on_database_selected()
            self.set_status(f"Loaded {len(dbs)} databases")
        except Exception as e:
            self.set_status(f"Error loading databases: {e}")

    def on_database_selected(self, event=None):
        db_name = self.db_var.get()
        if not db_name:
            return
        self.current_db = db_name

        try:
            conn = pymysql.connect(host='localhost', user='root', passwd='', database=db_name)
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            self.table_combo['values'] = tables
            if tables:
                self.table_combo.current(0)
                self.on_table_selected()
            else:
                self.table_combo.set("")
                self.current_table = None
            self.set_status(f"Loaded {len(tables)} tables in '{db_name}'")
        except Exception as e:
            self.set_status(f"Error loading tables: {e}")

    def on_table_selected(self, event=None):
        table_name = self.table_var.get()
        if table_name:
            self.current_table = table_name
            self.set_status(f"Selected table '{table_name}' in database '{self.current_db}'")
            self.view_table_data_right()  # auto load data when table changes
        else:
            self.current_table = None
            self.set_status("No table selected")
            self.clear_right_frame()

    def clear_right_frame(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()

    # --- View data in right panel ---
    def view_table_data_right(self):
        if not self.current_db or not self.current_table:
            self.set_status("Select database and table first.")
            return

        self.clear_right_frame()

        style = ttk.Style(self)
        style.configure("Treeview", font=("Arial", 14))
        style.configure("Treeview.Heading", font=("Arial", 14, "bold"))

        tree = ttk.Treeview(self.right_frame, show="headings", style="Treeview")
        tree.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(self.right_frame, orient="vertical", command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.configure(yscroll=vsb.set)

        hsb = ttk.Scrollbar(self.right_frame, orient="horizontal", command=tree.xview)
        hsb.pack(side="bottom", fill="x")
        tree.configure(xscroll=hsb.set)

        try:
            conn = pymysql.connect(host='localhost', user='root', passwd='', database=self.current_db)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM `{self.current_table}`")
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            conn.close()

            tree["columns"] = cols
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor="center")

            for row in rows:
                tree.insert("", "end", values=row)

            self.data_tree = tree
            self.set_status(f"Loaded {len(rows)} rows from {self.current_table}")
        except Exception as e:
            self.set_status(f"Error loading table data: {e}")

    # --- Insert record popup ---
    def insert_record_form(self):
        if not self.current_db or not self.current_table:
            messagebox.showerror("Error", "Please select database and table first.")
            return
        popup = ctk.CTkToplevel(self)
        popup.title(f"Insert Record into {self.current_db}.{self.current_table}")
        popup.geometry("500x400")
        popup.grab_set()

        frm = ctk.CTkScrollableFrame(popup)
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        try:
            conn = pymysql.connect(host='localhost', user='root', passwd='', database=self.current_db)
            cursor = conn.cursor()
            cursor.execute(f"DESCRIBE `{self.current_table}`")
            columns = cursor.fetchall()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load table schema: {e}")
            popup.destroy()
            return

        entries = {}
        for col in columns:
            field = col[0]
            label = ctk.CTkLabel(frm, text=f"{field}:", font=("Arial", 14))
            label.pack(anchor="w", pady=(10, 2))
            entry = ctk.CTkEntry(frm, font=("Arial", 14))
            entry.pack(fill="x", pady=2)
            entries[field] = entry

        def on_insert():
            data = {f: e.get().strip() for f, e in entries.items()}
            if any(v == "" for v in data.values()):
                self.set_status("Please fill all fields")
                return
            fields = ", ".join(f"`{f}`" for f in data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            values = list(data.values())
            try:
                conn = pymysql.connect(host='localhost', user='root', passwd='', database=self.current_db)
                cursor = conn.cursor()
                sql = f"INSERT INTO `{self.current_table}` ({fields}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                conn.commit()
                conn.close()
                self.set_status(f"Record inserted into {self.current_table}")
                popup.destroy()
                self.view_table_data_right()
            except Exception as e:
                messagebox.showerror("Insert Error", f"Failed to insert record: {e}")

        btn_frame = ctk.CTkFrame(popup)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Insert", command=on_insert).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=popup.destroy).pack(side="right", padx=5)

    # --- Delete record popup ---
    def delete_record_form(self):
        if not self.current_db or not self.current_table:
            messagebox.showerror("Error", "Please select database and table first.")
            return
        popup = ctk.CTkToplevel(self)
        popup.title(f"Delete Records from {self.current_db}.{self.current_table}")
        popup.geometry("900x400")
        popup.grab_set()

        style = ttk.Style(popup)
        style.configure("Treeview", font=("Arial", 14))
        style.configure("Treeview.Heading", font=("Arial", 14, "bold"))

        tree = ttk.Treeview(popup, show="headings", selectmode="extended", style="Treeview")
        tree.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(popup, orient="vertical", command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.configure(yscroll=vsb.set)

        hsb = ttk.Scrollbar(popup, orient="horizontal", command=tree.xview)
        hsb.pack(side="bottom", fill="x")
        tree.configure(xscroll=hsb.set)

        try:
            conn = pymysql.connect(host='localhost', user='root', passwd='', database=self.current_db)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM `{self.current_table}`")
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            conn.close()

            tree["columns"] = cols
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor="center")

            for row in rows:
                tree.insert("", "end", values=row)

            self.set_status(f"Loaded {len(rows)} rows from {self.current_table}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")
            popup.destroy()
            return

        def on_delete():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Select rows to delete")
                return
            if not messagebox.askyesno("Confirm Delete", f"Delete {len(selected)} selected rows?"):
                return
            try:
                conn = pymysql.connect(host='localhost', user='root', passwd='', database=self.current_db)
                cursor = conn.cursor()
                cursor.execute(f"SHOW KEYS FROM `{self.current_table}` WHERE Key_name = 'PRIMARY'")
                pk_cols = [r[4] for r in cursor.fetchall()]
                cols = tree["columns"]

                if not pk_cols:
                    # No PK: delete using all columns as criteria
                    for item in selected:
                        vals = tree.item(item)["values"]
                        where_clause = " AND ".join(f"`{c}`=%s" for c in cols)
                        sql = f"DELETE FROM `{self.current_table}` WHERE {where_clause} LIMIT 1"
                        cursor.execute(sql, vals)
                else:
                    pk_idx = [cols.index(pk) for pk in pk_cols]
                    for item in selected:
                        vals = tree.item(item)["values"]
                        pk_vals = [vals[i] for i in pk_idx]
                        where_clause = " AND ".join(f"`{pk}`=%s" for pk in pk_cols)
                        sql = f"DELETE FROM `{self.current_table}` WHERE {where_clause} LIMIT 1"
                        cursor.execute(sql, pk_vals)

                conn.commit()
                conn.close()
                self.set_status(f"Deleted {len(selected)} rows from {self.current_table}")
                popup.destroy()
                self.view_table_data_right()
            except Exception as e:
                messagebox.showerror("Delete Error", f"Failed to delete records: {e}")

        btn_frame = ctk.CTkFrame(popup)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Delete Selected", command=on_delete).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=popup.destroy).pack(side="right", padx=5)

    # --- Edit record popup ---
    def edit_record_form(self):
        if not self.current_db or not self.current_table:
            messagebox.showerror("Error", "Please select database and table first.")
            return

        popup = ctk.CTkToplevel(self)
        popup.title(f"Edit Record in {self.current_db}.{self.current_table}")
        popup.geometry("900x400")
        popup.grab_set()

        style = ttk.Style(popup)
        style.configure("Treeview", font=("Arial", 14))
        style.configure("Treeview.Heading", font=("Arial", 14, "bold"))

        tree = ttk.Treeview(popup, show="headings", selectmode="browse", style="Treeview")
        tree.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(popup, orient="vertical", command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.configure(yscroll=vsb.set)

        hsb = ttk.Scrollbar(popup, orient="horizontal", command=tree.xview)
        hsb.pack(side="bottom", fill="x")
        tree.configure(xscroll=hsb.set)

        try:
            conn = pymysql.connect(host='localhost', user='root', passwd='', database=self.current_db)
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM `{self.current_table}`")
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            conn.close()

            tree["columns"] = cols
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor="center")

            for row in rows:
                tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")
            popup.destroy()
            return

        def on_edit():
            selected = tree.selection()
            if not selected:
                messagebox.showerror("Error", "Select a single row to edit")
                return
            item = selected[0]
            vals = tree.item(item)["values"]

            edit_popup = ctk.CTkToplevel(popup)
            edit_popup.title("Edit Record Fields")
            edit_popup.geometry("500x400")
            edit_popup.grab_set()

            entries = {}
            for i, col in enumerate(cols):
                label = ctk.CTkLabel(edit_popup, text=f"{col}:", font=("Arial", 14))
                label.pack(anchor="w", pady=(10, 2))
                entry = ctk.CTkEntry(edit_popup, font=("Arial", 14))
                entry.pack(fill="x", pady=2)
                entry.insert(0, vals[i])
                entries[col] = entry

            def save_edit():
                new_data = {f: e.get().strip() for f, e in entries.items()}
                if any(v == "" for v in new_data.values()):
                    messagebox.showerror("Error", "Please fill all fields")
                    return

                try:
                    conn = pymysql.connect(host='localhost', user='root', passwd='', database=self.current_db)
                    cursor = conn.cursor()

                    cursor.execute(f"SHOW KEYS FROM `{self.current_table}` WHERE Key_name = 'PRIMARY'")
                    pk_cols = [r[4] for r in cursor.fetchall()]
                    if not pk_cols:
                        messagebox.showerror("Error", "Edit requires primary key on table")
                        edit_popup.destroy()
                        return

                    set_clause = ", ".join(f"`{col}`=%s" for col in new_data.keys())
                    where_clause = " AND ".join(f"`{pk}`=%s" for pk in pk_cols)

                    set_values = list(new_data.values())
                    pk_values = [vals[cols.index(pk)] for pk in pk_cols]

                    sql = f"UPDATE `{self.current_table}` SET {set_clause} WHERE {where_clause}"
                    cursor.execute(sql, set_values + pk_values)
                    conn.commit()
                    conn.close()

                    messagebox.showinfo("Success", "Record updated successfully.")
                    edit_popup.destroy()
                    popup.destroy()
                    self.view_table_data_right()
                except Exception as e:
                    messagebox.showerror("Update Error", f"Failed to update record: {e}")

            btn_frame = ctk.CTkFrame(edit_popup)
            btn_frame.pack(fill="x", padx=10, pady=10)
            ctk.CTkButton(btn_frame, text="Save", command=save_edit).pack(side="right", padx=5)
            ctk.CTkButton(btn_frame, text="Cancel", command=edit_popup.destroy).pack(side="right", padx=5)

        btn_frame = ctk.CTkFrame(popup)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Edit Selected", command=on_edit).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=popup.destroy).pack(side="right", padx=5)

if __name__ == "__main__":
    app = DatabaseApp()
    app.mainloop()
