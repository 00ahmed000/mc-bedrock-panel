"""
Panel-local cache of the gamerule values the panel has told each
server's console to set — see gamerules_data.py's docstring for why this
is a best-known cache rather than a live read of the server's actual
state (Bedrock has no gamerules file and no query-response console).
"""
import json
import os
from typing import Dict


def read_cache(path: str) -> Dict[str, object]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def write_cache(path: str, values: Dict[str, object]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(values, f, indent=2)
    os.replace(tmp_path, path)


def set_value(path: str, name: str, value: object) -> Dict[str, object]:
    values = read_cache(path)
    values[name] = value
    write_cache(path, values)
    return values
