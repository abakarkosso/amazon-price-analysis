from src.analytics import price_position, price_summary


def test_price_summary_never_mixes_currencies_or_counts_missing_prices_as_zero():
    products = [
        {"price": 10.0, "currency": "USD"},
        {"price": 30.0, "currency": "USD"},
        {"price": 50.0, "currency": "CAD"},
        {"price": None, "currency": "USD"},
        {"price": "N/A", "currency": "USD"},
        {"currency": "USD"},
    ]
    assert price_summary(products) == [
        {"currency": "CAD", "count": 1, "average": 50.0, "min": 50.0, "max": 50.0},
        {"currency": "USD", "count": 2, "average": 20.0, "min": 10.0, "max": 30.0},
    ]


def test_price_position_against_same_currency_competitors():
    product = {"price": 60.0, "currency": "USD"}
    competitors = [{"price": p, "currency": "USD"} for p in (40.0, 50.0, 70.0, 80.0)] + [
        {"price": 1.0, "currency": "CAD"},   # different currency: ignored
        {"price": None, "currency": "USD"},  # no price: ignored
    ]
    assert price_position(product, competitors) == {
        "comparable": 4, "cheaper_competitors": 2, "median": 60.0, "gap_to_median_pct": 0.0,
    }


def test_price_position_without_comparable_competitors():
    assert price_position({"price": 10.0, "currency": "USD"}, [{"price": 5.0, "currency": "EUR"}]) == {"comparable": 0}
