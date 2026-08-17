"""
Pydantic models shared across routers.

Every enum-like server.properties field below uses Literal[...] so an
invalid value (typo, stale docs, hand-edited file) is rejected with a
clear 422 instead of being written straight into server.properties and
silently crashing bedrock_server on its next boot. Valid values are
sourced from Mojang's own server.properties reference.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class FullServerProperties(BaseModel):
    server_name: str = "Dedicated Server"
    level_name: str = "Bedrock level"
    level_seed: str = ""
    gamemode: Literal["survival", "creative", "adventure"] = "survival"
    force_gamemode: bool = False
    difficulty: Literal["peaceful", "easy", "normal", "hard"] = "easy"
    allow_cheats: bool = False
    default_player_permission_level: Literal["visitor", "member", "operator"] = "member"

    server_port: int = Field(19132, ge=1, le=65535)
    server_portv6: int = Field(19133, ge=1, le=65535)
    enable_lan_visibility: bool = True
    online_mode: bool = True
    compression_threshold: int = Field(1, ge=0, le=65535)
    compression_algorithm: Literal["zlib", "snappy"] = "zlib"
    client_inactivity_timeout: int = Field(1073741824, ge=0)

    max_players: int = Field(10, ge=1, le=2000)
    view_distance: int = Field(32, ge=5, le=96)
    tick_distance: int = Field(4, ge=2, le=12)
    player_idle_timeout: int = Field(30, ge=0)
    max_threads: int = Field(8, ge=0)
    client_side_chunk_generation_enabled: bool = True

    server_authoritative_movement: Literal["client-auth", "server-auth", "server-auth-with-rewind"] = "server-auth"
    correct_player_movement: bool = True
    server_authoritative_block_breaking: bool = True
    server_authoritative_sound: bool = True
    player_movement_score_threshold: int = Field(20, ge=0)
    player_movement_distance_threshold: float = Field(0.3, ge=0)
    player_movement_duration_threshold_in_ms: int = Field(500, ge=0)

    texturepack_required: bool = False
    disable_custom_skins: bool = False
    disable_custom_skins_untrusted: bool = False
    disable_persona_skins: bool = False
    disable_client_mods: bool = False
    chat_restriction: Literal["None", "Dropped", "Disabled"] = "None"
    disable_player_interaction: bool = False
    content_log_file_enabled: bool = False
    emit_server_telemetry: bool = False
    allow_list: bool = False


# Maps each FullServerProperties field name to its literal key in
# server.properties. properties_store.py uses this in both directions so
# saving never has to know the mapping is there.
PROPERTY_KEY_MAP: dict[str, str] = {
    "server_name": "server-name",
    "level_name": "level-name",
    "level_seed": "level-seed",
    "gamemode": "gamemode",
    "force_gamemode": "force-gamemode",
    "difficulty": "difficulty",
    "allow_cheats": "allow-cheats",
    "default_player_permission_level": "default-player-permission-level",
    "server_port": "server-port",
    "server_portv6": "server-portv6",
    "enable_lan_visibility": "enable-lan-visibility",
    "online_mode": "online-mode",
    "compression_threshold": "compression-threshold",
    "compression_algorithm": "compression-algorithm",
    "client_inactivity_timeout": "client-inactivity-timeout",
    "max_players": "max-players",
    "view_distance": "view-distance",
    "tick_distance": "tick-distance",
    "player_idle_timeout": "player-idle-timeout",
    "max_threads": "max-threads",
    "client_side_chunk_generation_enabled": "client-side-chunk-generation-enabled",
    "server_authoritative_movement": "server-authoritative-movement",
    "correct_player_movement": "correct-player-movement",
    "server_authoritative_block_breaking": "server-authoritative-block-breaking",
    "server_authoritative_sound": "server-authoritative-sound",
    "player_movement_score_threshold": "player-movement-score-threshold",
    "player_movement_distance_threshold": "player-movement-distance-threshold",
    "player_movement_duration_threshold_in_ms": "player-movement-duration-threshold-in-ms",
    "texturepack_required": "texturepack-required",
    "disable_custom_skins": "disable-custom-skins",
    "disable_custom_skins_untrusted": "disable-custom-skins-untrusted",
    "disable_persona_skins": "disable-persona-skins",
    "disable_client_mods": "disable-client-mods",
    "chat_restriction": "chat-restriction",
    "disable_player_interaction": "disable-player-interaction",
    "content_log_file_enabled": "content-log-file-enabled",
    "emit_server_telemetry": "emit-server-telemetry",
    "allow_list": "allow-list",
}


class AllowlistEntry(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    xuid: Optional[str] = ""
    ignoresPlayerLimit: bool = False


class PermissionEntry(BaseModel):
    xuid: str = Field(..., min_length=1, max_length=32)
    permission: Literal["visitor", "member", "operator"]


class UpdatePayload(BaseModel):
    download_url: str


class SftpPasswordChange(BaseModel):
    """
    Only the password is changeable through the API. The SFTP username is
    fixed at first-boot setup (sftp/users.conf) because it's baked into
    the container's volume mount path in docker-compose.yml — see
    README.md's "Changing the SFTP username" section for how to change it
    manually.
    """
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def no_conf_delimiters(cls, v: str) -> str:
        if ":" in v or "\n" in v or "\r" in v:
            raise ValueError("Password cannot contain ':' or newline characters")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
