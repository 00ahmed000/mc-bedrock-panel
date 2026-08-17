from fastapi import APIRouter

from .. import properties_store
from ..schemas import FullServerProperties

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("", response_model=FullServerProperties)
def read_properties():
    return properties_store.get_properties()


@router.post("", response_model=FullServerProperties)
def write_properties(props: FullServerProperties):
    properties_store.save_properties(props)
    return properties_store.get_properties()
