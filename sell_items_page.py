import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os
import openpyxl

class SellItemsPage:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.frame, text="Sell Items", font=("Arial", 16)).pack(pady=10)

        # Table schema: Product Code, Product Name, Selling Price, Quantity, Available Stock, Total Amount
        self.columns = ("Product Code", "Product Name", "Selling Price", "Quantity", "Available Stock", "Total Amount")
        self.entries_frame = ttk.Frame(self.frame)
        self.entries_frame.pack(pady=5)
        self.entries = {}  # Store widgets for each column

        for idx, col in enumerate(self.columns[:-2]):  # Exclude "Available Stock" and "Total Amount" from entry fields
            tk.Label(self.entries_frame, text=col).grid(row=0, column=idx, padx=5, pady=5)

            if col == "Quantity":
                spinbox = ttk.Spinbox(self.entries_frame, from_=1, to=1000, width=10)  # Default quantity spinbox
                spinbox.grid(row=1, column=idx, padx=5, pady=5)
                self.entries[col] = spinbox
            else:
                entry = ttk.Entry(self.entries_frame, width=15)
                entry.grid(row=1, column=idx, padx=5, pady=5)
                self.entries[col] = entry

        # Label to display available stock
        self.available_stock_label = tk.Label(self.entries_frame, text="Available Stock: N/A", fg="blue")
        self.available_stock_label.grid(row=2, column=0, columnspan=3, pady=5, sticky="w")

        # Bind the Product Code entry to auto-fill details and update on barcode scan
        self.entries["Product Code"].bind("<FocusOut>", self.fill_product_details)
        self.entries["Product Code"].bind("<Return>", self.scan_barcode)  # Trigger barcode scan on Enter

        # Button to add the item to the table
        tk.Button(self.entries_frame, text="Add Item", command=self.add_item).grid(row=1, column=len(self.columns)-2, padx=5, pady=5)

        # Table for added items
        self.tree = ttk.Treeview(self.frame, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create a frame to hold both buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=10)

        # Define a common width for both buttons
        button_width = 20

        # Add the Save button
        tk.Button(button_frame, text="Save", command=self.save_items, width=button_width).pack(side=tk.LEFT, padx=5)

        # Add the Save and Generate Excel button
        tk.Button(button_frame, text="Save and Generate Excel", command=self.save_and_generate_excel, width=button_width).pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Delete Selected Transaction", command=self.delete_selected_transaction, width=button_width).pack(side=tk.LEFT, padx=5)



    def fill_product_details(self, event=None):
        """Auto-fill product details based on Product Code."""
        product_code = self.entries["Product Code"].get().strip()

        if product_code:
            conn = sqlite3.connect("inventory1.db")
            cursor = conn.cursor()

            # Fetch product name and selling price from new_products table
            cursor.execute("SELECT product_name, Selling_Price FROM new_products WHERE product_code=?", (product_code,))
            product_details = cursor.fetchone()

            # Fetch available stock from total_inventory table
            cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
            stock_details = cursor.fetchone()

            if product_details and stock_details:
                product_name, selling_price = product_details
                available_stock = stock_details[0]

                # Populate the entry fields
                self.entries["Product Name"].delete(0, tk.END)
                self.entries["Product Name"].insert(0, product_name)

                self.entries["Selling Price"].delete(0, tk.END)
                self.entries["Selling Price"].insert(0, f"{selling_price:.2f}")

                self.entries["Quantity"].config(to=available_stock)  # Limit quantity to available stock

                # Update available stock label
                self.available_stock_label.config(text=f"Available Stock: {available_stock}")
                
                # Check if item is already in the table and increment the quantity
                self.update_quantity_if_scanned(product_code)

            else:
                messagebox.showerror("Error", "Product code not found or no stock available.")
                self.available_stock_label.config(text="Available Stock: N/A")

            conn.close()

    def scan_barcode(self, event):
        """Handle barcode scanning to auto-fill product details and update quantity."""
        product_code = self.entries["Product Code"].get().strip()

        if product_code:
            conn = sqlite3.connect("inventory1.db")
            cursor = conn.cursor()

            # Fetch product name and selling price from new_products table
            cursor.execute("SELECT product_name, Selling_Price FROM new_products WHERE product_code=?", (product_code,))
            product_details = cursor.fetchone()

            # Fetch available stock from total_inventory table
            cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
            stock_details = cursor.fetchone()

            if product_details and stock_details:
                product_name, selling_price = product_details
                available_stock = stock_details[0]

                # Populate the entry fields
                self.entries["Product Name"].delete(0, tk.END)
                self.entries["Product Name"].insert(0, product_name)

                self.entries["Selling Price"].delete(0, tk.END)
                self.entries["Selling Price"].insert(0, f"{selling_price:.2f}")

                self.entries["Quantity"].config(to=available_stock)  # Limit quantity to available stock

                # Update available stock label
                self.available_stock_label.config(text=f"Available Stock: {available_stock}")
                
                # Check if item is already in the table and increment the quantity
                self.update_quantity_if_scanned(product_code)

            else:
                messagebox.showerror("Error", "Product code not found or no stock available.")
                self.available_stock_label.config(text="Available Stock: N/A")

            conn.close()

    def update_quantity_if_scanned(self, product_code):
        """If the product is already scanned, increment the quantity."""
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0] == product_code:  # Matching product code
                current_quantity = int(values[3])  # Get the current quantity
                new_quantity = current_quantity + 1
                self.tree.item(item, values=(values[0], values[1], values[2], str(new_quantity), values[4], values[5]))
                self.entries["Quantity"].delete(0, tk.END)
                self.entries["Quantity"].insert(0, str(new_quantity))  # Update quantity in entry
                return

    def add_item(self):
        """Add an item from entry fields to the table."""
        values = [self.entries[col].get().strip() for col in self.columns[:-2]]  # Exclude Available Stock and Total Amount

        # Validate that Product Code and Quantity are provided
        if not values[0]:
            messagebox.showerror("Error", "Product Code is required.")
            return

        if not values[3].isdigit() or int(values[3]) < 1:
            messagebox.showerror("Error", "Quantity must be a positive number.")
            return

        quantity = int(values[3])
        product_code = values[0]

        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()

        cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
        result = cursor.fetchone()
        if result and result[0] >= quantity:
            # Calculate total amount
            selling_price = float(values[2])
            total_amount = selling_price * quantity

            # Add the item to the table
            self.tree.insert("", "end", values=values + [result[0], f"{total_amount:.2f}"])

            # Clear entry fields (except Product Name, Selling Price)
            self.entries["Product Code"].delete(0, tk.END)
            self.entries["Quantity"].delete(0, tk.END)
            self.entries["Quantity"].insert(0, "1")  # Reset quantity to 1
            self.available_stock_label.config(text="Available Stock: N/A")
        else:
            messagebox.showerror("Error", "Not enough stock available.")

        conn.close()

    def save_items(self):
        """Save the added items to the database and update inventory."""
        items = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0]:  # Only save rows with a product code
                items.append(values)

        if not items:
            messagebox.showerror("Error", "No items to save.")
            return

        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()

        for product_code, product_name, selling_price, quantity, available_stock, total_amount in items:
            quantity = int(quantity)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insert into inventory_sell table
            cursor.execute("INSERT INTO inventory_sell (timestamp, product_name, product_code, qty_sold, price, total_amount) VALUES (?, ?, ?, ?, ?, ?)",
                           (timestamp, product_name, product_code, quantity, float(selling_price), float(total_amount)))

            # Update total_inventory
            cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
            result = cursor.fetchone()
            if result:
                new_stock = result[0] - quantity
                cursor.execute("UPDATE total_inventory SET available_stock=? WHERE product_code=?", (new_stock, product_code))

        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Items sold successfully!")

        # Refresh for the next items
        self.clear_entries()

    def save_and_generate_excel(self):
        """Save the added items to the database, update inventory, and generate an Excel file."""
        items = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0]:  # Only save rows with a product code
                items.append(values)

        if not items:
            messagebox.showerror("Error", "No items to save.")
            return

        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()

        for product_code, product_name, selling_price, quantity, available_stock, total_amount in items:
            quantity = int(quantity)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insert into inventory_sell table
            cursor.execute("INSERT INTO inventory_sell (timestamp, product_name, product_code, qty_sold, price, total_amount) VALUES (?, ?, ?, ?, ?, ?)",
                        (timestamp, product_name, product_code, quantity, float(selling_price), float(total_amount)))

            # Update total_inventory
            cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
            result = cursor.fetchone()
            if result:
                new_stock = result[0] - quantity
                cursor.execute("UPDATE total_inventory SET available_stock=? WHERE product_code=?", (new_stock, product_code))

        conn.commit()
        conn.close()

        # Generate Excel file
        import os
        import openpyxl

        # Create "inventory_sell" folder if not exists
        folder_path = "inventory_sell"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Create a new Excel workbook and sheet
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "Inventory Sales"

        # Write header row
        sheet.append(list(self.columns))

        # Write data rows
        for product_code, product_name, selling_price, quantity, available_stock, total_amount in items:
            # Ensure numeric values are written as numbers
            sheet.append([
                product_code,                    # Text
                product_name,                    # Text
                float(selling_price),            # Number
                int(quantity),                   # Number
                int(available_stock),            # Number
                float(total_amount)              # Number
            ])

        # Save the Excel file
        excel_path = os.path.join(folder_path, f"sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        wb.save(excel_path)

        messagebox.showinfo("Success", f"Items sold successfully and Excel file saved at {excel_path}")
        
        # Refresh for the next items
        self.clear_entries()

    def delete_selected_transaction(self):
        """Delete the selected transaction from the TreeView."""
        # Get the selected item in the TreeView
        selected_item = self.tree.selection()

        if not selected_item:
            messagebox.showerror("Error", "Please select a transaction to delete.")
            return

        # Get the selected transaction's data
        transaction_data = self.tree.item(selected_item, "values")
        if not transaction_data:
            messagebox.showerror("Error", "Could not retrieve transaction data.")
            return

        product_code = transaction_data[0]  # Assuming the first column is the Product Code

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the transaction for Product Code: {product_code}?"
        )
        if not confirm:
            return

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
        self.available_stock_label.config(text="Available Stock: N/A")

    def get_frame(self):
        return self.frame


# To test the application independently
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sell Items Page")
    app = SellItemsPage(root)
    app.get_frame()
    root.mainloop()
