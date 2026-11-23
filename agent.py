#!/usr/bin/env python3
"""
Business Research Agent
-----------------------
Takes a CSV/XLSX list of BUSINESSES (name + website), reads each company's
public website, summarizes what the business does, and recommends offers
from offers.yaml with a suggested outreach angle.

Scope: companies only. The tool reads only business columns
(business_name, website, city, country, notes) and ignores everything else.
It does not look up private individuals.

Usage:
  python agent.py input.csv                    # AI mode (needs ANTHROPIC_API_KEY)
  python agent.py input.csv --offline          # rule-based mode, no API key
  python agent.py input.csv -o results --max-pages 4
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib import robotparser

import requests
import yaml
from bs4 import BeautifulSoup

ALLOWED_COLUMNS = ["business_name", "website", "city", "country", "notes"]
USER_AGENT = "MarketMapper/1.0 (+public business website research)"
FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "live.com", "msn.com", "proton.me", "protonmail.com",
}
SUBPAGE_HINTS = re.compile(
    r"about|service|product|solution|contact|career|job|book|appointment|shop|store|menu|pricing",
    re.I,
)
SOCIAL_DOMAINS = ("facebook.com", "instagram.com", "linkedin.com", "twitter.com",
                  "x.com", "tiktok.com", "youtube.com")
MODEL = os.environ.get("AGENT_MODEL", "claude-sonnet-5-5")


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class Business:
    business_name: str
    website: str = ""
    city: str = ""
    country: str = ""
    notes: str = ""


@dataclass
class SiteData:
    url: str = ""
    reachable: bool = False
    error: str = ""
    pages_read: list[str] = field(default_factory=list)
    title: str = ""
    text: str = ""
    signals: dict = field(default_factory=dict)


@dataclass
class Result:
    business_name: str
    website: str
    city: str
    country: str
    status: str
    industry: str = ""
    summary: str = ""
    services: str = ""
    size_estimate: str = ""
    observed_gaps: str = ""
    recommended_offers: str = ""
    offer_reasons: str = ""
    priority: str = ""
    outreach_angle: str = ""
    confidence: str = ""
    pages_read: str = ""
    mode: str = ""


# --------------------------------------------------------------------------- #
# Input
# --------------------------------------------------------------------------- #
def load_businesses(path: Path) -> list[Business]:
    if path.suffix.lower() in (".xlsx", ".xls"):
        import pandas as pd  # optional dependency for Excel input
        rows = pd.read_excel(path, dtype=str).fillna("").to_dict("records")
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

    if not rows:
        sys.exit("Input file is empty.")

    cols = {c.strip().lower(): c for c in rows[0].keys()}
    if "business_name" not in cols:
        sys.exit("Input needs a 'business_name' column (and ideally 'website').")

    ignored = [c for k, c in cols.items() if k not in ALLOWED_COLUMNS]
    if ignored:
        print(f"[info] Ignoring non-business columns: {', '.join(ignored)}")

    out = []
    for r in rows:
        b = Business(**{k: str(r.get(cols[k], "") or "").strip()
                        for k in ALLOWED_COLUMNS if k in cols})
        if not b.business_name:
            continue
        out.append(b)
    return out


# --------------------------------------------------------------------------- #
# Website research
# --------------------------------------------------------------------------- #
def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if "@" in url and "://" not in url:  # someone pasted an email
        domain = url.split("@", 1)[1].lower()
        if domain in FREE_EMAIL_DOMAINS:
            return ""
        url = domain
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


def allowed_by_robots(url: str, session: requests.Session) -> bool:
    parts = urlparse(url)
    rp = robotparser.RobotFileParser()
    try:
        r = session.get(f"{parts.scheme}://{parts.netloc}/robots.txt", timeout=8)
        if r.status_code >= 400:
            return True
        rp.parse(r.text.splitlines())
        return rp.can_fetch(USER_AGENT, url)
    except requests.RequestException:
        return True


def fetch(url: str, session: requests.Session) -> tuple[str, str] | None:
    try:
        r = session.get(url, timeout=15, allow_redirects=True)
        ctype = r.headers.get("content-type", "")
        if r.status_code < 400 and "html" in ctype:
            return r.url, r.text
    except requests.RequestException:
        pass
    # retry over http if https failed on the root
    if url.startswith("https://") and urlparse(url).path in ("", "/"):
        try:
            r = session.get("http://" + url[8:], timeout=15, allow_redirects=True)
            if r.status_code < 400 and "html" in r.headers.get("content-type", ""):
                return r.url, r.text
        except requests.RequestException:
            pass
    return None


def page_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()


def detect_signals(final_url: str, home: BeautifulSoup, html_all: str, text_all: str) -> dict:
    t = text_all.lower()
    h = html_all.lower()
    links = [a.get("href", "") for a in home.find_all("a")]
    socials = sorted({d.split(".")[0] for d in SOCIAL_DOMAINS
                      if any(d in (l or "") for l in links)})
    return {
        "https": final_url.startswith("https://"),
        "mobile_viewport": bool(home.find("meta", attrs={"name": "viewport"})),
        "social_links": socials,
        "online_booking": any(k in h for k in ("calendly", "booksy", "acuityscheduling",
                                              "square.site/book", "book now", "book online",
                                              "schedule online", "setmore", "fresha")),
        "appointment_business": any(k in t for k in ("appointment", "schedule a", "estimate",
                                                    "consultation", "repair", "salon", "clinic",
                                                    "service call")),
        "checkout": any(k in h for k in ("add to cart", "checkout", "shopify", "woocommerce",
                                        "/cart")),
        "sells_products": any(k in t for k in ("shop", "products", "order online", "buy",
                                              "price", "menu")),
        "hiring": any(k in t for k in ("we're hiring", "we are hiring", "careers", "join our team",
                                      "job openings")),
        "growth_language": any(k in t for k in ("new location", "expanding", "now open",
                                               "second location", "grand opening")),
        "equipment_heavy": any(k in t for k in ("fleet", "trucks", "equipment", "machinery",
                                               "construction", "excavation", "manufactur")),
        "food_service": any(k in t for k in ("restaurant", "bakery", "cafe", "catering", "menu")),
        "word_count": len(text_all.split()),
    }


def research_site(b: Business, session: requests.Session, max_pages: int) -> SiteData:
    sd = SiteData(url=normalize_url(b.website))
    if not sd.url:
        sd.error = "no website provided"
        return sd
    if not allowed_by_robots(sd.url, session):
        sd.error = "blocked by robots.txt"
        return sd

    got = fetch(sd.url, session)
    if not got:
        sd.error = "website unreachable"
        return sd

    final_url, html = got
    sd.reachable = True
    sd.url = final_url
    home = BeautifulSoup(html, "html.parser")
    sd.title = (home.title.string or "").strip() if home.title else ""
    home_html = html
    texts = [page_text(BeautifulSoup(html, "html.parser"))]
    sd.pages_read.append(final_url)

    base_host = urlparse(final_url).netloc
    candidates = []
    for a in home.find_all("a", href=True):
        href = urljoin(final_url, a["href"]).split("#")[0]
        if urlparse(href).netloc != base_host or href in candidates or href == final_url:
            continue
        if SUBPAGE_HINTS.search(href) or SUBPAGE_HINTS.search(a.get_text(" ")):
            candidates.append(href)

    all_html = [home_html]
    for link in candidates[: max(0, max_pages - 1)]:
        if not allowed_by_robots(link, session):
            continue
        time.sleep(0.5)  # be polite
        sub = fetch(link, session)
        if sub:
            all_html.append(sub[1])
            texts.append(page_text(BeautifulSoup(sub[1], "html.parser")))
            sd.pages_read.append(sub[0])

    sd.text = "\n\n".join(texts)[:20000]
    sd.signals = detect_signals(final_url, home, "\n".join(all_html), sd.text)
    return sd


# --------------------------------------------------------------------------- #
# Analysis — AI mode
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """You are a B2B research analyst. You receive public website content \
for ONE business plus a catalog of offers. Your job:
1. Describe what the business does, its industry, main services/products and an \
approximate size (solo / small 2-10 / medium 11-50 / large 50+) based only on evidence.
2. List concrete gaps or opportunities you observe on the website.
3. Recommend up to 3 offers from the catalog (use their exact ids) that genuinely fit, \
each with a one-sentence reason tied to evidence. Recommend none if nothing fits.
4. Write a short, honest outreach angle (2-3 sentences) addressed to the business, \
not to any named individual.

Rules: Focus on the business, not on owners or employees as individuals. Do not \
infer personal information (income, age, family, home address) about anyone. \
If evidence is thin, say so and lower confidence.

Respond with ONLY a JSON object with keys:
industry, summary, services (list of strings), size_estimate, observed_gaps (list), \
recommended_offers (list of {id, reason}), priority ("high"|"medium"|"low"), \
outreach_angle, confidence ("high"|"medium"|"low")."""


def analyze_ai(b: Business, sd: SiteData, offers: list[dict], client) -> dict:
    catalog = "\n".join(f"- {o['id']}: {o['name']} — {o['fits']}" for o in offers)
    user = (
        f"Business: {b.business_name}\nLocation: {b.city}, {b.country}\n"
        f"Notes: {b.notes or '-'}\nWebsite: {sd.url or 'none'}\n"
        f"Website status: {'reachable' if sd.reachable else sd.error}\n"
        f"Page title: {sd.title}\n"
        f"Detected technical signals: {json.dumps(sd.signals)}\n\n"
        f"OFFER CATALOG:\n{catalog}\n\n"
        f"WEBSITE CONTENT (truncated):\n{sd.text[:15000] or '(no content)'}"
    )
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    raw = "".join(getattr(blk, "text", "") for blk in msg.content).strip()
    m = re.search(r"\{.*\}", raw, re.S)
    data = json.loads(m.group(0) if m else raw)
    valid_ids = {o["id"] for o in offers}
    data["recommended_offers"] = [r for r in data.get("recommended_offers", [])
                                  if r.get("id") in valid_ids][:3]
    return data


# --------------------------------------------------------------------------- #
# Analysis — offline rule-based mode
# --------------------------------------------------------------------------- #
INDUSTRY_KEYWORDS = {
    "Landscaping": ["landscap", "lawn", "garden"],
    "Auto repair": ["auto repair", "mechanic", "brake", "oil change"],
    "Food & bakery": ["bakery", "restaurant", "cafe", "catering"],
    "Construction": ["construction", "contractor", "remodel", "roofing"],
    "Health & wellness": ["clinic", "dental", "therapy", "fitness", "salon", "spa"],
    "Retail": ["shop", "store", "boutique"],
    "Professional services": ["consulting", "accounting", "law firm", "agency"],
}


def analyze_offline(b: Business, sd: SiteData, offers: list[dict]) -> dict:
    s = sd.signals
    blob = f"{b.business_name} {b.notes} {sd.title} {sd.text}".lower()
    industry = next((k for k, kws in INDUSTRY_KEYWORDS.items()
                     if any(w in blob for w in kws)), "Unknown")

    active = set()
    gaps = []
    if not sd.reachable:
        active.add("no_website")
        gaps.append(f"No working website ({sd.error})")
    else:
        if not s.get("https"):
            active.add("no_https"); gaps.append("Site not served over HTTPS")
        if not s.get("mobile_viewport"):
            active.add("no_mobile_viewport"); gaps.append("No mobile viewport (likely not mobile-friendly)")
        if s.get("word_count", 0) < 150:
            active.add("thin_content"); gaps.append("Very little content on the site")
        if not s.get("social_links"):
            active.add("no_social_links"); gaps.append("No social media links found")
        if s.get("appointment_business") and not s.get("online_booking"):
            active.update({"appointment_business", "no_online_booking"})
            gaps.append("Takes appointments/estimates but no online booking")
        if s.get("sells_products") and not s.get("checkout"):
            active.update({"sells_products", "no_checkout"})
            gaps.append("Sells products but no online checkout")
        for k in ("hiring", "growth_language", "equipment_heavy", "food_service"):
            if s.get(k):
                active.add(k)
    if industry in ("Food & bakery", "Retail", "Health & wellness", "Auto repair", "Landscaping"):
        active.update({"local_business", "consumer_facing"})
    if "food" in industry.lower():
        active.add("food_service")

    scored = []
    for o in offers:
        hits = [sig for sig in o.get("signals", []) if sig in active]
        if hits:
            scored.append((len(hits), o, hits))
    scored.sort(key=lambda x: -x[0])
    recs = [{"id": o["id"], "reason": "Signals: " + ", ".join(h)} for _, o, h in scored[:3]]

    priority = "high" if len(gaps) >= 3 else "medium" if gaps else "low"
    top = offers_by_id(offers).get(recs[0]["id"])["name"] if recs else None
    angle = (f"We noticed {gaps[0].lower()} for {b.business_name}. "
             f"Our {top.lower()} could help you win more customers in {b.city or 'your area'}."
             if recs and gaps else "")
    return {
        "industry": industry,
        "summary": sd.title or ("No website content available" if not sd.reachable else ""),
        "services": [],
        "size_estimate": "unknown",
        "observed_gaps": gaps,
        "recommended_offers": recs,
        "priority": priority,
        "outreach_angle": angle,
        "confidence": "low",
    }


def offers_by_id(offers: list[dict]) -> dict:
    return {o["id"]: o for o in offers}


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def to_result(b: Business, sd: SiteData, a: dict, offers: list[dict], mode: str) -> Result:
    names = offers_by_id(offers)
    recs = a.get("recommended_offers", [])
    return Result(
        business_name=b.business_name, website=sd.url or b.website,
        city=b.city, country=b.country,
        status="researched" if sd.reachable else sd.error,
        industry=a.get("industry", ""), summary=a.get("summary", ""),
        services="; ".join(a.get("services", []) or []),
        size_estimate=a.get("size_estimate", ""),
        observed_gaps="; ".join(a.get("observed_gaps", []) or []),
        recommended_offers="; ".join(names[r["id"]]["name"] for r in recs if r["id"] in names),
        offer_reasons=" | ".join(f"{r['id']}: {r.get('reason','')}" for r in recs),
        priority=a.get("priority", ""), outreach_angle=a.get("outreach_angle", ""),
        confidence=a.get("confidence", ""), pages_read=" ".join(sd.pages_read), mode=mode,
    )


def write_outputs(results: list[Result], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [asdict(r) for r in results]
    with open(out_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    (out_dir / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    order = {"high": 0, "medium": 1, "low": 2}
    md = ["# Business Research Report\n"]
    for r in sorted(results, key=lambda r: order.get(r.priority, 3)):
        md += [f"## {r.business_name}  ·  priority: {r.priority or '-'}",
               f"- **Website:** {r.website or '—'} ({r.status})",
               f"- **Location:** {', '.join(x for x in (r.city, r.country) if x) or '—'}",
               f"- **Industry:** {r.industry or '—'}   **Size:** {r.size_estimate or '—'}",
               f"- **Summary:** {r.summary or '—'}",
               f"- **Gaps:** {r.observed_gaps or '—'}",
               f"- **Recommended offers:** {r.recommended_offers or '—'}",
               f"- **Why:** {r.offer_reasons or '—'}",
               f"- **Outreach angle:** {r.outreach_angle or '—'}",
               f"- **Confidence:** {r.confidence}  ·  mode: {r.mode}\n"]
    (out_dir / "report.md").write_text("\n".join(md), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Research businesses and match offers.")
    ap.add_argument("input", type=Path, help="CSV or XLSX with business_name, website, ...")
    ap.add_argument("-o", "--out", type=Path, default=Path("results"))
    ap.add_argument("--offers", type=Path, default=Path(__file__).with_name("offers.yaml"))
    ap.add_argument("--offline", action="store_true", help="Rule-based mode, no API key needed")
    ap.add_argument("--max-pages", type=int, default=4, help="Pages to read per site")
    args = ap.parse_args()

    offers = yaml.safe_load(args.offers.read_text())["offers"]
    businesses = load_businesses(args.input)
    print(f"Loaded {len(businesses)} businesses, {len(offers)} offers.")

    client = None
    if not args.offline:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("[warn] ANTHROPIC_API_KEY not set — falling back to --offline mode.")
        else:
            import anthropic
            client = anthropic.Anthropic()

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    results = []
    for i, b in enumerate(businesses, 1):
        print(f"[{i}/{len(businesses)}] {b.business_name} ... ", end="", flush=True)
        sd = research_site(b, session, args.max_pages)
        mode = "ai" if client else "offline"
        try:
            a = analyze_ai(b, sd, offers, client) if client else analyze_offline(b, sd, offers)
        except Exception as e:  # keep the batch going
            print(f"(AI error: {e}; using offline) ", end="")
            a, mode = analyze_offline(b, sd, offers), "offline-fallback"
        results.append(to_result(b, sd, a, offers, mode))
        print(f"{results[-1].status}; offers: {results[-1].recommended_offers or 'none'}")

    write_outputs(results, args.out)
    print(f"\nDone. See {args.out}/results.csv, results.json and report.md")


if __name__ == "__main__":
    main()
