"""
Amazon Price Competitor Analysis - Main Application

A Streamlit web application for analyzing Amazon product prices and competitors
using web scraping and AI-powered insights.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Tuple, List
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
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        asin = st.text_input("ASIN", placeholder="e.g., B0CX23VSAS")
    with col2:
        geo = st.text_input("Zip/Postal Code", placeholder="e.g., 83980")
    with col3:
        domain = st.selectbox("Domain", [
            "com", "ca", "co.uk", "de", "fr", "it", "ae"
        ])
    return asin.strip(), geo.strip(), domain


def render_dashboard(products: List[Dict]) -> None:
    """
    Render a dashboard with aggregate statistics and charts.
    
    Args:
        products: List of all product dictionaries
    """
    if not products:
        return

    st.subheader("Dashboard")
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(products)
    
    # Clean price column
    def clean_price(p):
        if isinstance(p, (int, float)):
            return float(p)
        return 0.0
        
    df['price_val'] = df['price'].apply(clean_price)
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Products", len(df))
    col2.metric("Avg Price", f"${df['price_val'].mean():.2f}")
    col3.metric("Unique Brands", df['brand'].nunique())
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption("Price Distribution")
        st.bar_chart(df.set_index('title')['price_val'])
        
    with col2:
        if 'rating' in df.columns:
            st.caption("Rating Distribution")
            # Ensure rating is numeric
            df['rating_val'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
            st.scatter_chart(df, x='price_val', y='rating_val')


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
    st.set_page_config(
        page_title="Amazon Competitor Analysis", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar for navigation or global actions
    with st.sidebar:
        st.title("Navigation")
        st.info("Use the main area to search and analyze products.")
        
        db = Database()
        all_products = db.get_all_products()
        if all_products:
            df = pd.DataFrame(all_products)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Data (CSV)",
                csv,
                "amazon_products.csv",
                "text/csv",
                key='download-csv'
            )

    render_header()
    asin, geo, domain = render_inputs()

    if st.button("Scrape Product", type="primary") and asin:
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
        render_dashboard(products)
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
        
        comps = []
        if not existing_comps:
            try:
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                generator = fetch_and_store_competitors(selected_asin, domain, geo)
                
                # Consume generator
                while True:
                    try:
                        update = next(generator)
                        if update["status"] == "info":
                            progress_text.write(update["message"])
                        elif update["status"] == "progress":
                            progress_text.write(update["message"])
                            if update.get("total"):
                                progress_bar.progress(update["current"] / update["total"])
                        elif update["status"] == "warning":
                            st.warning(update["message"])
                    except StopIteration as e:
                        comps = e.value
                        break
                        
                progress_text.empty()
                progress_bar.empty()
                st.success(f"Found {len(comps)} competitors!")
            except Exception as e:
                st.error(f"Failed to fetch competitors: {str(e)}")
                comps = []
        else:
            st.info(f"Found {len(existing_comps)} existing competitors in the database.")
            comps = existing_comps

        if comps:
            st.write("Competitor Summary")
            
            # Competitor Table
            comp_df = pd.DataFrame(comps)
            if not comp_df.empty:
                display_cols = ['title', 'price', 'rating', 'brand']
                # Filter columns that exist
                display_cols = [c for c in display_cols if c in comp_df.columns]
                st.dataframe(comp_df[display_cols], use_container_width=True)
            
            st.write("---")

        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Refresh Competitors"):
                try:
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                    
                    generator = fetch_and_store_competitors(selected_asin, domain, geo)
                    
                    # Consume generator
                    while True:
                        try:
                            update = next(generator)
                            if update["status"] == "info":
                                progress_text.write(update["message"])
                            elif update["status"] == "progress":
                                progress_text.write(update["message"])
                                if update.get("total"):
                                    progress_bar.progress(update["current"] / update["total"])
                            elif update["status"] == "warning":
                                st.warning(update["message"])
                        except StopIteration as e:
                            comps = e.value
                            break
                            
                    progress_text.empty()
                    progress_bar.empty()
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