"""
Service layer for business logic operations.

Handles product scraping, competitor discovery, and data storage coordination.
"""

import streamlit as st
from typing import Dict, List
from src.db import Database
from src.oxylabs_client import scrape_product_details, search_competitors, scrape_multiple_products


def scrape_and_store_product(asin: str, geo_location: str, domain: str) -> Dict:
    """
    Scrape product details and store in database.
    
    Args:
        asin: Amazon Standard Identification Number
        geo_location: Geographic location (zip/postal code)
        domain: Amazon domain (com, ca, co.uk, etc.)
        
    Returns:
        Dictionary containing scraped product data
        
    Raises:
        Exception: If scraping fails or database operation fails
    """
    data = scrape_product_details(asin, geo_location, domain)
    db = Database()
    db.insert_product(data)
    return data


def fetch_and_store_competitors(parent_asin: str, domain: str, geo_location: str, pages: int = 2) -> List[Dict]:
    """
    Fetch competitor products and store them in the database.
    
    Searches for competitors based on the parent product's categories and title,
    then scrapes detailed information for each competitor.
    
    Args:
        parent_asin: ASIN of the parent product
        domain: Amazon domain to search
        geo_location: Geographic location for search
        pages: Number of pages to search per category (default: 2)
        
    Returns:
        List of competitor product dictionaries
        
    Raises:
        Exception: If parent product not found or scraping fails
    """
    db = Database()
    parent = db.get_product(parent_asin)
    if not parent:
        return []

    search_domain = parent.get("amazon_domain", domain)
    search_geo = parent.get("geo_location", geo_location)
    st.write(f"Using domain: {search_domain} | Geo Location: {search_geo}")

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

    product_details = scrape_multiple_products(competitor_asins[:20], geo_location, domain)

    stored_comps = []
    for comp in product_details:
        comp["parent_asin"] = parent_asin
        db.insert_product(comp)
        stored_comps.append(comp)

    st.write("Competitor Summary")
    for comp in stored_comps:
        price = comp.get("price", "-")
        currency = comp.get("currency", "-")
        if isinstance(price, (int, float)):
            price_str = f"{currency} {price:,.2f}" if currency else f"{price:,.2f}"
        else:
            price_str = str(price)

        st.write(f"- {comp.get('title')} - {price_str}")
    st.write("---")

    return stored_comps