from io import BytesIO
from pathlib import Path

import pytest
from src.app import app
from src.classifier.pipeline import _allowed_file


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.mark.parametrize(
    "ext, expected",
    [
        ("pdf", True),
        ("png", True),
        ("docx", True),
        ("mp4", False),
        ("", False),
    ],
)
def test_allowed_file(ext, expected):
    assert _allowed_file(ext) == expected


def test_no_file_in_request(client):
    response = client.post("/classify_file")

    assert response.status_code == 400

    data = response.get_json()
    assert data["error"]["code"] == "missing_file_part"
    assert "No file part" in data["error"]["message"]


def test_no_selected_file(client):
    data = {"file": (BytesIO(b""), "")}  # Empty filename
    response = client.post(
        "/classify_file", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 400

    data = response.get_json()
    assert data["error"]["code"] == "no_file_selected"
    assert "Select a file" in data["error"]["action"]


# Test end-to-end classification pipeline.
@pytest.mark.parametrize(
    "filename,expected_class,expected_status_code",
    [
        ("bank_statement_1.pdf", "bank_statement", 200),
        ("invoice_1.pdf", "invoice", 200),
        ("drivers_licence_1.jpg", "driving_license", 200),
        ("poorly_named.jpg", "driving_license", 200),
        ("poorly_named.pdf", "invoice", 200),
        ("poorly_named.csv", None, 400),
        ("poorly_named.docx", None, 422),
    ],
)
def test_success(client, filename, expected_class, expected_status_code):
    file_path = Path(__file__).parent / "files" / filename
    assert file_path.exists(), f"Test file not found: {file_path}"

    with open(file_path, "rb") as f:
        file_data = f.read()

    data = {"file": (BytesIO(file_data), filename)}
    response = client.post(
        "/classify_file", data=data, content_type="multipart/form-data"
    )

    assert response.status_code == expected_status_code

    if response.status_code == 200:
        assert response.get_json()["data"]["label"] == expected_class
    else:
        assert "error" in response.get_json()
