"""
LLM analysis module for competitor insights.

Uses OpenAI GPT-4 to analyze competitors and provide actionable insights.
"""

import os
from dotenv import load_dotenv
from src.db import Database
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

load_dotenv()


class CompetitorInsights(BaseModel):
    """Model for competitor insights from LLM analysis."""
    asin: str
    title: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    rating: Optional[float]
    key_points: List[str] = Field(default_factory=list)


class AnalysisOutput(BaseModel):
    """Model for complete competitor analysis output."""
    summary: str
    positioning: str
    top_competitors: List[CompetitorInsights]
    recommendations: List[str]


def format_competitors(db: Database, parent_asin: str) -> List[Dict]:
    """
    Format competitors from database for LLM analysis.
    
    Args:
        db: Database instance
        parent_asin: ASIN of the parent product
        
    Returns:
        List of formatted competitor dictionaries
    """
    comps = db.search_products({"parent_asin": parent_asin})
    return [
        {
            "asin": c["asin"],
            "title": c["title"],
            "price": c["price"],
            "currency": c.get("currency"),
            "rating": c["rating"],
            "amazon_domain": c.get("amazon_domain")
        }
        for c in comps
    ]

def analyze_competitors(asin: str) -> str:
    """
    Analyze competitors using OpenAI GPT-4.
    
    Generates comprehensive market analysis including summary, positioning,
    top competitors, and actionable recommendations.
    
    Args:
        asin: ASIN of the product to analyze
        
    Returns:
        Formatted analysis string
        
    Raises:
        Exception: If product not found, API call fails, or credentials missing
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser

    db = Database()
    product = db.get_product(asin)
    
    if not product:
        raise ValueError(f"Product with ASIN {asin} not found in database.")
    
    competitors = format_competitors(db, asin)
    
    if not competitors:
        raise ValueError(f"No competitors found for product {asin}.")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OpenAI API key not found. Please check your .env file.")

    parser = PydanticOutputParser(pydantic_object=AnalysisOutput)

    template = (
        "You are a market analyst. Given a product and its competitor list, "
        "write a concise analysis. Pay attention to currency and pricing context.\n\n"
        "Product Title: {product_title}\n"
        "Brand: {brand}\n"
        "Price: {currency} {price}\n"
        "Rating: {rating}\n"
        "Categories: {categories}\n"
        "Amazon Domain: {amazon_domain}\n\n"
        "Competitors (JSON): {competitors}\n\n"
        "IMPORTANT: All prices should be displayed with their correct currency symbol. "
        "When comparing prices, ensure you're using the same currency context.\n\n"
        "{format_instructions}"
    )

    prompt = PromptTemplate(
        template=template,
        input_variables=["product_title", "brand", "price", "rating", "categories", "amazon_domain", "competitors"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    llm = ChatOpenAI(model="gpt-4", temperature=0)

    chain = prompt | llm | parser

    result = chain.invoke(
        {
            "product_title": product["title"] if product else asin,
            "brand": product.get("brand") if product else None,
            "price": product.get("price") if product else None,
            "currency": product.get("currency") if product else "",
            "rating": product.get("rating") if product else None,
            "categories": product.get("categories") if product else None,
            "amazon_domain": product.get("amazon_domain") if product else "com",
            "competitors": competitors,
        }
    )

    lines = [
        "Summary:\n" + result.summary,
        "\nPositioning:\n" + result.positioning,
        "\nCompetitors:"
    ]
    for c in result.top_competitors[:5]:
        pts = "; ".join(c.key_points) if c.key_points else ""
        currency = c.currency if c.currency else ""
        price_str = f"{currency} {c.price}" if currency else f"${c.price}"
        lines.append(f"- {c.asin} | {c.title} | {price_str} | {c.rating} | {pts}")

    if result.recommendations:
        lines.append("\nRecommendations:")
        for r in result.recommendations:
            lines.append(f"- {r}")

    return "\n".join(lines)
