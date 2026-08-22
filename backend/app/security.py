"""
Security helper functions: path containment, safe archive extraction,
and download URL validation. Every filesystem/network operation in the
routers that touches a user-supplied name or URL goes through here first.
"""
import os
import re
import tarfile
import zipfile
from urllib.parse import urlparse

from . import config

_BACKUP_FILENAME_RE = re.compile(r"^backup_[a-z0-9-]+_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.tar\.gz$")


class UnsafePathError(Exception):
    """Raised when a path would resolve outside its intended base directory."""


def validate_backup_filename(filename: str) -> str:
    """
    Only accept filenames that exactly match what create_backup() generates
    (see routers/backups.py). This blocks path traversal (../, absolute
    paths, null bytes, etc.) by allowlisting the exact expected shape
    instead of trying to sanitize arbitrary input.
    """
    if not _BACKUP_FILENAME_RE.match(filename):
        raise UnsafePathError(f"'{filename}' is not a valid backup filename")
    return filename


def safe_join(base: str, *parts: str) -> str:
    """Join `parts` onto `base` and guarantee the resolved path still lives under `base`."""
    base_real = os.path.realpath(base)
    candidate = os.path.realpath(os.path.join(base, *parts))
    if candidate != base_real and not candidate.startswith(base_real + os.sep):
        raise UnsafePathError(f"Path '{candidate}' escapes base '{base_real}'")
    return candidate


def _is_within_directory(directory: str, target: str) -> bool:
    directory = os.path.realpath(directory)
    target = os.path.realpath(target)
    return target == directory or target.startswith(directory + os.sep)


def safe_extract_tar(tar: tarfile.TarFile, destination: str) -> None:
    """
    Extract a tar archive while refusing any member (or symlink/hardlink
    target) whose resolved path would land outside `destination` — the
    zip-slip / CVE-2007-4559 class of attack. Also relies on Python
    3.12's built-in `filter="data"` hardening (PEP 706) as a second,
    independently-implemented layer of the same protection.
    """
    os.makedirs(destination, exist_ok=True)
    for member in tar.getmembers():
        member_path = os.path.join(destination, member.name)
        if not _is_within_directory(destination, member_path):
            raise UnsafePathError(f"Archive member '{member.name}' would escape destination")
        if member.issym() or member.islnk():
            link_target = os.path.join(os.path.dirname(member_path), member.linkname)
            if not _is_within_directory(destination, link_target):
                raise UnsafePathError(f"Archive link '{member.name}' would escape destination")
    tar.extractall(path=destination, filter="data")


def safe_extract_zip(zip_ref: zipfile.ZipFile, destination: str) -> None:
    """Extract a zip archive while refusing any member that would escape `destination`."""
    os.makedirs(destination, exist_ok=True)
    for name in zip_ref.namelist():
        member_path = os.path.join(destination, name)
        if not _is_within_directory(destination, member_path):
            raise UnsafePathError(f"Archive member '{name}' would escape destination")
    zip_ref.extractall(path=destination)


def is_allowed_download_url(url: str) -> bool:
    """
    Only allow https:// URLs whose hostname is in UPDATE_ALLOWED_DOMAINS
    (see config.py / .env). Blocks non-https schemes (file://, ftp://,
    javascript:, etc.) and downloads from arbitrary hosts.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme != "https":
        return False
    hostname = (parsed.hostname or "").lower()
    return hostname in config.UPDATE_ALLOWED_DOMAINS
