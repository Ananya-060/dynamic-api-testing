"""
Validates the actual response against what the Excel row expected.
Status check always runs. Response body check only runs if
expected_response is non-empty.
"""


def check_status(response, expected_status: int):
    if expected_status is None:
        return True, "No expected_status provided - skipped"
    actual = response.status_code
    if actual == expected_status:
        return True, f"Status OK ({actual})"
    return False, f"Status mismatch: expected {expected_status}, got {actual}"


def check_response_fields(response, expected_response: dict):
    if not expected_response:
        return True, "No expected_response provided - skipped"

    try:
        actual_json = response.json()
    except ValueError:
        return False, "Response is not valid JSON, cannot compare fields"

    mismatches = []
    for key, expected_value in expected_response.items():
        actual_value = actual_json.get(key, "<<MISSING>>")
        if actual_value != expected_value:
            mismatches.append(f"'{key}': expected {expected_value!r}, got {actual_value!r}")

    if mismatches:
        return False, "Field mismatches: " + "; ".join(mismatches)
    return True, "All expected fields matched"


def evaluate(case: dict, response) -> dict:
    status_ok, status_msg = check_status(response, case["expected_status"])
    fields_ok, fields_msg = check_response_fields(response, case["expected_response"])
    passed = status_ok and fields_ok

    return {
        "test_id": case["test_id"],
        "endpoint_name": case["endpoint_name"],
        "method": case["method"],
        "url_path": case["url_path"],
        "passed": passed,
        "status_check": status_msg,
        "field_check": fields_msg,
        "actual_status": response.status_code,
        "response_snippet": response.text[:300],
    }