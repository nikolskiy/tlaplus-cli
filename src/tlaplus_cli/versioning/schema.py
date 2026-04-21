from dataclasses import dataclass
from enum import Enum
from pathlib import Path


@dataclass
class RemoteVersion:
    name: str
    short_sha: str
    full_sha: str
    jar_download_url: str
    published_at: str
    prerelease: bool


@dataclass
class LocalVersion:
    name: str
    short_sha: str
    path: Path


class FetchStatus(Enum):
    ONLINE = "online"
    CACHED = "cached"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
