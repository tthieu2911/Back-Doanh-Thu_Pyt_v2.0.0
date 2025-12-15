# tests/test_headers.py
import pandas as pd
import io
from app import read_workbook_build_headers

def make_excel(rows):
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, header=False)
    return buffer.getvalue()

def test_read_headers_basic():
    rows = [
        [""] * 6,  # row 1
        [""] * 6,
        [""] * 6,
        [""] * 6,
        [""] * 6,
        [""] * 6,
        ["A7", "B7", "C7", "D7", "E7", "F7"],  # row 7
        ["A8", "B8", "C8", "D8", "E8", "F8"],  # row 8
        [1, 2, 3, 4, 5, 6],                   # data
    ]

    content = make_excel(rows)
    df, headers = read_workbook_build_headers(content, "test.xlsx")

    assert headers[0] == "A7"
    assert headers[1] == "B8 B7"
    assert headers[2] == "C8 B7"
    assert headers[3] == "D8 B7"
    assert headers[4] == "E7"

    assert len(df) == 1

def test_header_fallback_column_name():
    rows = [[""] * 3] * 8
    content = make_excel(rows)

    df, headers = read_workbook_build_headers(content, "test.xlsx")

    assert headers == []

def test_xls_loader(monkeypatch):
    def fake_read(*args, **kwargs):
        return pd.DataFrame([[None]*3]*8)

    monkeypatch.setattr(pd, "read_excel", fake_read)

    df, headers = read_workbook_build_headers(b"fake", "test.xls")
    assert len(headers) == 3