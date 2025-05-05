import re
import pytest

from src.classifier.filename_classifier.classifier import classify_using_filename
from src.classifier.filename_classifier.rule_matchers import (
    _FUZZY_THRESHOLD,
    get_fuzzy_score,
    regex_match_filename,
)
from src.classifier.config_loader import DOCUMENT_RULES, SUPPORTED_FILETYPES


# Test filename regex pattern matching works as expected.
@pytest.mark.parametrize(
    "filename, patterns, expected",
    [
        (
            "bank_statement_Q1.pdf",
            [r"(bank|acct|account).*statement"],
            (True, "bank_statement"),
        ),
        ("stmt_2023.pdf", [r"stmt[_-]?\d{4}"], (True, "stmt_2023")),
        ("invoice-00123.pdf", [r"stmt[_-]?\d{4}"], (False, None)),
        ("dl_12345.jpg", [r"\bdl[_-]?\d{5,}"], (True, "dl_12345")),
    ],
)
def test_regex_match_filename(filename, patterns, expected):
    compiled = [re.compile(p, re.I) for p in patterns]
    assert regex_match_filename(compiled, filename) == expected


# Test filename fuzzy matching performs reasonably.
@pytest.mark.parametrize(
    "fuzzy_keywords, filename, expected_keyword",
    [
        (
            ["driver's license", "dl", "driving license"],
            "my_driving_license.png",
            "driving license",
        ),
        (["invoice"], "invoic_2023.pdf", "invoice"),
        ([], "somefile.txt", None),
        (["passport", "visa"], "my_driving_license.pdf", None),
    ],
)
def test_get_fuzzy_score(fuzzy_keywords, filename, expected_keyword):
    score, keyword = get_fuzzy_score(fuzzy_keywords, filename)

    if expected_keyword is None:
        assert score < _FUZZY_THRESHOLD
        assert keyword is None
    else:
        assert score >= _FUZZY_THRESHOLD
        assert keyword == expected_keyword


TEST_RULES = [
    {
        "label": "driving_license",
        "filename_regex": [re.compile(r"(driver|driving)[-_]?licen[cs]e", re.I)],
        "fuzzy_keywords": ["driver license", "driving licence"],
    },
    {
        "label": "bank_statement",
        "filename_regex": [re.compile(r"(bank|acct|account).*statement", re.I)],
        "fuzzy_keywords": ["bank statement", "statement of account"],
    },
]


# Test end-to-end filename classifier works as expected.
@pytest.mark.parametrize(
    "filename, expected_label, expected_step, expected_match_type",
    [
        ("my_driving_license.pdf", "driving_license", 1, "regex"),
        ("bank_statement_q1.pdf", "bank_statement", 1, "regex"),
        ("driving_license_final.pdf", "driving_license", 1, "regex"),
        ("driverlcence_copy.pdf", "driving_license", 2, "fuzzy"),
        ("accountsummary.pdf", None, None, None),
    ],
)
def test_classify_using_filename(
    filename, expected_label, expected_step, expected_match_type
):
    result = classify_using_filename(filename, TEST_RULES)

    if expected_label is None:
        assert result is None or result.get("success") is not True
    else:
        assert result["success"] is True
        assert result["data"]["label"] == expected_label
        assert result["data"]["step"] == expected_step
        assert result["data"]["match_type"] == expected_match_type
