"""
Shared "fetch a Bedrock server build and install it into a server's
working directory" pipeline, used by both the Update tab
(routers/server.py) and the server-creation wizard's auto-install step
(routers/servers.py), so there's exactly one implementation of the
download/verify/extract/ownership-repair sequence.
"""
import hashlib
import os
import shutil
import urllib.request
import zipfile
from typing import Optional

from fastapi import HTTPException

from . import config, docker_utils, fsutil, security, servers_registry
from .server_context import ServerContext

PROTECTED_ITEMS = {"worlds", "server.properties", "allowlist.json", "permissions.json", "_panel_gamerules.json"}


def resolve_url(version: Optional[str], download_url: Optional[str]) -> str:
    if download_url:
        return download_url
    if version:
        return config.BEDROCK_DOWNLOAD_URL_TEMPLATE.format(version=version)
    raise HTTPException(status_code=400, detail="Provide either 'version' or 'download_url'")


def validate_url(url: str) -> None:
    if not security.is_allowed_download_url(url):
        allowed = ", ".join(sorted(config.UPDATE_ALLOWED_DOMAINS))
        raise HTTPException(
            status_code=400,
            detail=(
                f"The resulting download URL isn't from an allowed domain ({allowed}). "
                f"If Mojang has moved the download again, add the new domain to UPDATE_ALLOWED_DOMAINS in .env."
            ),
        )


def _download_with_cap(url: str, destination: str) -> str:
    """Downloads to `destination`, enforcing the size cap, and returns the sha256 hex digest."""
    req = urllib.request.Request(url, headers={"User-Agent": "bedrock-panel/1.0"})
    max_bytes = config.MAX_UPDATE_DOWNLOAD_MB * 1024 * 1024
    hasher = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(req, timeout=60) as response, open(destination, "wb") as out_file:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"Download exceeded the {config.MAX_UPDATE_DOWNLOAD_MB} MB limit")
            hasher.update(chunk)
            out_file.write(chunk)
    return hasher.hexdigest()


def install(
    ctx: ServerContext,
    url: str,
    expected_sha256: Optional[str],
    version: Optional[str],
    start_after: Optional[bool] = None,
) -> None:
    """
    Download, verify, and extract a server build into ctx.working_dir.

    `start_after` controls whether the container is (re)started once
    installation finishes:
      - None (default): restart it only if it was already running before
        this call — the normal "Update" behavior.
      - True/False: force that outcome regardless of prior state — used
        by server creation, where the container exists but has never
        been started yet.
    """
    tmp_zip = f"/tmp/bedrock_update_{ctx.id}.zip"
    tmp_extract = f"/tmp/bedrock_extracted_{ctx.id}"

    digest = _download_with_cap(url, tmp_zip)
    if expected_sha256 and digest.lower() != expected_sha256.lower():
        os.remove(tmp_zip)
        raise ValueError(f"SHA256 mismatch: expected {expected_sha256}, got {digest}. Download discarded.")

    if os.path.exists(tmp_extract):
        shutil.rmtree(tmp_extract)
    with zipfile.ZipFile(tmp_zip, "r") as zip_ref:
        security.safe_extract_zip(zip_ref, tmp_extract)

    container = docker_utils.get_container(ctx.container_name)
    was_running = False
    if container is not None:
        container.reload()
        was_running = container.status == "running"
        if was_running:
            container.stop(timeout=30)

    try:
        for root, _dirs, files in os.walk(tmp_extract):
            rel_path = os.path.relpath(root, tmp_extract)
            target_dir = ctx.working_dir if rel_path == "." else os.path.join(ctx.working_dir, rel_path)
            os.makedirs(target_dir, exist_ok=True)
            for file in files:
                if rel_path == "." and file in PROTECTED_ITEMS:
                    continue
                shutil.copy2(os.path.join(root, file), os.path.join(target_dir, file))

        bedrock_bin = os.path.join(ctx.working_dir, "bedrock_server")
        if os.path.exists(bedrock_bin):
            os.chmod(bedrock_bin, 0o755)
        fsutil.set_bedrock_ownership(ctx.working_dir)
        servers_registry.set_installed_version(ctx.id, version)
    finally:
        should_start = was_running if start_after is None else start_after
        if should_start and container is not None:
            container.start()
        if os.path.exists(tmp_zip):
            os.remove(tmp_zip)
        shutil.rmtree(tmp_extract, ignore_errors=True)
