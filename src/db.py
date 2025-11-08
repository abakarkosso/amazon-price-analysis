"""
Database module for managing product data storage.

Uses TinyDB for lightweight JSON-based database operations.
"""

from tinydb import TinyDB, Query
from datetime import datetime
from typing import Dict, List, Optional
import os


class Database:
    """Database class for managing product data using TinyDB."""
    
    def __init__(self, db_path: str = "data.json") -> None:
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the JSON database file
        """
        dirname = os.path.dirname(db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        self.db = TinyDB(db_path)
        self.products = self.db.table("products")

    def insert_product(self, product_data: Dict) -> int:
        """
        Insert a product into the database.
        
        Args:
            product_data: Dictionary containing product information
            
        Returns:
            Document ID of the inserted product
        """
        product_data["created_at"] = datetime.now().isoformat()
        return self.products.insert(product_data)

    def get_product(self, asin: str) -> Optional[Dict]:
        """
        Retrieve a product by ASIN.
        
        Args:
            asin: Amazon Standard Identification Number
            
        Returns:
            Product dictionary if found, None otherwise
        """
        Product = Query()
        return self.products.get(Product.asin == asin)

    def get_all_products(self) -> List[Dict]:
        """
        Retrieve all products from the database.
        
        Returns:
            List of all product dictionaries
        """
        return self.products.all()

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