"""Fetch a business's public website politely (robots.txt, timeouts, page cap)."""
import ipaddress
import re
import socket
import time
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.services.research.signals import detect_signals
from app.services.research.types import SiteData

USER_AGENT = "MarketMapper/1.0 (+public business website research)"
FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
                      "icloud.com", "live.com", "msn.com", "proton.me", "protonmail.com"}
SUBPAGE_HINTS = re.compile(
    r"about|service|product|solution|contact|career|job|book|appointment|shop|store|pricing", re.I
)
MAX_TEXT_CHARS = 20_000


def normalize_url(raw: str) -> str:
    url = (raw or "").strip()
    if not url:
        return ""
    if "@" in url and "://" not in url:  # an email was pasted; use its domain if it's a company one
        domain = url.split("@", 1)[1].lower()
        if domain in FREE_EMAIL_DOMAINS:
            return ""
        url = domain
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


def _is_public_host(url: str) -> bool:
    """Block internal/private addresses so uploads can't make the server probe its own network."""
    if get_settings().allow_private_urls:
        return True
    host = urlparse(url).hostname
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


class _Fetcher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self._robots: dict[str, robotparser.RobotFileParser | None] = {}

    def allowed(self, url: str) -> bool:
        parts = urlparse(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            rp = robotparser.RobotFileParser()
            try:
                r = self.session.get(f"{origin}/robots.txt", timeout=8)
                if r.status_code < 400:
                    rp.parse(r.text.splitlines())
                    self._robots[origin] = rp
                else:
                    self._robots[origin] = None
            except requests.RequestException:
                self._robots[origin] = None
        rp = self._robots[origin]
        return rp is None or rp.can_fetch(USER_AGENT, url)

    def get_html(self, url: str) -> tuple[str, str] | None:
        if not _is_public_host(url):
            return None
        try:
            r = self.session.get(url, timeout=self.settings.request_timeout_seconds)
        except requests.RequestException:
            return None
        if r.status_code >= 400 or "html" not in r.headers.get("content-type", ""):
            return None
        if not _is_public_host(r.url):  # redirected somewhere internal
            return None
        if not r.encoding or r.encoding.lower() == "iso-8859-1":  # header missing a charset
            r.encoding = r.apparent_encoding
        return r.url, r.text


def _page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()


def _subpage_links(home: BeautifulSoup, base_url: str) -> list[str]:
    host = urlparse(base_url).netloc
    links: list[str] = []
    for a in home.find_all("a", href=True):
        href = urljoin(base_url, a["href"]).split("#")[0]
        if urlparse(href).netloc != host or href in links or href.rstrip("/") == base_url.rstrip("/"):
            continue
        if SUBPAGE_HINTS.search(href) or SUBPAGE_HINTS.search(a.get_text(" ")):
            links.append(href)
    return links


def research_site(website: str) -> SiteData:
    settings = get_settings()
    site = SiteData(url=normalize_url(website))
    if not site.url:
        site.error = "no website provided"
        return site

    fetcher = _Fetcher()
    if not fetcher.allowed(site.url):
        site.error = "blocked by robots.txt"
        return site

    started = time.monotonic()
    home_page = fetcher.get_html(site.url)
    if not home_page and site.url.startswith("https://"):
        home_page = fetcher.get_html("http://" + site.url[len("https://"):])
    load_seconds = time.monotonic() - started
    if not home_page:
        site.error = "website unreachable"
        return site

    final_url, home_html = home_page
    home = BeautifulSoup(home_html, "html.parser")
    site.reachable, site.url = True, final_url
    site.title = (home.title.string or "").strip() if home.title and home.title.string else ""
    site.pages_read.append(final_url)

    htmls, texts = [home_html], [_page_text(home_html)]
    for link in _subpage_links(home, final_url)[: max(0, settings.max_pages_per_site - 1)]:
        if not fetcher.allowed(link):
            continue
        time.sleep(0.5)  # be polite to small business servers
        page = fetcher.get_html(link)
        if page:
            site.pages_read.append(page[0])
            htmls.append(page[1])
            texts.append(_page_text(page[1]))

    site.text = "\n\n".join(texts)[:MAX_TEXT_CHARS]
    site.signals = detect_signals(final_url, home, "\n".join(htmls), site.text)
    site.signals["load_seconds"] = round(load_seconds, 2)
    return site
