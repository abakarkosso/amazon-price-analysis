"""
Service Layer

Business logic for scraping and data management.
"""

import os
from typing import Dict, Generator, List, Optional

from src.db import Database
from src.oxylabs_client import scrape_multiple_products, scrape_product_details, search_competitors


def _limit(name: str, default: int) -> int:
    """Scraping limits are settings because every Oxylabs request is billed."""
    try:
        return max(1, int(os.getenv(name, default)))
    except ValueError:
        return default


def scrape_and_store_product(asin: str, geo_location: str, domain: str, db: Optional[Database] = None) -> Dict:
    data = scrape_product_details(asin, geo_location, domain)
    (db or Database()).insert_product(data)
    return data


def fetch_and_store_competitors(parent_asin: str, domain: str, geo_location: str, pages: Optional[int] = None,
                                db: Optional[Database] = None) -> Generator[Dict, None, List[Dict]]:
    """
    Finds competitors for a given product.

    1. Gets the parent product's category.
    2. Searches Amazon for that category.
    3. Scrapes details for the top results.

    The search and the scrapes both use the market the parent was scraped from, so a .ca
    product is compared with .ca competitors whatever the form currently shows.
    """
    db = db or Database()
    parent = db.get_product(parent_asin)
    if not parent:
        return []

    search_domain = parent.get("amazon_domain", domain)
    search_geo = parent.get("geo_location", geo_location)
    pages = pages or _limit("SEARCH_PAGES", 2)
    max_competitors = _limit("MAX_COMPETITORS", 20)

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
            query_title=parent.get("title") or parent_asin,
            domain=search_domain,
            categories=[category],
            pages=pages,
            geo_location=search_geo,
        )
        all_results.extend(search_results)

    # dict.fromkeys keeps search order (the best matches first) while removing duplicates.
    competitor_asins = list(dict.fromkeys(
        r.get("asin") for r in all_results
        if r.get("asin") and r.get("asin") != parent_asin and r.get("title")
    ))[:max_competitors]

    yield {"status": "info", "message": f"Found {len(competitor_asins)} potential competitors. Scraping details..."}

    stored_comps = []
    for update in scrape_multiple_products(competitor_asins, search_geo, search_domain):
        if update["status"] == "success":
            comp = update["product"]
            comp["parent_asin"] = parent_asin
            db.insert_product(comp)
            stored_comps.append(comp)
            yield {"status": "progress", "current": len(stored_comps), "total": len(competitor_asins),
                   "message": f"Found: {comp.get('title')}"}
        elif update["status"] == "processing":
            yield {"status": "progress", "current": update["current"], "total": update["total"],
                   "message": f"Processing {update['asin']}..."}
        elif update["status"] == "error":
            yield {"status": "warning", "message": f"Failed to scrape {update['asin']}: {update['message']}"}

    return stored_comps
