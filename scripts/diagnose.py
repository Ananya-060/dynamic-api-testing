import os
import sys
sys.path.append('.')

from core.excel_reader import load_config, load_test_cases
from core.test_templates import run_positive_template

EXCEL_PATH = os.getenv("TEST_DATA_PATH", r"C:\Users\ADMIN\Downloads\test_data3.xlsx")
CONFIG = load_config(EXCEL_PATH)
CASES = load_test_cases(EXCEL_PATH)

context = {}

for case in CASES:
    if case.get("run_flag", "Y").upper() != "Y":
        continue

    case_copy = dict(case)
    case_copy.setdefault("headers", {"Content-Type": "application/json"})
    response = run_positive_template(case_copy, CONFIG, context)

    try:
        response_json = response.json()
        if isinstance(response_json, dict):
            for key, value in response_json.items():
                context[f"{case['test_id']}.{key}"] = value
    except ValueError:
        pass
