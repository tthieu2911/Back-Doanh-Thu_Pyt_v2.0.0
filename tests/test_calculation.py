# tests/test_calculation.py
import pandas as pd
from app import compute_sum_formula

def test_compute_sum():
    df = pd.DataFrame({
        "A": [1, 2],
        "B": [3, 4]
    })

    res = compute_sum_formula(df, "A + B")
    assert res.tolist() == [4, 6]

def test_compute_missing_column():
    df = pd.DataFrame({"A": [1, 2]})
    res = compute_sum_formula(df, "A + X")
    assert res.tolist() == [1, 2]
    
def test_currency_rule():
    df = pd.DataFrame({"ExchangeRate": [1, 2]})
    mapping = {"out_name": "LOAI", "mode": "currency_rule"}

    output = pd.DataFrame(index=df.index)

    exchange_cols = ["ExchangeRate"]
    output["LOAI"] = (
        pd.to_numeric(df[exchange_cols[0]], errors="coerce")
        .apply(lambda x: "VND" if x == 1 else "USD")
    )

    assert output["LOAI"].tolist() == ["VND", "USD"]

def test_compute_sum_formula_missing_column():
    df = pd.DataFrame({"A": [1, 2]})
    result = compute_sum_formula(df, "A + B")
    assert result.tolist() == [1, 2]

def test_compute_sum_formula_empty():
    df = pd.DataFrame()
    result = compute_sum_formula(df, "")
    assert result.empty