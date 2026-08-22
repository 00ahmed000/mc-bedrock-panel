"""
FastAPI application entrypoint: wires up every router behind the shared
JWT auth dependency (auth.get_current_user), starts the task scheduler,
and runs a few startup sanity checks that only ever warn — a container
that refuses to boot is much harder to debug than one that logs a loud
warning and keeps going.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from . import config, scheduler
from .auth import get_current_user
from .auth import router as auth_router
from .routers import allowlist, backups, gamerules, permissions, properties, server, servers, settings, sftp, tasks, versions

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bedrock_panel")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if config.ADMIN_PASSWORD in ("admin", "password", "changeme", ""):
        logger.warning("ADMIN_PASSWORD is set to a weak/default value. Change it in .env before exposing this panel.")
    if len(config.JWT_SECRET) < 32:
        logger.warning("JWT_SECRET is short. Generate a strong one with: openssl rand -hex 32")
    os.makedirs(config.SERVERS_ROOT, exist_ok=True)
    scheduler.start()
    logger.info("Task scheduler started")
    yield


app = FastAPI(title="Bedrock Panel API", version="2.0.0", lifespan=lifespan)

# /api/auth/login is the only route that does NOT require a valid token.
app.include_router(auth_router)
app.include_router(versions.router, dependencies=[Depends(get_current_user)])

_protected = [Depends(get_current_user)]
app.include_router(servers.router, dependencies=_protected)
app.include_router(properties.router, dependencies=_protected)
app.include_router(backups.router, dependencies=_protected)
app.include_router(server.router, dependencies=_protected)
app.include_router(settings.router, dependencies=_protected)
app.include_router(gamerules.router, dependencies=_protected)
app.include_router(sftp.router, dependencies=_protected)
app.include_router(allowlist.router, dependencies=_protected)
app.include_router(permissions.router, dependencies=_protected)
app.include_router(tasks.router, dependencies=_protected)


@app.get("/api/health")
def health():
    """Unauthenticated on purpose — used by Docker's HEALTHCHECK and nginx."""
    return {"status": "ok"}
