"""Parse uploaded CSV / Excel files into business rows.

Only business fields are kept. Any other column (e.g. personal phone/email)
is dropped and reported back so the user knows it was ignored.
"""
import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import load_workbook

# canonical field -> accepted header spellings (lower-case, normalized)
COLUMN_ALIASES: dict[str, set[str]] = {
    "business_name": {"business_name", "business", "company", "company_name", "name_of_business",
                      "organization", "organisation", "business name", "company name"},
    "website": {"website", "url", "site", "domain", "web", "website_url", "company_website"},
    "city": {"city", "town"},
    "country": {"country"},
    "notes": {"notes", "note", "comments"},
}
SUPPORTED_SUFFIXES = {".csv", ".xlsx"}


class IngestError(ValueError):
    """Raised when an upload can't be parsed. Message is safe to show users."""


@dataclass
class ParsedRow:
    business_name: str
    website: str = ""
    city: str = ""
    country: str = ""
    notes: str = ""


@dataclass
class ParsedUpload:
    rows: list[ParsedRow]
    ignored_columns: list[str] = field(default_factory=list)


def _normalize(header: str) -> str:
    return " ".join(str(header or "").strip().lower().replace("-", "_").split())


def _map_headers(headers: list[str]) -> tuple[dict[str, int], list[str]]:
    mapping: dict[str, int] = {}
    ignored: list[str] = []
    for idx, raw in enumerate(headers):
        norm = _normalize(raw)
        target = next(
            (canon for canon, aliases in COLUMN_ALIASES.items()
             if norm in aliases or norm.replace(" ", "_") in aliases),
            None,
        )
        if target and target not in mapping:
            mapping[target] = idx
        elif str(raw or "").strip():
            ignored.append(str(raw).strip())
    if "business_name" not in mapping:
        raise IngestError("The file needs a business name column (e.g. 'business_name' or 'company').")
    return mapping, ignored


def _read_table(filename: str, content: bytes) -> list[list[str]]:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise IngestError("Only .csv and .xlsx files are supported.")
    if suffix == ".csv":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        return [row for row in csv.reader(io.StringIO(text))]
    try:
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # openpyxl raises many types for bad files
        raise IngestError("Could not read the Excel file. Is it a valid .xlsx?") from exc
    sheet = wb.worksheets[0]
    return [["" if v is None else str(v) for v in row] for row in sheet.iter_rows(values_only=True)]


def parse_upload(filename: str, content: bytes, max_rows: int) -> ParsedUpload:
    table = [r for r in _read_table(filename, content) if any(str(c).strip() for c in r)]
    if len(table) < 2:
        raise IngestError("The file has no data rows.")

    mapping, ignored = _map_headers(table[0])

    def cell(row: list[str], key: str) -> str:
        idx = mapping.get(key)
        return str(row[idx]).strip() if idx is not None and idx < len(row) else ""

    rows = [
        ParsedRow(**{key: cell(r, key) for key in COLUMN_ALIASES})
        for r in table[1:]
    ]
    rows = [r for r in rows if r.business_name]
    if not rows:
        raise IngestError("No rows have a business name.")
    if len(rows) > max_rows:
        raise IngestError(f"Too many rows ({len(rows)}). The limit is {max_rows} per upload.")
    return ParsedUpload(rows=rows, ignored_columns=ignored)
