"""
SFTP credential management. Only the password is changeable here — see
schemas.SftpPasswordChange for why the username is fixed at first-boot
setup. Rewriting users.conf and calling recreate_container_preserving_
identity() together are what make a password change actually take
effect; see docker_utils.py's docstring for the full explanation.
"""
import os

from docker.errors import APIError
from fastapi import APIRouter, HTTPException

from .. import config, docker_utils
from ..docker_utils import ContainerNotFoundError
from ..schemas import SftpPasswordChange

router = APIRouter(prefix="/api/sftp", tags=["sftp"])


def _read_current_username() -> str:
    if os.path.exists(config.USERS_CONF_PATH):
        with open(config.USERS_CONF_PATH, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if first_line:
            return first_line.split(":", 1)[0]
    return config.SFTP_DEFAULT_USERNAME


@router.get("/info")
def sftp_info():
    status = docker_utils.container_status(config.SFTP_CONTAINER_NAME)
    return {
        "running": status["status"] == "running",
        "port": config.SFTP_PORT,
        "username": _read_current_username(),
    }


@router.post("/configure")
def configure_sftp(payload: SftpPasswordChange):
    username = _read_current_username()

    try:
        os.makedirs(os.path.dirname(config.USERS_CONF_PATH), exist_ok=True)
        with open(config.USERS_CONF_PATH, "w", encoding="utf-8") as f:
            f.write(f"{username}:{payload.password}:{config.BEDROCK_UID}:{config.BEDROCK_GID}\n")
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Could not write SFTP config: {e}")

    try:
        docker_utils.recreate_container_preserving_identity(config.SFTP_CONTAINER_NAME)
    except ContainerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker error while recreating the SFTP container: {e}")

    return {"status": "success", "message": f"SFTP password updated for '{username}'."}
