from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import docker_utils, gamerules_store
from ..docker_utils import ContainerNotFoundError
from ..gamerules_data import KNOWN_GAMERULES, VALID_GAMERULE_NAMES
from ..server_context import ServerContext, get_server_ctx

router = APIRouter(prefix="/api/servers/{server_id}/gamerules", tags=["gamerules"])


class SetGameruleRequest(BaseModel):
    name: str
    value: bool | int


@router.get("")
def list_gamerules(ctx: ServerContext = Depends(get_server_ctx)):
    cache = gamerules_store.read_cache(ctx.gamerules_path)
    rules = [{**rule, "current": cache.get(rule["name"], None)} for rule in KNOWN_GAMERULES]
    return {"rules": rules}


@router.post("")
def set_gamerule(payload: SetGameruleRequest, ctx: ServerContext = Depends(get_server_ctx)):
    if payload.name not in VALID_GAMERULE_NAMES:
        raise HTTPException(status_code=400, detail=f"'{payload.name}' isn't a known Bedrock gamerule")

    command_value = "true" if payload.value is True else "false" if payload.value is False else str(payload.value)
    try:
        docker_utils.send_console_command(ctx.container_name, f"gamerule {payload.name} {command_value}")
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=409, detail=f"{e}. Gamerules can only be sent to a running server."
        )

    values = gamerules_store.set_value(ctx.gamerules_path, payload.name, payload.value)
    return {"status": "success", "values": values}
