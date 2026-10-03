"""Smoke test: runs the real Streamlit app in demo mode and clicks through the main flow."""
from streamlit.testing.v1 import AppTest


def demo_app(monkeypatch, tmp_path):
    for var in ("OXYLABS_USERNAME", "OXYLABS_PASSWORD", "OPENAI_API_KEY", "DB_PATH"):
        monkeypatch.delenv(var, raising=False)
    # Keep the test from loading a developer's real .env.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    monkeypatch.chdir(tmp_path)
    return AppTest.from_file(str(__import__("pathlib").Path(__file__).parent.parent / "main.py"), default_timeout=30)


def test_demo_mode_renders_dashboard_and_tracked_product(monkeypatch, tmp_path):
    at = demo_app(monkeypatch, tmp_path).run()
    assert not at.exception
    assert any("Demo mode" in i.value for i in at.info)
    assert [s.value for s in at.subheader][:2] == ["Dashboard", "Tracked Products"]
    # The scrape button is off without credentials.
    assert any(b.label == "Scrape Product" and b.disabled for b in at.button)


def test_demo_mode_competitor_analysis_flow(monkeypatch, tmp_path):
    at = demo_app(monkeypatch, tmp_path).run()
    at.button(key="analyze_DEMO000001").click().run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Cheaper competitors"] == "3 of 6"
    assert metrics["Gap to median"] == "+4.3%"
    # Competitors with recorded prices get their own history chart.
    assert any(sb.label == "Competitor price history" for sb in at.selectbox)
    next(b for b in at.button if b.label == "Analyze with LLM").click().run()
    assert not at.exception
    assert any("Sample analysis" in m.value for m in at.markdown)
