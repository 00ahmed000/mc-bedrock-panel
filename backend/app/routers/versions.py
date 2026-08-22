from fastapi import APIRouter

from .. import version_catalog

router = APIRouter(prefix="/api/minecraft-versions", tags=["versions"])


@router.get("")
def list_versions(refresh: bool = False):
    return {"versions": version_catalog.get_versions(force_refresh=refresh)}
