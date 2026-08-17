"""
Server lifecycle control plus the "Update Server" pipeline. The update
flow only accepts https:// links from an allowlisted domain
(security.is_allowed_download_url), enforces a size cap while streaming
the download, and extracts the zip through security.safe_extract_zip to
block zip-slip — see docker_utils.py/security.py docstrings for why.
"""
import os
import shutil
import urllib.request
import zipfile

from fastapi import APIRouter, BackgroundTasks, HTTPException

from .. import config, docker_utils, fsutil, security
from ..docker_utils import ContainerNotFoundError
from ..schemas import UpdatePayload

router = APIRouter(prefix="/api/server", tags=["server"])

PROTECTED_ITEMS = {"worlds", "server.properties", "allowlist.json", "permissions.json"}
_TMP_ZIP = "/tmp/bedrock_update.zip"
_TMP_EXTRACT = "/tmp/bedrock_extracted"


@router.get("/status")
def server_status():
    return docker_utils.container_status(config.MINECRAFT_CONTAINER_NAME)


@router.post("/start")
def start_server():
    try:
        docker_utils.start_container(config.MINECRAFT_CONTAINER_NAME)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "success", "message": "Server starting"}


@router.post("/stop")
def stop_server():
    try:
        docker_utils.stop_container(config.MINECRAFT_CONTAINER_NAME)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "success", "message": "Server stopping"}


@router.post("/restart")
def restart_server():
    try:
        docker_utils.restart_container(config.MINECRAFT_CONTAINER_NAME)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "success", "message": "Server restarting"}


@router.get("/logs")
def server_logs(tail: int = 200):
    try:
        return {"logs": docker_utils.container_logs(config.MINECRAFT_CONTAINER_NAME, tail=min(tail, 2000))}
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _download_with_cap(url: str, destination: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "bedrock-panel/1.0"})
    max_bytes = config.MAX_UPDATE_DOWNLOAD_MB * 1024 * 1024
    total = 0
    with urllib.request.urlopen(req, timeout=60) as response, open(destination, "wb") as out_file:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"Download exceeded the {config.MAX_UPDATE_DOWNLOAD_MB} MB limit")
            out_file.write(chunk)


def _process_update(url: str) -> None:
    _download_with_cap(url, _TMP_ZIP)

    if os.path.exists(_TMP_EXTRACT):
        shutil.rmtree(_TMP_EXTRACT)
    with zipfile.ZipFile(_TMP_ZIP, "r") as zip_ref:
        security.safe_extract_zip(zip_ref, _TMP_EXTRACT)

    container = docker_utils.get_container(config.MINECRAFT_CONTAINER_NAME)
    was_running = False
    if container is not None:
        container.reload()
        was_running = container.status == "running"
        if was_running:
            container.stop(timeout=30)

    try:
        for root, _dirs, files in os.walk(_TMP_EXTRACT):
            rel_path = os.path.relpath(root, _TMP_EXTRACT)
            target_dir = config.BEDROCK_PATH if rel_path == "." else os.path.join(config.BEDROCK_PATH, rel_path)
            os.makedirs(target_dir, exist_ok=True)
            for file in files:
                if rel_path == "." and file in PROTECTED_ITEMS:
                    continue
                shutil.copy2(os.path.join(root, file), os.path.join(target_dir, file))

        bedrock_bin = os.path.join(config.BEDROCK_PATH, "bedrock_server")
        if os.path.exists(bedrock_bin):
            os.chmod(bedrock_bin, 0o755)
        fsutil.set_bedrock_ownership(config.BEDROCK_PATH)
    finally:
        if was_running and container is not None:
            container.start()
        if os.path.exists(_TMP_ZIP):
            os.remove(_TMP_ZIP)
        shutil.rmtree(_TMP_EXTRACT, ignore_errors=True)


@router.post("/update")
def update_server(payload: UpdatePayload, background_tasks: BackgroundTasks):
    if not security.is_allowed_download_url(payload.download_url):
        allowed = ", ".join(sorted(config.UPDATE_ALLOWED_DOMAINS))
        raise HTTPException(
            status_code=400,
            detail=(
                f"download_url must be an https:// link from one of: {allowed}. "
                f"If Mojang has moved the download again, add the new domain to "
                f"UPDATE_ALLOWED_DOMAINS in .env."
            ),
        )
    background_tasks.add_task(_process_update, payload.download_url)
    return {"status": "success", "message": "Update started in background"}
