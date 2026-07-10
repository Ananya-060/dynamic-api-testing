"""
Builds and sends the actual HTTP request for a given test case row.
No endpoint is ever hardcoded here - everything comes from the row
dict (from excel_reader.py) and the config dict.
"""

import logging
import re
import time
import requests

PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z0-9_.]+)\}")
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
logger = logging.getLogger(__name__)


def resolve_placeholders(obj, context: dict):
    if isinstance(obj, dict):
        return {k: resolve_placeholders(v, context) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_placeholders(item, context) for item in obj]
    if isinstance(obj, str):
        def _replace(match):
            key = match.group(1)
            return str(context[key]) if key in context else match.group(0)
        return PLACEHOLDER_PATTERN.sub(_replace, obj)
    return obj


def build_url(base_url: str, url_path: str, path_params: dict) -> str:
    path = url_path
    for key, value in path_params.items():
        path = path.replace("{" + key + "}", str(value))
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def send_request(case: dict, config: dict, context: dict, timeout: int = 30):
    full_context = {**config, **context}

    base_url = config.get("base_url", "").rstrip("/")
    url = build_url(base_url, case["url_path"], case["path_params"])

    headers = resolve_placeholders(case["headers"], full_context)
    query_params = resolve_placeholders(case["query_params"], full_context)
    body = resolve_placeholders(case["body"], full_context)

    max_retries = int(config.get("max_retries", 0))
    retry_delay_seconds = float(config.get("retry_delay_seconds", 0))
    retries_attempted = 0

    logger.info(
        "Making request | test_id=%s | method=%s | url=%s | headers=%s | body=%s",
        case.get("test_id"),
        case.get("method"),
        url,
        headers,
        body,
    )

    while True:
        try:
            response = requests.request(
                method=case["method"],
                url=url,
                headers=headers,
                params=query_params if query_params else None,
                json=body if body else None,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            if retries_attempted >= max_retries:
                logger.exception(
                    "Request failed after retries",
                    extra={"test_id": case.get("test_id"), "error": str(exc)},
                )
                raise
            retries_attempted += 1
            logger.warning(
                "Request failed, retrying | test_id=%s | attempt=%s | error=%s",
                case.get("test_id"),
                retries_attempted,
                str(exc),
            )
            time.sleep(retry_delay_seconds)
            continue

        if response.status_code in RETRYABLE_STATUS_CODES and retries_attempted < max_retries:
            retries_attempted += 1
            logger.warning(
                "Received retryable status, retrying | test_id=%s | attempt=%s | status_code=%s | response_text=%s",
                case.get("test_id"),
                retries_attempted,
                response.status_code,
                response.text[:500],
            )
            time.sleep(retry_delay_seconds)
            continue

        logger.info(
            "Request completed | test_id=%s | status_code=%s | response_text=%s",
            case.get("test_id"),
            response.status_code,
            response.text[:500],
        )
        return response