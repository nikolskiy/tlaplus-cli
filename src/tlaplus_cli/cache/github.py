import json
from dataclasses import asdict
from pathlib import Path

import typer

from tlaplus_cli.versioning.schema import RemoteVersion


def load_github_cache(cache_file: Path) -> list[RemoteVersion] | None:
    if cache_file.exists():
        try:
            with cache_file.open("r") as f:
                data = json.load(f)
            return [RemoteVersion(**item) for item in data]
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to read cache: {e}", err=True)
    return None


def save_github_cache(cache_file: Path, versions: list[RemoteVersion]) -> None:
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with cache_file.open("w") as f:
            json.dump([asdict(v) for v in versions], f)
    except Exception as e:
        typer.echo(f"⚠ Warning: Failed to save cache: {e}", err=True)
