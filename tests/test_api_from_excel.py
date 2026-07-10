"""Generate pytest cases dynamically from the Excel workbook."""

import os
import pytest
from core.excel_reader import load_test_cases
from core.test_templates import run_positive_template

EXCEL_PATH = os.getenv("TEST_DATA_PATH", r"C:\Users\ADMIN\Downloads\test_data3.xlsx")

_all_cases = load_test_cases(EXCEL_PATH)
_active_cases = [c for c in _all_cases if c["run_flag"] == "Y"]


@pytest.mark.parametrize(
    "case",
    _active_cases,
    ids=[c["test_id"] for c in _active_cases],
)
def test_api_endpoint(case, config, context):
    case_copy = dict(case)
    case_copy.setdefault("headers", {"Content-Type": "application/json"})

    response = run_positive_template(case_copy, config, context)

    try:
        response_json = response.json()
        if isinstance(response_json, dict):
            for key, value in response_json.items():
                context[f"{case['test_id']}.{key}"] = value
    except ValueError:
        pass
