from types import SimpleNamespace

from core import api_client


def test_send_request_retries_on_retryable_status(monkeypatch):
    calls = []
    responses = [
        SimpleNamespace(status_code=500, text="server error"),
        SimpleNamespace(status_code=200, text="ok"),
    ]

    def fake_request(**kwargs):
        calls.append(kwargs)
        return responses.pop(0)

    monkeypatch.setattr(api_client.requests, "request", fake_request)

    case = {
        "method": "GET",
        "url_path": "/ping",
        "path_params": {},
        "query_params": {},
        "headers": {"Content-Type": "application/json"},
        "body": {},
    }
    config = {
        "base_url": "https://example.test",
        "max_retries": 2,
        "retry_delay_seconds": 0,
    }

    response = api_client.send_request(case, config, context={})

    assert response.status_code == 200
    assert len(calls) == 2
