"""Command-line mode: research a CSV/XLSX without the web app.

    python -m app.cli businesses.csv -o results.csv
"""
import argparse
import csv
from pathlib import Path

from app.core.config import get_settings
from app.services.ingest import parse_upload
from app.services.research.pipeline import run_research
from app.services.research.types import BusinessInput


def main() -> None:
    parser = argparse.ArgumentParser(description="Research businesses and match offers.")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--out", type=Path, default=Path("results.csv"))
    args = parser.parse_args()

    parsed = parse_upload(args.input.name, args.input.read_bytes(), get_settings().max_rows_per_upload)
    if parsed.ignored_columns:
        print(f"Ignoring non-business columns: {', '.join(parsed.ignored_columns)}")

    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["business_name", "website", "status", "industry", "summary", "gaps",
                         "recommended_offers", "priority", "outreach_angle", "confidence", "mode"])
        for i, row in enumerate(parsed.rows, start=1):
            print(f"[{i}/{len(parsed.rows)}] {row.business_name}")
            site, a = run_research(BusinessInput(**vars(row)))
            writer.writerow([row.business_name, site.url, site.status, a.industry, a.summary,
                             "; ".join(a.gaps), "; ".join(o["name"] for o in a.offers),
                             a.priority, a.outreach_angle, a.confidence, a.mode])
    print(f"Done -> {args.out}")


if __name__ == "__main__":
    main()
