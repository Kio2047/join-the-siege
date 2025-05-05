from pathlib import Path
import os, yaml, importlib.resources as pkg
import re


# Load raw rules from override / default config
def load_config(filename, override=False):

    # If the override flag is true, check for the presence of an overriding config file
    if override:

        config_dir_paths = []

        # Get explicit path to config override dir via env variable
        env_config_dir = os.getenv("CLASSIFIER_CONFIG_DIR")
        if env_config_dir:
            config_dir_paths.append(Path(env_config_dir))

        # Get local config override dir wherever the process starts
        config_dir_paths.append(Path.cwd() / "config")

        # Check to see whether config override file exists in either dir (prioritising env path)
        for dir_path in config_dir_paths:
            file_path = dir_path / filename
            if file_path.exists():
                with file_path.open() as file:
                    return yaml.safe_load(file)

    # Fall back on the default config shipped in src/classifier/config/
    with pkg.files("classifier.config").joinpath(filename).open() as file:
        return yaml.safe_load(file)


# Validates each rule has a non-empty 'label'
# All other fields must be either empty or lists of strings
def _validate_rule(rule):
    label = rule.get("label", "")
    if not label.strip():
        raise ValueError(
            f"Rule {rule} is missing a valid 'label' (must be non-empty string)"
        )

    for key, value in rule.items():

        if key == "label":
            continue

        if value is None:
            continue

        if key == "content_regex":

            if not isinstance(value, dict):
                raise ValueError(
                    f"Rule '{label}' field 'content_regex' must be a dictionary"
                )

            allowed_subkeys = {"required", "supporting", "negative"}

            for subkey, subvalue in value.items():
                if subkey not in allowed_subkeys:
                    raise ValueError(
                        f"Rule '{label}' content_regex contains invalid field '{subkey}'"
                    )

                if subvalue is None:
                    continue

                if not isinstance(subvalue, list):
                    raise ValueError(
                        f"Rule '{label}' content_regex field '{subkey}' must be a list"
                    )

                if not all(isinstance(item, str) for item in subvalue):
                    raise ValueError(
                        f"Rule '{label}' content_regex field '{subkey}' must be a list of strings"
                    )

            continue

        if not isinstance(value, list):
            raise ValueError(f"Rule '{label}' field '{key}' must be a list")

        if not all(isinstance(item, str) for item in value):
            raise ValueError(f"Rule '{label}' field '{key}' must be a list of strings")


# Validates each rule before compiling regex patterns and lowercasing fuzzy keywords
def _compile_rules(raw_rules):
    compiled_rules = []

    for rule in raw_rules:
        _validate_rule(rule)

        content_regex = rule.get("content_regex", {})
        compiled_content_regex = {
            "required": [
                re.compile(pattern, re.I)
                for pattern in content_regex.get("required", [])
            ],
            "supporting": [
                re.compile(pattern, re.I)
                for pattern in content_regex.get("supporting", [])
            ],
            "negative": [
                re.compile(pattern, re.I)
                for pattern in content_regex.get("negative", [])
            ],
        }

        compiled_rules.append(
            {
                "label": rule.get("label", ""),
                "filename_regex": [
                    re.compile(pattern, re.I)
                    for pattern in rule.get("filename_regex", [])
                ],
                "fuzzy_keywords": [
                    keyword.lower() for keyword in rule.get("fuzzy_keywords", [])
                ],
                "content_regex": compiled_content_regex,
            }
        )
    return compiled_rules


def _validate_filetypes(mapping):
    for extension, mimes in mapping.items():
        if not isinstance(extension, str) or not extension.startswith("."):
            raise ValueError(f"Invalid extension key: {extension}")
        if not isinstance(mimes, list) or not all(
            isinstance(mime, str) for mime in mimes
        ):
            raise ValueError(f"Invalid MIME list for {extension}")
    return mapping


_RAW_RULES = load_config("industry_rules.yaml", True)
DOCUMENT_RULES = _compile_rules(_RAW_RULES)

_RAW_FILETYPES = load_config("supported_filetypes.yaml", False)
SUPPORTED_FILETYPES = _validate_filetypes(_RAW_FILETYPES)
