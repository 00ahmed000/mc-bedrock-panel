"""
Container-level settings for a server: restart policy and resource
limits, editable straight from the panel. Applying a change recreates
the container (see docker_utils.update_container_settings) — there's no
way to change these on a live container without one.
"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .. import docker_utils
from ..docker_utils import ContainerNotFoundError
from ..server_context import ServerContext, get_server_ctx

router = APIRouter(prefix="/api/servers/{server_id}/settings", tags=["settings"])


class ContainerSettingsUpdate(BaseModel):
    restart_policy: Optional[Literal["no", "always", "unless-stopped", "on-failure"]] = None
    mem_limit: Optional[str] = Field(None, description='e.g. "2g", "512m" \u2014 empty string removes the limit')
    cpu_limit: Optional[str] = Field(None, description='e.g. "1.5" cores \u2014 empty string removes the limit')


@router.get("")
def get_settings(ctx: ServerContext = Depends(get_server_ctx)):
    try:
        settings = docker_utils.get_container_settings(ctx.container_name)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {**settings, "port": ctx.port, "portv6": ctx.portv6}


@router.post("")
def update_settings(payload: ContainerSettingsUpdate, ctx: ServerContext = Depends(get_server_ctx)):
    try:
        docker_utils.update_container_settings(
            ctx.container_name,
            restart_policy=payload.restart_policy,
            mem_limit=payload.mem_limit,
            cpu_limit=payload.cpu_limit,
        )
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "success", "message": "Container settings updated \u2014 the server was briefly recreated to apply them."}
