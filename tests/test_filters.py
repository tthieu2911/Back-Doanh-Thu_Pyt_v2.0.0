from app import apply_filter

def test_filter_equals():
    data = [{"name": "Alice"}, {"name": "Bob"}]
    result = apply_filter(data, "name", "=", "Alice")
    assert len(result) == 1
    assert result[0]["name"] == "Alice"


def test_filter_contains():
    data = [{"desc": "hello world"}, {"desc": "no match"}]
    result = apply_filter(data, "desc", "contains", "world")
    assert len(result) == 1


def test_filter_greater_than():
    data = [{"qty": 5}, {"qty": 20}]
    result = apply_filter(data, "qty", ">", 10)
    assert len(result) == 1
    assert result[0]["qty"] == 20