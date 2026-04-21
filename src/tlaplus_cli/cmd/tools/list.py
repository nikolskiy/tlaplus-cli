import typer
from rich.console import Console
from rich.table import Table

from tlaplus_cli.cmd.tools import app
from tlaplus_cli.config.loader import load_config
from tlaplus_cli.versioning import (
    FetchStatus,
    fetch_remote_versions,
    get_pinned_version_dir,
    list_local_versions,
    read_version_metadata,
)


@app.command(name="list")
def list_versions() -> None:
    config = load_config()
    versions, status = fetch_remote_versions(config.tla.urls.tags, config.tla.urls.releases, config.tla.urls.per_page)

    local_versions = list_local_versions()
    pinned_dir = get_pinned_version_dir()
    pinned_dir_name = pinned_dir.name if pinned_dir else None

    # Track what we've displayed to handle local-only and duplicates
    # key: (name, short_sha)
    displayed: set[tuple[str, str]] = set()

    title = "TLA+ Tools Versions"
    if status == FetchStatus.STALE:
        title += " (cached)"
    elif status == FetchStatus.UNAVAILABLE:
        typer.echo("⚠ remote data unavailable")

    table = Table(title=title)
    table.add_column("Version", style="cyan")
    table.add_column("Tag/SHA", style="magenta")
    table.add_column("Published", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Pinned", style="yellow", justify="center")

    def format_date(date_str: str) -> str:
        if not date_str:
            return ""
        return date_str.split("T", maxsplit=1)[0]

    if status == FetchStatus.UNAVAILABLE:
        for lv in local_versions:
            dir_name = f"{lv.name}-{lv.short_sha}"
            is_pinned = "[green]✓[/green]" if pinned_dir_name == dir_name else ""
            meta = read_version_metadata(lv.path)
            published = format_date(meta.get("published_at", "")) if meta else ""
            table.add_row(lv.name, lv.short_sha, published, "installed", is_pinned)
    else:
        remote_names = {v.name for v in versions}
        # First, remote versions
        for v in versions:
            dir_name = f"{v.name}-{v.short_sha}"
            is_pinned = "[green]✓[/green]" if pinned_dir_name == dir_name else ""

            # Check if this exact version (name+sha) is installed
            installed = any(lv.name == v.name and lv.short_sha == v.short_sha for lv in local_versions)
            row_status = "installed" if installed else "available"

            table.add_row(v.name, v.short_sha, format_date(v.published_at), row_status, is_pinned)
            displayed.add((v.name, v.short_sha))

        # Then, local versions not in remote (or with different SHAs)
        for lv in local_versions:
            if (lv.name, lv.short_sha) not in displayed:
                dir_name = f"{lv.name}-{lv.short_sha}"
                is_pinned = "[green]✓[/green]" if pinned_dir_name == dir_name else ""
                meta = read_version_metadata(lv.path)
                published = format_date(meta.get("published_at", "")) if meta else ""

                row_status = "installed" if lv.name in remote_names else "local only"
                table.add_row(lv.name, lv.short_sha, published, row_status, is_pinned)

    console = Console()
    console.print(table)
