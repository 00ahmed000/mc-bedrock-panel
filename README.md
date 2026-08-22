#**Warrning: make by AI**


# Bedrock Panel

A self-hosted control panel for Minecraft Bedrock Dedicated Servers, built
because the generic panels (Pterodactyl, Crafty, AMP) don't expose every
`server.properties` field, `allowlist.json`/`permissions.json`, gamerules,
a real console, backups, in-place updates, or multi-server management in
one place.

**Stack:** FastAPI (Python) + Vue 3/Vite/Tailwind + nginx + Docker Compose.
The backend mounts the Docker socket and creates/controls Bedrock server
containers directly — there's no separate orchestrator.

---

## 1. First-time setup

```bash
cp .env.example .env
cp sftp/users.conf.example sftp/users.conf
```

Edit both:

- **`.env`** — set `ADMIN_USERNAME`/`ADMIN_PASSWORD` (panel login) and
  `JWT_SECRET` (`openssl rand -hex 32`). Set `TZ` to your timezone if
  you plan to use scheduled tasks. Everything else has a sane default.
- **`sftp/users.conf`** — change the password on the `admin:...` line.
  The username must match `SFTP_USERNAME` in `.env`.

Build the image every server instance is created from, then start the
stack:

```bash
docker compose build minecraft
docker compose up -d --build
```

Open `http://<your-server-ip>:${PANEL_PORT:-80}`, log in, and go to
**Servers → Create a server**. Give it a name — the panel allocates it a
port pair automatically. Then open its **Update** tab, enter a version
number (e.g. `1.21.90.4` — check
[minecraft.net/download/server/bedrock](https://www.minecraft.net/en-us/download/server/bedrock)
for the current one), and run the update once to install the server
binary and world files.

---

## 2. Navigation

The panel is a real multi-page app (Vue Router, not tab-swapping) —
every page has its own URL, refreshes cleanly, and is bookmarkable:
`/servers`, `/servers/<id>/dashboard`, `/servers/<id>/properties`, etc.
Pick a server in the sidebar and its own set of pages (Dashboard,
Properties, Gamerules, Backups, Update, Allowlist, Permissions,
Container) appears underneath it, Discord/Discopanel-style.

## 3. What's in the panel

| Tab | Scope | What it does |
|---|---|---|
| Servers | panel-wide | Create servers with a proper wizard (version, gamemode, difficulty, max players, seed, online-mode, resource limits) and a live version picker; list/delete existing ones |
| Dashboard | per-server | Start/stop/restart, live status, log tail, **interactive console** |
| Properties | per-server | Every `server.properties` field, grouped and validated |
| Gamerules | per-server | Toggle Bedrock's ~30 known gamerules, sent live via the console |
| Backups | per-server | Create/list/download/restore/delete `.tar.gz` snapshots |
| Update | per-server | Pick a version from a live-fetched list (or type one, or paste a direct link), with optional SHA256 verification |
| Allowlist | per-server | Add/remove players (`allowlist.json`) |
| Permissions | per-server | Set operator/member/visitor by XUID (`permissions.json`) |
| Container | per-server | Restart policy and memory/CPU limits, applied straight to that server's Docker container |
| Tasks | panel-wide | Schedule recurring backups/restarts, per server |
| SFTP | panel-wide | One account, connection info + password rotation, browses every server under `servers/<id>/` |

Properties/allowlist/permissions edits are written to disk and need a
restart (or the matching in-game `reload` command) to take effect — the
UI reminds you each time you save. Gamerules and console commands take
effect immediately since they go straight to the running server.

### The console

Sends whatever you type straight to the server's stdin — the same
channel `/gamerule`, `say`, `kick`, `op`, etc. all go through. No leading
slash needed. Only works while the server is running.

### Gamerules

Bedrock has no gamerules file and no query-response command, so there's
no way to reliably *read back* a live value — the panel shows the last
value **it** told the server to set, not necessarily the true live state
if someone changed a rule directly in-game. The UI is upfront about this
rather than pretending otherwise.

### Choosing a version

The version list combines Mojang's own official "current release /
current preview" API with the community-maintained
[Bedrock-OSS/BDS-Versions](https://github.com/Bedrock-OSS/BDS-Versions)
history archive, cached for an hour. If both sources are ever
unreachable, you can still type a version number by hand or paste a
direct download link — the picker is a convenience layered on top of the
same `version`/`download_url` fields, not a hard requirement.

### What didn't make it in, and why

A couple of things from other panels are genuinely Java-Edition-specific
and don't translate to Bedrock's raw-UDP (RakNet) protocol, so they're
not here: hostname-based "smart proxy" routing (Bedrock clients connect
by IP:port directly — there's no SNI/hostname layer to route on) and
CurseForge modpack installs (Bedrock doesn't have a Java-style mod
ecosystem; it has behavior/resource packs instead, which aren't wired
into this panel yet). Auto-idle-stop (spin a server down when nobody's
connected) is a reasonable future addition but isn't in this pass.

---

## 4. Multi-server architecture

Every server the panel creates is a real, independent container, but
they all share one Docker volume (`servers_data`), each scoped to its
own `servers/<server-id>/` subdirectory rather than getting a dedicated
volume. This is what lets you create a new server from the UI without
ever having to restart the panel itself.

```
                    ┌────────────────┐
  Internet ───────▶ │  nginx (80)    │  static Vue build + reverse proxy
                    └───────┬────────┘
                            │ /api/*
                    ┌───────▼────────┐        ┌──────────────────┐
                    │ backend (8000) │───────▶│ docker.sock      │
                    │ FastAPI + JWT  │        │ (creates/controls│
                    │ + scheduler    │        │  every container │
                    └───────┬────────┘        │  below)          │
                            │                  └──────────────────┘
       ┌───────────┬────────┴────────┬───────────┐
       ▼           ▼                 ▼           ▼
  ┌─────────┐ ┌─────────┐      ┌─────────┐  ┌──────────┐
  │ server  │ │ server  │ ...  │ sftp    │  │ (more    │
  │ "surv"  │ │ "creat" │      │         │  │ servers) │
  └─────────┘ └─────────┘      └─────────┘  └──────────┘
       └───────────┴──── servers_data volume ───┘
             servers/surv/, servers/creat/, ...

  Second volume: backups_data (every server's .tar.gz snapshots)
```

`minecraft` is built once (`docker compose build minecraft`) but is
intentionally **not** started by `docker compose up` — it's tagged
`bedrock-panel-minecraft:latest` and the backend creates a real,
individually-named container from that image for every server you
create, each with its own published port pair and `working_dir` (so one
image safely serves any number of servers).

Rotating the SFTP password does more than rewrite `users.conf`:
atmoz/sftp only reads that file on a container's first boot, so a plain
restart wouldn't apply a change. The backend instead clones the running
container's own resolved config (image, env, labels, mounts, network)
and recreates it — see `recreate_container_preserving_identity()` in
`backend/app/docker_utils.py`. The **Container** page uses the same
underlying routine (`update_container_settings()`) to apply a new
restart policy or resource limit to one server's container without
touching anything else about it.

---

## 5. Scheduled tasks & stability notes

- The task scheduler (APScheduler) runs **inside** the backend process.
  This is why `backend` must never run with more than one worker or
  replica — a second copy would fire every scheduled job twice. Don't
  add `--workers` to the uvicorn command or scale the service.
- All four services log with `json-file`, capped at 10MB × 3 files, so
  logs can't quietly fill your disk over months of uptime.
- `MC_MEM_LIMIT` / `MC_CPU_LIMIT` in `.env` cap resources per server
  container — worth setting once you're running more than one or two
  servers on the same host, so a misbehaving one can't starve the rest.
- `TZ` in `.env` controls what timezone "daily at HH:MM" tasks use.

---

## 6. Security notes

- Only `PANEL_PORT` (nginx) is meant to be exposed to the internet.
  `backend` has no published port, and every route except
  `/api/auth/login` requires a JWT from that login.
- `backend` mounts `/var/run/docker.sock` and therefore has
  root-equivalent access to the host — that's what lets it create/manage
  server containers. It runs as root inside its own container rather
  than pretending a non-root `USER` would meaningfully sandbox it (a
  socket-mounted container already has that power regardless). Keep this
  stack behind your own firewall/VPN if you don't want it reachable by
  anyone but you.
- "Update Server" only downloads `https://` links from
  `UPDATE_ALLOWED_DOMAINS` (`.env`). An optional SHA256 field verifies
  the download before it's extracted.
- Backup/filename-based routes validate filenames against the exact
  pattern the panel itself generates, and are scoped to the requesting
  server's own prefix — arbitrary or cross-server filenames are rejected
  outright.
- Archive extraction (restore, update) is hardened against zip-slip on
  top of Python 3.12's own `tarfile` extraction filter.

For anything beyond this — TLS, fail2ban, etc. — put a proper reverse
proxy (Caddy, Traefik) in front of nginx, or restrict `PANEL_PORT` at
your firewall to a VPN/known IP range.

---

## 7. Changing the SFTP username

Not editable from the panel (only the password is) — it's baked into
the `sftp` service's mount path in `docker-compose.yml`:

1. `docker compose down`
2. Edit `SFTP_USERNAME` in `.env`
3. Edit the username on the line in `sftp/users.conf` to match
4. `docker compose up -d --build`

---

## 8. Local frontend development

```bash
cd backend && uvicorn app.main:app --reload --port 8000   # terminal 1
cd frontend && npm install && npm run dev                  # terminal 2
```

`vite.config.js` proxies `/api` to `localhost:8000` for hot reload
against a live backend without nginx or CORS in the loop. Note the
backend still needs a real Docker socket to do anything server-related,
so this mode is mainly useful for UI-only iteration.

---

## 9. Troubleshooting

- **No servers listed on first login** — expected; go to **Servers** and
  create one.
- **A server keeps restarting right after creation** — expected until
  you run **Update** once to install the actual binary.
- **SFTP shows an empty folder** — look inside `servers/<server-id>/`;
  that's where each server's files live.
- **"Permission denied" writing files over SFTP** — check `BEDROCK_UID`/
  `BEDROCK_GID` in `.env`; if you changed them after first boot, rebuild
  (`docker compose build minecraft`) and recreate affected servers.
- **Console input is disabled** — the server has to be running (it's
  writing to the process's own stdin).
- **Update rejected with a domain error** — the message lists which
  domains are currently allowed; add the new one to
  `UPDATE_ALLOWED_DOMAINS` in `.env` if Mojang's link has moved.
- **"No free port pairs left"** when creating a server — widen
  `MULTISERVER_PORT_RANGE_END` in `.env` and restart the backend.
- **Navigating away from a page and back leaves it stuck / a hard
  refresh is needed** — this was a real bug in the old tab-swapping
  navigation (hand-rolled component lifecycle management, not the more
  battle-tested logic a real router provides) and is fixed as of the
  Vue Router rewrite. If you still see it, it's a new bug — check the
  browser console for an error and open an issue with what it says.
