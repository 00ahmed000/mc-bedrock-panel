"""
allowlist.json CRUD. Entries are keyed by player name (case-insensitive)
since that's what an admin adds a player by; xuid fills in automatically
once Mojang's own client resolves it (see AllowlistEntry in schemas.py).
"""
import json
import os
from typing import List

from fastapi import APIRouter, HTTPException

from .. import config, fsutil
from ..schemas import AllowlistEntry

router = APIRouter(prefix="/api/allowlist", tags=["allowlist"])

_RELOAD_NOTE = "Restart the server (or run 'allowlist reload' in-game as an operator) to apply changes."


def _read() -> List[dict]:
    if not os.path.exists(config.ALLOWLIST_PATH):
        return []
    with open(config.ALLOWLIST_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    return data if isinstance(data, list) else []


def _write(entries: List[dict]) -> None:
    os.makedirs(os.path.dirname(config.ALLOWLIST_PATH), exist_ok=True)
    tmp_path = config.ALLOWLIST_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    os.replace(tmp_path, config.ALLOWLIST_PATH)
    fsutil.set_bedrock_ownership(config.ALLOWLIST_PATH)


@router.get("")
def list_allowlist():
    return {"entries": _read(), "note": _RELOAD_NOTE}


@router.post("")
def add_allowlist_entry(entry: AllowlistEntry):
    entries = _read()
    if any(e.get("name", "").lower() == entry.name.lower() for e in entries):
        raise HTTPException(status_code=409, detail=f"'{entry.name}' is already on the allowlist")
    entries.append(entry.model_dump())
    _write(entries)
    return {"status": "success", "entries": entries, "note": _RELOAD_NOTE}


@router.delete("/{name}")
def remove_allowlist_entry(name: str):
    entries = _read()
    filtered = [e for e in entries if e.get("name", "").lower() != name.lower()]
    if len(filtered) == len(entries):
        raise HTTPException(status_code=404, detail=f"'{name}' is not on the allowlist")
    _write(filtered)
    return {"status": "success", "entries": filtered, "note": _RELOAD_NOTE}
