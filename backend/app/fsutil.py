"""
Small filesystem helper for keeping the shared /bedrock volume's
ownership consistent across three containers that touch it: the
backend (runs as root), and the minecraft + sftp containers (which
both run as BEDROCK_UID:BEDROCK_GID, see docker-compose.yml).

Without this, any file the backend writes (server.properties,
allowlist.json, permissions.json, a restored backup, an updated server
binary) would be root-owned, and the non-root minecraft process
wouldn't be able to write to it — e.g. it auto-fills a connecting
player's xuid into allowlist.json, which silently fails if the file
isn't writable by BEDROCK_UID.
"""
import logging
import os

from . import config

logger = logging.getLogger("bedrock_panel")


def set_bedrock_ownership(path: str) -> None:
    """
    Recursively chown `path` (file or directory) to BEDROCK_UID:BEDROCK_GID.
    Only callable from the backend container, which runs as root and can
    always chown. Errors are logged, not raised — ownership drift is a
    permissions inconvenience to flag, not a reason to fail the request
    that triggered it.
    """
    try:
        if os.path.isfile(path):
            os.chown(path, config.BEDROCK_UID, config.BEDROCK_GID)
            return
        for root, _dirs, files in os.walk(path):
            try:
                os.chown(root, config.BEDROCK_UID, config.BEDROCK_GID)
            except OSError:
                continue
            for name in files:
                try:
                    os.chown(os.path.join(root, name), config.BEDROCK_UID, config.BEDROCK_GID)
                except OSError:
                    continue
    except OSError as e:
        logger.warning(f"Could not set ownership on '{path}': {e}")
