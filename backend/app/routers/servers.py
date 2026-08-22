"""
Server instance management. Creating a server allocates a port pair,
makes its subdirectory under the shared SERVERS_ROOT volume, registers
it, starts a fresh container for it, then in the background installs
the chosen version and seeds server.properties with the wizard's
choices — see _bootstrap_new_server.
"""
import logging
import os
import shutil
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from .. import config, docker_utils, fsutil, properties_store, servers_registry, update_pipeline, version_catalog
from ..server_context import ServerContext

logger = logging.getLogger("bedrock_panel")
router = APIRouter(prefix="/api/servers", tags=["servers"])


class CreateServerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=48)
    version: Optional[str] = None  # None = install the latest release
    gamemode: Literal["survival", "creative", "adventure"] = "survival"
    difficulty: Literal["peaceful", "easy", "normal", "hard"] = "easy"
    max_players: int = Field(10, ge=1, le=200)
    level_seed: str = ""
    online_mode: bool = True
    mem_limit: Optional[str] = Field(None, description='e.g. "2g" \u2014 blank uses the .env-wide default')
    cpu_limit: Optional[str] = Field(None, description='e.g. "1.5" \u2014 blank uses the .env-wide default')


@router.get("")
def list_servers():
    servers = []
    for entry in servers_registry.list_servers():
        status = docker_utils.container_status(entry["container_name"])
        servers.append({**entry, "status": status["status"]})
    return {"servers": servers}


def _bootstrap_new_server(entry: dict, payload: CreateServerRequest) -> None:
    ctx = ServerContext(entry)
    version = payload.version or version_catalog.latest_release_version()

    try:
        url = update_pipeline.resolve_url(version, None)
        update_pipeline.validate_url(url)
        update_pipeline.install(ctx, url, None, version, start_after=False)
    except Exception as e:
        logger.warning(f"Auto-install failed for new server '{entry['id']}': {e}")
        return  # left registered so the admin can retry from its Update tab

    props = properties_store.get_properties(ctx.properties_path)
    props.gamemode = payload.gamemode
    props.difficulty = payload.difficulty
    props.max_players = payload.max_players
    props.level_seed = payload.level_seed
    props.online_mode = payload.online_mode
    properties_store.save_properties(ctx.properties_path, props)

    try:
        docker_utils.start_container(ctx.container_name)
    except docker_utils.ContainerNotFoundError as e:
        logger.warning(f"Could not start newly-bootstrapped server '{entry['id']}': {e}")


@router.post("")
def create_server(payload: CreateServerRequest, background_tasks: BackgroundTasks):
    server_id = servers_registry.allocate_server_id(payload.name)
    port, portv6 = servers_registry.allocate_port_pair()
    working_dir = f"{config.SERVERS_ROOT}/{server_id}"

    os.makedirs(working_dir, exist_ok=True)
    fsutil.set_bedrock_ownership(working_dir)
    entry = servers_registry.register(server_id, payload.name, port, portv6)

    try:
        docker_utils.create_minecraft_container(
            server_id, entry["container_name"], port, portv6, mem_limit=payload.mem_limit, cpu_limit=payload.cpu_limit
        )
    except Exception as e:
        servers_registry.unregister(server_id)
        shutil.rmtree(working_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Could not create the server container: {e}")

    background_tasks.add_task(_bootstrap_new_server, entry, payload)
    return {"status": "success", "server": entry}


@router.delete("/{server_id}")
def delete_server(server_id: str, delete_data: bool = False):
    entry = servers_registry.get_server(server_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"No server with id '{server_id}'")

    docker_utils.remove_minecraft_container(entry["container_name"])
    servers_registry.unregister(server_id)

    if delete_data:
        shutil.rmtree(entry["working_dir"], ignore_errors=True)

    return {"status": "success", "message": f"Deleted '{entry['name']}'", "data_deleted": delete_data}
