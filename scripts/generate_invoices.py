import random
import pandas as pd
import os

# Variant labels and templates
invoice_number_labels = ["Invoice Number", "Inv No", "Invoice No", "Invoce #"]
issue_date_labels = ["Issue Date", "Date of Issue", "Invoice Date"]
due_date_labels = ["Due Date", "Payment Due", "Terms", "Due Dt"]
subtotal_labels = ["Subtotal", "Sub total", "Sub-Total"]
tax_labels = ["Tax", "VAT", "Sales Tax"]
discount_labels = ["Discount", "Promo Disc", "Discount Amt"]
total_labels = ["Total", "TOTAL", "Total Amnt", "T O T A L"]
footer_options = [
    "Thank you for your business!",
    "Contact: support@example.com",
    "Send questions to billing@example.com",
    "Phone: +1 (800) 555-1212",
    "",
]

companies = [
    "Acme Corp",
    "Timmerman Industries",
    "Zeta Solutions",
    "Studio Shodwe",
    "Nova Creatives",
]
clients = [
    "Skyline Ventures",
    "Brightworks Ltd",
    "Greenfield Inc",
    "Morgan Maxwell",
    "Apollo Partners",
]
services = [
    "Logo Design",
    "UX Research",
    "Web Development",
    "Print Setup",
    "Marketing Strategy",
    "Brochure Design",
    "Letterhead Design",
    "Proposal Layout",
    "Consulting",
    "Site Audit",
]


def ocr_quirk(text):
    if random.random() < 0.15:
        text = text.replace("Invoice", "Invoce")
    if random.random() < 0.15:
        text = text.replace("Total", "Total Amnt")
    if random.random() < 0.2:
        text = text.replace(":", "")  # dropped colons
    if random.random() < 0.1:
        text = text.lower()
    if random.random() < 0.1:
        text = text.upper()
    return text


def generate_invoice():
    lines = []

    # Header
    seller = random.choice(companies)
    buyer = random.choice(clients)
    lines.append(seller)
    lines.append(f"Bill To: {buyer}")

    # Metadata
    inv_num = random.randint(1000, 9999)
    issue_date = f"{random.randint(1,28):02}/0{random.randint(1,9)}/2023"
    due_date = f"{random.randint(1,28):02}/1{random.randint(0,1)}/2023"

    lines.append(ocr_quirk(f"{random.choice(invoice_number_labels)}: {inv_num}"))
    lines.append(ocr_quirk(f"{random.choice(issue_date_labels)}: {issue_date}"))
    lines.append(ocr_quirk(f"{random.choice(due_date_labels)}: {due_date}"))

    # Optional payment terms
    if random.random() < 0.5:
        lines.append("Payment Terms: Net 30 days from issue date")

    # Item table header (optional)
    if random.random() < 0.6:
        lines.append("Item Description | Qty/Hrs | Rate | Amount")

    subtotal = 0
    for _ in range(random.randint(2, 5)):
        desc = random.choice(services)
        qty = random.randint(1, 10)
        rate = round(random.uniform(50, 300), 2)
        amount = round(qty * rate, 2)
        subtotal += amount
        if random.random() < 0.5:
            lines.append(f"{desc} – ${amount:.2f}")
        else:
            lines.append(f"{desc} | {qty} | ${rate:.2f} | ${amount:.2f}")

    # Totals
    lines.append(ocr_quirk(f"{random.choice(subtotal_labels)}: ${subtotal:.2f}"))
    if random.random() < 0.5:
        discount = round(random.uniform(10, 50), 2)
        lines.append(ocr_quirk(f"{random.choice(discount_labels)}: -${discount:.2f}"))
        subtotal -= discount
    if random.random() < 0.7:
        tax = round(subtotal * random.uniform(0.05, 0.15), 2)
        lines.append(ocr_quirk(f"{random.choice(tax_labels)}: ${tax:.2f}"))
        subtotal += tax

    lines.append(ocr_quirk(f"{random.choice(total_labels)}: ${subtotal:.2f}"))

    # Payment section
    if random.random() < 0.7:
        lines.append("Send Payment To:")
        lines.append("Bank Name: Example Bank")
        lines.append("Account No: 123-456-7890")

    # Optional footer
    footer = random.choice(footer_options)
    if footer:
        lines.append(footer)

    # Add OCR-like quirks in structure
    if random.random() < 0.1:
        lines.insert(random.randint(2, 4), "")  # insert blank line
    if random.random() < 0.1 and len(lines) > 6:
        del lines[random.randint(2, 5)]  # drop a line

    return {"text": "\\n".join(lines), "label": "invoice"}


def save_invoices(num, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = [generate_invoice() for _ in range(num)]
    pd.DataFrame(data).to_csv(path, index=False)
    print(f"Generated {num} synthetic invoices and saved to '{path}'")


if __name__ == "__main__":
    save_invoices(300, "data/training/invoices_train.csv")
    save_invoices(30, "data/validation/invoices_val.csv")
