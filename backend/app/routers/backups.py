"""
Backup lifecycle. Every route that takes a filename runs it through
security.validate_backup_filename() first, which allowlists the exact
shape create_backup() generates and rejects anything else outright —
this is what closes the path-traversal hole in the original endpoint.
"""
import os
import tarfile
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from .. import config, docker_utils, fsutil, security

router = APIRouter(prefix="/api/backups", tags=["backups"])

BACKUP_TARGETS = ["worlds", "server.properties", "allowlist.json", "permissions.json"]


def _perform_backup(destination: str) -> None:
    with tarfile.open(destination, "w:gz") as tar:
        for item in BACKUP_TARGETS:
            item_path = os.path.join(config.BEDROCK_PATH, item)
            if os.path.exists(item_path):
                tar.add(item_path, arcname=item)


@router.post("/create")
def create_backup(background_tasks: BackgroundTasks):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backup_{timestamp}.tar.gz"
    destination = os.path.join(config.BACKUP_PATH, filename)
    background_tasks.add_task(_perform_backup, destination)
    return {"status": "success", "message": "Backup started", "file": filename}


@router.get("")
def list_backups():
    backups = []
    if os.path.isdir(config.BACKUP_PATH):
        for file in os.listdir(config.BACKUP_PATH):
            if not file.endswith(".tar.gz"):
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


def _resolve_backup_path(filename: str) -> str:
    try:
        safe_name = security.validate_backup_filename(filename)
        return security.safe_join(config.BACKUP_PATH, safe_name)
    except security.UnsafePathError:
        raise HTTPException(status_code=400, detail="Invalid backup filename")


@router.get("/{filename}/download")
def download_backup(filename: str):
    full_path = _resolve_backup_path(filename)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(full_path, filename=os.path.basename(full_path), media_type="application/gzip")


@router.delete("/{filename}")
def delete_backup(filename: str):
    full_path = _resolve_backup_path(filename)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    os.remove(full_path)
    return {"status": "success", "message": f"Deleted {os.path.basename(full_path)}"}


@router.post("/restore/{filename}")
def restore_backup(filename: str):
    full_path = _resolve_backup_path(filename)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    container = docker_utils.get_container(config.MINECRAFT_CONTAINER_NAME)
    was_running = False
    if container is not None:
        container.reload()
        was_running = container.status == "running"
        if was_running:
            container.stop(timeout=30)

    try:
        with tarfile.open(full_path, "r:gz") as tar:
            security.safe_extract_tar(tar, config.BEDROCK_PATH)
        fsutil.set_bedrock_ownership(config.BEDROCK_PATH)
    finally:
        if was_running and container is not None:
            container.start()

    return {
        "status": "success",
        "message": f"Restored {os.path.basename(full_path)}",
        "server_restarted": was_running,
    }
