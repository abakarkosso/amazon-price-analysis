"""
Service Layer

Business logic for scraping and data management.
"""

from typing import Dict, List, Generator, Any
from src.db import Database
from src.oxylabs_client import scrape_product_details, search_competitors, scrape_multiple_products


def scrape_and_store_product(asin: str, geo_location: str, domain: str) -> Dict:
    data = scrape_product_details(asin, geo_location, domain)
    db = Database()
    db.insert_product(data)
    return data


def fetch_and_store_competitors(parent_asin: str, domain: str, geo_location: str, pages: int = 2) -> Generator[Dict, None, List[Dict]]:
    """
    Finds competitors for a given product.
    
    1. Gets the parent product's category.
    2. Searches Amazon for that category.
    3. Scrapes details for the top results.
    """
    db = Database()
    parent = db.get_product(parent_asin)
    if not parent:
        return []

    search_domain = parent.get("amazon_domain", domain)
    search_geo = parent.get("geo_location", geo_location)
    
    yield {"status": "info", "message": f"Using domain: {search_domain} | Geo Location: {search_geo}"}

    search_categories = []
    if parent.get("categories"):
        search_categories.extend(str(cat) for cat in parent["categories"] if cat)
    if parent.get("category_path"):
        search_categories.extend(str(cat) for cat in parent["category_path"] if cat)

    search_categories = list(set(
        cat.strip()
        for cat in search_categories
        if cat and isinstance(cat, str) and cat.strip()
    ))

    all_results = []
    yield {"status": "info", "message": "Searching for competitors..."}
    
    for category in search_categories[:3]:
        search_results = search_competitors(
            query_title=parent["title"],
            domain=search_domain,
            categories=[category],
            pages=pages,
            geo_location=search_geo,
        )
        all_results.extend(search_results)

    competitor_asins = list(set(
        r.get("asin") for r in all_results
        if r.get("asin") and r.get("asin") != parent_asin and r.get("title")
    ))
    
    yield {"status": "info", "message": f"Found {len(competitor_asins)} potential competitors. Scraping details..."}

    stored_comps = []
    for update in scrape_multiple_products(competitor_asins[:20], geo_location, domain):
        if update["status"] == "success":
            comp = update["product"]
            comp["parent_asin"] = parent_asin
            db.insert_product(comp)
            stored_comps.append(comp)
            yield {"status": "progress", "current": len(stored_comps), "total": min(len(competitor_asins), 20), "message": f"Found: {comp.get('title')}"}
        elif update["status"] == "processing":
            yield {"status": "progress", "current": update["current"], "total": update["total"], "message": f"Processing {update['asin']}..."}
        elif update["status"] == "error":
            yield {"status": "warning", "message": f"Failed to scrape {update['asin']}: {update['message']}"}

    return stored_comps