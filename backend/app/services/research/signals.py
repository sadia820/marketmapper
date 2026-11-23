"""Detect simple, explainable signals from a business website's HTML/text."""
from bs4 import BeautifulSoup

SOCIAL_DOMAINS = ("facebook.com", "instagram.com", "linkedin.com", "twitter.com",
                  "x.com", "tiktok.com", "youtube.com")


def _any(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(n in haystack for n in needles)


def detect_signals(final_url: str, home: BeautifulSoup, html: str, text: str) -> dict:
    t, h = text.lower(), html.lower()
    links = [a.get("href") or "" for a in home.find_all("a")]
    socials = sorted({d.split(".")[0] for d in SOCIAL_DOMAINS if any(d in link for link in links)})
    is_hiring = _any(t, ("we're hiring", "we are hiring", "careers", "join our team", "job openings"))

    return {
        "https": final_url.startswith("https://"),
        "mobile_viewport": bool(home.find("meta", attrs={"name": "viewport"})),
        "social_links": socials,
        "online_booking": _any(h, ("calendly", "booksy", "acuityscheduling", "book now", "book online",
                                   "schedule online", "setmore", "fresha")),
        "appointment_business": _any(t, ("appointment", "schedule a", "estimate", "consultation",
                                         "repair", "salon", "clinic", "service call")),
        "checkout": _any(h, ("add to cart", "checkout", "shopify", "woocommerce", "/cart")),
        "sells_products": _any(t, ("shop", "products", "order online", "buy", "menu")),
        "hiring": is_hiring,
        "hiring_tech": is_hiring and _any(t, ("software engineer", "developer", "devops",
                                              "frontend", "backend engineer")),
        "growth_language": _any(t, ("new location", "expanding", "now open", "second location",
                                    "grand opening")),
        "has_mobile_app": _any(h, ("apps.apple.com", "play.google.com", "itunes.apple.com")),
        "has_chatbot": _any(h, ("intercom", "drift.com", "tawk.to", "zendesk", "crisp.chat",
                                "livechat", "hubspot-messages", "tidio", "freshchat")),
        "saas": _any(t, ("free trial", "start your trial", "sign up free", "per user", "saas",
                         "dashboard", "integrations")),
        "has_api": _any(t, ("api docs", "api documentation", "developer docs", "rest api")),
        "fintech": _any(t, ("fintech", "lending platform", "kyc", "neobank", "banking app",
                            "payment processing", "insurtech")),
        "healthcare": _any(t, ("patient", "clinic", "medical", "dental", "therapy", "healthcare",
                               "physician")),
        "real_estate": _any(t, ("real estate", "realtor", "listings", "property management",
                                "homes for sale", "brokerage")),
        "agency": _any(t, ("marketing agency", "digital agency", "creative agency", "our clients",
                           "case studies")),
        "startup": _any(t, ("startup", "seed round", "series a", "join the waitlist",
                            "early access", "beta")),
        "word_count": len(text.split()),
    }
