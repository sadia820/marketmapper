import io

import pytest
from openpyxl import Workbook

from app.services.ingest import IngestError, parse_upload


def test_csv_aliases_and_ignored_columns():
    content = b"Company,URL,City,owner_phone,owner_email\nAcme Co,acme.com,Lahore,123,a@b.com\n"
    parsed = parse_upload("list.csv", content, max_rows=10)

    assert len(parsed.rows) == 1
    row = parsed.rows[0]
    assert (row.business_name, row.website, row.city) == ("Acme Co", "acme.com", "Lahore")
    assert parsed.ignored_columns == ["owner_phone", "owner_email"]


def test_xlsx_is_supported():
    wb = Workbook()
    wb.active.append(["business_name", "website"])
    wb.active.append(["Sunrise Bakery", None])
    buf = io.BytesIO()
    wb.save(buf)

    parsed = parse_upload("list.xlsx", buf.getvalue(), max_rows=10)
    assert parsed.rows[0].business_name == "Sunrise Bakery"
    assert parsed.rows[0].website == ""


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("list.txt", b"x", "Only .csv and .xlsx"),
        ("list.csv", b"website\nacme.com\n", "business name column"),
        ("list.csv", b"business_name\n", "no data rows"),
        ("list.csv", b"business_name\nA\nB\nC\n", "Too many rows"),
    ],
)
def test_invalid_uploads(filename, content, message):
    with pytest.raises(IngestError, match=message):
        parse_upload(filename, content, max_rows=2)
