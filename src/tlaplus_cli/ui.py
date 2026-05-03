import typer


def warn(message: str) -> None:
    """Print a standardized warning message to stderr."""
    typer.echo(f"{typer.style('⚠', fg=typer.colors.YELLOW)} Warning: {message}", err=True)


def error(message: str) -> None:
    """Print a standardized error message to stderr."""
    typer.echo(f"{typer.style('✖', fg=typer.colors.RED)} Error: {message}", err=True)


def info(message: str) -> None:
    """Print a standardized info message to stderr."""
    typer.echo(f"{typer.style('i', fg=typer.colors.CYAN)} Info: {message}", err=True)


def success(message: str) -> None:
    """Print a standardized success message to stderr."""
    typer.echo(f"{typer.style('✔', fg=typer.colors.GREEN)} Success: {message}", err=True)
