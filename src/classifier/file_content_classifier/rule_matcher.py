# Tunable scoring constants.
_BASE_SCORE = 0.60  # Score once every required pattern is found
_ADDITIONAL_RANGE = 0.35  # Max confidence boost from supporting patterns

# Ensure the confidence cap does not exceed 1.0. Ideally the max confidence should be below 1 — content-based rules are ultimately heuristics, but appropriate numbers are difficult to define without analysis of classification performance in production.
if _BASE_SCORE + _ADDITIONAL_RANGE > 1.0:
    raise ValueError("Combined _BASE_SCORE and _ADDITIONAL_RANGE must not exceed 1.0")


# Search file text content for regex pattern matches.
def regex_match_file_content(file_content_patterns, file_text):
    # Store found matches.
    text_matches = {
        "required": [],
        "supporting": [],
        "negative": [],
    }

    # Exit early if no text is passed in.
    if not file_text:
        return 0, text_matches

    # Check for negative matches — if any are found, disqualify early.
    for pattern in file_content_patterns.get("negative", []):
        match = pattern.search(file_text)
        if match:
            text_matches["negative"].append(match.group())
            return 0, text_matches

    # Check that all required patterns are present — if any are not found, disqualify.
    for pattern in file_content_patterns.get("required", []):
        match = pattern.search(file_text)
        if match:
            text_matches["required"].append(match.group())
        else:
            return 0, text_matches

    # Search for supporting matches.
    for pattern in file_content_patterns.get("supporting", []):
        for match in pattern.finditer(file_text):
            text_matches["supporting"].append(match.group())

    # Calculate confidence level based on found matches.
    supporting_match_count = len(text_matches["supporting"])
    supporting_patterns = file_content_patterns.get("supporting", [])
    if supporting_patterns:
        frac = supporting_match_count / len(supporting_patterns)
    else:
        frac = 1
    confidence = _BASE_SCORE + (frac * _ADDITIONAL_RANGE)

    return confidence, text_matches
