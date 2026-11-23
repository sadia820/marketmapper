"""Offer catalog loaded from offers.yaml."""
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import get_settings


@dataclass(frozen=True)
class Offer:
    id: str
    name: str
    fits: str
    signals: tuple[str, ...] = field(default_factory=tuple)
    weight: int = 1

    @property
    def short_name(self) -> str:
        return self.name.split(" (")[0]


@dataclass(frozen=True)
class Catalog:
    seller: str
    offers: tuple[Offer, ...]

    def get(self, offer_id: str) -> Offer | None:
        return next((o for o in self.offers if o.id == offer_id), None)


def load_catalog(path: Path) -> Catalog:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    offers = tuple(
        Offer(
            id=o["id"], name=o["name"], fits=o.get("fits", ""),
            signals=tuple(o.get("signals", [])), weight=int(o.get("weight", 1)),
        )
        for o in data.get("offers", [])
    )
    return Catalog(seller=str(data.get("seller", "")).strip(), offers=offers)


@lru_cache
def get_catalog() -> Catalog:
    return load_catalog(get_settings().offers_path)
