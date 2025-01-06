import os
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from tkcalendar import DateEntry
import pandas as pd  # Ensure you have pandas installed



class ReportPage:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        tk.Label(self.frame, text="Inventory & Sales Report", font=("Arial", 16)).pack(pady=10)

        # Radio buttons for report type
        self.report_type_frame = ttk.Frame(self.frame)
        self.report_type_frame.pack(pady=5)
        self.report_type = tk.StringVar(value="range")  # Default to "range"
        tk.Radiobutton(self.report_type_frame, text="Date Range", variable=self.report_type, value="range",
                       command=self.toggle_date_inputs).grid(row=0, column=0, padx=5, sticky="w")
        tk.Radiobutton(self.report_type_frame, text="Single Date", variable=self.report_type, value="single",
                       command=self.toggle_date_inputs).grid(row=0, column=1, padx=5, sticky="w")

        # Date Selection Frame
        self.date_frame = ttk.Frame(self.frame)
        self.date_frame.pack(pady=5)

        # Date Range Inputs
        self.from_date_label = tk.Label(self.date_frame, text="From Date:")
        self.from_date_entry = DateEntry(self.date_frame, date_pattern="yyyy-mm-dd")
        self.to_date_label = tk.Label(self.date_frame, text="To Date:")
        self.to_date_entry = DateEntry(self.date_frame, date_pattern="yyyy-mm-dd")

        self.from_date_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.from_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.to_date_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.to_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Single Date Input (hidden initially)
        self.single_date_label = tk.Label(self.date_frame, text="Date:")
        self.single_date_entry = DateEntry(self.date_frame, date_pattern="yyyy-mm-dd")

        # Generate Report Button
        tk.Button(self.frame, text="Generate Report", command=self.generate_report).pack(pady=10)

        # Save and Generate Excel Button
        tk.Button(self.frame, text="Save and Generate Excel", command=self.save_and_generate_excel).pack(pady=10)

        # Summary Label
        self.summary_label = tk.Label(self.frame, text="", font=("Arial", 12), justify="left")
        self.summary_label.pack(pady=10)

        # Report Table
        self.report_table = ttk.Treeview(
            self.frame,
            columns=("product_code", "product_name", "sold_qty", "total_revenue", "current_stock"),
            show="headings"
        )

        self.report_table.pack(fill=tk.BOTH, expand=True, pady=10)

        for col in ("product_code", "product_name", "sold_qty", "total_revenue", "current_stock"):
            self.report_table.heading(col, text=col.replace("_", " ").capitalize())

        # Bind double-click event
        self.report_table.bind("<Double-1>", self.open_transaction_details)

    def toggle_date_inputs(self):
        """Toggle between date range and single date input."""
        if self.report_type.get() == "range":
            self.single_date_label.grid_forget()
            self.single_date_entry.grid_forget()
            self.from_date_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.from_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            self.to_date_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.to_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        else:
            self.from_date_label.grid_forget()
            self.from_date_entry.grid_forget()
            self.to_date_label.grid_forget()
            self.to_date_entry.grid_forget()
            self.single_date_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.single_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    def generate_report(self):
        report_type = self.report_type.get()

        if report_type == "range":
            from_date = self.from_date_entry.get()
            to_date = self.to_date_entry.get()
        else:
            single_date = self.single_date_entry.get()
            from_date = to_date = single_date

        try:
            datetime.strptime(from_date, "%Y-%m-%d")
            datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid dates in the format YYYY-MM-DD.")
            return

        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()

        query = """ 
                SELECT ti.product_code,
                       ti.product_name,
                       COALESCE(SUM(isell.qty_sold), 0) AS total_qty,
                       COALESCE(SUM(isell.total_amount), 0) AS total_revenue,
                       ti.available_stock 
                FROM total_inventory ti 
                LEFT JOIN inventory_sell isell ON ti.product_code = isell.product_code 
                """

        conditions = []
        params = []

        if from_date:
            conditions.append("DATE(isell.timestamp) >= ?")
            params.append(from_date)

        if to_date:
            conditions.append("DATE(isell.timestamp) <= ?")
            params.append(to_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " GROUP BY ti.product_code, ti.product_name"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        # Clear the table
        for row in self.report_table.get_children():
            self.report_table.delete(row)

        total_sold_items = 0
        total_revenue = 0.0

        if rows:
            for row in rows:
                self.report_table.insert("", tk.END, values=row)
                total_sold_items += row[2]
                total_revenue += row[3]
        else:
            messagebox.showinfo("Info", "No records found for the selected date range.")

        conn.close()

        self.summary_label.config(
            text=f"Total Items Sold: {total_sold_items}\nTotal Revenue: ₹{total_revenue:.2f}"
        )



    def save_and_generate_excel(self):
        """Convert Treeview data to Excel and save it in the report folder."""
        report_folder = 'report'
        if not os.path.exists(report_folder):
            os.makedirs(report_folder)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = os.path.join(report_folder, f"report_{timestamp}.xlsx")

        # Define the columns for the report
        columns = ["product_code", "product_name", "sold_qty", "total_revenue", "current_stock"]
        
        data = [columns]  # Add the column headers first

        # Retrieve data from the Treeview widget
        for item in self.report_table.get_children():
            values = self.report_table.item(item, "values")
            data.append(values)

        # Create a DataFrame and ensure that numerical columns are of the correct type
        df = pd.DataFrame(data[1:], columns=data[0])  # Skip header row for DataFrame creation

        # Convert sold_qty, total_revenue, and current_stock to numeric, ensuring errors are handled
        df['sold_qty'] = pd.to_numeric(df['sold_qty'], errors='coerce', downcast='integer')
        df['total_revenue'] = pd.to_numeric(df['total_revenue'], errors='coerce', downcast='float')
        df['current_stock'] = pd.to_numeric(df['current_stock'], errors='coerce', downcast='integer')

        # Write the DataFrame to an Excel file
        df.to_excel(excel_filename, index=False)

        # Show success message
        messagebox.showinfo("Success", f"Excel report generated successfully at {excel_filename}.")


    def open_transaction_details(self, event):
        """Open a new window with sales and purchase transactions for the selected product in the selected date range."""
        selected_item = self.report_table.selection()
        if not selected_item:
            return

        # Get product details from the selected row
        item_values = self.report_table.item(selected_item, "values")
        product_code = item_values[0]
        product_name = item_values[1]

        # Get the selected date range
        from_date = self.from_date_entry.get()
        to_date = self.to_date_entry.get()

        # Connect to the database and retrieve transactions within the date range
        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()

        # Fetch add item transactions within the date range
        cursor.execute("""
            SELECT timestamp, qty_bought, Selling_Price
            FROM inventory_bought
            WHERE product_code=? AND DATE(timestamp) BETWEEN ? AND ?
        """, (product_code, from_date, to_date))
        bought_records = cursor.fetchall()

        # Fetch sales transactions within the date range
        cursor.execute("""
            SELECT timestamp, qty_sold, total_amount
            FROM inventory_sell
            WHERE product_code=? AND DATE(timestamp) BETWEEN ? AND ?
        """, (product_code, from_date, to_date))
        sold_records = cursor.fetchall()

        conn.close()

        # Create a new window to display transactions
        transaction_window = tk.Toplevel(self.frame)
        transaction_window.title(f"Transactions for {product_name} (Code: {product_code})")

        # Display add item transactions
        tk.Label(transaction_window, text=f"Add Item Transactions for {product_name}", font=("Arial", 12, "bold")).pack(pady=5)
        add_table = ttk.Treeview(transaction_window, columns=("timestamp", "qty_bought", "Selling_Price"), show="headings")
        add_table.pack(fill=tk.BOTH, expand=True, pady=5)

        for col in ("timestamp", "qty_bought", "Selling_Price"):
            add_table.heading(col, text=col.replace("_", " ").capitalize())

        for record in bought_records:
            add_table.insert("", tk.END, values=record)

        # Display sales transactions
        tk.Label(transaction_window, text=f"Sales Transactions for {product_name}", font=("Arial", 12, "bold")).pack(pady=5)
        sell_table = ttk.Treeview(transaction_window, columns=("timestamp", "qty_sold", "total_amount"), show="headings")
        sell_table.pack(fill=tk.BOTH, expand=True, pady=5)

        for col in ("timestamp", "qty_sold", "total_amount"):
            sell_table.heading(col, text=col.replace("_", " ").capitalize())

        for record in sold_records:
            sell_table.insert("", tk.END, values=record)



# To test the application independently:
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Inventory Report Page")
    app = ReportPage(root)
    app.frame.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
