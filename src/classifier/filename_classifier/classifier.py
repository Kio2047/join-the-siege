from .rule_matchers import regex_match_filename, get_fuzzy_score


# Tries exact pattern matching against the filename, before falling back on fuzzy keyword scoring if no exact match is found.
def classify_using_filename(filename, RULES):
    filename = filename.lower()

    for rule in RULES:
        matched, matching_text = regex_match_filename(rule["filename_regex"], filename)
        if matched:
            return {
                "label": rule["label"],
                "step": 1,
                "based_on": "filename",
                "match_type": "regex",
                "additional_info": {"matching_text": matching_text},
                "confidence": 1.0,
            }

    for rule in RULES:
        score, best_matching_text = get_fuzzy_score(rule["fuzzy_keywords"], filename)
        return {
            "label": rule["label"],
            "step": 2,
            "based_on": "filename",
            "match_type": "fuzzy",
            "additional_info": {"best_matching_text": best_matching_text},
            "confidence": round(score / 100, 2),
        }
