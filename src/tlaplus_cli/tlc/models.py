"""Data models for TLC model checking results.

Ported and adapted from ts-output-parser/model/check.ts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CheckState(Enum):
    """Overall state of the model checking process."""

    Running = "R"
    Success = "S"
    Error = "E"
    Stopped = "X"


class CheckStatus(Enum):
    """Specific status of the model checking process."""

    NotStarted = 0
    Starting = 1
    SanyParsing = 2
    SanyFinished = 3
    InitialStatesComputing = 4
    SuccessorStatesComputing = 5
    Checkpointing = 6
    CheckingLiveness = 7
    CheckingLivenessFinal = 8
    ServerRunning = 9
    WorkersRegistered = 10
    Finished = 11


@dataclass
class InitialStateStatItem:
    """Statistics on state generation."""

    timestamp: str
    diameter: int
    total: int
    distinct: int
    queue_size: int


@dataclass
class CoverageItem:
    """Statistics on coverage."""

    module: str
    action: str
    file_path: str | None
    range_start_line: int
    range_start_col: int
    range_end_line: int
    range_end_col: int
    total: int
    distinct: int


@dataclass
class MessageLine:
    """A line of a message."""

    text: str

    def __str__(self) -> str:
        return self.text


@dataclass
class TlaValue:
    """Represents a TLA+ value."""

    key: str | int
    value: str  # Currently just the string representation
    children: list["TlaValue"] = field(default_factory=list)


@dataclass
class ErrorTraceItem:
    """A single state in an error trace."""

    num: int
    title: str
    module: str
    action: str
    variables: list[TlaValue] = field(default_factory=list)
    file_path: str | None = None
    range_start_line: int | None = None
    range_start_col: int | None = None
    range_end_line: int | None = None
    range_end_col: int | None = None


@dataclass
class WarningInfo:
    """A warning issued by TLC."""

    lines: list[MessageLine]


@dataclass
class ErrorInfo:
    """An error issued by TLC."""

    lines: list[MessageLine]
    error_trace: list[ErrorTraceItem] = field(default_factory=list)


@dataclass
class ModelCheckResult:
    """The result of a model check."""

    state: CheckState = CheckState.Running
    status: CheckStatus = CheckStatus.NotStarted
    process_info: str | None = None
    initial_states_stat: list[InitialStateStatItem] = field(default_factory=list)
    coverage_stat: list[CoverageItem] = field(default_factory=list)
    warnings: list[WarningInfo] = field(default_factory=list)
    errors: list[ErrorInfo] = field(default_factory=list)
    start_date_time: datetime | None = None
    end_date_time: datetime | None = None
    duration: int | None = None  # msec
    workers_count: int = 0
    collision_probability: str | None = None
    output_lines: list[str] = field(default_factory=list)
    sany_errors: list[Any] = field(default_factory=list)
    trace_file_path: str | None = None
