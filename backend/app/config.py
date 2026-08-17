"""
Centralized environment configuration for the Bedrock Panel backend.
Every value below is read once at import time from environment variables
that docker-compose injects from .env. See .env.example at the project
root for the full list with explanations.
"""
import os


def _require(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(
            f"Required environment variable '{name}' is not set. "
            f"Copy .env.example to .env, fill it in, and restart the stack."
        )
    return value


# --- Paths (mounted volumes inside the backend container) ---
BEDROCK_PATH = os.getenv("BEDROCK_PATH", "/bedrock")
BACKUP_PATH = os.getenv("BACKUP_PATH", "/backups")
SFTP_CONFIG_PATH = os.getenv("SFTP_CONFIG_PATH", "/sftp_config")

PROPERTIES_PATH = os.path.join(BEDROCK_PATH, "server.properties")
ALLOWLIST_PATH = os.path.join(BEDROCK_PATH, "allowlist.json")
PERMISSIONS_PATH = os.path.join(BEDROCK_PATH, "permissions.json")
USERS_CONF_PATH = os.path.join(SFTP_CONFIG_PATH, "users.conf")

# --- Shared volume ownership (must match the `minecraft` and `sftp`
# services' UID/GID so all three containers can read/write the same
# files) ---
BEDROCK_UID = int(os.getenv("BEDROCK_UID", "1000"))
BEDROCK_GID = int(os.getenv("BEDROCK_GID", "1000"))

# --- Docker container names (must match docker-compose.yml) ---
MINECRAFT_CONTAINER_NAME = os.getenv("MINECRAFT_CONTAINER_NAME", "bedrock_server")
SFTP_CONTAINER_NAME = os.getenv("SFTP_CONTAINER_NAME", "bedrock_sftp")

# --- SFTP display info (the username itself is set once via
# sftp/users.conf before first boot and is intentionally not
# changeable through the API — see routers/sftp.py) ---
SFTP_PORT = int(os.getenv("SFTP_PORT", "2222"))
SFTP_DEFAULT_USERNAME = os.getenv("SFTP_USERNAME", "admin")

# --- Auth ---
ADMIN_USERNAME = _require("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = _require("ADMIN_PASSWORD")
JWT_SECRET = _require("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))  # 12 hours

# --- Server update security ---
# Mojang has changed the Bedrock download domain before (most recently in
# 2026). If "Update Server" starts rejecting a legitimate download link,
# add the new domain here (or set UPDATE_ALLOWED_DOMAINS in .env) rather
# than removing the check.
_default_domains = "www.minecraft.net,minecraft.net,minecraft.azureedge.net"
UPDATE_ALLOWED_DOMAINS = {
    d.strip().lower()
    for d in os.getenv("UPDATE_ALLOWED_DOMAINS", _default_domains).split(",")
    if d.strip()
}
MAX_UPDATE_DOWNLOAD_MB = int(os.getenv("MAX_UPDATE_DOWNLOAD_MB", "500"))
