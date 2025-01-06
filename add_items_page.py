import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os
import openpyxl

class AddItemsPage:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(self.frame, text="Add Items", font=("Arial", 16)).pack(pady=10)

        # Table schema: Product Code, Product Name, Selling Price, Quantity
        self.columns = ("Product Code", "Product Name", "Selling Price", "Quantity", "Available Stock")
        self.entries_frame = ttk.Frame(self.frame)
        self.entries_frame.pack(pady=5)
        self.entries = {}

        for idx, col in enumerate(self.columns[:-1]):
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

        # Bind the Product Code entry to auto-fill details
        self.entries["Product Code"].bind("<FocusOut>", self.fill_product_details)

        # Button to add the item to the table
        tk.Button(self.entries_frame, text="Add Item", command=self.add_item).grid(row=1, column=len(self.columns), padx=5, pady=5)

        # Table for added items
        self.tree = ttk.Treeview(self.frame, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create a frame to hold all three buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=10)

        # Define a common width for all buttons
        button_width = 20
        
        # Add buttons
        tk.Button(button_frame, text="Save", command=self.save_items, width=button_width).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Save and Generate Excel", command=self.save_and_generate_excel, width=button_width).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Selected Transaction", command=self.delete_selected_transaction, width=button_width).pack(side=tk.LEFT, padx=5)

        # Ensure the 'inventory_bought' folder exists
        if not os.path.exists("inventory_bought"):
            os.makedirs("inventory_bought")

    def fill_product_details(self, event=None):
        """Auto-fill product details based on Product Code and display available stock."""
        product_code = self.entries["Product Code"].get().strip()

        if product_code:
            conn = sqlite3.connect("inventory1.db")
            cursor = conn.cursor()

            # Fetch product details
            cursor.execute("SELECT product_name, Selling_Price FROM new_products WHERE product_code=?", (product_code,))
            product = cursor.fetchone()

            # Fetch available stock from total_inventory table
            cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
            stock_details = cursor.fetchone()
            
            conn.close()

            if product:
                # Populate product name and selling price
                product_name, selling_price = product
                self.entries["Product Name"].delete(0, tk.END)
                self.entries["Product Name"].insert(0, product_name)

                self.entries["Selling Price"].delete(0, tk.END)
                self.entries["Selling Price"].insert(0, f"{selling_price:.2f}")
            else:
                # Clear fields and show error if product not found
                self.entries["Product Name"].delete(0, tk.END)
                self.entries["Selling Price"].delete(0, tk.END)
                self.available_stock_label.config(text="Available Stock: N/A", fg="red")
                messagebox.showerror("Error", "Product code not found.")
                return

            # Update available stock label
            if stock_details:
                available_stock = stock_details[0]
                self.available_stock_label.config(
                    text=f"Available Stock: {available_stock}", fg="green"
                )
            else:
                self.available_stock_label.config(
                    text="Available Stock: 0 (Not in inventory)", fg="orange"
                )


    def add_item(self):
        """Add an item from entry fields to the table."""
        # Exclude 'Available Stock' from the values list, as it is not an entry field
        values = [self.entries[col].get().strip() for col in self.columns[:-1]]  # Exclude the last column "Available Stock"

        # Validate that Product Code and Quantity are provided
        if not values[0]:
            messagebox.showerror("Error", "Product Code is required.")
            return

        if not values[3].isdigit() or int(values[3]) < 1:
            messagebox.showerror("Error", "Quantity must be a positive number.")
            return

        # Add the item to the table
        self.tree.insert("", "end", values=values)

        # Clear entry fields (except Product Name and Selling Price)
        self.entries["Product Code"].delete(0, tk.END)
        self.entries["Quantity"].delete(0, tk.END)
        self.entries["Quantity"].insert(0, "1")  # Reset quantity to 1


    def save_items(self, clear_tree=True):
        """Save the added items to the database and update inventory."""
        items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            if values[0]:  # Only save rows with a product code
                items.append(values)

        if not items:
            messagebox.showerror("Error", "No items to save.")
            return

        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()

        for product_code, product_name, selling_price, quantity in items:
            quantity = int(quantity)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insert into inventory_bought table
            cursor.execute("INSERT INTO inventory_bought (timestamp, product_name, product_code, qty_bought, Selling_Price) VALUES (?, ?, ?, ?, ?)",
                           (timestamp, product_name, product_code, quantity, float(selling_price)))

            # Update total_inventory
            cursor.execute("SELECT available_stock FROM total_inventory WHERE product_code=?", (product_code,))
            result = cursor.fetchone()

            if result:
                new_stock = result[0] + quantity
                cursor.execute("UPDATE total_inventory SET available_stock=? WHERE product_code=?", (new_stock, product_code))
            else:
                cursor.execute("INSERT INTO total_inventory (product_code , product_name , available_stock) VALUES (?, ?, ?)",
                               (product_code , product_name , quantity))

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Items saved successfully!")
        if clear_tree:
            self.clear_entries()


    def save_and_generate_excel(self):
        """Save items and generate an Excel file in the 'inventory_bought' folder."""
        # Save items without clearing entries
        self.save_items(clear_tree=False)

        # Prepare data for Excel
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            data.append(values)

        if not data:
            messagebox.showerror("Error", "No data to save in Excel.")
            return

        # Ensure the 'inventory_bought' folder exists
        if not os.path.exists("inventory_bought"):
            os.makedirs("inventory_bought")

        # Create a new Excel workbook and sheet
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Inventory Bought"

        # Define the headers
        headers = ["Product Code", "Product Name", "Selling Price", "Quantity"]

        # Write the headers
        sheet.append(headers)

        # Write the data with proper type casting
        for row in data:
            sheet.append([
                row[0],         # Product Code (Text)
                row[1],         # Product Name (Text)
                float(row[2]),  # Selling Price (Numeric)
                int(row[3])     # Quantity (Numeric)
            ])

        # Generate the filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"inventory_bought/inventory_{timestamp}.xlsx"

        try:
            workbook.save(file_name)
            messagebox.showinfo("Success", f"Excel file generated: {file_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save Excel file: {e}")

        # Clear entries after saving the Excel file
        self.clear_entries()


    def delete_selected_transaction(self):
       """Delete the selected transaction from the TreeView."""
       selected_item = self.tree.selection()

       if not selected_item:
           messagebox.showerror("Error", "Please select a transaction to delete.")
           return

       transaction_data = self.tree.item(selected_item)["values"]

       if not transaction_data:
           messagebox.showerror("Error", "Could not retrieve transaction data.")
           return

       product_code = transaction_data[0]  # Assuming first column is Product Code

       confirm = messagebox.askyesno(
           "Confirm Delete",
           f"Are you sure you want to delete the transaction for Product Code: {product_code}?"
       )

       if not confirm:
           return

       conn = sqlite3.connect("inventory1.db")

       try:
           cursor = conn.cursor()
           cursor.execute("DELETE FROM inventory_bought WHERE product_code=?", (product_code,))
           conn.commit()

           # Delete from Treeview as well
           self.tree.delete(selected_item)
           messagebox.showinfo("Success", f"Transaction for Product Code: {product_code} deleted successfully.")

       except Exception as e:
           conn.rollback()
           messagebox.showerror("Error", f"Failed to delete transaction: {e}")

       finally:
           conn.close()

    def clear_entries(self):
      """Clear all inputs and the table."""
      for item in self.tree.get_children():
          self.tree.delete(item)  # Remove all rows from table

      for entry in self.entries.values():
          if isinstance(entry , ttk.Entry):
              entry.delete(0 , tk.END)  # Clear text entries 
          elif isinstance(entry , ttk.Spinbox):
              entry.delete(0 , tk.END) 
              entry.insert(0 , "1")  # Reset quantity to 1 

    def get_frame(self):
      return self.frame  # This method returns the frame of AddItemsPage


# To test the application independently 
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Add Items Page")
    app = AddItemsPage(root)
    root.mainloop()
