"""
Fetches the list of available Bedrock Dedicated Server versions for the
version picker in the server-creation wizard, from two sources:

1. The official Microsoft/Mojang download-links API — the same one the
   official download page itself uses — for the current stable and
   preview builds. This is the authoritative "latest" source.
2. Bedrock-OSS/BDS-Versions on GitHub, an actively-maintained community
   archive, for the historical list so older versions are pickable too.

Results are cached in-memory (GitHub's unauthenticated API is rate
limited) and a failure in either source just means a shorter list, never
a hard error — the version field everywhere it's used also still accepts
a free-typed version number as a fallback.
"""
import json
import logging
import re
import time
import urllib.request

logger = logging.getLogger("bedrock_panel")

_OFFICIAL_LINKS_URL = "https://net-secondary.web.minecraft-services.net/api/v1.0/download/links"
_HISTORY_INDEX_URL = "https://api.github.com/repos/Bedrock-OSS/BDS-Versions/contents/linux"
_CACHE_TTL_SECONDS = 3600

_cache: dict = {"versions": [], "fetched_at": 0}

_FALLBACK_VERSIONS = [
    {"version": "1.21.90.4", "channel": "release", "label": "1.21.90.4 (fallback \u2014 version sources unreachable)"},
]


def _fetch_json(url: str, timeout: int = 10):
    req = urllib.request.Request(url, headers={"User-Agent": "bedrock-panel/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_official_latest() -> list:
    data = _fetch_json(_OFFICIAL_LINKS_URL)
    out = []
    for link in data.get("result", {}).get("links", []):
        dtype = link.get("downloadType", "")
        url = link.get("downloadUrl", "")
        m = re.search(r"bedrock-server-([\d.]+)\.zip", url)
        if not m:
            continue
        version = m.group(1)
        if dtype == "serverBedrockLinux":
            out.append({"version": version, "channel": "release", "label": f"{version} \u2014 latest release"})
        elif dtype == "serverBedrockPreviewLinux":
            out.append({"version": version, "channel": "preview", "label": f"{version} \u2014 latest preview"})
    return out


def _fetch_history() -> list:
    entries = _fetch_json(_HISTORY_INDEX_URL)
    out = []
    for entry in entries:
        name = entry.get("name", "")
        if name.endswith(".json"):
            version = name[: -len(".json")]
            out.append({"version": version, "channel": "release", "label": version})
    return out


def _sort_key(v: dict):
    return [int(p) if p.isdigit() else 0 for p in re.split(r"[.\-]", v["version"])]


def get_versions(force_refresh: bool = False) -> list:
    now = time.time()
    if not force_refresh and _cache["versions"] and (now - _cache["fetched_at"]) < _CACHE_TTL_SECONDS:
        return _cache["versions"]

    combined = {}
    try:
        for v in _fetch_official_latest():
            combined[v["version"]] = v
    except Exception as e:
        logger.warning(f"Could not fetch official BDS version links: {e}")

    try:
        for v in _fetch_history():
            combined.setdefault(v["version"], v)
    except Exception as e:
        logger.warning(f"Could not fetch BDS version history: {e}")

    versions = sorted(combined.values(), key=_sort_key, reverse=True)
    if versions:
        _cache["versions"] = versions
        _cache["fetched_at"] = now
        return versions
    return _cache["versions"] or _FALLBACK_VERSIONS


def latest_release_version() -> str:
    for v in get_versions():
        if v["channel"] == "release":
            return v["version"]
    return _FALLBACK_VERSIONS[0]["version"]
