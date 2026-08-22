from fastapi import APIRouter, Depends

from .. import properties_store
from ..schemas import FullServerProperties
from ..server_context import ServerContext, get_server_ctx

router = APIRouter(prefix="/api/servers/{server_id}/properties", tags=["properties"])


@router.get("", response_model=FullServerProperties)
def read_properties(ctx: ServerContext = Depends(get_server_ctx)):
    return properties_store.get_properties(ctx.properties_path)


@router.post("", response_model=FullServerProperties)
def write_properties(props: FullServerProperties, ctx: ServerContext = Depends(get_server_ctx)):
    properties_store.save_properties(ctx.properties_path, props)
    return properties_store.get_properties(ctx.properties_path)
