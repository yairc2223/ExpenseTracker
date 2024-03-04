# report_generator.py

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from storage import Storage
from datetime import datetime

def generate_pdf_report(filename='Monthly_Report.pdf'):
    storage = Storage()
    transactions = storage.get_transactions_for_current_month()

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.drawString(100, height - 50, "Financial Report for " + datetime.now().strftime("%B %Y"))
    c.drawString(100, height - 100, "Incomes and Expenses Summary:")

    # Dynamically add transaction details
    start_height = height - 125
    for transaction in transactions:
        start_height -= 25
        c.drawString(100, start_height, str(transaction))

    c.save()


# Add to user_interface.py or a new module

import pandas as pd

def export_to_excel(transactions, filename='monthly_report.xlsx'):
    df = pd.DataFrame([t.__dict__ for t in transactions])
    df.to_excel(filename, index=False)
    print(f"Report exported to {filename}")


print("PDF report generated.")
