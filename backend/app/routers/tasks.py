from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import scheduler, servers_registry

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    server_id: str
    action: Literal["backup", "restart"]
    schedule_type: Literal["interval", "daily"]
    interval_minutes: Optional[int] = Field(None, ge=5, le=10080)
    daily_hour: Optional[int] = Field(None, ge=0, le=23)
    daily_minute: Optional[int] = Field(None, ge=0, le=59)


@router.get("")
def list_tasks():
    return {"tasks": scheduler.list_tasks()}


@router.post("")
def create_task(payload: CreateTaskRequest):
    if servers_registry.get_server(payload.server_id) is None:
        raise HTTPException(status_code=404, detail=f"No server with id '{payload.server_id}'")

    if payload.schedule_type == "interval":
        if not payload.interval_minutes:
            raise HTTPException(status_code=400, detail="interval_minutes is required for an interval task")
        kwargs = {"interval_minutes": payload.interval_minutes}
    else:
        if payload.daily_hour is None or payload.daily_minute is None:
            raise HTTPException(status_code=400, detail="daily_hour and daily_minute are required for a daily task")
        kwargs = {"daily_hour": payload.daily_hour, "daily_minute": payload.daily_minute}

    task = scheduler.create_task(payload.server_id, payload.action, payload.schedule_type, **kwargs)
    return {"status": "success", "task": task}


@router.delete("/{task_id}")
def delete_task(task_id: str):
    if not scheduler.delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"No task with id '{task_id}'")
    return {"status": "success"}
