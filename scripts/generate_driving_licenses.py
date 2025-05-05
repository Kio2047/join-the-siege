import os
import random
import string
import pandas as pd


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


def random_dob():
    year = random.randint(1950, 2002)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{day:02}/{month:02}/{year}"


def random_license_number():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=9))


def random_expiry():
    year = random.randint(2025, 2035)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02}-{day:02}"


def random_quirks(text):
    quirks = [
        lambda s: s.replace(":", ""),  # drop colons
        lambda s: s.replace("DOB", "D0B"),  # letter O vs zero
        lambda s: s.replace("Expires", "Expiries"),  # misspelling
        lambda s: s.replace("License", "Licnse"),  # typo
        lambda s: s.replace(" ", "  "),  # extra spaces
        lambda s: s.replace("Name", "N a m e"),  # spacing
        lambda s: s.replace("ID", "1D"),  # OCR confusion
    ]
    for _ in range(random.randint(1, 3)):
        text = random.choice(quirks)(text)
    return text


def generate_license():
    name = random_name()
    dob = random_dob()
    license_no = random_license_number()
    expiry = random_expiry()
    authority = random.choice(["DVLA", "DMV", "State Issuer", "Authority Office"])

    format_templates = [
        f"DRIVER’S LICENSE\nName: {name}\nDOB: {dob}\nID: {license_no}\nExpires: {expiry}",
        f"Name {name}\nLicnse No {license_no}\nD.O.B {dob}\nExp: {expiry}",
        f"DRIVING LICENCE\n{license_no}\n{name}\nDate of Birth: {dob}\nValid Until: {expiry}",
        f"Lic: {license_no}\nHolder: {name}\nDOB - {dob}\nExpiry Date: {expiry}\nAuth: {authority}",
        f"{name}\nDOB {dob}  ID {license_no}\nExp Date {expiry}\nIssuer: {authority}",
    ]

    text = random.choice(format_templates)
    text = random_quirks(text)
    return {"text": text.replace("\n", "\\n"), "label": "driving_license"}


def save_licenses(num, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = [generate_license() for _ in range(num)]
    pd.DataFrame(data).to_csv(path, index=False)
    print(f"Generated {num} synthetic driving licenses and saved to '{path}'")


if __name__ == "__main__":
    save_licenses(300, "data/training/driving_licenses_train.csv")
    save_licenses(30, "data/validation/driving_licenses_val.csv")
