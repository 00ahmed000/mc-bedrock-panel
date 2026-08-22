"""permissions.json CRUD, per server. Entries are keyed by xuid, matching Mojang's own format."""
import json
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from .. import fsutil
from ..schemas import PermissionEntry
from ..server_context import ServerContext, get_server_ctx

router = APIRouter(prefix="/api/servers/{server_id}/permissions", tags=["permissions"])

_RELOAD_NOTE = "Restart the server (or run 'permission reload' in-game/console as an operator) to apply changes."


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
def list_permissions(ctx: ServerContext = Depends(get_server_ctx)):
    return {"entries": _read(ctx.permissions_path), "note": _RELOAD_NOTE}


@router.post("")
def set_permission(entry: PermissionEntry, ctx: ServerContext = Depends(get_server_ctx)):
    entries = _read(ctx.permissions_path)
    filtered = [e for e in entries if e.get("xuid") != entry.xuid]
    filtered.append(entry.model_dump())
    _write(ctx.permissions_path, filtered)
    return {"status": "success", "entries": filtered, "note": _RELOAD_NOTE}


@router.delete("/{xuid}")
def remove_permission(xuid: str, ctx: ServerContext = Depends(get_server_ctx)):
    entries = _read(ctx.permissions_path)
    filtered = [e for e in entries if e.get("xuid") != xuid]
    if len(filtered) == len(entries):
        raise HTTPException(status_code=404, detail=f"No permission entry for xuid '{xuid}'")
    _write(ctx.permissions_path, filtered)
    return {"status": "success", "entries": filtered, "note": _RELOAD_NOTE}
