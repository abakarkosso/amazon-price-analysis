"""
Database module for managing product data storage.

Uses TinyDB for lightweight JSON-based database operations.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from tinydb import Query, TinyDB


class Database:
    """Database class for managing product data using TinyDB."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize the database connection.

        Args:
            db_path: Path to the JSON database file. Defaults to $DB_PATH or data.json.
        """
        db_path = db_path or os.getenv("DB_PATH", "data.json")
        dirname = os.path.dirname(db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        self.db = TinyDB(db_path)
        self.products = self.db.table("products")
        self.prices = self.db.table("price_history")

    def insert_product(self, product_data: Dict) -> int:
        """
        Store a product, replacing any earlier copy of it.

        A product is identified by its ASIN plus the product it was found as a competitor of
        (if any), so re-scraping updates it instead of adding a duplicate. Every scrape that
        returns a price is also appended to the price history.

        Returns:
            Document ID of the stored product
        """
        now = datetime.now().isoformat()
        product_data["created_at"] = now
        Product = Query()
        key = (Product.asin == product_data.get("asin")) & (
            Product.parent_asin == product_data["parent_asin"]
            if product_data.get("parent_asin")
            else ~Product.parent_asin.exists()
        )
        if product_data.get("price") is not None:
            self.prices.insert({
                "asin": product_data.get("asin"),
                "price": product_data["price"],
                "currency": product_data.get("currency"),
                "scraped_at": now,
            })
        return self.products.upsert(product_data, key)[0]

    def get_product(self, asin: str) -> Optional[Dict]:
        """
        Retrieve a tracked product (not a competitor copy) by ASIN, falling back to any copy.

        Returns:
            Product dictionary if found, None otherwise
        """
        Product = Query()
        return (self.products.get((Product.asin == asin) & ~Product.parent_asin.exists())
                or self.products.get(Product.asin == asin))

    def get_all_products(self) -> List[Dict]:
        """Retrieve every stored product, tracked products and competitors alike."""
        return self.products.all()

    def tracked_products(self) -> List[Dict]:
        """Products the user scraped directly, without the competitors found for them."""
        Product = Query()
        return self.products.search(~Product.parent_asin.exists())

    def price_history(self, asin: str) -> List[Dict]:
        """Every recorded price for a product, oldest first."""
        Price = Query()
        return sorted(self.prices.search(Price.asin == asin), key=lambda p: p["scraped_at"])

    def search_products(self, search_criteria: Dict) -> List[Dict]:
        """
        Search for products matching the given criteria.

        Args:
            search_criteria: Dictionary of search criteria (key-value pairs)

        Returns:
            List of matching product dictionaries
        """
        Product = Query()
        query = None
        for key, value in search_criteria.items():
            if query is None:
                query = (Product[key] == value)
            else:
                query &= (Product[key] == value)

        return self.products.search(query) if query else []
