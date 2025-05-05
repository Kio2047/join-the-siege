import pytest
from werkzeug.datastructures import FileStorage
import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import classification_report, accuracy_score, f1_score
import joblib
import re

from src.classifier.extract import extract_file_text
from src.classifier.file_content_classifier.rule_matcher import regex_match_file_content


# Test text extraction works as expected.
@pytest.mark.parametrize(
    "filename, ext, expected_substrings",
    [
        (
            "files/bank_statement_1.pdf",
            "pdf",
            ["Debit Card Purchase", "Account Number"],
        ),
        (
            "files/drivers_license_1.jpg",
            "jpg",
            ["DRIVER LICENSE", "Eyes", "License No."],
        ),
        (
            "files/invoice_2.pdf",
            "pdf",
            ["INVOICE", "SEND PAYMENT TO"],
        ),
    ],
)
def test_extract_file_text(filename, ext, expected_substrings):
    with open(filename, "rb") as f:
        file = FileStorage(stream=f, filename=filename)

        text = extract_file_text(file, ext)

        assert isinstance(text, str)
        for expected in expected_substrings:
            assert (
                expected.lower() in text.lower()
            ), f"Missing expected text: '{expected}'"


# Test text content pattern scoring works as expected
@pytest.mark.parametrize(
    "file_text, patterns, expected_confidence, expected_required, expected_supporting, expected_negative",
    [
        # All required and all supporting present
        (
            "Invoice Number: 12345\nTotal Amount: $1000\nPayment Due: tomorrow",
            {
                "required": [re.compile(r"invoice number", re.I)],
                "supporting": [
                    re.compile(r"total amount", re.I),
                    re.compile(r"payment due", re.I),
                ],
                "negative": [],
            },
            0.95,  # _BASE_SCORE + 2/2 * _ADDITIONAL_RANGE = 0.60 + 1 * 0.35
            ["Invoice Number"],
            ["Total Amount", "Payment Due"],
            [],
        ),
        # Required present, 1/2 supporting
        (
            "Invoice Number: 12345\nTotal Amount: $1000",
            {
                "required": [re.compile(r"invoice number", re.I)],
                "supporting": [
                    re.compile(r"total amount", re.I),
                    re.compile(r"payment due", re.I),
                ],
                "negative": [],
            },
            0.775,  # 0.60 + (0.5 * 0.35)
            ["Invoice Number"],
            ["Total Amount"],
            [],
        ),
        # Required match missing
        (
            "Total Amount: $1000",
            {
                "required": [re.compile(r"invoice number", re.I)],
                "supporting": [re.compile(r"total amount", re.I)],
                "negative": [],
            },
            0,
            [],
            [],
            [],
        ),
        # Negative match found
        (
            "Invoice Number: 12345\nCONFIDENTIAL - DO NOT SHARE",
            {
                "required": [re.compile(r"invoice number", re.I)],
                "supporting": [],
                "negative": [re.compile(r"confidential", re.I)],
            },
            0,
            [],
            [],
            ["CONFIDENTIAL"],
        ),
        # Required match, no supporting patterns defined
        (
            "Invoice Number: 12345",
            {
                "required": [re.compile(r"invoice number", re.I)],
                "supporting": [],
                "negative": [],
            },
            0.95,  # Supporting list is empty => frac = 1
            ["Invoice Number"],
            [],
            [],
        ),
    ],
)
def test_regex_match_file_content(
    file_text,
    patterns,
    expected_confidence,
    expected_required,
    expected_supporting,
    expected_negative,
):
    confidence, matches = regex_match_file_content(patterns, file_text)

    assert round(confidence, 3) == round(expected_confidence, 3)
    assert [s.lower() for s in matches["required"]] == [
        s.lower() for s in expected_required
    ]
    assert [s.lower() for s in matches["supporting"]] == [
        s.lower() for s in expected_supporting
    ]
    assert [s.lower() for s in matches["negative"]] == [
        s.lower() for s in expected_negative
    ]


VAL_PATH = "data/validation"
MODEL_PATH = "src/classifier/file_content_classifier/models"


# Evaluate classifier performance on synthetic validation data
@pytest.mark.skipif(not os.path.isdir(VAL_PATH), reason="Validation data not available")
def test_classifier_accuracy_threshold():
    # Load model components
    embedder_name = open(os.path.join(MODEL_PATH, "embedder.txt")).read().strip()
    embedder = SentenceTransformer(embedder_name)
    clf = joblib.load(os.path.join(MODEL_PATH, "classifier.joblib"))
    label_encoder = joblib.load(os.path.join(MODEL_PATH, "label_encoder.joblib"))

    # Load validation data
    texts, labels = [], []
    for filename in os.listdir(VAL_PATH):
        if filename.endswith(".csv"):
            df = pd.read_csv(os.path.join(VAL_PATH, filename))
            texts.extend(df["text"].tolist())
            labels.extend(df["label"].tolist())

    assert texts and labels, "Validation dataset is empty"

    # Encode and predict
    X_val = embedder.encode(texts, convert_to_tensor=False, show_progress_bar=False)
    y_true = label_encoder.transform(labels)
    y_pred = clf.predict(X_val)

    # Evaluate metrics
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro")

    # Assert minimum acceptable performance
    assert acc >= 0.80, f"Accuracy too low: {acc:.2f}"
    assert macro_f1 >= 0.75, f"Macro F1 too low: {macro_f1:.2f}"


# TODO: Test end-to-end file content classifier works as expected, mocking its dependencies.
