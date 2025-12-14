import pandas as pd
from app import load_excel_file

def test_load_excel_file_valid(tmp_path):
    # Arrange
    file = tmp_path / "test.xlsx"
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
    df.to_excel(file, index=False)

    # Act
    result = load_excel_file(str(file))

    # Assert
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["A", "B"]


def test_load_excel_file_invalid():
    import pytest
    
    with pytest.raises(FileNotFoundError):
        load_excel_file("non_existing.xlsx")