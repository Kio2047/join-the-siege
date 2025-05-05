from pathlib import Path
import filetype
from werkzeug.datastructures import FileStorage

from .config_loader import DOCUMENT_RULES, SUPPORTED_FILETYPES
from .filename_classifier.classifier import classify_using_filename
from .file_content_classifier.classifier import classify_using_file_content
from .extract import extract_file_text
from .save_unclassifiable import save_unclassifiable_file


MIN_CONFIDENCE = 80


# Check whether file extension is an existing key in SUPPORTED_FILETYPES.yaml config file.
def _allowed_file(ext):
    ext = ext.lower()
    return ext in SUPPORTED_FILETYPES


# Get file MIME type using filetype (less accurate and broad than python-magic but sufficient here).
def _detect_mime(file):
    kind = filetype.guess(file.stream)
    return kind.mime if kind else "application/octet-stream"


# Check whether detected file MIME type matches the filename extension.
def _check_mime_match(ext, mime_type):
    return mime_type in SUPPORTED_FILETYPES.get(ext.lower(), [])


# Classification pipeline.
def classify_file(file):
    filename = file.filename
    file_ext = Path(filename).suffix.lstrip(".")

    # Reject unsupported file extensions.
    if not _allowed_file(file_ext):
        return (
            {
                "success": False,
                "error": {
                    "message": f"File extension '{file_ext}' not supported.",
                    "action": "Ensure file is of supported type.",
                    "code": "unsupported_file",
                    "details": {"provided_extension": file_ext},
                },
            },
            400,
        )

    # Attempt filename-based classification.

    filename_classification_result = classify_using_filename(filename, DOCUMENT_RULES)
    if (
        filename_classification_result is not None
        and filename_classification_result["data"]["confidence"] >= MIN_CONFIDENCE
    ):
        return filename_classification_result, 200

    # Verify MIME type matches extension.
    mime_type = _detect_mime(file)
    if mime_type == "application/octet-stream" or not _check_mime_match(
        file_ext, mime_type
    ):
        return (
            {
                "success": False,
                "error": {
                    "message": "File extension and detected MIME type do not match.",
                    "action": "Ensure file is not corrupted and has the correct extension.",
                    "code": "mime_mismatch",
                    "details": {
                        "declared_extnsion": file_ext,
                        "detected_mime_type": mime_type,
                    },
                },
            },
            400,
        )

    # Attempt content-based classification.
    file_text = extract_file_text(file, file_ext)
    file_content_classification_result = classify_using_file_content(
        file_text, DOCUMENT_RULES, MIN_CONFIDENCE
    )

    if file_content_classification_result["success"]:
        return file_content_classification_result, 200
    else:
        # Final fallback — save unclassifiable document for manual review.
        save_unclassifiable_file(file)
        return file_content_classification_result, 422
