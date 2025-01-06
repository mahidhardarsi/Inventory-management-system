import os
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from openpyxl import Workbook  # Required for Excel generation
import openpyxl

class ReturnsPage:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.frame, text="Returns Items", font=("Arial", 16)).pack(pady=10)

        # Dropdown to select return type
        self.return_type = tk.StringVar(value="sales_return")
        tk.Label(self.frame, text="Return Type:").pack(pady=5)
        return_type_dropdown = ttk.Combobox(
            self.frame, textvariable=self.return_type, state="readonly",
            values=["sales_return", "purchase_return"]
        )
        return_type_dropdown.pack(pady=5)

        # Table schema: Product Code, Product Name, Selling Price, Quantity
        self.columns = ("Product Code", "Product Name", "Selling Price", "Quantity")
        self.entries_frame = ttk.Frame(self.frame)
        self.entries_frame.pack(pady=5)

        self.entries = {}  # Store widgets for each column
        for idx, col in enumerate(self.columns):
            tk.Label(self.entries_frame, text=col).grid(row=0, column=idx, padx=5, pady=5)

            if col == "Quantity":
                spinbox = ttk.Spinbox(self.entries_frame, from_=1, to=1000, width=10)  # Default quantity spinbox
                spinbox.grid(row=1, column=idx, padx=5, pady=5)
                self.entries[col] = spinbox
            else:
                entry = ttk.Entry(self.entries_frame, width=15)
                entry.grid(row=1, column=idx, padx=5, pady=5)
                self.entries[col] = entry

        # Bind the Product Code entry to auto-fill details and trigger barcode scan on Enter
        self.entries["Product Code"].bind("<FocusOut>", self.fill_product_details)
        self.entries["Product Code"].bind("<Return>", self.scan_barcode)  # Trigger barcode scan on Enter

        # Buttons to add returns and damaged items
        tk.Button(self.entries_frame, text="Add Return", command=self.add_return).grid(row=1, column=len(self.columns), padx=5, pady=5)
        tk.Button(self.entries_frame, text="Damaged", command=self.add_damaged_return).grid(row=1, column=len(self.columns) + 1, padx=5, pady=5)

        # Table for added returns
        self.tree = ttk.Treeview(self.frame, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # Save buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady = 10)
        button_width = 20
        tk.Button(button_frame, text="Save Returns", command=self.save_returns, width=button_width).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save and Generate Excel", command=self.save_and_generate_excel, width=button_width).pack(side=tk.LEFT, padx=5)

    

    def fill_product_details(self, event=None):
        """Auto-fill product details based on Product Code."""
        product_code = self.entries["Product Code"].get().strip()

        if product_code:
            conn = sqlite3.connect("inventory1.db")
            cursor = conn.cursor()

            cursor.execute("SELECT product_name, Selling_Price FROM new_products WHERE product_code=?", (product_code,))
            product = cursor.fetchone()
            conn.close()

            if product:
                product_name, selling_price = product
                self.entries["Product Name"].delete(0, tk.END)
                self.entries["Product Name"].insert(0, product_name)

                self.entries["Selling Price"].delete(0, tk.END)
                self.entries["Selling Price"].insert(0, f"{selling_price:.2f}")
            else:
                messagebox.showerror("Error", "Product code not found.")

    def scan_barcode(self, event):
        """Handle barcode scanning to auto-fill product details and update quantity."""
        product_code = self.entries["Product Code"].get().strip()

        if product_code:
            conn = sqlite3.connect("inventory1.db")
            cursor = conn.cursor()

            cursor.execute("SELECT product_name, Selling_Price FROM new_products WHERE product_code=?", (product_code,))
            product = cursor.fetchone()

            cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
            stock_details = cursor.fetchone()

            if product and stock_details:
                product_name, selling_price = product
                available_stock = stock_details[0]

                # Populate the entry fields
                self.entries["Product Name"].delete(0, tk.END)
                self.entries["Product Name"].insert(0, product_name)

                self.entries["Selling Price"].delete(0, tk.END)
                self.entries["Selling Price"].insert(0, f"{selling_price:.2f}")

                self.entries["Quantity"].config(to=available_stock)  # Limit quantity to available stock

                # Update available stock label (optional)
                self.available_stock_label.config(text=f"Available Stock: {available_stock}")

            else:
                messagebox.showerror("Error", "Product code not found or no stock available.")

            conn.close()

    def add_return(self):
        """Add a return item from entry fields to the table."""
        self._add_item(damaged=False)

    def add_damaged_return(self):
        """Add a damaged return item to the table."""
        self._add_item(damaged=True)

    def _add_item(self, damaged):
        """Helper function to add an item to the table."""
        values = [self.entries[col].get().strip() for col in self.columns]

        # Validate that Product Code and Quantity are provided
        if not values[0]:
            messagebox.showerror("Error", "Product Code is required.")
            return

        if not values[3].isdigit() or int(values[3]) < 1:
            messagebox.showerror("Error", "Quantity must be a positive number.")
            return

        # Add a special flag to the values to indicate whether it is damaged
        values.append("damaged" if damaged else "good")

        # Add the item to the table
        self.tree.insert("", "end", values=values)

        # Clear entry fields (except Product Name, Selling Price)
        self.entries["Product Code"].delete(0, tk.END)
        self.entries["Quantity"].delete(0, tk.END)
        self.entries["Quantity"].insert(0, "1")  # Reset quantity to 1

    def save_returns(self):
        """Save the return items to the database and update inventory."""
        returns = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0]:  # Only save rows with a product code
                returns.append(values)

        if not returns:
            messagebox.showerror("Error", "No returns to save.")
            return

        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()

        for product_code, product_name, selling_price, qty_ret, condition in returns:
            qty_ret = int(qty_ret)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insert into returns table
            cursor.execute(
                "INSERT INTO returns (timestamp, product_name, product_code, qty_ret, Selling_Price, return_type, condition) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (timestamp, product_name, product_code, qty_ret, float(selling_price), self.return_type.get(), condition)
            )

            # Update total_inventory based on return type and condition
            cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
            result = cursor.fetchone()

            if result:
                available_stock = result[0]
                if self.return_type.get() == "sales_return":
                    if condition == "good":
                        new_stock = available_stock + qty_ret
                    else:
                        new_stock = available_stock
                elif self.return_type.get() == "purchase_return":
                    new_stock = available_stock - qty_ret

                if new_stock < 0:
                    messagebox.showerror("Error", f"Not enough stock to return for {product_name}.")
                    conn.close()
                    return

                cursor.execute("UPDATE total_inventory SET available_stock=? WHERE product_code=?", (new_stock, product_code))
            else:
                messagebox.showerror("Error", f"Product {product_name} not found in inventory.")
                conn.close()
                return

        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Returns saved successfully!")

        # Refresh for the next returns
        self.clear_entries()

    def clear_entries(self):
        """Clear all inputs and the table."""
        for item in self.tree.get_children():
            self.tree.delete(item)  # Remove all rows from the table
        for entry in self.entries.values():
            if isinstance(entry, ttk.Entry):
                entry.delete(0, tk.END)  # Clear text entries
            elif isinstance(entry, ttk.Spinbox):
                entry.delete(0, tk.END)
                entry.insert(0, "1")  # Reset quantity to 1

    def get_frame(self):
        return self.frame
        

    def save_and_generate_excel(self):
        """Save return items to the database and generate an Excel file."""
        # Save data to the database but skip clearing the table
        returns = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0]:  # Only save rows with a product code
                returns.append(values)

        if not returns:
            messagebox.showerror("Error", "No returns to save.")
            return

        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()

        for product_code, product_name, selling_price, qty_ret, condition in returns:
            try:
                qty_ret = int(qty_ret)  # Convert quantity to an integer
                selling_price = float(selling_price)  # Convert selling price to a float
            except ValueError:
                messagebox.showerror("Error", "Invalid data type for quantity or selling price.")
                conn.close()
                return
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insert into returns table
            cursor.execute(
                "INSERT INTO returns (timestamp, product_name, product_code, qty_ret, Selling_Price, return_type, condition) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (timestamp, product_name, product_code, qty_ret, selling_price, self.return_type.get(), condition)
            )

            # Update total_inventory based on return type and condition
            cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
            result = cursor.fetchone()

            if result:
                available_stock = result[0]
                if self.return_type.get() == "sales_return":
                    if condition == "good":
                        new_stock = available_stock + qty_ret
                    else:
                        new_stock = available_stock
                elif self.return_type.get() == "purchase_return":
                    new_stock = available_stock - qty_ret

                if new_stock < 0:
                    messagebox.showerror("Error", f"Not enough stock to return for {product_name}.")
                    conn.close()
                    return

                cursor.execute("UPDATE total_inventory SET available_stock=? WHERE product_code=?", (new_stock, product_code))
            else:
                messagebox.showerror("Error", f"Product {product_name} not found in inventory.")
                conn.close()
                return

        conn.commit()
        conn.close()

        # Generate Excel file
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Returns"

        # Write the headers
        headers = ["Product Code", "Product Name", "Selling Price", "Quantity Returned", "Condition"]
        sheet.append(headers)

        # Write the data, ensuring quantities and prices are stored as numbers
        for row in returns:
            # Ensure that quantities and prices are properly converted before appending
            qty_ret = int(row[3])  # Convert Quantity Returned to integer
            selling_price = float(row[2])  # Convert Selling Price to float
            sheet.append([row[0], row[1], selling_price, qty_ret, row[4]])

        # Generate the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = "returns"
        os.makedirs(folder_name, exist_ok=True)
        file_name = os.path.join(folder_name, f"returns_{timestamp}.xlsx")

        # Save the Excel file
        workbook.save(file_name)
        messagebox.showinfo("Success", f"Returns saved and Excel file generated: {file_name}")

        # Clear entries and table for the next returns
        self.clear_entries()






# To test the application independently
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Returns Page")
    app = ReturnsPage(root)
    app.get_frame()
    root.mainloop()
