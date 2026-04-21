import typer


def warn(message: str) -> None:
    """Print a standardized warning message to stderr."""
    typer.echo(f"⚠ Warning: {message}", err=True)
