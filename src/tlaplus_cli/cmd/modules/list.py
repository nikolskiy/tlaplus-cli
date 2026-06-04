import json

import typer
from rich.console import Console
from rich.table import Table

from tlaplus_cli.versioning.paths import get_modules_dir


def list_modules() -> None:
    """List all custom TLA+ modules added to the cache."""
    modules_dir = get_modules_dir()

    if not modules_dir.is_dir():
        typer.echo("No modules currently added.")
        return

    modules_data = []
    for item in sorted(modules_dir.iterdir()):
        if item.is_dir():
            metadata_file = item / "metadata.json"
            if metadata_file.exists():
                try:
                    meta = json.loads(metadata_file.read_text())
                    name = meta.get("name", item.name)
                    built_at = meta.get("built_at", "Unknown")
                    modules_data.append((name, built_at))
                except Exception:
                    modules_data.append((item.name, "Corrupt Metadata"))
            else:
                modules_data.append((item.name, "Unknown"))

    if not modules_data:
        typer.echo("No modules currently added.")
        return

    table = Table()
    table.add_column("Module Name", style="cyan")
    table.add_column("Last Built/Modified", style="magenta")

    for name, built_at in modules_data:
        table.add_row(name, built_at)

    console = Console()
    console.print(table)
