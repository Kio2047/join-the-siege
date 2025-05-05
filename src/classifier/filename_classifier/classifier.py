from .rule_matchers import regex_match_filename, get_fuzzy_score


# Tries exact pattern matching against the filename
# Falls back to fuzzy keyword scoring if no regex match is found
# fuzzy_threshold defaults to 90 — this can be tuned in production by assessing balance between false positives vs. missed matches
def classify_using_filename(filename, RULES, fuzzy_threshold=90):

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

        if score >= fuzzy_threshold:
            return {
                "label": rule["label"],
                "step": 2,
                "based_on": "filename",
                "match_type": "fuzzy",
                "additional_info": {"best_matching_text": best_matching_text},
                "confidence": round(score / 100, 2),
            }
