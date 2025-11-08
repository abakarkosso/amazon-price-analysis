"""
Amazon Price Competitor Analysis - Main Application

A Streamlit web application for analyzing Amazon product prices and competitors
using web scraping and AI-powered insights.
"""

import streamlit as st
from typing import Dict, Tuple
from src.services import scrape_and_store_product, fetch_and_store_competitors
from src.db import Database
from src.llm import analyze_competitors


def render_header() -> None:
    """Render the application header with title and caption."""
    st.title("Amazon Competitor Analysis")
    st.caption("Enter your ASIN to get product insights.")


def render_inputs() -> Tuple[str, str, str]:
    """
    Render input fields for ASIN, geographic location, and Amazon domain.
    
    Returns:
        Tuple of (asin, geo_location, domain) strings
    """
    asin = st.text_input("ASIN", placeholder="e.g., B0CX23VSAS")
    geo = st.text_input("Zip/Postal Code", placeholder="e.g., 83980")
    domain = st.selectbox("Domain", [
        "com", "ca", "co.uk", "de", "fr", "it", "ae"
    ])
    return asin.strip(), geo.strip(), domain


def render_product_card(product: Dict) -> None:
    """
    Render a product card with product details and analysis button.
    
    Args:
        product: Dictionary containing product information (asin, title, price, etc.)
    """
    with st.container(border=True):
        cols = st.columns([1, 2])

        try:
            images = product.get("images", [])
            if images and len(images) > 0:
                cols[0].image(images[0], width=200)
            else:
                cols[0].write("No image found.")
        except Exception as e:
            cols[0].write("Error loading image")
            st.error(f"Failed to load product image: {str(e)}")

        with cols[1]:
            st.subheader(product.get("title") or product["asin"])
            info_cols = st.columns(3)
            currency = product.get("currency", "")
            price = product.get("price", "-")
            info_cols[0].metric("Price", f"{currency} {price}" if currency else price)
            info_cols[1].write(f"Brand: {product.get('brand', '-')}")
            info_cols[2].write(f"Product: {product.get('product', '-')}")

            domain_info = f"amazon.{product.get('amazon_domain', 'com')}"
            geo_info = product.get("geo_location", "-")
            st.caption(f"Domain: {domain_info} | Geo Location: {geo_info}")

            st.write(product.get("url", ""))
            if st.button("Start analyzing competitors", key=f"analyze_{product['asin']}"):
                st.session_state["analyzing_asin"] = product["asin"]

def main() -> None:
    """
    Main application entry point.
    
    Sets up the Streamlit page configuration and renders the main application UI,
    including product scraping, competitor discovery, and AI analysis features.
    """
    st.set_page_config(page_title="Amazon Competitor Analysis", layout="wide")
    render_header()
    asin, geo, domain = render_inputs()

    if st.button("Scrape Product") and asin:
        try:
            with st.spinner("Scraping product..."):
                scrape_and_store_product(asin, geo, domain)
            st.success("Product scraped successfully!")
        except Exception as e:
            st.error(f"Failed to scrape product: {str(e)}")
            st.info("Please check your ASIN, credentials, and network connection.")

    db = Database()
    products = db.get_all_products()
    if products:
        st.divider()
        st.subheader("Product Scraped")

        items_per_page = 10
        total_pages = (len(products) + items_per_page - 1) // items_per_page

        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1) - 1

        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(products))

        st.write(f"Showing {start_idx + 1} - {end_idx} of {len(products)} products")

        for p in products[start_idx:end_idx]:
            render_product_card(p)

    selected_asin = st.session_state.get("analyzing_asin")
    if selected_asin:
        st.divider()
        st.subheader(f"Competitor analysis for {selected_asin}")

        db = Database()
        existing_comps = db.search_products({"parent_asin": selected_asin})

        if not existing_comps:
            try:
                with st.spinner("Searching..."):
                    comps = fetch_and_store_competitors(selected_asin, domain, geo)
                st.success(f"Found {len(comps)} competitors!")
            except Exception as e:
                st.error(f"Failed to fetch competitors: {str(e)}")
                comps = []
        else:
            st.info(f"Found {len(existing_comps)} existing competitors in the database.")
            comps = existing_comps

        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Refresh Competitors"):
                try:
                    with st.spinner("Refreshing..."):
                        comps = fetch_and_store_competitors(selected_asin, domain, geo)
                    st.success(f"Found {len(comps)} competitors!")
                except Exception as e:
                    st.error(f"Failed to refresh competitors: {str(e)}")

        with col1:
            if st.button("Analyze with LLM", type="primary"):
                try:
                    with st.spinner("Running LLM analysis..."):
                        analysis = analyze_competitors(selected_asin)
                        st.markdown(analysis)
                except Exception as e:
                    st.error(f"Failed to analyze competitors: {str(e)}")
                    st.info("Please check your OpenAI API key and ensure competitors are loaded.")


if __name__ == "__main__":
    main()