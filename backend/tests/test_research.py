from app.services.research.ai import parse_response
from app.services.research.catalog import get_catalog
from app.services.research.fetcher import normalize_url
from app.services.research.pipeline import run_research
from app.services.research.types import BusinessInput


def offer_ids(analysis):
    return [o["id"] for o in analysis.offers]


def test_normalize_url():
    assert normalize_url("acme.com") == "https://acme.com"
    assert normalize_url("info@acme.com") == "https://acme.com"
    assert normalize_url("someone@gmail.com") == ""
    assert normalize_url("") == ""


def test_saas_site_gets_industry_offer_first(site_url):
    site, analysis = run_research(BusinessInput("Flowly", f"{site_url}/saas/"))

    assert site.reachable and len(site.pages_read) == 2
    assert analysis.industry == "SaaS / Software"
    assert offer_ids(analysis)[0] == "ai_saas"


def test_local_business_gets_automation_offer(site_url):
    _, analysis = run_research(BusinessInput("Green Valley", f"{site_url}/landscaping/", "Austin"))

    assert analysis.industry == "Landscaping"
    assert offer_ids(analysis)[0] == "ai_automation"
    assert "Green Valley" in analysis.outreach_angle


def test_business_without_website():
    site, analysis = run_research(BusinessInput("Sunrise Bakery"))

    assert site.status == "no website provided"
    assert "product_engineering" in offer_ids(analysis)
    assert analysis.priority == "medium"


def test_ai_response_parsing_drops_unknown_offers():
    raw = """```json
    {"industry": "SaaS", "summary": "x", "recommended_offers": [
        {"id": "ai_saas", "reason": "trial"}, {"id": "made_up", "reason": "?"}],
     "priority": "urgent", "confidence": "high"}
    ```"""
    analysis = parse_response(raw, get_catalog())

    assert offer_ids(analysis) == ["ai_saas"]
    assert analysis.priority == "medium"  # invalid value falls back
    assert analysis.mode == "ai"


def test_ai_provider_resolution():
    from app.core.config import Settings

    assert Settings(anthropic_api_key="", openai_api_key="").resolved_ai_provider is None
    assert Settings(openai_api_key="sk-proj-x").resolved_ai_provider == "openai"
    both = {"anthropic_api_key": "sk-ant-x", "openai_api_key": "sk-proj-x"}
    assert Settings(**both).resolved_ai_provider == "anthropic"
    assert Settings(**both, ai_provider="openai").resolved_ai_provider == "openai"
    assert Settings(ai_provider="openai").resolved_ai_provider is None  # chosen but no key


def test_openai_call_shape(monkeypatch):
    from types import SimpleNamespace

    from app.core.config import get_settings
    from app.services.research import ai

    calls = {}

    class FakeResponses:
        def create(self, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(output_text='{"industry": "SaaS", "recommended_offers": []}')

    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "sk-proj-test")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    monkeypatch.setattr(ai, "_openai_client", lambda: SimpleNamespace(responses=FakeResponses()))

    analysis = ai.analyze_ai(BusinessInput("Flowly"), ai.SiteData(), get_catalog())
    assert calls["model"] == settings.openai_model and "instructions" in calls
    assert analysis.industry == "SaaS" and analysis.mode == "ai"
