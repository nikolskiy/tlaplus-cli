import requests
import typer

from tlaplus_cli import ui
from tlaplus_cli.cmd.modules import app
from tlaplus_cli.config.loader import load_config
from tlaplus_cli.versioning import (
    download_version,
    download_version_from_url,
    fetch_remote_versions,
    is_url,
)
from tlaplus_cli.versioning.paths import get_modules_dir


@app.command(name="install-community")
def install_community(
    version: str = typer.Argument(
        None, help="Version tag (e.g. 'v202412171801') or a direct URL to CommunityModules.jar."
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Re-download if already installed."),
) -> None:
    """Download and install a specific version of CommunityModules."""
    base_dir = get_modules_dir()
    jar_name = "CommunityModules.jar"

    if version and is_url(version):
        try:
            version_dir = download_version_from_url(version, base_dir=base_dir, jar_name=jar_name)
        except (requests.RequestException, OSError, ValueError) as e:
            ui.error(f"Failed to download: {e}")
            raise typer.Exit(1) from e
        else:
            ui.success(f"Successfully installed from URL to {version_dir}")
            return

    config = load_config()
    if not config.tla.community_modules:
        ui.error("Community modules URLs not configured in settings.")
        raise typer.Exit(1)

    versions, status = fetch_remote_versions(
        config.tla.community_modules.tags,
        config.tla.community_modules.releases,
        config.tla.community_modules.per_page,
        asset_name=jar_name,
    )

    if not versions:
        ui.error(f"Could not fetch remote versions (status: {status.value})")
        raise typer.Exit(1)

    target = None
    if version:
        target = next((v for v in versions if v.name == version), None)
        if not target:
            ui.error(f"Version {version} not found.")
            raise typer.Exit(1)
    else:
        # Default to latest non-prerelease
        target = next((v for v in versions if not v.prerelease), versions[0])
        ui.info(f"No version specified, selecting latest stable release: {target.name}")

    # Check if already installed
    target_dir = base_dir / f"{target.name}-{target.short_sha}"
    if target_dir.exists() and not force:
        ui.info(f"Version {target.name} is already installed at {target_dir}")
        return

    try:
        version_dir = download_version(target, force=force, base_dir=base_dir, jar_name=jar_name)
        ui.success(f"Successfully installed {target.name} to {version_dir}")
    except (requests.RequestException, OSError) as e:
        ui.error(f"Failed to download: {e}")
        raise typer.Exit(1) from e
