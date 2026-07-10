"""
Reads the TestCases sheet and Config sheet from the Excel file.
Nothing here is hardcoded to a specific endpoint - it just reads
whatever rows/keys exist at runtime.
"""

import json
import pandas as pd


def load_config(excel_path: str, sheet_name: str = "Config") -> dict:
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    df.columns = [c.strip().lower() for c in df.columns]

    if "key" not in df.columns or "value" not in df.columns:
        raise ValueError(
            f"Config sheet must have 'key' and 'value' columns. Found: {list(df.columns)}"
        )

    config = {}
    for _, row in df.iterrows():
        key = str(row["key"]).strip()
        value = row["value"]
        if pd.isna(value):
            value = ""
        config[key] = str(value).strip()
    return config


def _safe_json_loads(value, field_name="", test_id=""):
    if pd.isna(value) or str(value).strip() == "":
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"[{test_id}] Invalid JSON in column '{field_name}': {value!r} -> {e}"
        )


def load_test_cases(excel_path: str, sheet_name: str = "TestCases") -> list:
    df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]

    required_cols = [
        "test_id", "endpoint_name", "method", "url_path",
        "path_params", "query_params", "headers", "body",
        "expected_status", "expected_response", "run_flag",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"TestCases sheet is missing required columns: {missing}")

    test_cases = []
    for _, row in df.iterrows():
        test_id = str(row["test_id"]).strip()

        case = {
            "test_id": test_id,
            "endpoint_name": str(row["endpoint_name"]).strip(),
            "method": str(row["method"]).strip().upper(),
            "url_path": str(row["url_path"]).strip(),
            "path_params": _safe_json_loads(row["path_params"], "path_params", test_id),
            "query_params": _safe_json_loads(row["query_params"], "query_params", test_id),
            "headers": _safe_json_loads(row["headers"], "headers", test_id),
            "body": _safe_json_loads(row["body"], "body", test_id),
            "expected_status": int(float(row["expected_status"])) if not pd.isna(row["expected_status"]) else None,
            "expected_response": _safe_json_loads(row["expected_response"], "expected_response", test_id),
            "run_flag": str(row.get("run_flag", "Y")).strip().upper(),
            "depends_on": str(row.get("depends_on", "")).strip() if "depends_on" in df.columns else "",
        }
        test_cases.append(case)

    return test_cases