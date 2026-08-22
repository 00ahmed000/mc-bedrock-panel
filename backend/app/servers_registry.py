"""
Registry of every Bedrock server instance the panel manages. Each entry
tracks just enough to find and operate on that server: its container
name, its working directory inside the shared SERVERS_ROOT volume, its
published ports, and its last-known installed version.

The registry file itself lives inside SERVERS_ROOT (the same shared
volume every server's files live in), so it survives a backend container
recreation/rebuild with zero extra plumbing — no separate volume needed
just for this.
"""
import json
import os
import re
import time
from typing import Dict, List, Optional

from . import config

_SLUG_RE = re.compile(r"[^a-z0-9-]+")
_lock_free = True  # single-process backend (see docker-compose.yml note on why workers=1)


def slugify(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.strip().lower()).strip("-")
    return slug or "server"


def _load() -> Dict[str, dict]:
    if not os.path.exists(config.REGISTRY_PATH):
        return {}
    with open(config.REGISTRY_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data: Dict[str, dict]) -> None:
    os.makedirs(config.SERVERS_ROOT, exist_ok=True)
    tmp_path = config.REGISTRY_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, config.REGISTRY_PATH)


def list_servers() -> List[dict]:
    return sorted(_load().values(), key=lambda s: s["created_at"])


def get_server(server_id: str) -> Optional[dict]:
    return _load().get(server_id)


def allocate_server_id(name: str) -> str:
    """Turn a display name into a unique, filesystem/container-name-safe id."""
    registry = _load()
    base_slug = slugify(name)
    slug = base_slug
    n = 2
    while slug in registry:
        slug = f"{base_slug}-{n}"
        n += 1
    return slug


def _used_ports(registry: Dict[str, dict]) -> set:
    ports = set()
    for entry in registry.values():
        ports.add(entry["port"])
        ports.add(entry["portv6"])
    return ports


def allocate_port_pair() -> tuple[int, int]:
    used = _used_ports(_load())
    port = config.MULTISERVER_PORT_RANGE_START
    while port + 1 <= config.MULTISERVER_PORT_RANGE_END:
        if port not in used and (port + 1) not in used:
            return port, port + 1
        port += 2
    raise RuntimeError(
        f"No free port pairs left between {config.MULTISERVER_PORT_RANGE_START} and "
        f"{config.MULTISERVER_PORT_RANGE_END} — widen MULTISERVER_PORT_RANGE_END in .env."
    )


def register(server_id: str, name: str, port: int, portv6: int) -> dict:
    registry = _load()
    entry = {
        "id": server_id,
        "name": name,
        "container_name": f"{config.MC_CONTAINER_PREFIX}{server_id}",
        "working_dir": f"{config.SERVERS_ROOT}/{server_id}",
        "port": port,
        "portv6": portv6,
        "installed_version": None,
        "created_at": int(time.time()),
    }
    registry[server_id] = entry
    _save(registry)
    return entry


def unregister(server_id: str) -> None:
    registry = _load()
    registry.pop(server_id, None)
    _save(registry)


def set_installed_version(server_id: str, version: Optional[str]) -> None:
    registry = _load()
    if server_id in registry:
        registry[server_id]["installed_version"] = version
        _save(registry)
