import os
import random
import pandas as pd


# Components for realistic bank statement generation
bank_names = [
    "Bank of Horizon",
    "First National Bank",
    "Metro Credit Union",
    "Citadel Trust",
    "Union Savings",
    "Global Bank",
    "Bank 1 of Testing",
]

descriptions = [
    "Amazon",
    "Payroll",
    "ATM Withdrawal",
    "Online Transfer",
    "Check Deposit",
    "POS Purchase",
    "Bank Fee",
    "Loan Repayment",
    "Direct Deposit",
    "Wire Transfer",
    "Utility Payment",
    "Grocery Store",
]

# Variants for header labels
statement_date_variants = ["Statement Date", "Statement Period", "Date of Statement"]
account_variants = ["Account", "Account Number", "Acct No."]
account_holder_variants = ["Account Holder", "Customer Name", "Holder", "Name"]
opening_balance_variants = ["Opening Balance", "Opening Bal", "Start Balance"]
closing_balance_variants = ["Closing Balance", "Closing Bal", "End Balance"]
end_of_statement_variants = ["End of Statement", "--- End ---", "*** End ***", "END"]


def random_name():
    first = random.choice(
        [
            "Alex",
            "Jamie",
            "Taylor",
            "Morgan",
            "Jordan",
            "Casey",
            "Robin",
            "Chris",
            "Pat",
            "Drew",
        ]
    )
    last = random.choice(
        [
            "Smith",
            "Johnson",
            "Taylor",
            "Brown",
            "Williams",
            "Jones",
            "Miller",
            "Davis",
            "Wilson",
            "Moore",
        ]
    )
    return f"{first} {last}"


def random_transaction_line():
    date = f"{random.randint(1,28):02}/0{random.randint(1,9)}"
    desc = random.choice(descriptions)
    amt = round(random.uniform(10.0, 1000.0), 2)
    sign = random.choice(["-", "+"])
    return f"{date} {desc} {sign}${amt}"


def generate_statement():
    bank = random.choice(bank_names)
    acct = f"XXXX-XXXX-XXXX-{random.randint(1000,9999)}"
    holder = random_name()
    open_bal = f"${round(random.uniform(500, 2000), 2)}"
    close_bal = f"${round(random.uniform(1000, 3000), 2)}"
    date = f"2023-0{random.randint(1, 9)}"

    lines = [
        f"{bank}",
        f"{random.choice(statement_date_variants)}: {date}",
        f"{random.choice(account_holder_variants)}: {holder}",
        f"{random.choice(account_variants)}: {acct}",
        f"{random.choice(opening_balance_variants)}: {open_bal}",
    ]

    for _ in range(random.randint(3, 6)):
        lines.append(random_transaction_line())

    lines.append(f"{random.choice(closing_balance_variants)}: {close_bal}")

    # Optional customer support line
    if random.random() < 0.3:
        support_num = f"1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
        lines.append(f"Support: {support_num}")

    # Optional end-of-statement footer
    if random.random() < 0.5:
        lines.append(random.choice(end_of_statement_variants))

    # Add OCR quirks
    if random.random() < 0.3:
        lines = [line.replace(":", "") for line in lines]
    if random.random() < 0.2:
        lines = [line.replace("Balance", "Bal") for line in lines]
    if random.random() < 0.2:
        random.shuffle(lines[1:-1])  # Shuffle middle content

    return {"text": "\\n".join(lines), "label": "bank_statement"}


def save_statements(num, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = [generate_statement() for _ in range(num)]
    pd.DataFrame(data).to_csv(path, index=False)
    print(f"Generated {num} synthetic bank statements and saved to '{path}'")


if __name__ == "__main__":
    save_statements(300, "data/training/bank_statements_train.csv")
    save_statements(30, "data/validation/bank_statements_val.csv")
