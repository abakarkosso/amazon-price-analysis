"""
Amazon Price Competitor Analysis - Main Application

A Streamlit web application for analyzing Amazon product prices and competitors
using web scraping and AI-powered insights.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Generator, List, Tuple

import pandas as pd
import streamlit as st

from src.analytics import price_change, price_position, price_summary
from src.db import Database
from src.llm import analyze_competitors
from src.services import fetch_and_store_competitors, parse_asins, scrape_and_store_product

DEMO_DIR = Path(__file__).parent / "demo"

# Without scraping credentials the app runs on bundled sample data, so anyone can try it.
DEMO_MODE = not (os.getenv("OXYLABS_USERNAME") and os.getenv("OXYLABS_PASSWORD"))
if DEMO_MODE and not os.getenv("DB_PATH"):
    # Work on a copy so the bundled sample file is never modified.
    demo_copy = Path(tempfile.gettempdir()) / "amazon-price-analysis-demo.json"
    shutil.copy(DEMO_DIR / "demo_data.json", demo_copy)
    os.environ["DB_PATH"] = str(demo_copy)


def render_header() -> None:
    """Render the application header with title and caption."""
    st.title("Amazon Competitor Analysis")
    st.caption("Enter your ASIN to get product insights.")
    if DEMO_MODE:
        st.info("Demo mode: showing bundled sample data. Add Oxylabs credentials to `.env` to scrape real "
                "products (see the README).")


def render_inputs() -> Tuple[str, str, str]:
    """
    Render input fields for ASIN, geographic location, and Amazon domain.

    Returns:
        Tuple of (asin, geo_location, domain) strings
    """
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        asin = st.text_input("ASIN (or several, comma-separated)", placeholder="e.g., B0CX23VSAS, B0ABC12345")
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
    df = pd.DataFrame(products)
    df["price_val"] = pd.to_numeric(df.get("price"), errors="coerce")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Products", len(df))
    col3.metric("Unique Brands", df["brand"].nunique() if "brand" in df else 0)
    # One average per currency; products without a price are left out, not counted as zero.
    summary = price_summary(products)
    col2.metric("Avg Price", " / ".join(f"{s['currency']} {s['average']:.2f}" for s in summary) or "-")

    col1, col2 = st.columns(2)
    priced = df.dropna(subset=["price_val"])
    with col1:
        st.caption("Price Distribution")
        if not priced.empty:
            st.bar_chart(priced.set_index("asin")["price_val"], x_label="ASIN", y_label="Price")
    with col2:
        if "rating" in df.columns and not priced.empty:
            st.caption("Price vs Rating")
            chart = priced.assign(Rating=pd.to_numeric(priced["rating"], errors="coerce"), Price=priced["price_val"])
            st.scatter_chart(chart.dropna(subset=["Rating"]), x="Price", y="Rating")


def render_product_card(product: Dict, db: Database) -> None:
    """
    Render a product card with product details and analysis button.

    Args:
        product: Dictionary containing product information (asin, title, price, etc.)
    """
    with st.container(border=True):
        cols = st.columns([1, 2])

        images = product.get("images") or []
        if images:
            cols[0].image(images[0], width=200)
        else:
            cols[0].write("No image found.")

        with cols[1]:
            st.subheader(product.get("title") or product["asin"])
            info_cols = st.columns(3)
            currency = product.get("currency", "")
            price = product.get("price", "-")
            change = price_change(db.price_history(product["asin"]))
            info_cols[0].metric("Price", f"{currency} {price}" if currency else price,
                                delta=None if change is None else f"{change:+.1f}% since last check",
                                delta_color="off")
            info_cols[1].write(f"Brand: {product.get('brand', '-')}")
            info_cols[2].write(f"ASIN: {product['asin']}")

            domain_info = f"amazon.{product.get('amazon_domain', 'com')}"
            geo_info = product.get("geo_location", "-")
            st.caption(f"Domain: {domain_info} | Geo Location: {geo_info}")

            st.write(product.get("url", ""))
            if st.button("Start analyzing competitors", key=f"analyze_{product['asin']}"):
                st.session_state["analyzing_asin"] = product["asin"]


def run_with_progress(updates: Generator[Dict, None, List[Dict]]) -> List[Dict]:
    """Show a generator's progress updates and return its final value."""
    progress_text = st.empty()
    progress_bar = st.progress(0)
    try:
        while True:
            update = next(updates)
            if update["status"] in ("info", "progress"):
                progress_text.write(update["message"])
            if update["status"] == "progress" and update.get("total"):
                progress_bar.progress(min(1.0, update["current"] / update["total"]))
            elif update["status"] == "warning":
                st.warning(update["message"])
    except StopIteration as done:
        return done.value or []
    finally:
        progress_text.empty()
        progress_bar.empty()


def render_price_history(db: Database, asin: str) -> None:
    """Line chart of every recorded price for a product."""
    history = db.price_history(asin)
    if len(history) < 2:
        st.caption("Price history appears after the product has been scraped more than once.")
        return
    df = pd.DataFrame(history)
    df["scraped_at"] = pd.to_datetime(df["scraped_at"])
    st.caption(f"Price history ({history[-1].get('currency') or ''})")
    st.line_chart(df.set_index("scraped_at")["price"])


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
    db = Database()

    with st.sidebar:
        st.title("Navigation")
        st.info("Use the main area to search and analyze products.")
        all_products = db.get_all_products()
        if all_products:
            csv = pd.DataFrame(all_products).to_csv(index=False).encode("utf-8")
            st.download_button("Download Data (CSV)", csv, "amazon_products.csv", "text/csv", key="download-csv")

    render_header()
    asin, geo, domain = render_inputs()

    asins = parse_asins(asin)
    if st.button("Scrape Product", type="primary", disabled=DEMO_MODE) and asins:
        progress = st.progress(0)
        failed = []
        # One bad ASIN shouldn't stop the rest.
        for i, a in enumerate(asins, 1):
            try:
                with st.spinner(f"Scraping {a} ({i} of {len(asins)})..."):
                    scrape_and_store_product(a, geo, domain, db=db)
            except Exception as e:
                failed.append(a)
                st.error(f"Failed to scrape {a}: {str(e)}")
            progress.progress(i / len(asins))
        progress.empty()
        if len(failed) < len(asins):
            st.success(f"Scraped {len(asins) - len(failed)} of {len(asins)} products.")
        if failed:
            st.info("Please check those ASINs, your credentials, and your network connection.")

    # Cards are for products the user tracks; their competitors show up in the analysis below.
    products = db.tracked_products()
    if products:
        st.divider()
        render_dashboard(db.get_all_products())
        st.divider()
        st.subheader("Tracked Products")

        items_per_page = 10
        total_pages = (len(products) + items_per_page - 1) // items_per_page
        col1, col2, col3 = st.columns([2, 3, 2])
        with col2:
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1) - 1

        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(products))
        st.write(f"Showing {start_idx + 1} - {end_idx} of {len(products)} products")
        for p in products[start_idx:end_idx]:
            render_product_card(p, db)

    selected_asin = st.session_state.get("analyzing_asin")
    if not selected_asin:
        return

    st.divider()
    st.subheader(f"Competitor analysis for {selected_asin}")
    parent = db.get_product(selected_asin) or {"asin": selected_asin}
    comps = db.search_products({"parent_asin": selected_asin})

    if not comps and not DEMO_MODE:
        try:
            comps = run_with_progress(fetch_and_store_competitors(selected_asin, domain, geo, db=db))
            st.success(f"Found {len(comps)} competitors!")
        except Exception as e:
            st.error(f"Failed to fetch competitors: {str(e)}")
    elif comps:
        st.info(f"Found {len(comps)} existing competitors in the database.")

    render_price_history(db, selected_asin)

    if comps:
        position = price_position(parent, comps)
        if position["comparable"]:
            cols = st.columns(3)
            cols[0].metric("Cheaper competitors", f"{position['cheaper_competitors']} of {position['comparable']}")
            cols[1].metric("Competitor median", f"{parent.get('currency') or ''} {position['median']:.2f}")
            cols[2].metric("Gap to median", f"{position['gap_to_median_pct']:+.1f}%")

        tracked = {c["asin"]: c.get("title") or c["asin"] for c in comps if len(db.price_history(c["asin"])) >= 2}
        if tracked:
            chosen = st.selectbox("Competitor price history", list(tracked), format_func=lambda a: tracked[a])
            render_price_history(db, chosen)

        st.write("Competitor Summary")
        comp_df = pd.DataFrame(comps)
        display_cols = [c for c in ["title", "price", "currency", "rating", "brand"] if c in comp_df.columns]
        st.dataframe(comp_df[display_cols], use_container_width=True)
        st.write("---")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Refresh Competitors", disabled=DEMO_MODE):
            try:
                comps = run_with_progress(fetch_and_store_competitors(selected_asin, domain, geo, db=db))
                st.success(f"Found {len(comps)} competitors!")
            except Exception as e:
                st.error(f"Failed to refresh competitors: {str(e)}")

    with col1:
        if st.button("Analyze with LLM", type="primary"):
            if DEMO_MODE and not os.getenv("OPENAI_API_KEY"):
                st.markdown((DEMO_DIR / "sample_analysis.md").read_text())
            else:
                try:
                    with st.spinner("Running LLM analysis..."):
                        st.markdown(analyze_competitors(selected_asin))
                except Exception as e:
                    st.error(f"Failed to analyze competitors: {str(e)}")
                    st.info("Please check your OpenAI API key and ensure competitors are loaded.")


if __name__ == "__main__":
    main()
