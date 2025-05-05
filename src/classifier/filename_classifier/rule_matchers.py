from rapidfuzz import fuzz, process


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
        filename, fuzzy_keywords, fuzz.partial_ratio
    )
    return score, best_match
