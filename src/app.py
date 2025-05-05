from flask import Flask, request, jsonify

from src.classifier.pipeline import classify_file

app = Flask(__name__)


@app.route("/classify_file", methods=["POST"])
def classify_file_route():

    if "file" not in request.files:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "No file part in the request.",
                        "action": "Ensure form field includes a file with name 'file'.",
                        "code": "missing_file_part",
                        "details": {},
                    },
                }
            ),
            400,
        )

    file = request.files["file"]
    if file.filename == "":
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "No selected file.",
                        "action": "Select a file before submitting.",
                        "code": "no_file_selected",
                        "details": {},
                    },
                }
            ),
            400,
        )

    classification_result, status_code = classify_file(file)
    return jsonify(classification_result), status_code


if __name__ == "__main__":
    app.run(debug=True)
