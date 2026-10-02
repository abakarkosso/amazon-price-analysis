from src.db import Database
from src.llm import format_competitors


def test_format_competitors_tolerates_missing_fields(tmp_path):
    db = Database(str(tmp_path / "d.json"))
    db.insert_product({"asin": "C1", "parent_asin": "P"})  # scrape returned no title, price or rating
    assert format_competitors(db, "P") == [
        {"asin": "C1", "title": None, "price": None, "currency": None, "rating": None, "amazon_domain": None}
    ]
