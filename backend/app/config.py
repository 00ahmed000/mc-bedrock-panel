"""
Centralized environment configuration for the Bedrock Panel backend.
Every value below is read once at import time from environment variables
that docker-compose injects from .env. See .env.example at the project
root for the full list with explanations.

v2 architecture note: the panel now manages an arbitrary number of
Bedrock server instances instead of one fixed one. They all live as
sibling subdirectories of ONE shared named volume mounted at
SERVERS_ROOT ("/servers/<server_id>/..." for each), rather than each
server getting its own Docker volume. This is what lets the backend
create/delete servers on the fly without ever needing to recreate
itself with a new mount — see servers_registry.py and
docker_utils.create_minecraft_container().
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
SERVERS_ROOT = os.getenv("SERVERS_ROOT", "/servers")  # shared across all server instances
BACKUP_PATH = os.getenv("BACKUP_PATH", "/backups")
SFTP_CONFIG_PATH = os.getenv("SFTP_CONFIG_PATH", "/sftp_config")
USERS_CONF_PATH = os.path.join(SFTP_CONFIG_PATH, "users.conf")
REGISTRY_PATH = os.path.join(SERVERS_ROOT, "_registry.json")
TASKS_PATH = os.path.join(SERVERS_ROOT, "_tasks.json")

# --- Shared volume ownership (must match every dynamically-created
# minecraft container's UID/GID, and the sftp service's, so all of them
# can read/write the same files) ---
BEDROCK_UID = int(os.getenv("BEDROCK_UID", "1000"))
BEDROCK_GID = int(os.getenv("BEDROCK_GID", "1000"))

# --- Docker ---
BACKEND_CONTAINER_NAME = os.getenv("BACKEND_CONTAINER_NAME", "bedrock_backend")
SFTP_CONTAINER_NAME = os.getenv("SFTP_CONTAINER_NAME", "bedrock_sftp")
# Built by `docker compose build minecraft` — see docker-compose.yml, this
# service is intentionally profile-gated so plain `up` never starts a
# stray container from it directly; the backend creates real per-server
# containers from this same image on demand.
MINECRAFT_IMAGE = os.getenv("MINECRAFT_IMAGE", "bedrock-panel-minecraft:latest")
DOCKER_NETWORK = os.getenv("DOCKER_NETWORK", "bedrock-panel_internal")
MC_CONTAINER_PREFIX = "bedrock_server_"

# Port range the panel allocates two consecutive ports from (IPv4 + IPv6)
# for each new server it creates.
MULTISERVER_PORT_RANGE_START = int(os.getenv("MULTISERVER_PORT_RANGE_START", "19132"))
MULTISERVER_PORT_RANGE_END = int(os.getenv("MULTISERVER_PORT_RANGE_END", "19332"))

# Optional per-server resource limits, applied to every dynamically
# created minecraft container. Leave blank in .env for "no limit".
MC_MEM_LIMIT = os.getenv("MC_MEM_LIMIT", "").strip() or None
MC_CPU_LIMIT = os.getenv("MC_CPU_LIMIT", "").strip() or None

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
BEDROCK_DOWNLOAD_URL_TEMPLATE = "https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-{version}.zip"
