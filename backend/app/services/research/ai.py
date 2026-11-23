"""AI analyzer (Anthropic or OpenAI). Richer summaries and better offer matching."""
import json
import re
from functools import lru_cache

from app.core.config import get_settings
from app.services.research.catalog import Catalog
from app.services.research.types import Analysis, BusinessInput, SiteData

SYSTEM_PROMPT = """You are a B2B research analyst. You receive public website content for ONE \
business plus a catalog of offers from the seller. Your job:
1. Describe what the business does, its industry, main services/products and an approximate \
size (solo / small 2-10 / medium 11-50 / large 50+) based only on evidence.
2. List concrete gaps or opportunities you observe on the website.
3. Recommend up to 3 offers from the catalog (use their exact ids) that genuinely fit, each with \
a one-sentence reason tied to evidence. Recommend none if nothing fits.
4. Write a short, honest outreach angle (2-3 sentences) from the seller to the business, not to \
any named individual. Prefer the Free AI Audit as a low-friction first step when it fits.

Rules: Focus on the business, not on owners or employees as individuals. Do not infer personal \
information (income, age, family, home address) about anyone. If evidence is thin, say so and \
lower confidence.

Respond with ONLY a JSON object with keys: industry, summary, services (list of strings), \
size_estimate, observed_gaps (list), recommended_offers (list of {id, reason}), \
priority ("high"|"medium"|"low"), outreach_angle, confidence ("high"|"medium"|"low")."""

MAX_CONTENT_CHARS = 15_000
MAX_OUTPUT_TOKENS = 4000


@lru_cache
def _anthropic_client():
    import anthropic

    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key)


@lru_cache
def _openai_client():
    import openai

    return openai.OpenAI(api_key=get_settings().openai_api_key)


def _complete(system: str, user: str) -> str:
    """Send one prompt to the configured provider and return the text reply."""
    settings = get_settings()
    provider = settings.resolved_ai_provider
    if provider == "anthropic":
        message = _anthropic_client().messages.create(
            model=settings.agent_model,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(getattr(block, "text", "") for block in message.content)
    if provider == "openai":
        response = _openai_client().responses.create(
            model=settings.openai_model,
            instructions=system,
            input=user,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
        return response.output_text
    raise RuntimeError("No AI provider configured")


def _build_prompt(business: BusinessInput, site: SiteData, catalog: Catalog) -> str:
    offers = "\n".join(f"- {o.id}: {o.name} — {o.fits}" for o in catalog.offers)
    return (
        f"SELLER: {catalog.seller or 'a services company'}\n\n"
        f"OFFER CATALOG:\n{offers}\n\n"
        f"BUSINESS: {business.business_name}\n"
        f"Location: {', '.join(x for x in (business.city, business.country) if x) or 'unknown'}\n"
        f"Notes: {business.notes or '-'}\n"
        f"Website: {site.url or 'none'} ({site.status})\n"
        f"Page title: {site.title}\n"
        f"Detected signals: {json.dumps(site.signals)}\n\n"
        f"WEBSITE CONTENT (truncated):\n{site.text[:MAX_CONTENT_CHARS] or '(no content)'}"
    )


def parse_response(raw: str, catalog: Catalog) -> Analysis:
    match = re.search(r"\{.*\}", raw, re.S)
    data = json.loads(match.group(0) if match else raw)

    offers = []
    for rec in data.get("recommended_offers", [])[:3]:
        offer = catalog.get(rec.get("id", ""))
        if offer:
            offers.append({"id": offer.id, "name": offer.name, "reason": rec.get("reason", "")})

    def pick(value: str, allowed: set[str], default: str) -> str:
        return value if value in allowed else default

    levels = {"high", "medium", "low"}
    return Analysis(
        industry=str(data.get("industry", "")),
        summary=str(data.get("summary", "")),
        services=[str(s) for s in data.get("services", [])][:10],
        size_estimate=str(data.get("size_estimate", "unknown")),
        gaps=[str(g) for g in data.get("observed_gaps", [])][:10],
        offers=offers,
        priority=pick(data.get("priority"), levels, "medium"),
        outreach_angle=str(data.get("outreach_angle", "")),
        confidence=pick(data.get("confidence"), levels, "low"),
        mode="ai",
    )


def analyze_ai(business: BusinessInput, site: SiteData, catalog: Catalog) -> Analysis:
    raw = _complete(SYSTEM_PROMPT, _build_prompt(business, site, catalog))
    return parse_response(raw, catalog)
