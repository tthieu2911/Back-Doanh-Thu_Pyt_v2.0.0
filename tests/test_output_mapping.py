from app import map_output_row

def test_map_output_copy_field():
    row = {"A": 10, "B": 20}
    mapping = {"OutputA": ("A", "keep")}
    
    result = map_output_row(row, mapping)
    
    assert result["OutputA"] == 10


def test_map_output_calculated_sum():
    row = {"A": 10, "B": 20}
    mapping = {"Total": ("A+B", "calculate")}
    
    result = map_output_row(row, mapping)
    
    assert result["Total"] == 30