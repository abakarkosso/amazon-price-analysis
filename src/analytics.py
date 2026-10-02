"""
Small, pure helpers behind the dashboard, kept out of the Streamlit code so they can be tested.
"""

from typing import Dict, List


def price_summary(products: List[Dict]) -> List[Dict]:
    """
    Average price per currency. Products without a numeric price are left out rather than
    counted as zero, and currencies are never mixed into one average.
    """
    by_currency: Dict[str, List[float]] = {}
    for p in products:
        price = p.get("price")
        if isinstance(price, (int, float)) and not isinstance(price, bool):
            by_currency.setdefault(p.get("currency") or "Unknown", []).append(float(price))
    return [
        {"currency": currency, "count": len(prices), "average": sum(prices) / len(prices),
         "min": min(prices), "max": max(prices)}
        for currency, prices in sorted(by_currency.items())
    ]


def price_position(product: Dict, competitors: List[Dict]) -> Dict:
    """
    Where a product's price sits among competitors in the same currency:
    how many are cheaper, and the percentage gap to the competitor median.
    """
    price = product.get("price")
    currency = product.get("currency")
    rivals = sorted(c["price"] for c in competitors
                    if isinstance(c.get("price"), (int, float)) and c.get("currency") == currency)
    if not isinstance(price, (int, float)) or not rivals:
        return {"comparable": 0}
    mid = len(rivals) // 2
    median = rivals[mid] if len(rivals) % 2 else (rivals[mid - 1] + rivals[mid]) / 2
    return {
        "comparable": len(rivals),
        "cheaper_competitors": sum(1 for r in rivals if r < price),
        "median": median,
        "gap_to_median_pct": round((price - median) / median * 100, 1),
    }
