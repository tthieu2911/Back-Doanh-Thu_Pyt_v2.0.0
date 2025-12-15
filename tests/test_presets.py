# tests/test_presets.py
import json
from pathlib import Path
from app import load_presets, save_presets, normalize_presets, PRESET_FILE

def test_load_presets_file_not_exist(tmp_path, monkeypatch):
    monkeypatch.setattr("app.PRESET_FILE", tmp_path / "missing.json")
    assert load_presets() == {}

def test_load_presets_empty_file(tmp_path, monkeypatch):
    p = tmp_path / "empty.json"
    p.write_text("", encoding="utf-8")
    monkeypatch.setattr("app.PRESET_FILE", p)
    assert load_presets() == {}

def test_load_presets_invalid_json(tmp_path, monkeypatch):
    p = tmp_path / "bad.json"
    p.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr("app.PRESET_FILE", p)

    result = load_presets()
    assert result == {}
    assert json.loads(p.read_text()) == {}
    
def test_save_presets(tmp_path, monkeypatch):
    p = tmp_path / "presets.json"
    monkeypatch.setattr("app.PRESET_FILE", p)

    data = {"A": [{"out_name": "X"}]}
    save_presets(data)

    assert json.loads(p.read_text()) == data

def test_normalize_presets():
    presets = {
        "test": [{
            "out_name": "A",
            "mode": "fixed",
            "input_col": "X",
            "fixed_value": "1",
            "formula": ""
        }]
    }

    result = normalize_presets(presets)

    assert result["test"][0]["out_name"] == "A"
    assert "formula" in result["test"][0]