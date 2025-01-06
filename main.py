import tkinter as tk
from tkinter import ttk
from dashboard_page import DashboardPage
from report_page import ReportPage
from add_items_page import AddItemsPage
from sell_items_page import SellItemsPage
from history_page import HistoryPage
from inventory_db import init_db
from new_products_page import NewProductsPage
from returns import ReturnsPage

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management")
        self.root.geometry("900x700")

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)

        # Initialize pages
        self.dashboard_tab = DashboardPage(self.tabs)
        self.report_tab = ReportPage(self.tabs)
        self.add_tab = AddItemsPage(self.tabs)
        self.sell_tab = SellItemsPage(self.tabs)
        self.history_tab = HistoryPage(self.tabs)
        self.new_products_tab = NewProductsPage(self.tabs)  
        self.returns_tab = ReturnsPage(self.tabs)  

        # Add tabs (pass the frame attribute of each page)
        self.tabs.add(self.dashboard_tab.frame, text="Dashboard")
        self.tabs.add(self.report_tab.frame, text="Report")
        self.tabs.add(self.add_tab.frame, text="Add Items")
        self.tabs.add(self.sell_tab.frame, text="Sell Items")
        self.tabs.add(self.history_tab.frame, text="History")
        self.tabs.add(self.new_products_tab.frame, text="New Products")
        self.tabs.add(self.returns_tab.frame, text="Returns")  

        # Bind the Dashboard tab to refresh the graph
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):
        selected_tab = event.widget.index(event.widget.select())
        if selected_tab == 0:  
            self.dashboard_tab.refresh()

def show_splash_screen(duration=3000):
    splash_root = tk.Tk()
    splash_root.title("Splash Screen")
    splash_root.geometry("400x300")

    # Load an image for the splash screen (optional)
    logo_image = tk.PhotoImage(file='zest.png')  # Replace with your image path
    logo_label = tk.Label(splash_root, image=logo_image)
    logo_label.pack(expand=True)

    # Close the splash screen and open the main application after the specified duration
    splash_root.after(duration, lambda: [splash_root.destroy(), main_application()])

    splash_root.mainloop()

def main_application():
    root = tk.Tk()
    # root.iconbitmap(r'ZEST ENTERPRISES.ico')  # Replace with your .ico file path
    # logo_image = tk.PhotoImage(file=r'zest.png')
    # logo_label = tk.Label(root, image=logo_image)
    # logo_label.pack()
    app = InventoryApp(root)
    root.mainloop()

if __name__ == "__main__":
    init_db()
    show_splash_screen(duration=1000)  # Show splash screen for 1 second
