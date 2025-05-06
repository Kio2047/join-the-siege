from sentence_transformers import SentenceTransformer
import joblib
import os

from .rule_matcher import regex_match_file_content


_MODEL_PATH = "src/classifier/file_content_classifier/models"


# Initialise embedding model, classifier and label encoder.
_embedder = SentenceTransformer(
    open(os.path.join(_MODEL_PATH, "embedder.txt")).read().strip()
)
_classifier = joblib.load(os.path.join(_MODEL_PATH, "classifier.joblib"))
_label_encoder = joblib.load(os.path.join(_MODEL_PATH, "label_encoder.joblib"))


def classify_using_file_content(file_text, RULES, MIN_CONFIDENCE):
    # Try rule-based matching.
    for rule in RULES:
        confidence, text_matches = regex_match_file_content(
            rule.get("content_regex", []), file_text
        )

        if confidence >= MIN_CONFIDENCE:
            return {
                "success": True,
                "data": {
                    "label": rule["label"],
                    "step": 3,
                    "based_on": "file content",
                    "match_type": "regex",
                    "additional_info": {"text_matches": text_matches},
                    "confidence": confidence,
                },
            }

    # Fall back on use embedding + classifier if rule-based match confidence is insufficinet.
    # Embed file text.
    embedding = _embedder.encode([file_text])[0]

    # Predict label with an associated level of confidence using classifier.
    prediction = _classifier.predict([embedding])[0]
    label = _label_encoder.inverse_transform([prediction])[0]
    confidence = max(_classifier.predict_proba([embedding])[0])

    if confidence >= MIN_CONFIDENCE:
        return {
            "success": True,
            "data": {
                "label": label,
                "step": 4,
                "based_on": "file content",
                "match_type": "embedding + classifier",
                "additional_info": {},
                "confidence": confidence,
            },
        }

    else:
        return {
            "success": False,
            "error": {
                "message": "Could not confidently classify document.",
                "action": "Document saved for manual review.",
                "code": "unclassifiable_file",
                "details": {
                    "final_predicted_label": label,
                    "predicted_confidence": confidence,
                    "min_confidence_required": MIN_CONFIDENCE,
                    "fallback_model": "embedding + classifier",
                },
            },
        }
