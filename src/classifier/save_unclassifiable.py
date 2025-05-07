import os


_UNCLASSIFIABLE_DIR = "manual_review"


# Save unclassifiable file for manual review.
def save_unclassifiable_file(file):
    os.makedirs(_UNCLASSIFIABLE_DIR, exist_ok=True)
    file_path = os.path.join(_UNCLASSIFIABLE_DIR, file.filename)
    file.save(file_path)
