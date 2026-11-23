from dataclasses import dataclass, field


@dataclass
class BusinessInput:
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
    title: str = ""
    text: str = ""
    pages_read: list[str] = field(default_factory=list)
    signals: dict = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "researched" if self.reachable else self.error


@dataclass
class Analysis:
    industry: str = ""
    summary: str = ""
    services: list[str] = field(default_factory=list)
    size_estimate: str = "unknown"
    gaps: list[str] = field(default_factory=list)
    offers: list[dict] = field(default_factory=list)  # [{id, name, reason}]
    priority: str = "low"
    outreach_angle: str = ""
    confidence: str = "low"
    mode: str = "rules"
