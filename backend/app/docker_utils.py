"""
Docker SDK helpers: a shared client, container status/lifecycle helpers,
the create/remove/console routines behind multi-server support, and one
shared clone-and-recreate routine used both to apply SFTP credential
changes and to let the panel edit a server container's resource limits
and restart policy after the fact — Discopanel-style.
"""
import docker
from docker.errors import APIError, NotFound

from . import config

_client = None
_volume_name_cache: dict = {}


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


def resolve_volume_name_for_mount(container_name: str, mount_target: str) -> str:
    """
    Look up which volume (or host path) is bound to `mount_target` inside
    `container_name`'s HostConfig, by inspecting the container itself,
    rather than guessing what Compose named the volume (which varies by
    Compose version and project name). Cached — this never changes for a
    running stack.
    """
    if mount_target in _volume_name_cache:
        return _volume_name_cache[mount_target]

    container = _require_container(container_name)
    binds = container.attrs["HostConfig"].get("Binds") or []
    for bind in binds:
        parts = bind.split(":")
        if len(parts) >= 2 and parts[1] == mount_target:
            _volume_name_cache[mount_target] = parts[0]
            return parts[0]
    raise RuntimeError(f"Container '{container_name}' has no bind mount at '{mount_target}'")


def _clone_create_params(container) -> dict:
    """
    Extract create_container()-ready parameters from a running
    container's own resolved attrs (Docker already turned any
    compose-relative paths into absolute host paths, and any shorthand
    port syntax into its full inspect-format, at creation time — so this
    needs no knowledge of the host filesystem layout or how the
    container was originally created).
    """
    attrs = container.attrs
    cfg = attrs["Config"]
    host_cfg = attrs["HostConfig"]
    networks = attrs["NetworkSettings"]["Networks"]

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

    return {
        "image": cfg["Image"],
        "env": cfg.get("Env", []),
        "labels": cfg.get("Labels") or {},
        "working_dir": cfg.get("WorkingDir") or None,
        "user": cfg.get("User") or None,
        "stdin_open": bool(cfg.get("OpenStdin", False)),
        "tty": bool(cfg.get("Tty", False)),
        "binds": host_cfg.get("Binds") or [],
        "restart_policy": host_cfg.get("RestartPolicy") or {"Name": "unless-stopped"},
        "mem_limit": host_cfg.get("Memory") or None,
        "nano_cpus": host_cfg.get("NanoCpus") or None,
        "ports_list": ports_list,
        "port_bindings": port_bindings,
        "network_names": list(networks.keys()),
    }


def _recreate_container(container_name: str, overrides: dict = None) -> None:
    """
    Stop, remove, and recreate `container_name`, cloning everything from
    its current resolved config except whatever's in `overrides`.

    Why recreate at all instead of just restarting: some images (like
    atmoz/sftp) only read their config file on first boot, so a plain
    restart() won't pick up an on-disk change — see
    github.com/atmoz/sftp/issues/34. A full recreate forces a fresh first
    boot. Cloning preserves the `com.docker.compose.*` labels compose
    uses to decide whether a running container still matches its file,
    so a later `docker compose up -d` won't try to recreate it again and
    undo the change.
    """
    client = get_client()
    api = client.api

    old = _require_container(container_name)
    params = _clone_create_params(old)
    if overrides:
        params.update(overrides)

    old.stop(timeout=15)
    old.remove()

    host_config_kwargs = dict(
        binds=params["binds"],
        restart_policy=params["restart_policy"],
        port_bindings=params["port_bindings"],
        network_mode=params["network_names"][0] if params["network_names"] else None,
    )
    if params.get("mem_limit"):
        host_config_kwargs["mem_limit"] = params["mem_limit"]
    if params.get("nano_cpus"):
        host_config_kwargs["nano_cpus"] = params["nano_cpus"]

    host_config = api.create_host_config(**host_config_kwargs)
    created = api.create_container(
        image=params["image"],
        name=container_name,
        environment=params["env"],
        labels=params["labels"],
        working_dir=params["working_dir"],
        user=params["user"],
        stdin_open=params["stdin_open"],
        tty=params["tty"],
        ports=params["ports_list"] or None,
        host_config=host_config,
        detach=True,
    )
    container_id = created["Id"]

    for net_name in params["network_names"][1:]:
        try:
            client.networks.get(net_name).connect(container_id)
        except APIError:
            pass

    api.start(container_id)


def recreate_container_preserving_identity(container_name: str) -> None:
    """Pure clone-and-recreate with no overrides — used after rewriting sftp/users.conf."""
    _recreate_container(container_name)


def get_container_settings(container_name: str) -> dict:
    container = _require_container(container_name)
    host_cfg = container.attrs["HostConfig"]
    mem_bytes = host_cfg.get("Memory") or 0
    nano_cpus = host_cfg.get("NanoCpus") or 0
    return {
        "restart_policy": (host_cfg.get("RestartPolicy") or {}).get("Name", "unless-stopped"),
        "mem_limit": f"{mem_bytes // (1024 * 1024)}m" if mem_bytes else "",
        "cpu_limit": str(round(nano_cpus / 1_000_000_000, 2)) if nano_cpus else "",
    }


def update_container_settings(
    container_name: str,
    restart_policy: str = None,
    mem_limit: str = None,
    cpu_limit: str = None,
) -> None:
    """
    Recreate a server container with new resource limits / restart
    policy, leaving image, mounts, network, ports, user, and working
    directory untouched. Pass an empty string for mem_limit/cpu_limit to
    remove that limit entirely.
    """
    overrides = {}
    if restart_policy:
        overrides["restart_policy"] = {"Name": restart_policy}
    if mem_limit is not None:
        overrides["mem_limit"] = mem_limit or None
    if cpu_limit is not None:
        overrides["nano_cpus"] = int(float(cpu_limit) * 1_000_000_000) if cpu_limit else None
    _recreate_container(container_name, overrides)


def create_minecraft_container(
    server_id: str,
    container_name: str,
    port: int,
    portv6: int,
    mem_limit: str = None,
    cpu_limit: str = None,
) -> None:
    """
    Create and start a new Bedrock server container sharing the same
    SERVERS_ROOT volume every other server (and the backend) uses,
    scoped to its own subdirectory via `working_dir` rather than needing
    its own dedicated volume/mount — see config.py's module docstring for
    why that matters. mem_limit/cpu_limit override the .env-wide
    MC_MEM_LIMIT/MC_CPU_LIMIT defaults for this one server, if given.
    """
    client = get_client()
    api = client.api

    volume_name = resolve_volume_name_for_mount(config.BACKEND_CONTAINER_NAME, config.SERVERS_ROOT)
    effective_mem = mem_limit or config.MC_MEM_LIMIT
    effective_cpu = cpu_limit or config.MC_CPU_LIMIT

    host_config_kwargs = dict(
        binds=[f"{volume_name}:{config.SERVERS_ROOT}"],
        restart_policy={"Name": "unless-stopped"},
        port_bindings={"19132/udp": str(port), "19133/udp": str(portv6)},
        network_mode=config.DOCKER_NETWORK,
    )
    if effective_mem:
        host_config_kwargs["mem_limit"] = effective_mem
    if effective_cpu:
        try:
            host_config_kwargs["nano_cpus"] = int(float(effective_cpu) * 1_000_000_000)
        except ValueError:
            pass

    host_config = api.create_host_config(**host_config_kwargs)
    created = api.create_container(
        image=config.MINECRAFT_IMAGE,
        name=container_name,
        user=f"{config.BEDROCK_UID}:{config.BEDROCK_GID}",
        working_dir=f"{config.SERVERS_ROOT}/{server_id}",
        stdin_open=True,
        tty=False,
        ports=[(19132, "udp"), (19133, "udp")],
        labels={"bedrock-panel.managed": "true", "bedrock-panel.server-id": server_id},
        host_config=host_config,
        detach=True,
    )
    api.start(created["Id"])


def remove_minecraft_container(container_name: str) -> None:
    container = get_container(container_name)
    if container is None:
        return
    try:
        container.stop(timeout=30)
    except APIError:
        pass
    container.remove(force=True)


def send_console_command(container_name: str, command: str) -> None:
    """
    Write a line to a running container's stdin — the same mechanism
    `docker attach` uses. Requires the container to have been created
    with stdin_open=True (every minecraft container this panel creates
    is). docker-py's attach_socket() has returned slightly different
    wrapper objects across versions, so this tries a couple of known
    shapes rather than assuming one.
    """
    container = _require_container(container_name)
    if container.status != "running":
        raise RuntimeError(f"'{container_name}' isn't running, so it can't accept console commands")

    client = get_client()
    payload = (command.strip() + "\n").encode("utf-8")
    sock = client.api.attach_socket(container.id, params={"stdin": 1, "stream": 1})
    try:
        raw = getattr(sock, "_sock", sock)
        if hasattr(raw, "sendall"):
            raw.sendall(payload)
        elif hasattr(sock, "write"):
            sock.write(payload)
        else:
            raise RuntimeError("Could not find a writable handle on the attached console socket")
    finally:
        try:
            sock.close()
        except Exception:
            pass
