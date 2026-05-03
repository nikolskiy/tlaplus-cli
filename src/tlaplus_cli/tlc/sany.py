"""SANY output parser.

Ported and adapted from ts-output-parser/parsers/sany.ts.
"""

import re
from dataclasses import dataclass


@dataclass
class SanyMessage:
    """A message from SANY (error or warning)."""

    message: str
    module: str | None = None
    range_start_line: int | None = None
    range_start_col: int | None = None
    range_end_line: int | None = None
    range_end_col: int | None = None


class SanyParser:
    """Parser for SANY output."""

    def __init__(self) -> None:
        self.errors: list[SanyMessage] = []
        self.warnings: list[SanyMessage] = []
        self.current_module: str | None = None
        self.current_block: str | None = None  # "Errors", "Warnings", etc.
        self.current_message: SanyMessage | None = None

    def process_line(self, line: str) -> None:
        """Process a single line of SANY output."""
        if line.startswith("Parsing file "):
            return
        if line.startswith("Semantic processing of module "):
            self.current_module = line[len("Semantic processing of module ") :].strip()
            return

        if line.startswith("*** Errors:"):
            self._flush_message()
            self.current_block = "Errors"
            return
        if line.startswith(("*** Warnings:", "Warnings (")):
            self._flush_message()
            self.current_block = "Warnings"
            return
        if line.startswith("***Parse Error***"):
            self._flush_message()
            self.current_block = "Errors"
            return

        # Location pattern: line 10, col 5 to line 10, col 20 of module M
        loc_pattern = r"line (\d+), col (\d+) to line (\d+), col (\d+) of module (\w+)"
        match = re.search(loc_pattern, line)
        if match:
            self._flush_message()
            self.current_message = SanyMessage(
                message="",
                range_start_line=int(match.group(1)),
                range_start_col=int(match.group(2)),
                range_end_line=int(match.group(3)),
                range_end_col=int(match.group(4)),
                module=match.group(5),
            )
            return

        if self.current_block:
            if self.current_message:
                if self.current_message.message:
                    self.current_message.message += "\n" + line
                else:
                    self.current_message.message = line
            else:
                # Rangeless message
                self.current_message = SanyMessage(message=line, module=self.current_module)

    def _flush_message(self) -> None:
        if self.current_message:
            if self.current_block == "Errors":
                self.errors.append(self.current_message)
            elif self.current_block == "Warnings":
                self.warnings.append(self.current_message)
            self.current_message = None

    def get_errors(self) -> list[SanyMessage]:
        """Get all parsed errors."""
        self._flush_message()
        return self.errors

    def get_warnings(self) -> list[SanyMessage]:
        """Get all parsed warnings."""
        self._flush_message()
        return self.warnings
