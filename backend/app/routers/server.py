"""
Per-server lifecycle control, the interactive console, and the "Update
Server" endpoint. See update_pipeline.py for the actual download/verify/
extract logic, which this and the server-creation wizard both call.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from .. import docker_utils, update_pipeline
from ..docker_utils import ContainerNotFoundError
from ..schemas import ConsoleCommandRequest, UpdatePayload
from ..server_context import ServerContext, get_server_ctx

router = APIRouter(prefix="/api/servers/{server_id}", tags=["server"])


@router.get("/status")
def server_status(ctx: ServerContext = Depends(get_server_ctx)):
    return docker_utils.container_status(ctx.container_name)


@router.post("/start")
def start_server(ctx: ServerContext = Depends(get_server_ctx)):
    try:
        docker_utils.start_container(ctx.container_name)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "success", "message": "Server starting"}


@router.post("/stop")
def stop_server(ctx: ServerContext = Depends(get_server_ctx)):
    try:
        docker_utils.stop_container(ctx.container_name)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "success", "message": "Server stopping"}


@router.post("/restart")
def restart_server(ctx: ServerContext = Depends(get_server_ctx)):
    try:
        docker_utils.restart_container(ctx.container_name)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "success", "message": "Server restarting"}


@router.get("/logs")
def server_logs(tail: int = 200, ctx: ServerContext = Depends(get_server_ctx)):
    try:
        return {"logs": docker_utils.container_logs(ctx.container_name, tail=min(tail, 2000))}
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/console")
def send_console(payload: ConsoleCommandRequest, ctx: ServerContext = Depends(get_server_ctx)):
    command = payload.command.lstrip("/").strip()
    try:
        docker_utils.send_console_command(ctx.container_name, command)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"status": "success", "message": f"Sent: {command}"}


@router.post("/update")
def update_server(payload: UpdatePayload, background_tasks: BackgroundTasks, ctx: ServerContext = Depends(get_server_ctx)):
    url = update_pipeline.resolve_url(payload.version, payload.download_url)
    update_pipeline.validate_url(url)
    background_tasks.add_task(update_pipeline.install, ctx, url, payload.expected_sha256, payload.version)
    return {"status": "success", "message": "Update started in background", "url": url}
