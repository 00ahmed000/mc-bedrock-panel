"""
Shared FastAPI dependency for every /api/servers/{server_id}/... route:
resolves the path parameter against the registry and 404s early with a
clear message, so individual routers never have to duplicate that check.
"""
import os

from fastapi import HTTPException

from . import servers_registry


class ServerContext:
    __slots__ = ("id", "name", "container_name", "working_dir", "port", "portv6", "installed_version")

    def __init__(self, entry: dict):
        self.id = entry["id"]
        self.name = entry["name"]
        self.container_name = entry["container_name"]
        self.working_dir = entry["working_dir"]
        self.port = entry["port"]
        self.portv6 = entry["portv6"]
        self.installed_version = entry.get("installed_version")

    @property
    def properties_path(self) -> str:
        return os.path.join(self.working_dir, "server.properties")

    @property
    def allowlist_path(self) -> str:
        return os.path.join(self.working_dir, "allowlist.json")

    @property
    def permissions_path(self) -> str:
        return os.path.join(self.working_dir, "permissions.json")

    @property
    def gamerules_path(self) -> str:
        return os.path.join(self.working_dir, "_panel_gamerules.json")


def get_server_ctx(server_id: str) -> ServerContext:
    entry = servers_registry.get_server(server_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"No server with id '{server_id}'")
    return ServerContext(entry)
