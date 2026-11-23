"""Rule-based analyzer: fast, free and explainable. Used when no AI key is set."""
from app.services.research.catalog import Catalog
from app.services.research.types import Analysis, BusinessInput, SiteData

INDUSTRY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "SaaS / Software": ("saas", "free trial", "software platform", "per user"),
    "Fintech": ("fintech", "lending platform", "kyc", "payment processing"),
    "Healthcare": ("clinic", "patient", "medical", "dental"),
    "Real estate": ("real estate", "realtor", "listings", "brokerage"),
    "Agency": ("marketing agency", "digital agency", "creative agency"),
    "E-commerce": ("add to cart", "shop now", "checkout"),
    "Landscaping": ("landscap", "lawn", "garden"),
    "Auto repair": ("auto repair", "mechanic", "brake", "oil change"),
    "Food & hospitality": ("bakery", "restaurant", "cafe", "catering"),
    "Construction": ("construction", "contractor", "remodel", "roofing"),
    "Retail": ("boutique", "store"),
    "Professional services": ("consulting", "accounting", "law firm"),
}
INDUSTRY_SIGNAL = {"SaaS / Software": "saas", "Fintech": "fintech", "Healthcare": "healthcare",
                   "Real estate": "real_estate", "Agency": "agency", "E-commerce": "ecommerce"}
LOCAL_INDUSTRIES = {"Food & hospitality", "Retail", "Healthcare", "Auto repair", "Landscaping",
                    "Construction"}
PASSTHROUGH_SIGNALS = ("hiring", "hiring_tech", "growth_language", "saas", "has_api", "fintech",
                       "healthcare", "real_estate", "agency", "startup", "appointment_business")
FALLBACK_OFFER = "free_ai_audit"
MAX_OFFERS = 3


def _detect_industry(business: BusinessInput, site: SiteData) -> str:
    blob = f"{business.business_name} {business.notes} {site.title} {site.text}".lower()
    return next((name for name, kws in INDUSTRY_KEYWORDS.items() if any(k in blob for k in kws)),
                "Unknown")


def _active_signals(site: SiteData, industry: str) -> tuple[set[str], list[str]]:
    active: set[str] = set()
    gaps: list[str] = []
    s = site.signals

    if not site.reachable:
        active.add("no_website")
        gaps.append(f"No working website ({site.error})")
    else:
        checks = [
            (not s.get("https"), "no_https", "Site is not served over HTTPS"),
            (not s.get("mobile_viewport"), "no_mobile_viewport", "Site is not mobile-friendly"),
            (s.get("word_count", 0) < 150, "thin_content", "Very little content on the site"),
            (s.get("load_seconds", 0) > 3, "slow_site", f"Slow home page ({s.get('load_seconds')}s)"),
            (not s.get("has_chatbot"), "no_chatbot", "No live chat or support automation"),
        ]
        for condition, signal, gap in checks:
            if condition:
                active.add(signal)
                gaps.append(gap)
        if not s.get("has_mobile_app"):
            active.add("no_mobile_app")
        if s.get("checkout"):
            active.add("ecommerce")
        active.update(k for k in PASSTHROUGH_SIGNALS if s.get(k))

    if industry in INDUSTRY_SIGNAL:
        active.add(INDUSTRY_SIGNAL[industry])
    if industry in LOCAL_INDUSTRIES:
        active.update({"local_business", "consumer_facing"})
    return active, gaps


def analyze_rules(business: BusinessInput, site: SiteData, catalog: Catalog) -> Analysis:
    industry = _detect_industry(business, site)
    active, gaps = _active_signals(site, industry)

    scored = sorted(
        ((len(hits) * offer.weight, offer, hits)
         for offer in catalog.offers
         if (hits := [sig for sig in offer.signals if sig in active])),
        key=lambda item: -item[0],
    )
    offers = [{"id": o.id, "name": o.name, "reason": "Signals: " + ", ".join(hits)}
              for _, o, hits in scored[:MAX_OFFERS]]

    fallback = catalog.get(FALLBACK_OFFER)
    if fallback and len(offers) < MAX_OFFERS and all(o["id"] != fallback.id for o in offers):
        offers.append({"id": fallback.id, "name": fallback.name,
                       "reason": "Low-friction first step for any SMB"})

    angle = ""
    if offers:
        top = catalog.get(offers[0]["id"])
        opener = (f"While looking at {business.business_name}, we noticed: "
                  f"{gaps[0][0].lower() + gaps[0][1:]}. ") if gaps else ""
        angle = (f"{opener}Our {top.short_name} work could help here. "
                 "Happy to start with a free AI audit to show where you could save time or grow.")

    return Analysis(
        industry=industry,
        summary=site.title or ("No website content available" if not site.reachable else ""),
        gaps=gaps,
        offers=offers,
        priority="high" if len(gaps) >= 3 else "medium" if gaps else "low",
        outreach_angle=angle,
        confidence="low",
        mode="rules",
    )
