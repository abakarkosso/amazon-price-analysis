"""
Oxylabs API client for Amazon product scraping and search.

Handles all interactions with the Oxylabs API for scraping Amazon products
and performing search queries.
"""

import json
import os
import time
import requests
import streamlit as st
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

OXYLABS_BASE_URL = "https://realtime.oxylabs.io/v1/queries"


def extract_content(payload: Dict) -> Dict:
    """
    Extract content from Oxylabs API response payload.
    
    Args:
        payload: Raw API response dictionary
        
    Returns:
        Extracted content dictionary
    """
    if isinstance(payload, dict):
        if "results" in payload and isinstance(payload["results"], list) and payload["results"]:
            first = payload["results"][0]
            if isinstance(first, dict) and "content" in first:
                return first["content"] or {}
        if "content" in payload:
            return payload.get("content", {})

    return payload


def post_query(payload: Dict) -> Dict:
    """
    Send a POST request to the Oxylabs API.
    
    Args:
        payload: Request payload dictionary
        
    Returns:
        API response as dictionary
        
    Raises:
        requests.HTTPError: If the API request fails
        ValueError: If credentials are missing
    """
    username = os.getenv("OXYLABS_USERNAME")
    password = os.getenv("OXYLABS_PASSWORD")
    
    if not username or not password:
        raise ValueError("Oxylabs credentials not found. Please check your .env file.")

    response = requests.post(OXYLABS_BASE_URL, auth=(username, password), json=payload)
    response.raise_for_status()
    response_json = response.json()

    return response_json


def normalize_product(content: Dict) -> Dict:
    """
    Normalize product data from Oxylabs API response.
    
    Args:
        content: Raw product content from API
        
    Returns:
        Normalized product dictionary with standardized fields
    """
    category_path = []
    if content.get("category_path"):
        category_path = [cat.strip() for cat in content["category_path"] if cat]

    return {
        "asin": content.get("asin"),
        "url": content.get("url"),
        "brand": content.get("brand"),
        "price": content.get("price"),
        "stock": content.get("stock"),
        "title": content.get("title"),
        "rating": content.get("rating"),
        "images": content.get("images", []),
        "categories": content.get("category", []) or content.get("categories", []),
        "category_path": category_path,
        "currency": content.get("currency"),
        "buybox": content.get("buybox", []),
        "product_overview": content.get("product_overview", []),
    }


def scrape_product_details(asin: str, geo_location: str, domain: str) -> Dict:
    """
    Scrape detailed product information from Amazon.
    
    Args:
        asin: Amazon Standard Identification Number
        geo_location: Geographic location (zip/postal code)
        domain: Amazon domain (com, ca, co.uk, etc.)
        
    Returns:
        Dictionary containing normalized product details
        
    Raises:
        Exception: If scraping fails or API returns invalid data
    """
    payload = {
        "source": "amazon_product",
        "query": asin,
        "geo_location": geo_location,
        "domain": domain,
        "parse": True
    }
    raw = post_query(payload)
    content = extract_content(raw)
    normalized = normalize_product(content)
    if not normalized.get("asin"):
        normalized["asin"] = asin

    normalized["amazon_domain"] = domain
    normalized["geo_location"] = geo_location
    return normalized


def clean_product_name(title: str) -> str:
    """
    Clean product title by removing common separators and extra text.
    
    Args:
        title: Raw product title string
        
    Returns:
        Cleaned product title
    """
    if "-" in title:
        title = title.split("-")[0]
    if "|" in title:
        title = title.split("|")[0]
    return title.strip()


def extract_search_results(content: Dict) -> List[Dict]:
    """
    Extract search results from Oxylabs API response.
    
    Args:
        content: API response content dictionary
        
    Returns:
        List of search result items
    """
    items = []
    if not isinstance(content, dict):
        return items

    if "results" in content:
        results = content["results"]
        if isinstance(results, dict):
            if "organic" in results:
                items.extend(results["organic"])
            if "paid" in results:
                items.extend(results["paid"])
    elif "products" in content and isinstance(content["products"], list):
        items.extend(content["products"])

    return items


def normalize_search_result(item: Dict) -> Optional[Dict]:
    """
    Normalize a single search result item.
    
    Args:
        item: Raw search result item dictionary
        
    Returns:
        Normalized search result dictionary, or None if invalid
    """
    asin = item.get("asin") or item.get("product_asin")
    title = item.get("title")

    if not (asin or title):
        return None

    return {
        "asin": asin,
        "title": title,
        "category": item.get("category"),
        "price": item.get("price"),
        "rating": item.get("rating")
    }


def search_competitors(query_title: str, domain: str, categories: List[str], pages: int = 1, geo_location: str = "") -> List[Dict]:
    """
    Search for competitor products on Amazon.
    
    Uses multiple sorting strategies (featured, price_asc, price_desc, avg_rating)
    to find relevant competitors across multiple pages.
    
    Args:
        query_title: Product title to search for
        domain: Amazon domain to search
        categories: List of category filters
        pages: Number of pages to search per strategy (default: 1)
        geo_location: Geographic location for search
        
    Returns:
        List of competitor search result dictionaries
    """
    st.write("🔎 Searching for competitors")

    search_title = clean_product_name(query_title)
    results = []
    seen_asins = set()

    strategies = ["featured", "price_asc", "price_desc", "avg_rating"]

    for sort_by in strategies:
        for page in range(1, max(1, pages) + 1):
            payload = {
                "source": "amazon_search",
                "query": search_title,
                "parse": True,
                "domain": domain,
                "page": page,
                "sort_by": sort_by,
                "geo_location": geo_location
            }

            if categories and categories[0]:
                payload["refinements"] = {"category": categories[0]}

            content = extract_content(post_query(payload))
            items = extract_search_results(content)

            for item in items:
                result = normalize_search_result(item)
                if result and result["asin"] not in seen_asins:
                    seen_asins.add(result["asin"])
                    results.append(result)

            time.sleep(0.1)

    st.write(f"✅ Found {len(results)} competitors")
    return results


def scrape_multiple_products(asins: List[str], geo_location: str, domain: str) -> List[Dict]:
    """
    Scrape detailed information for multiple products.
    
    Shows progress bar and handles errors gracefully for individual products.
    
    Args:
        asins: List of ASINs to scrape
        geo_location: Geographic location for scraping
        domain: Amazon domain to scrape from
        
    Returns:
        List of product dictionaries (may be shorter than input if some fail)
    """
    st.write("🔎 Scraping details")
    products = []

    progress_text = st.empty()
    progress_bar = st.progress(0)
    total = len(asins)

    for idx, a in enumerate(asins, 1):
        try:
            progress_text.write(f"Processing competitor {idx}/{total}: {a}")
            progress_bar.progress(idx / total)

            product = scrape_product_details(a, geo_location, domain)
            products.append(product)
            progress_text.write(f"✅ Found: {product.get('title', a)}")
        except Exception as e:
            st.warning(f"Failed to scrape {a}: {str(e)}")
            continue
        time.sleep(0.1)

    progress_text.empty()
    progress_bar.empty()

    st.write(f"✅ Successfully scraped {len(products)} out of {total} competitors")
    return products