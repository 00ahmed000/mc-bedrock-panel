# Bedrock Panel

A self-hosted control panel for a Minecraft Bedrock Dedicated Server, built
because the generic panels (Pterodactyl, Crafty, AMP) don't expose every
`server.properties` field, `allowlist.json`/`permissions.json`, backups,
in-place updates, and SFTP access rotation in one place.

**Stack:** FastAPI (Python) + Vue 3/Vite/Tailwind + nginx + Docker Compose,
with a Docker-socket-mounted backend that drives an `atmoz/sftp` container
and the Bedrock server container directly.

---

## 1. First-time setup

```bash
cp .env.example .env
cp sftp/users.conf.example sftp/users.conf
```

Now edit both files:

- **`.env`** — set `ADMIN_USERNAME`/`ADMIN_PASSWORD` (panel login) and
  `JWT_SECRET` (generate one with `openssl rand -hex 32`). Everything else
  has a sane default.
- **`sftp/users.conf`** — change the password on the `admin:...` line.
  The username here must match `SFTP_USERNAME` in `.env` (defaults to
  `admin` in both).

Then build and start everything:

```bash
docker compose up -d --build
```

Open `http://<your-server-ip>:${PANEL_PORT:-80}` and log in with the
`ADMIN_USERNAME`/`ADMIN_PASSWORD` you set. The Minecraft container will
crash-loop until you use it — that's expected. Go to **Update Server**,
paste the official Linux download link from
[minecraft.net/download/server/bedrock](https://www.minecraft.net/en-us/download/server/bedrock),
and run it once. That populates the server binary and world files, after
which the server starts normally.

---

## 2. What's in the panel

| Tab | What it does |
|---|---|
| Dashboard | Start/stop/restart, live status, last 300 log lines |
| Properties | Every `server.properties` field, grouped and validated |
| Backups | Create/list/download/restore/delete `.tar.gz` snapshots |
| Update | Swap in a new `bedrock_server` build from an official link |
| SFTP | Connection info + password rotation |
| Allowlist | Add/remove players (`allowlist.json`) |
| Permissions | Set operator/member/visitor by XUID (`permissions.json`) |

Properties, allowlist, and permissions edits are written straight to disk;
Bedrock only picks them up on the next restart (or via `allowlist reload`
/ `permission reload` typed in-game as an operator) — the UI reminds you
each time you save.

---

## 3. Security notes

- The **only** port meant to be exposed to the internet is
  `PANEL_PORT` (nginx). `backend` has no published port — nginx is the
  sole entry point, and every route except `/api/auth/login` requires a
  JWT from that login.
- `backend` mounts `/var/run/docker.sock` and therefore has root-equivalent
  access to the host — this is what lets it start/stop the Minecraft
  container and rotate SFTP credentials. It deliberately runs as root
  inside its own container rather than pretending a non-root `USER`
  would meaningfully sandbox it (a socket-mounted container already has
  that power regardless). Keep this stack behind your own firewall/VPN if
  you don't want it reachable by anyone but you.
- "Update Server" only downloads from `UPDATE_ALLOWED_DOMAINS` in `.env`
  (defaults to Mojang's known domains) over `https://`. If Mojang moves
  the download again and the panel rejects a legitimate link, add the new
  domain there.
- Backup restore and filename-based routes validate the filename against
  the exact pattern the panel itself generates — arbitrary filenames
  (`../../etc/passwd`, etc.) are rejected outright, not sanitized.
- Archive extraction (backup restore, server update) is hardened against
  zip-slip / path-traversal archives on top of Python 3.12's own
  `tarfile` extraction filter.

For anything beyond this — TLS, fail2ban, etc. — put a proper reverse
proxy (Caddy, Traefik) in front of nginx, or restrict `PANEL_PORT` at
your firewall to a VPN/known IP range.

---

## 4. Changing the SFTP username

The username is intentionally **not** editable from the panel (only the
password is) — it's baked into the `sftp` service's volume mount path in
`docker-compose.yml`, so changing it needs a manual step:

1. Stop the stack: `docker compose down`
2. Edit `SFTP_USERNAME` in `.env`
3. Edit the username on the line in `sftp/users.conf` to match
4. `docker compose up -d --build`

---

## 5. Local frontend development

```bash
cd backend && uvicorn app.main:app --reload --port 8000   # terminal 1
cd frontend && npm install && npm run dev                  # terminal 2
```

`vite.config.js` proxies `/api` to `localhost:8000`, so you get hot reload
against a live backend without touching nginx or CORS.

---

## 6. Architecture

```
                    ┌────────────────┐
  Internet ───────▶ │  nginx (80)    │  static Vue build + reverse proxy
                    └───────┬────────┘
                            │ /api/*
                    ┌───────▼────────┐        ┌──────────────────┐
                    │ backend (8000) │───────▶│ docker.sock       │
                    │ FastAPI + JWT  │        │ (controls the two │
                    └───────┬────────┘        │  containers below)│
                            │                  └──────────────────┘
              ┌─────────────┼─────────────┐
              ▼                           ▼
     ┌─────────────────┐        ┌──────────────────┐
     │ minecraft        │        │ sftp             │
     │ bedrock_server   │◀──────▶│ atmoz/sftp       │  shares bedrock_data
     └─────────────────┘  volume └──────────────────┘

  Named volumes: bedrock_data (world + server files), backups_data
```

`bedrock_data` is shared read/write by `minecraft`, `sftp`, and `backend`.
All three agree on `BEDROCK_UID`/`BEDROCK_GID` (default `1000:1000`) so
none of them end up unable to write files the others created — `backend`
runs as root and re-chowns anything it writes into that volume to keep it
that way (see `backend/app/fsutil.py`).

Rotating the SFTP password does more than rewrite `users.conf`: atmoz/sftp
only reads that file on a container's first boot, so a plain restart
wouldn't apply a change. The backend instead clones the running
container's own resolved config (image, env, labels, mounts, network) and
recreates it — see the docstring on
`recreate_container_preserving_identity()` in `backend/app/docker_utils.py`
for the full reasoning.

---

## 7. Troubleshooting

- **Minecraft container keeps restarting on first boot** — expected until
  you run Update Server once (see step 1).
- **SFTP login works but I see an empty folder** — look inside the
  `server/` subfolder; that's where the bind mount puts your world files.
- **"Permission denied" writing files over SFTP** — check `BEDROCK_UID`/
  `BEDROCK_GID` in `.env` match across a fresh `docker compose up -d
  --build`; if you changed them after first boot, the `minecraft` image
  needs rebuilding (`docker compose build minecraft`).
- **Update rejected with a domain error** — the message lists which
  domains are currently allowed; add the new one to
  `UPDATE_ALLOWED_DOMAINS` in `.env` if Mojang's download link has moved.
