import pytest

from src.oxylabs_client import clean_product_name, extract_content, normalize_product


def test_clean_product_name():
    assert clean_product_name("Product Name - Extra Info") == "Product Name"
    assert clean_product_name("Product Name | Brand") == "Product Name"
    assert clean_product_name("Clean Name") == "Clean Name"

def test_extract_content_nested():
    payload = {
        "results": [
            {
                "content": {"title": "Test"}
            }
        ]
    }
    assert extract_content(payload) == {"title": "Test"}

def test_extract_content_direct():
    payload = {"content": {"title": "Test"}}
    assert extract_content(payload) == {"title": "Test"}

def test_normalize_product():
    raw = {
        "asin": "123",
        "title": "Test",
        "price": 10.99,
        "category_path": ["Cat1", "Cat2"]
    }
    normalized = normalize_product(raw)
    assert normalized["asin"] == "123"
    assert normalized["title"] == "Test"
    assert normalized["price"] == 10.99
    assert normalized["category_path"] == ["Cat1", "Cat2"]
    assert "images" in normalized


def test_clean_product_name_keeps_hyphenated_words():
    assert clean_product_name("TP-Link Wi-Fi 6 Router - AX1800 Dual Band") == "TP-Link Wi-Fi 6 Router"
    assert clean_product_name("USB-C Cable | 2 Pack") == "USB-C Cable"


class FakeResponse:
    def __init__(self, status, body=None):
        self.status_code = status
        self._body = body or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"HTTP {self.status_code}")


def test_post_query_sets_a_timeout_and_retries_transient_errors(monkeypatch):
    import src.oxylabs_client as client
    monkeypatch.setenv("OXYLABS_USERNAME", "u")
    monkeypatch.setenv("OXYLABS_PASSWORD", "p")
    monkeypatch.setattr(client.time, "sleep", lambda s: None)
    calls = []
    replies = [FakeResponse(429), FakeResponse(503), FakeResponse(200, {"ok": True})]

    def fake_post(url, **kwargs):
        calls.append(kwargs)
        return replies.pop(0)

    monkeypatch.setattr(client.requests, "post", fake_post)
    assert client.post_query({"q": 1}) == {"ok": True}
    assert len(calls) == 3
    assert all(c.get("timeout") for c in calls)


def test_post_query_does_not_retry_client_errors(monkeypatch):
    import requests

    import src.oxylabs_client as client
    monkeypatch.setenv("OXYLABS_USERNAME", "u")
    monkeypatch.setenv("OXYLABS_PASSWORD", "p")
    calls = []
    monkeypatch.setattr(client.requests, "post", lambda url, **kw: calls.append(kw) or FakeResponse(401))
    with pytest.raises(requests.HTTPError):
        client.post_query({"q": 1})
    assert len(calls) == 1
