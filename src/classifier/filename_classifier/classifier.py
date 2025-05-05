from .rule_matchers import regex_match_filename, get_fuzzy_score


# Attempt to classify the file based on its filename.
def classify_using_filename(filename, RULES):
    filename = filename.lower()

    # Search for regex pattern match in filename.
    for rule in RULES:
        matched, matching_text = regex_match_filename(
            rule.get("filename_regex", []), filename
        )

        if matched:
            return {
                "success": True,
                "data": {
                    "label": rule["label"],
                    "step": 1,
                    "based_on": "filename",
                    "match_type": "regex",
                    "additional_info": {"matching_text": matching_text},
                    "confidence": 1.0,
                },
            }

    # If no exact match is found, fall back on fuzzy matching.
    for rule in RULES:
        score, best_matching_text = get_fuzzy_score(
            rule.get("fuzzy_keywords", []), filename
        )

        if best_matching_text is not None:
            return {
                "success": True,
                "data": {
                    "label": rule["label"],
                    "step": 2,
                    "based_on": "filename",
                    "match_type": "fuzzy",
                    "additional_info": {"best_matching_text": best_matching_text},
                    "confidence": round(score / 100, 2),
                },
            }
