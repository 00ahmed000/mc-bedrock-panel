"""
allowlist.json CRUD, per server. Entries are keyed by player name
(case-insensitive) since that's what an admin adds a player by; xuid
fills in automatically once Mojang's own client resolves it.
"""
import json
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from .. import fsutil
from ..schemas import AllowlistEntry
from ..server_context import ServerContext, get_server_ctx

router = APIRouter(prefix="/api/servers/{server_id}/allowlist", tags=["allowlist"])

_RELOAD_NOTE = "Restart the server (or run 'allowlist reload' in-game/console as an operator) to apply changes."


def _read(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    return data if isinstance(data, list) else []


def _write(path: str, entries: List[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    os.replace(tmp_path, path)
    fsutil.set_bedrock_ownership(path)


@router.get("")
def list_allowlist(ctx: ServerContext = Depends(get_server_ctx)):
    return {"entries": _read(ctx.allowlist_path), "note": _RELOAD_NOTE}


@router.post("")
def add_allowlist_entry(entry: AllowlistEntry, ctx: ServerContext = Depends(get_server_ctx)):
    entries = _read(ctx.allowlist_path)
    if any(e.get("name", "").lower() == entry.name.lower() for e in entries):
        raise HTTPException(status_code=409, detail=f"'{entry.name}' is already on the allowlist")
    entries.append(entry.model_dump())
    _write(ctx.allowlist_path, entries)
    return {"status": "success", "entries": entries, "note": _RELOAD_NOTE}


@router.delete("/{name}")
def remove_allowlist_entry(name: str, ctx: ServerContext = Depends(get_server_ctx)):
    entries = _read(ctx.allowlist_path)
    filtered = [e for e in entries if e.get("name", "").lower() != name.lower()]
    if len(filtered) == len(entries):
        raise HTTPException(status_code=404, detail=f"'{name}' is not on the allowlist")
    _write(ctx.allowlist_path, filtered)
    return {"status": "success", "entries": filtered, "note": _RELOAD_NOTE}
