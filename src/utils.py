from pathlib import Path
import json

def read_json(file: Path):
    try:
        with file.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def write_json(file: Path, data):
    try:
        with file.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass