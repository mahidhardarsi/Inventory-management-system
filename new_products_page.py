import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class NewProductsPage:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)  # Ensure the frame is added to the root window

        tk.Label(self.frame, text="New Products", font=("Arial", 16)).pack(pady=10)

        # Entry fields for new product
        tk.Label(self.frame, text="Product Code:").pack(pady=5)
        self.code_entry = tk.Entry(self.frame)
        self.code_entry.pack()

        tk.Label(self.frame, text="Product Name:").pack(pady=5)
        self.name_entry = tk.Entry(self.frame)
        self.name_entry.pack()

        tk.Label(self.frame, text="MRP:").pack(pady=5)
        self.mrp_entry = tk.Entry(self.frame)
        self.mrp_entry.pack()

        tk.Label(self.frame, text="Selling Price:").pack(pady=5)
        self.selling_price_entry = tk.Entry(self.frame)
        self.selling_price_entry.pack()

        tk.Button(self.frame, text="Add Product", command=self.add_product).pack(pady=10)
        tk.Button(self.frame, text="Show All Products", command=self.show_all_products).pack(pady=5)

    def add_product(self):
        code = self.code_entry.get()
        name = self.name_entry.get()
        try:
            mrp = float(self.mrp_entry.get())
            selling_price = float(self.selling_price_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for MRP and Selling Price.")
            return

        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()

        cursor.execute("INSERT INTO new_products (product_code, product_name, MRP, Selling_Price) VALUES (?, ?, ?, ?)",
                       (code, name, mrp, selling_price))
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Product added successfully!")
        self.clear_entries()

    def clear_entries(self):
        self.code_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.mrp_entry.delete(0, tk.END)
        self.selling_price_entry.delete(0, tk.END)

    def show_all_products(self):
        conn = sqlite3.connect("inventory1.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM new_products")
        products = cursor.fetchall()
        conn.close()

        if not products:
            messagebox.showinfo("Info", "No products found.")
            return

        # Create a new window to display products
        product_window = tk.Toplevel(self.frame)
        product_window.title("All Products")
        product_window.geometry("600x400")

        # Create a treeview to display products
        product_table = ttk.Treeview(product_window, columns=("Product Code", "Product Name", "MRP", "Selling Price"), show="headings")
        product_table.heading("Product Code", text="Product Code")
        product_table.heading("Product Name", text="Product Name")
        product_table.heading("MRP", text="MRP")
        product_table.heading("Selling Price", text="Selling Price")
        product_table.pack(fill=tk.BOTH, expand=True)

        for product in products:
            product_table.insert("", tk.END, values=product)

        # Edit button
        edit_button = tk.Button(product_window, text="Edit Selected Product", command=lambda: self.edit_product(product_table))
        edit_button.pack(pady=10)

    def edit_product(self, product_table):
        selected_item = product_table.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a product to edit.")
            return

        product_data = product_table.item(selected_item, "values")
        edit_window = tk.Toplevel(self.frame)
        edit_window.title("Edit Product")
        edit_window.geometry("400x300")

        tk.Label(edit_window, text="Edit Product", font=("Arial", 16)).pack(pady=10)

        tk.Label(edit_window, text="Product Code:").pack(pady=5)
        code_entry = tk.Entry(edit_window)
        code_entry.insert(0, product_data[0])
        code_entry.pack()

        tk.Label(edit_window, text="Product Name:").pack(pady=5)
        name_entry = tk.Entry(edit_window)
        name_entry.insert(0, product_data[1])
        name_entry.pack()

        tk.Label(edit_window, text="MRP:").pack(pady=5)
        mrp_entry = tk.Entry(edit_window)
        mrp_entry.insert(0, product_data[2])
        mrp_entry.pack()

        tk.Label(edit_window, text="Selling Price:").pack(pady=5)
        selling_price_entry = tk.Entry(edit_window)
        selling_price_entry.insert(0, product_data[3])
        selling_price_entry.pack()

        def save_changes():
            new_code = code_entry.get()
            new_name = name_entry.get()
            try:
                new_mrp = float(mrp_entry.get())
                new_selling_price = float(selling_price_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for MRP and Selling Price.")
                return

            conn = sqlite3.connect("inventory1.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE new_products SET product_code=?, product_name=?, MRP=?, Selling_Price=? WHERE product_code=?",
                           (new_code, new_name, new_mrp, new_selling_price, product_data[0]))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Product updated successfully!")
            edit_window.destroy()
            product_table.delete(selected_item)
            product_table.insert("", tk.END, values=(new_code, new_name, new_mrp, new_selling_price))

    def get_frame(self):
        return self.frame


# Main application setup
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Inventory Management")
    root.geometry("400x300")

    new_products_page = NewProductsPage(root)
    root.mainloop()
