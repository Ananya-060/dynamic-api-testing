import copy
from core.api_client import send_request
from core.assertions import evaluate


def _clone_body(body):
    return copy.deepcopy(body) if isinstance(body, (dict, list)) else body


def run_positive_template(case, config, context=None):
    """Run a positive (happy-path) test for any endpoint.

    Args:
        case (dict): test case dict with at least `method`, `url_path`, and `body`.
        config (dict): CONFIG loaded from Excel.
        context (dict): optional context passed to `send_request`.

    Returns:
        requests.Response
    """
    context = context or {}
    method = case.get("method", "GET").upper()
    url_path = case.get("url_path")
    headers = case.get("headers", {"Content-Type": "application/json"})
    body = _clone_body(case.get("body"))

    request_case = {
        "method": method,
        "url_path": url_path,
        "path_params": case.get("path_params", {}),
        "query_params": case.get("query_params", {}),
        "headers": headers,
        "body": body,
    }

    response = send_request(request_case, config, context=context)
    result = evaluate(case, response)
    assert result.get("passed"), f"Positive case failed: {result}"
    return response


def run_negative_template(case, config, scenario, context=None):
    """Run a negative test scenario against any endpoint.

    Args:
        case (dict): base test case dict.
        config (dict): CONFIG loaded from Excel.
        scenario (dict): scenario override with optional keys: method, url_path, headers, body_fn, expected_statuses
        context (dict): optional context for send_request

    Returns:
        requests.Response
    """
    context = context or {}
    method = scenario.get("method", case.get("method", "GET")).upper()
    url_path = scenario.get("url_path", case.get("url_path"))
    headers = scenario.get("headers", case.get("headers", {"Content-Type": "application/json"}))
    body_fn = scenario.get("body_fn", lambda b: b)
    body = body_fn(_clone_body(case.get("body")))

    request_case = {
        "method": method,
        "url_path": url_path,
        "path_params": case.get("path_params", {}),
        "query_params": case.get("query_params", {}),
        "headers": headers,
        "body": body,
    }

    response = send_request(request_case, config, context=context)
    expected = scenario.get("expected_statuses", [400, 422])
    case_id = case.get("test_id", "UNKNOWN")
    name = scenario.get("name", "scenario")
    assert response.status_code in expected, f"{case_id} {name} expected {expected}, got {response.status_code}"
    return response
