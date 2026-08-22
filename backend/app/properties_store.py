"""
Read/write helpers for server.properties that MERGE the typed, validated
fields into whatever is already on disk, instead of clobbering the file
down to exactly the fields FullServerProperties happens to model. Mojang
adds new server.properties keys over time; any key our schema doesn't
know about yet is preserved untouched rather than deleted on save.

Every function takes an explicit `path` (from ServerContext.properties_path)
instead of a fixed global, since v2 manages many servers at once.
"""
import os
from typing import Dict

from . import fsutil
from .schemas import PROPERTY_KEY_MAP, FullServerProperties


def _to_properties_string(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _from_properties_string(raw: str, field_name: str):
    annotation = FullServerProperties.model_fields[field_name].annotation
    if annotation is bool:
        return raw.strip().lower() == "true"
    if annotation is int:
        try:
            return int(raw)
        except ValueError:
            return FullServerProperties.model_fields[field_name].default
    if annotation is float:
        try:
            return float(raw)
        except ValueError:
            return FullServerProperties.model_fields[field_name].default
    return raw


def parse_raw_properties(path: str) -> Dict[str, str]:
    """Read a server.properties file into a flat {key: rawvalue} dict; comments and blank lines dropped."""
    raw: Dict[str, str] = {}
    if not os.path.exists(path):
        return raw
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            raw[key.strip()] = value.strip()
    return raw


def get_properties(path: str) -> FullServerProperties:
    """
    Return a server.properties file, typed and validated. Any single
    on-disk value that fails validation (e.g. hand-edited to something
    invalid) falls back to that field's default instead of failing the
    whole read.
    """
    raw = parse_raw_properties(path)
    values = {}
    for field_name in FullServerProperties.model_fields:
        key = PROPERTY_KEY_MAP[field_name]
        if key in raw:
            values[field_name] = _from_properties_string(raw[key], field_name)

    try:
        return FullServerProperties.model_validate(values)
    except Exception:
        cleaned = {}
        for field_name, value in values.items():
            try:
                FullServerProperties.model_validate({field_name: value})
                cleaned[field_name] = value
            except Exception:
                continue
        return FullServerProperties.model_validate(cleaned)


def save_properties(path: str, props: FullServerProperties) -> None:
    """Merge the typed fields into the on-disk file and write atomically."""
    raw = parse_raw_properties(path)
    for field_name, value in props.model_dump().items():
        key = PROPERTY_KEY_MAP[field_name]
        raw[key] = _to_properties_string(value)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.writelines(f"{k}={v}\n" for k, v in raw.items())
    os.replace(tmp_path, path)
    fsutil.set_bedrock_ownership(path)
