# tests/test_dates.py
import pandas as pd
from app import last_day_of_last_month, try_parse_date_value, try_parse_date_series
from datetime import date

def test_last_day_of_last_month():
    d = last_day_of_last_month()
    assert d.day in (28, 29, 30, 31)

def test_parse_valid_date():
    d = try_parse_date_value("31/12/2024")
    assert d.year == 2024

def test_parse_invalid_date():
    assert try_parse_date_value("abc") is None

def test_try_parse_date_series_invalid():
    s = pd.Series(["abc", "xyz"])
    assert try_parse_date_series(s) is None

def test_try_parse_date_value_invalid():
    assert try_parse_date_value("not-a-date") is None