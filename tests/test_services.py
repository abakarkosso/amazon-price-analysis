import src.services as services
from src.db import Database


def test_competitors_are_scraped_with_the_parent_products_market(tmp_path, monkeypatch):
    db = Database(str(tmp_path / "d.json"))
    db.insert_product({"asin": "P", "title": "Wi-Fi Router - AX1800", "categories": ["Routers"],
                       "amazon_domain": "ca", "geo_location": "M5V"})
    searched, scraped = [], []

    def fake_search(query_title, domain, categories, pages, geo_location):
        searched.append((domain, geo_location))
        return [{"asin": "C1", "title": "Other router"}, {"asin": "P", "title": "itself"}]

    def fake_scrape(asins, geo_location, domain):
        scraped.append((domain, geo_location))
        for a in asins:
            yield {"status": "success", "product": {"asin": a, "title": "Other router", "price": 99.0}}

    monkeypatch.setattr(services, "search_competitors", fake_search)
    monkeypatch.setattr(services, "scrape_multiple_products", fake_scrape)

    # The form currently says .com / 10001, but the product was scraped from .ca.
    gen = services.fetch_and_store_competitors("P", domain="com", geo_location="10001", db=db)
    updates = []
    try:
        while True:
            updates.append(next(gen))
    except StopIteration as done:
        stored = done.value

    assert set(searched) == {("ca", "M5V")}
    assert scraped == [("ca", "M5V")]
    assert [c["asin"] for c in stored] == ["C1"]          # the product itself is never its own competitor
    assert db.search_products({"parent_asin": "P"})[0]["asin"] == "C1"


def test_competitor_count_is_capped_to_limit_scraping_cost(tmp_path, monkeypatch):
    db = Database(str(tmp_path / "d.json"))
    db.insert_product({"asin": "P", "title": "Thing", "categories": ["Cat"]})
    monkeypatch.setenv("MAX_COMPETITORS", "3")
    monkeypatch.setattr(services, "search_competitors",
                        lambda **kw: [{"asin": f"C{i}", "title": "t"} for i in range(10)])
    seen = []
    monkeypatch.setattr(services, "scrape_multiple_products",
                        lambda asins, g, d: seen.extend(asins) or iter(()))
    list(services.fetch_and_store_competitors("P", "com", "", db=db))
    assert len(seen) == 3


def test_parse_asins_handles_spaces_duplicates_case_and_empty_items():
    from src.services import parse_asins
    raw = " B0CX23VSAS, b0abc12345 ,,B0CX23VSAS\nB0ZZZ99999 "
    assert parse_asins(raw) == ["B0CX23VSAS", "B0ABC12345", "B0ZZZ99999"]
    assert parse_asins("  ,  ") == []
