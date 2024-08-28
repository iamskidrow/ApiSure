from typing import Dict, Any, Tuple, Set


def validate_schema(response: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[Set[str], Set[str]]:
    if schema.get('type') == 'object':
        properties = schema.get('properties', {})
        required = set(schema.get('required', []))
        response_keys = set(response.keys())
        missing_keys = required - response_keys
        extra_keys = response_keys - properties.keys()

        for key, value in properties.items():
            if key in response:
                response_value = response[key]
                if value.get('type') == 'object' and isinstance(response_value, dict):
                    nested_missing, nested_extra = validate_schema(response_value, value)
                    missing_keys.update(nested_missing)
                    extra_keys.update(nested_extra)
                elif value.get('type') == 'array' and isinstance(response_value, list) and response_value:
                    nested_missing, nested_extra = validate_schema(response_value[0], value['items'])
                    missing_keys.update(nested_missing)
                    extra_keys.update(nested_extra)

        return missing_keys, extra_keys
    elif schema.get('type') == 'array' and isinstance(response, list) and response:
        return validate_schema(response[0], schema['items'])
    return set(), set()


def validate_content(response_json: Dict[str, Any], expected_content: Dict[str, Any]) -> Tuple[bool, str]:
    for key, value in expected_content.items():
        if key not in response_json:
            return False, f"Key '{key}' not found in response"
        if response_json[key] != value:
            return False, f"Value mismatch for key '{key}': expected '{value}', got '{response_json[key]}'"
    return True, "Content validation passed"


def validate_content_type(response_json: Dict[str, Any], expected_types: Dict[str, type]) -> Tuple[bool, str]:
    for key, expected_type in expected_types.items():
        if key not in response_json:
            return False, f"Key '{key}' not found in response"
        if not isinstance(response_json[key], expected_type):
            return False, f"Type mismatch for key '{key}': expected {expected_type.__name__}, got {type(response_json[key]).__name__}"
    return True, "Content type validation passed"


def validate_headers(response_headers: Dict[str, str], expected_headers: Dict[str, str],
                     forbidden_headers: list[str]) -> Tuple[bool, str]:
    for header, value in expected_headers.items():
        if header not in response_headers:
            return False, f"Expected header '{header}' not found"
        if response_headers[header] != value:
            return False, f"Header '{header}' value mismatch: expected '{value}', got '{response_headers[header]}'"

    for header in forbidden_headers:
        if header in response_headers:
            return False, f"Forbidden header '{header}' found in response"

    return True, "Header validation passed"
