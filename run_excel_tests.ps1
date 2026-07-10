param(
    [string]$ExcelPath = "C:\Users\ADMIN\Downloads\test_data3.xlsx"
)

$env:TEST_DATA_PATH = $ExcelPath
pytest -q tests/test_api_from_excel.py
