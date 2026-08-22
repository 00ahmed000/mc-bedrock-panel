"""
Backup lifecycle, per server. Every route that takes a filename runs it
through security.validate_backup_filename() first, which allowlists the
exact shape create_backup() generates and rejects anything else outright.
Filenames are prefixed with the server id so BACKUP_PATH can hold every
server's backups together without collisions, and listing/restore are
scoped to the requesting server's own files by that same prefix.
"""
import os
import tarfile
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from .. import config, docker_utils, fsutil, security
from ..server_context import ServerContext, get_server_ctx

router = APIRouter(prefix="/api/servers/{server_id}/backups", tags=["backups"])

BACKUP_TARGETS = ["worlds", "server.properties", "allowlist.json", "permissions.json"]


def _perform_backup(working_dir: str, destination: str) -> None:
    with tarfile.open(destination, "w:gz") as tar:
        for item in BACKUP_TARGETS:
            item_path = os.path.join(working_dir, item)
            if os.path.exists(item_path):
                tar.add(item_path, arcname=item)


@router.post("/create")
def create_backup(background_tasks: BackgroundTasks, ctx: ServerContext = Depends(get_server_ctx)):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backup_{ctx.id}_{timestamp}.tar.gz"
    destination = os.path.join(config.BACKUP_PATH, filename)
    background_tasks.add_task(_perform_backup, ctx.working_dir, destination)
    return {"status": "success", "message": "Backup started", "file": filename}


@router.get("")
def list_backups(ctx: ServerContext = Depends(get_server_ctx)):
    backups = []
    prefix = f"backup_{ctx.id}_"
    if os.path.isdir(config.BACKUP_PATH):
        for file in os.listdir(config.BACKUP_PATH):
            if not (file.startswith(prefix) and file.endswith(".tar.gz")):
                continue
            full_path = os.path.join(config.BACKUP_PATH, file)
            stats = os.stat(full_path)
            backups.append(
                {
                    "filename": file,
                    "size_mb": round(stats.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    return {"backups": sorted(backups, key=lambda x: x["created_at"], reverse=True)}


def _resolve_backup_path(server_id: str, filename: str) -> str:
    try:
        safe_name = security.validate_backup_filename(filename)
    except security.UnsafePathError:
        raise HTTPException(status_code=400, detail="Invalid backup filename")
    if not safe_name.startswith(f"backup_{server_id}_"):
        raise HTTPException(status_code=404, detail="Backup not found")
    try:
        return security.safe_join(config.BACKUP_PATH, safe_name)
    except security.UnsafePathError:
        raise HTTPException(status_code=400, detail="Invalid backup filename")


@router.get("/{filename}/download")
def download_backup(filename: str, ctx: ServerContext = Depends(get_server_ctx)):
    full_path = _resolve_backup_path(ctx.id, filename)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(full_path, filename=os.path.basename(full_path), media_type="application/gzip")


@router.delete("/{filename}")
def delete_backup(filename: str, ctx: ServerContext = Depends(get_server_ctx)):
    full_path = _resolve_backup_path(ctx.id, filename)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    os.remove(full_path)
    return {"status": "success", "message": f"Deleted {os.path.basename(full_path)}"}


@router.post("/restore/{filename}")
def restore_backup(filename: str, ctx: ServerContext = Depends(get_server_ctx)):
    full_path = _resolve_backup_path(ctx.id, filename)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    container = docker_utils.get_container(ctx.container_name)
    was_running = False
    if container is not None:
        container.reload()
        was_running = container.status == "running"
        if was_running:
            container.stop(timeout=30)

    try:
        with tarfile.open(full_path, "r:gz") as tar:
            security.safe_extract_tar(tar, ctx.working_dir)
        fsutil.set_bedrock_ownership(ctx.working_dir)
    finally:
        if was_running and container is not None:
            container.start()

    return {
        "status": "success",
        "message": f"Restored {os.path.basename(full_path)}",
        "server_restarted": was_running,
    }
