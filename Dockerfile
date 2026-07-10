FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["pytest", "-q", "tests/test_api_client.py", "tests/test_api_from_excel.py", "-s"]
