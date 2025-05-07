from rapidfuzz import fuzz, process


# In production, the threshold for fuzzy search should tuned by assessing balance between false positives vs. missed matches. For simplicity, in this task I've set it as equal to the MIN_CONFIDENCE rating used throughout the pipeline.
_FUZZY_THRESHOLD = 80


# Search for the first regex pattern with a filename match.
def regex_match_filename(filename_patterns, filename):
    for pattern in filename_patterns:
        match = pattern.search(filename)
        if match:
            return True, match.group()
    return False, None


# Get fuzzy search score and best match in filename.
# The optimal scorer ultimately depends on the nature of the filenames we receive.
# partial_ratio works well if filenames are mostly clean and keywords appear as substrings.
# If keywords are often out of order (e.g., license_driver.png) then token_sort_ratio would be more appropriate.
# If keywords are often out of order and filenames can be noisy (e.g., license_final_copy_driver_2023.png), then token_set_ratio might be a more robust option.
def get_fuzzy_score(fuzzy_keywords, filename):
    if not fuzzy_keywords:
        return 0, None

    best_match, score, _ = process.extractOne(
        filename, fuzzy_keywords, scorer=fuzz.partial_ratio
    )

    if score >= _FUZZY_THRESHOLD:
        return score, best_match
    else:
        return score, None
