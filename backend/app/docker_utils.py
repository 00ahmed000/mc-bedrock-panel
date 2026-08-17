"""
Docker SDK helpers: a shared client, container status/lifecycle helpers,
and the clone-and-recreate routine used to apply SFTP credential changes
without drifting from what `docker compose up -d` expects on the next run.
"""
import docker
from docker.errors import APIError, NotFound

_client = None


class ContainerNotFoundError(Exception):
    """Raised when a helper is asked to act on a container that doesn't exist."""


def get_client() -> docker.DockerClient:
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client


def get_container(name: str):
    """Return the container, or None if it doesn't exist. Never raises for a missing container."""
    try:
        return get_client().containers.get(name)
    except NotFound:
        return None


def _require_container(name: str):
    container = get_container(name)
    if container is None:
        raise ContainerNotFoundError(
            f"Container '{name}' was not found. Is the stack running (docker compose up -d)?"
        )
    return container


def container_status(name: str) -> dict:
    container = get_container(name)
    if container is None:
        return {"exists": False, "status": "not_found", "health": None, "started_at": None}
    container.reload()
    health_info = container.attrs.get("State", {}).get("Health")
    return {
        "exists": True,
        "status": container.status,  # running, exited, paused, restarting, created, ...
        "health": health_info.get("Status") if health_info else None,
        "started_at": container.attrs.get("State", {}).get("StartedAt"),
    }


def start_container(name: str) -> None:
    _require_container(name).start()


def stop_container(name: str) -> None:
    _require_container(name).stop(timeout=30)


def restart_container(name: str) -> None:
    _require_container(name).restart(timeout=30)


def container_logs(name: str, tail: int = 200) -> str:
    raw = _require_container(name).logs(tail=tail, timestamps=True)
    return raw.decode("utf-8", errors="replace")


def recreate_container_preserving_identity(container_name: str) -> None:
    """
    Stop, remove, and recreate `container_name` using the exact image,
    environment, labels, restart policy, port bindings, network(s), and
    bind mounts docker-compose originally gave it.

    Why this exists: some images (atmoz/sftp among them) only read their
    config file at first boot, so a plain `restart()` won't pick up an
    on-disk config change like a rewritten users.conf — see
    github.com/atmoz/sftp/issues/34. A full recreate forces a fresh first
    boot so the new credentials actually take effect.

    Because we clone the running container's own resolved attrs (Docker
    already turned any compose-relative paths into absolute host paths at
    creation time) instead of re-deriving them ourselves, this needs no
    knowledge of the host filesystem layout, and it preserves the
    `com.docker.compose.*` labels compose uses to decide whether a running
    container still matches its file — so a later `docker compose up -d`
    will NOT try to recreate this container again and undo the change.
    """
    client = get_client()
    api = client.api

    old = _require_container(container_name)
    attrs = old.attrs
    cfg = attrs["Config"]
    host_cfg = attrs["HostConfig"]
    networks = attrs["NetworkSettings"]["Networks"]

    image = cfg["Image"]
    env = cfg.get("Env", [])
    labels = cfg.get("Labels") or {}
    binds = host_cfg.get("Binds") or []
    restart_policy = host_cfg.get("RestartPolicy") or {"Name": "always"}

    # Reshape Docker's inspect-format port bindings ({"22/tcp": [{"HostIp":
    # "", "HostPort": "2222"}]}) into what create_container()/
    # create_host_config() expect ("ports" as a list of (port, proto)
    # tuples, "port_bindings" as {"22/tcp": "2222"} or a list of those).
    raw_ports = host_cfg.get("PortBindings") or {}
    port_bindings = {}
    ports_list = []
    for container_port, host_entries in raw_ports.items():
        port_num, proto = container_port.split("/")
        ports_list.append((int(port_num), proto))
        if not host_entries:
            continue
        mapped = []
        for entry in host_entries:
            host_ip = entry.get("HostIp") or ""
            host_port = entry.get("HostPort")
            mapped.append((host_ip, host_port) if host_ip else host_port)
        port_bindings[container_port] = mapped if len(mapped) > 1 else mapped[0]

    network_names = list(networks.keys())
    primary_network = network_names[0] if network_names else None

    old.stop(timeout=15)
    old.remove()

    host_config = api.create_host_config(
        binds=binds,
        restart_policy=restart_policy,
        port_bindings=port_bindings,
        network_mode=primary_network,
    )
    created = api.create_container(
        image=image,
        name=container_name,
        environment=env,
        labels=labels,
        ports=ports_list or None,
        host_config=host_config,
        detach=True,
    )
    container_id = created["Id"]

    # Attach any additional networks beyond the primary one set above.
    for net_name in network_names[1:]:
        try:
            client.networks.get(net_name).connect(container_id)
        except APIError:
            pass

    api.start(container_id)
