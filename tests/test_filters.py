# tests/test_filters.py
import pandas as pd
from app import apply_single_filter, apply_filters, new_filter, is_number_like

def test_string_contains():
    df = pd.DataFrame({"A": ["Apple", "Banana", "Cherry"]})
    mask = apply_single_filter(df, "A", "contains", "an")
    assert df[mask]["A"].tolist() == ["Banana"]

def test_all_string_ops():
    df = pd.DataFrame({"A": ["Hello", "World"]})

    assert apply_single_filter(df, "A", "begins with", "He").tolist() == [True, False]
    assert apply_single_filter(df, "A", "not begins with", "He").tolist() == [False, True]
    assert apply_single_filter(df, "A", "ends with", "ld").tolist() == [False, True]
    assert apply_single_filter(df, "A", "not ends with", "ld").tolist() == [True, False]

def test_string_begins_with():
    df = pd.DataFrame({"col": ["abc", "xyz"]})
    mask = apply_single_filter(df, "col", "begins with", "a")
    assert mask.tolist() == [True, False]

def test_string_not_ends_with():
    df = pd.DataFrame({"col": ["test", "done"]})
    mask = apply_single_filter(df, "col", "not ends with", "e")
    assert mask.tolist() == [True, False]

def test_numeric_greater_than():
    df = pd.DataFrame({"A": [1, 5, 10]})
    mask = apply_single_filter(df, "A", ">", "4")
    assert df[mask]["A"].tolist() == [5, 10]

def test_numeric_invalid_value():
    df = pd.DataFrame({"A": ["x", "y"]})
    mask = apply_single_filter(df, "A", ">", "10")
    assert mask.tolist() == [False, False]

def test_is_number_like():
    assert is_number_like("10") is True
    assert is_number_like("10.5") is True
    assert is_number_like("abc") is False

def test_date_equal():
    df = pd.DataFrame({"A": ["01/01/2024", "02/01/2024"]})
    mask = apply_single_filter(df, "A", "=", "01/01/2024")
    assert mask.tolist() == [True, False]

def test_apply_multiple_filters():
    df = pd.DataFrame({
        "A": [1, 2, 3],
        "B": ["X", "Y", "X"]
    })

    filters = [
        {"col": "A", "op": ">", "val": "1"},
        {"col": "B", "op": "=", "val": "X"}
    ]

    result = apply_filters(df, filters)
    assert result["A"].tolist() == [3]
    
def test_new_filter():
    f = new_filter("COL1")
    assert f["col"] == "COL1"
    assert f["op"] == "="
    assert "id" in f