import pytest

from src.db import Database


@pytest.fixture
def db(tmp_path):
    return Database(str(tmp_path / "test_data.json"))


def test_insert_product(db):
    doc_id = db.insert_product({"asin": "123", "title": "Test Product"})
    assert doc_id is not None
    assert db.get_product("123")["title"] == "Test Product"


def test_get_product(db):
    db.insert_product({"asin": "123", "title": "Test Product"})
    assert db.get_product("123")["asin"] == "123"
    assert db.get_product("999") is None


def test_get_all_products(db):
    db.insert_product({"asin": "1", "title": "P1"})
    db.insert_product({"asin": "2", "title": "P2"})
    assert len(db.get_all_products()) == 2


def test_search_products(db):
    db.insert_product({"asin": "1", "parent_asin": "A"})
    db.insert_product({"asin": "2", "parent_asin": "A"})
    db.insert_product({"asin": "3", "parent_asin": "B"})
    results = db.search_products({"parent_asin": "A"})
    assert len(results) == 2
    assert all(r["parent_asin"] == "A" for r in results)


def test_rescraping_updates_instead_of_duplicating(db):
    db.insert_product({"asin": "123", "title": "Old title", "price": 20.0})
    db.insert_product({"asin": "123", "title": "New title", "price": 18.0})
    assert len(db.get_all_products()) == 1
    assert db.get_product("123")["title"] == "New title"


def test_same_competitor_under_two_parents_is_kept_once_per_parent(db):
    db.insert_product({"asin": "C1", "parent_asin": "A"})
    db.insert_product({"asin": "C1", "parent_asin": "A"})
    db.insert_product({"asin": "C1", "parent_asin": "B"})
    assert len(db.search_products({"parent_asin": "A"})) == 1
    assert len(db.search_products({"parent_asin": "B"})) == 1


def test_every_scrape_with_a_price_is_kept_as_history(db):
    db.insert_product({"asin": "123", "price": 20.0, "currency": "USD"})
    db.insert_product({"asin": "123", "price": 18.5, "currency": "USD"})
    db.insert_product({"asin": "123", "price": None})
    history = db.price_history("123")
    assert [h["price"] for h in history] == [20.0, 18.5]
    assert all(h["currency"] == "USD" and h["scraped_at"] for h in history)


def test_tracked_products_excludes_competitors(db):
    db.insert_product({"asin": "P"})
    db.insert_product({"asin": "C", "parent_asin": "P"})
    assert [p["asin"] for p in db.tracked_products()] == ["P"]
