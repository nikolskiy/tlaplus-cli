"""The ``tla`` command: print a notice, then run the same command through tlaup."""

import sys

NOTICE = (
    "Notice: tlaplus-cli is now called tlaup and is no longer maintained. "
    "Switch with 'uv tool uninstall tlaplus-cli && uv tool install tlaup', then use 'tlaup' instead of 'tla'."
)


def main() -> None:
    """Entry point for [project.scripts]."""
    print(NOTICE, file=sys.stderr)
    from tlaup.cli import main as tlaup_main  # noqa: PLC0415

    tlaup_main()
