"""Research one business end to end: website -> analysis. No database code here."""
import logging

from app.core.config import get_settings
from app.services.research.catalog import get_catalog
from app.services.research.fetcher import research_site
from app.services.research.rules import analyze_rules
from app.services.research.types import Analysis, BusinessInput, SiteData

log = logging.getLogger(__name__)


def run_research(business: BusinessInput) -> tuple[SiteData, Analysis]:
    catalog = get_catalog()
    site = research_site(business.website)

    if get_settings().ai_enabled:
        try:
            from app.services.research.ai import analyze_ai

            return site, analyze_ai(business, site, catalog)
        except Exception:  # never lose a row because the AI call failed
            log.exception("AI analysis failed for %s; using rules", business.business_name)
            analysis = analyze_rules(business, site, catalog)
            analysis.mode = "rules-fallback"
            return site, analysis

    return site, analyze_rules(business, site, catalog)
