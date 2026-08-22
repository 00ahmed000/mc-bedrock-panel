"""
Lightweight recurring-task scheduler for automated backups/restarts.
Runs in-process via APScheduler's AsyncIOScheduler, sharing the same
event loop uvicorn already runs — no extra process or container.

This is also why the backend MUST stay a single process/worker (see the
comment on `backend` in docker-compose.yml): a second uvicorn worker
would run its own independent copy of this scheduler and every job would
fire twice.
"""
import json
import logging
import os
import secrets
import tarfile
import time
from datetime import datetime
from typing import Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from . import config, docker_utils, servers_registry

logger = logging.getLogger("bedrock_panel")
_scheduler = AsyncIOScheduler()

BACKUP_TARGETS = ["worlds", "server.properties", "allowlist.json", "permissions.json"]


def _load_tasks() -> Dict[str, dict]:
    if not os.path.exists(config.TASKS_PATH):
        return {}
    with open(config.TASKS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save_tasks(tasks: Dict[str, dict]) -> None:
    os.makedirs(config.SERVERS_ROOT, exist_ok=True)
    tmp_path = config.TASKS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)
    os.replace(tmp_path, config.TASKS_PATH)


def _make_trigger(task: dict):
    if task["schedule_type"] == "interval":
        return IntervalTrigger(minutes=task["interval_minutes"])
    if task["schedule_type"] == "daily":
        return CronTrigger(hour=task["daily_hour"], minute=task["daily_minute"])
    raise ValueError(f"Unknown schedule_type '{task['schedule_type']}'")


async def _run_backup(server_id: str) -> None:
    entry = servers_registry.get_server(server_id)
    if entry is None:
        logger.warning(f"Scheduled backup skipped: server '{server_id}' no longer exists")
        return
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backup_{server_id}_{timestamp}.tar.gz"
    destination = os.path.join(config.BACKUP_PATH, filename)
    try:
        with tarfile.open(destination, "w:gz") as tar:
            for item in BACKUP_TARGETS:
                item_path = os.path.join(entry["working_dir"], item)
                if os.path.exists(item_path):
                    tar.add(item_path, arcname=item)
        logger.info(f"Scheduled backup completed for '{server_id}': {filename}")
    except Exception as e:
        logger.warning(f"Scheduled backup failed for '{server_id}': {e}")


async def _run_restart(server_id: str) -> None:
    entry = servers_registry.get_server(server_id)
    if entry is None:
        logger.warning(f"Scheduled restart skipped: server '{server_id}' no longer exists")
        return
    try:
        docker_utils.restart_container(entry["container_name"])
        logger.info(f"Scheduled restart completed for '{server_id}'")
    except Exception as e:
        logger.warning(f"Scheduled restart failed for '{server_id}': {e}")


def _add_job(task: dict) -> None:
    func = _run_backup if task["action"] == "backup" else _run_restart
    _scheduler.add_job(
        func,
        trigger=_make_trigger(task),
        args=[task["server_id"]],
        id=task["task_id"],
        replace_existing=True,
    )


def start() -> None:
    """Call once at app startup: starts the scheduler and loads persisted tasks."""
    if not _scheduler.running:
        _scheduler.start()
    for task in _load_tasks().values():
        if task.get("enabled", True):
            try:
                _add_job(task)
            except Exception as e:
                logger.warning(f"Could not schedule task '{task.get('task_id')}': {e}")


def list_tasks() -> list:
    return sorted(_load_tasks().values(), key=lambda t: t["created_at"])


def create_task(server_id: str, action: str, schedule_type: str, **schedule_kwargs) -> dict:
    tasks = _load_tasks()
    task_id = f"task_{secrets.token_hex(4)}"
    task = {
        "task_id": task_id,
        "server_id": server_id,
        "action": action,
        "schedule_type": schedule_type,
        "enabled": True,
        "created_at": int(time.time()),
        **schedule_kwargs,
    }
    tasks[task_id] = task
    _save_tasks(tasks)
    _add_job(task)
    return task


def delete_task(task_id: str) -> bool:
    tasks = _load_tasks()
    if task_id not in tasks:
        return False
    tasks.pop(task_id)
    _save_tasks(tasks)
    try:
        _scheduler.remove_job(task_id)
    except Exception:
        pass
    return True
