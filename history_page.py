import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from tkcalendar import DateEntry
import os
from openpyxl import Workbook
from datetime import datetime


class HistoryPage:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

        tk.Label(self.frame, text="Transaction History", font=("Arial", 16)).pack(pady=10)

        # Dropdown for selecting transaction type
        self.transaction_type = tk.StringVar(value="inventory_sell")
        transaction_dropdown = ttk.Combobox(
            self.frame, textvariable=self.transaction_type, state="readonly",
            values=["inventory_sell", "inventory_bought", "returns"]
        )
        transaction_dropdown.pack(pady=5)
        transaction_dropdown.bind("<<ComboboxSelected>>", self.toggle_table_columns)

        # Radio buttons for Single Date and Date Range
        self.report_type = tk.StringVar(value="single")
        self.radio_frame = ttk.Frame(self.frame)
        self.radio_frame.pack(pady=5)

        tk.Radiobutton(
            self.radio_frame, text="Single Date", variable=self.report_type, value="single", 
            command=self.toggle_date_inputs
        ).grid(row=0, column=0, padx=10, sticky="w")
        tk.Radiobutton(
            self.radio_frame, text="Date Range", variable=self.report_type, value="range", 
            command=self.toggle_date_inputs
        ).grid(row=0, column=1, padx=10, sticky="w")

        # Date input fields
        self.date_frame = ttk.Frame(self.frame)
        self.date_frame.pack(pady=5)

        # Single Date input
        self.single_date_label = tk.Label(self.date_frame, text="Select Date:")
        self.single_date_entry = DateEntry(self.date_frame, date_pattern="yyyy-mm-dd")

        # Date Range inputs (hidden initially)
        self.from_date_label = tk.Label(self.date_frame, text="From Date:")
        self.from_date_entry = DateEntry(self.date_frame, date_pattern="yyyy-mm-dd")
        self.to_date_label = tk.Label(self.date_frame, text="To Date:")
        self.to_date_entry = DateEntry(self.date_frame, date_pattern="yyyy-mm-dd")

        # Initialize with Single Date input
        self.single_date_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.single_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Filters for 'returns': return_type and condition
        self.filter_frame = ttk.Frame(self.frame)
        self.filter_frame.pack(pady=5)

        self.return_type_dropdown = ttk.Combobox(
            self.filter_frame, state="readonly", values=["all", "purchase_return", "sales_return"]
        )
        self.return_type_dropdown.set("all")
        self.return_type_dropdown.grid(row=0, column=0, padx=5, pady=5)
        self.return_type_dropdown.bind("<<ComboboxSelected>>", self.fetch_transactions)

        self.condition_dropdown = ttk.Combobox(
            self.filter_frame, state="readonly", values=["all", "good", "damaged"]
        )
        self.condition_dropdown.set("all")
        self.condition_dropdown.grid(row=0, column=1, padx=5, pady=5)
        self.condition_dropdown.bind("<<ComboboxSelected>>", self.fetch_transactions)

        # Table for transactions
        self.columns = ("bill_no", "timestamp", "product_name", "product_code", "Quantity")
        self.bill_table = ttk.Treeview(self.frame, columns=self.columns, show="headings")
        self.bill_table.pack(fill=tk.BOTH, expand=True, pady=10)

        for col in self.columns:
            self.bill_table.heading(col, text=col.replace('_', ' ').capitalize())

        # Buttons
        # Create a frame to hold all three buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=10)

        # Define a common width for all buttons
        button_width = 20

        tk.Button(button_frame, text="Fetch Transactions", command=self.fetch_transactions, width=button_width).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit Selected Transaction", command=self.edit_transaction, width=button_width).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save and Generate Excel", command=self.save_to_excel, width=button_width).pack(side=tk.LEFT, padx=5)
    def toggle_date_inputs(self):
        """Toggle between single date and date range inputs."""
        if self.report_type.get() == "single":
            # Show Single Date input
            self.from_date_label.grid_forget()
            self.from_date_entry.grid_forget()
            self.to_date_label.grid_forget()
            self.to_date_entry.grid_forget()

            self.single_date_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.single_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        else:
            # Show Date Range inputs
            self.single_date_label.grid_forget()
            self.single_date_entry.grid_forget()

            self.from_date_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.from_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            self.to_date_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.to_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    def toggle_table_columns(self, event):
        """Adjust table columns based on the selected transaction type."""
        transaction_type = self.transaction_type.get()

        if transaction_type == "inventory_sell":
            self.columns = ("bill_no", "timestamp", "product_name", "product_code", "Quantity", "price","total_amount" )
            self.filter_frame.pack_forget()  # Hide filters for returns
        elif transaction_type == "inventory_bought":
            self.columns = ("receipt_no", "timestamp", "product_name", "product_code", "quantity", "price")
            self.filter_frame.pack_forget()  # Hide filters for returns
        elif transaction_type == "returns":
            self.columns = ("ret_no", "timestamp", "product_name", "product_code", "qty_ret", "Selling_Price", "return_type", "condition")
            self.filter_frame.pack(pady=5)  # Show filters for returns

        self.bill_table.delete(*self.bill_table.get_children())
        self.bill_table['columns'] = self.columns

        for col in self.columns:
            self.bill_table.heading(col, text=col.replace('_', ' ').capitalize())


    def fetch_transactions(self, event=None):
        report_type = self.report_type.get()
        transaction_type = self.transaction_type.get()

        # Get selected filters for 'returns'
        return_type_filter = self.return_type_dropdown.get()
        condition_filter = self.condition_dropdown.get()

        if report_type == "single":
            date = self.single_date_entry.get()
            query = f"""
                SELECT * 
                FROM {transaction_type} 
                WHERE DATE(timestamp) = ?
            """
            params = (date,)
        else:
            from_date = self.from_date_entry.get()
            to_date = self.to_date_entry.get()

            if not from_date or not to_date:
                messagebox.showerror("Error", "Please enter both start and end dates for the range.")
                return

            query = f"""
                SELECT * 
                FROM {transaction_type} 
                WHERE DATE(timestamp) BETWEEN ? AND ?
            """
            params = (from_date, to_date)

        if transaction_type == "returns":
            # Add filters for 'return_type' and 'condition'
            if return_type_filter != "all":
                query += " AND return_type = ?"
                params += (return_type_filter,)
            if condition_filter != "all":
                query += " AND condition = ?"
                params += (condition_filter,)

        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Clear existing data in the table
        for row in self.bill_table.get_children():
            self.bill_table.delete(row)

        # Populate the table with fetched transactions
        if not rows:
            messagebox.showinfo("Info", "No transactions found for the selected date(s) and filters.")
        else:
            for row in rows:
                self.bill_table.insert("", tk.END, values=row)

    def edit_transaction(self):
        selected_item = self.bill_table.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a transaction to edit.")
            return

        transaction_data = self.bill_table.item(selected_item, "values")
        transaction_no = transaction_data[0]

        edit_window = tk.Toplevel()
        edit_window.title(f"Edit Transaction #{transaction_no}")
        edit_window.geometry("300x200")

        tk.Label(edit_window, text=f"Editing Transaction #{transaction_no}", font=("Arial", 14)).pack(pady=10)

        tk.Label(edit_window, text="New Quantity:").pack(pady=5)
        qty_entry = tk.Entry(edit_window)
        qty_entry.pack()

        def save_changes():
            try:
                new_qty = int(qty_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Enter a valid numeric quantity.")
                return

            conn = sqlite3.connect("inventory1.db")
            cursor = conn.cursor()

            if self.transaction_type.get() == "inventory_sell":
                cursor.execute("SELECT product_code, qty_sold FROM inventory_sell WHERE out_bill_no = ?", (transaction_no,))
                original_data = cursor.fetchone()
                if not original_data:
                    messagebox.showerror("Error", "Original transaction not found.")
                    conn.close()
                    return

                product_code, original_qty = original_data
                qty_difference = new_qty - original_qty
                cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code = ?", (product_code,))
                stock = cursor.fetchone()[0]

                if stock + qty_difference < 0:
                    messagebox.showerror("Error", "Not enough stock.")
                    conn.close()
                    return

                cursor.execute("UPDATE total_inventory SET available_stock = available_stock + ? WHERE product_code = ?", (qty_difference, product_code))
                cursor.execute("UPDATE inventory_sell SET qty_sold = ?, total_amount = qty_sold * price WHERE out_bill_no = ?", (new_qty, transaction_no))
            elif self.transaction_type.get() == "inventory_bought":
                cursor.execute("SELECT product_code, qty_bought FROM inventory_bought WHERE receipt_no = ?", (transaction_no,))
                original_data = cursor.fetchone()
                if not original_data:
                    messagebox.showerror("Error", "Original transaction not found.")
                    conn.close()
                    return

                product_code, original_qty = original_data
                qty_difference = new_qty - original_qty

                cursor.execute("UPDATE total_inventory SET available_stock = available_stock - ? WHERE product_code = ?", (qty_difference, product_code))
                cursor.execute("UPDATE inventory_bought SET qty_bought = ?, total_amount = qty_bought * price WHERE receipt_no = ?", (new_qty, transaction_no))
            elif self.transaction_type.get() == "returns":
                cursor.execute("SELECT product_code, qty_ret FROM returns WHERE ret_no = ?", (transaction_no,))
                original_data = cursor.fetchone()
                if not original_data:
                    messagebox.showerror("Error", "Original return transaction not found.")
                    conn.close()
                    return

                product_code, original_qty = original_data
                qty_difference = new_qty - original_qty

                cursor.execute("UPDATE total_inventory SET available_stock = available_stock + ? WHERE product_code = ?", (qty_difference, product_code))
                cursor.execute("UPDATE returns SET qty_ret = ?, total_amount = qty_ret * Selling_Price WHERE ret_no = ?", (new_qty, transaction_no))

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", f"Transaction #{transaction_no} updated successfully.")
            edit_window.destroy()
            self.fetch_transactions()

        tk.Button(edit_window, text="Save Changes", command=save_changes).pack(pady=20)
    # New function to save Treeview data to Excel


    def save_to_excel(self):
        """Save the Treeview data to an Excel file."""
        folder_name = "history"
        os.makedirs(folder_name, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        transaction_type = self.transaction_type.get()

        # Set the correct file name based on the transaction type
        file_path = os.path.join(folder_name, f"{transaction_type}_transactions_{timestamp}.xlsx")
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = transaction_type.capitalize()

        # Define the correct columns based on the transaction type
        if transaction_type == "inventory_sell":
            self.columns = ["Bill no", "Timestamp", "Product name", "Product code", "Quantity", "Price per Unit", "Total Price"]
        elif transaction_type == "inventory_bought":
            self.columns = ["Receipt no", "Timestamp", "Product name", "Product code", "Quantity", "Price per Unit", "Total Price"]
        elif transaction_type == "returns":
            self.columns = ["Ret no", "Timestamp", "Product name", "Product code", "Quantity ret", "Selling price", "Return type", "Condition"]

        sheet.append([col for col in self.columns])

        # Add data rows with proper numeric conversion
        for row in self.bill_table.get_children():
            values = self.bill_table.item(row, "values")

            # Convert numeric fields to numbers
            try:
                if transaction_type == "returns":
                    # Convert Quantity Ret (int) and Selling Price (float) for returns
                    qty_ret = int(values[4]) if values[4].isdigit() else 0  # Quantity ret (convert to int)
                    selling_price = float(values[5]) if self.is_numeric(values[5]) else 0.0  # Selling price (convert to float)
                    values = [
                        int(values[0]),  # Ret no (converted to int)
                        values[1],  # Timestamp (string, no change needed)
                        values[2],  # Product name (string, no change needed)
                        values[3],  # Product code (string, no change needed)
                        qty_ret,  # Quantity ret (converted to int)
                        selling_price,  # Selling price (converted to float)
                        values[6],  # Return type (string, no change needed)
                        values[7],  # Condition (string, no change needed)
                    ]
                else:
                    # Handle for other transaction types (inventory_sell, inventory_bought)
                    quantity = int(values[4]) if values[4].isdigit() else 0  # Quantity (convert to int)
                    price_per_unit = float(values[5]) if self.is_numeric(values[5]) else 0.0  # Price per Unit (convert to float)
                    total_price = float(values[6]) if self.is_numeric(values[6]) else 0.0  # Total Price (convert to float)

                    values = [
                        values[0],  # Bill no / Receipt no (string, no change needed)
                        values[1],  # Timestamp (string, no change needed)
                        values[2],  # Product name (string, no change needed)
                        values[3],  # Product code (string, no change needed)
                        quantity,  # Quantity (converted to int)
                        price_per_unit,  # Price per Unit (converted to float)
                        total_price  # Total Price (converted to float)
                    ]
            except ValueError:
                # In case of conversion failure, use default value
                values = [values[0], values[1], values[2], values[3], 0, 0.0, 0.0]

            # Add the row to the sheet
            sheet.append(values)

        # Save the Excel file
        workbook.save(file_path)
        messagebox.showinfo("Success", f"Excel file saved successfully at {file_path}")



    def is_numeric(self, value):
        """Check if the given value can be interpreted as a number (int or float)."""
        try:
            float(value)
            return True
        except ValueError:
            return False





# To test the application independently:
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Transaction History Page")
    app = HistoryPage(root)
    app.frame.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
