import pytest
from src.oxylabs_client import clean_product_name, normalize_product, extract_content

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
