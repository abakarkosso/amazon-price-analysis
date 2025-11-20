import pytest
import os
from src.db import Database
from tinydb import TinyDB

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_data.json")

@pytest.fixture
def db(db_path):
    return Database(db_path)

def test_insert_product(db):
    product = {"asin": "123", "title": "Test Product"}
    doc_id = db.insert_product(product)
    assert doc_id is not None
    assert db.get_product("123")["title"] == "Test Product"

def test_get_product(db):
    product = {"asin": "123", "title": "Test Product"}
    db.insert_product(product)
    retrieved = db.get_product("123")
    assert retrieved is not None
    assert retrieved["asin"] == "123"
    assert db.get_product("999") is None

def test_get_all_products(db):
    db.insert_product({"asin": "1", "title": "P1"})
    db.insert_product({"asin": "2", "title": "P2"})
    all_products = db.get_all_products()
    assert len(all_products) == 2

def test_search_products(db):
    db.insert_product({"asin": "1", "parent_asin": "A"})
    db.insert_product({"asin": "2", "parent_asin": "A"})
    db.insert_product({"asin": "3", "parent_asin": "B"})
    
    results = db.search_products({"parent_asin": "A"})
    assert len(results) == 2
    assert all(r["parent_asin"] == "A" for r in results)
