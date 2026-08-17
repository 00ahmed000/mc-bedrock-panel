"""
permissions.json CRUD. Entries are keyed by xuid (that's all this file
stores — no player name), matching Mojang's own format.
"""
import json
import os
from typing import List

from fastapi import APIRouter, HTTPException

from .. import config, fsutil
from ..schemas import PermissionEntry

router = APIRouter(prefix="/api/permissions", tags=["permissions"])

_RELOAD_NOTE = "Restart the server (or run 'permission reload' in-game as an operator) to apply changes."


def _read() -> List[dict]:
    if not os.path.exists(config.PERMISSIONS_PATH):
        return []
    with open(config.PERMISSIONS_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    return data if isinstance(data, list) else []


def _write(entries: List[dict]) -> None:
    os.makedirs(os.path.dirname(config.PERMISSIONS_PATH), exist_ok=True)
    tmp_path = config.PERMISSIONS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    os.replace(tmp_path, config.PERMISSIONS_PATH)
    fsutil.set_bedrock_ownership(config.PERMISSIONS_PATH)


@router.get("")
def list_permissions():
    return {"entries": _read(), "note": _RELOAD_NOTE}


@router.post("")
def set_permission(entry: PermissionEntry):
    entries = _read()
    filtered = [e for e in entries if e.get("xuid") != entry.xuid]
    filtered.append(entry.model_dump())
    _write(filtered)
    return {"status": "success", "entries": filtered, "note": _RELOAD_NOTE}


@router.delete("/{xuid}")
def remove_permission(xuid: str):
    entries = _read()
    filtered = [e for e in entries if e.get("xuid") != xuid]
    if len(filtered) == len(entries):
        raise HTTPException(status_code=404, detail=f"No permission entry for xuid '{xuid}'")
    _write(filtered)
    return {"status": "success", "entries": filtered, "note": _RELOAD_NOTE}
