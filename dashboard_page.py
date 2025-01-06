import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from inventory_db import fetch_sales_data

class DashboardPage:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.sales_label = tk.Label(self.frame, text="Dashboard", font=("Arial", 16))
        self.sales_label.pack(pady=10)

        self.sales_info = tk.Label(self.frame, font=("Arial", 14))
        self.sales_info.pack()

        # Create a placeholder for the chart
        self.figure = plt.Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.chart = FigureCanvasTkAgg(self.figure, self.frame)
        self.chart.get_tk_widget().pack()

    def refresh(self):
        """Fetch new data and update the graph."""
        sales = fetch_sales_data()

        # Update sales info
        self.sales_info.config(text=f"Total Sales Today: ₹{sales[-1]:.2f}")

        # Clear the current graph
        self.ax.clear()

        # Plot the new data
        self.ax.plot(range(1, len(sales) + 1), sales, marker='o')
        self.ax.set_title("Sales in the Last 5 Days")
        self.ax.set_xlabel("Days")
        self.ax.set_ylabel("Sales (₹)")

        # Redraw the canvas
        self.chart.draw()
