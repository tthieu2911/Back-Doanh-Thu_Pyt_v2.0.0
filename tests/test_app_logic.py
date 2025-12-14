from app import filter_and_transform_data

def test_filter_and_transform():
    rows = [
        {"qty": 10, "price": 2},
        {"qty": 50, "price": 5}
    ]
    
    filters = [
        ("qty", ">", 20)
    ]
    
    output_mapping = {
        "TotalMoney": ("qty+price", "calculate")
    }

    result = filter_and_transform_data(rows, filters, output_mapping)

    assert len(result) == 1
    assert result[0]["TotalMoney"] == 50 + 5