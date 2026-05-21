"""TLC output parser.

Ported and adapted from ts-output-parser/parsers/tlc.ts.
"""

import re
from datetime import datetime

from . import codes
from .codes import TlcCodeType, get_tlc_code
from .models import (
    CheckState,
    CheckStatus,
    CoverageItem,
    ErrorInfo,
    ErrorTraceItem,
    InitialStateStatItem,
    MessageLine,
    ModelCheckResult,
    WarningInfo,
)
from .values import parse_variable_value


class MessageType:
    def __init__(self, code: int, forced_type: TlcCodeType | None = None) -> None:
        self.code = code
        self.forced_type = forced_type

    def is_unknown(self) -> bool:
        return self.code == -1


class Message:
    def __init__(self, message_type: MessageType) -> None:
        self.type = message_type
        self.lines: list[str] = []


class MessageStack:
    def __init__(self) -> None:
        self.current = Message(MessageType(-1))
        self.previous: list[Message] = []

    def start(self, message_type: MessageType) -> None:
        if message_type.is_unknown():
            msg = "Cannot start message of unknown type"
            raise ValueError(msg)
        self.previous.append(self.current)
        self.current = Message(message_type)

    def finish(self) -> Message:
        if self.current.type.is_unknown():
            return Message(MessageType(-1))
        finished = self.current
        if self.previous:
            self.current = self.previous.pop()
        else:
            self.current = Message(MessageType(-1))
        return finished

    def add_line(self, line: str) -> None:
        if not self.current.type.is_unknown():
            self.current.lines.append(line)


class TlcParser:
    def __init__(self) -> None:
        self.result = ModelCheckResult()
        self.messages = MessageStack()

    def get_result(self) -> ModelCheckResult:
        return self.result

    def process_line(self, line: str) -> None:
        """Process a single line of TLC output."""
        # Handle message end
        end_match = re.search(r"^(.*)@!@!@ENDMSG -?\d+ @!@!@(.*)$", line)
        if end_match:
            prefix, suffix = end_match.groups()
            if prefix:
                self.messages.add_line(prefix)
            message = self.messages.finish()
            self._handle_message_end(message)
            if suffix:
                self.process_line(suffix)
            return

        # Handle message start
        start_match = re.search(r"^(.*)@!@!@STARTMSG (-?\d+)(:\d+)? @!@!@$", line)
        if start_match:
            prefix, code_str, severity_str = start_match.groups()
            if prefix:
                self.messages.add_line(prefix)
            code = int(code_str)
            forced_type = None
            if severity_str:
                severity = int(severity_str[1:])
                if severity in (1, 2):
                    forced_type = TlcCodeType.Error
                elif severity == 3:
                    forced_type = TlcCodeType.Warning

            self.messages.start(MessageType(code, forced_type))
            return

        # Regular line
        if not self.messages.current.type.is_unknown():
            self.messages.add_line(line)
        elif line.strip():
            self.result.output_lines.append(line)

    def _handle_message_end(self, message: Message) -> None:
        if message.type.is_unknown():
            return

        if self.result.status == CheckStatus.NotStarted:
            self.result.status = CheckStatus.Starting

        code_obj = get_tlc_code(message.type.code)
        if not code_obj or code_obj.type == TlcCodeType.Ignore:
            return

        effective_type = message.type.forced_type or code_obj.type

        if effective_type == TlcCodeType.Warning:
            self.result.warnings.append(WarningInfo([MessageLine(line) for line in message.lines]))
            return

        if effective_type == TlcCodeType.Error:
            self.result.state = CheckState.Error
            self.result.errors.append(ErrorInfo([MessageLine(line) for line in message.lines]))
            return

        self._dispatch_message(message)

    def _dispatch_message(self, message: Message) -> None:
        code = message.type.code
        if code == codes.TLC_STARTING.num:
            self._parse_starting(message.lines)
            self.result.status = CheckStatus.Starting
        elif code == codes.TLC_VERSION.num:
            self.result.process_info = "".join(message.lines).strip()
        elif code == codes.TLC_PROGRESS_STATS.num:
            self._parse_progress_stats(message.lines)
            self.result.status = CheckStatus.SuccessorStatesComputing
        elif code in (codes.TLC_STATE_PRINT1.num, codes.TLC_STATE_PRINT2.num, codes.TLC_STATE_PRINT3.num):
            self._parse_error_trace_item(message.lines)
        elif code in (codes.TLC_COVERAGE_INIT.num, codes.TLC_COVERAGE_NEXT.num):
            self._parse_coverage(message.lines)
        elif code == codes.TLC_FINISHED.num:
            self._parse_finished(message.lines)
            self.result.status = CheckStatus.Finished
        elif code == codes.TLC_SUCCESS.num:
            if self.result.state != CheckState.Error:
                self.result.state = CheckState.Success
        elif code == codes.TLC_SANY_START.num:
            self.result.status = CheckStatus.SanyParsing
        elif code == codes.TLC_SANY_END.num:
            self.result.status = CheckStatus.SanyFinished

    def _parse_starting(self, lines: list[str]) -> None:
        content = "".join(lines)
        match = re.search(r"Starting\.\.\. \((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)", content)
        if match:
            self.result.start_date_time = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")

    def _parse_progress_stats(self, lines: list[str]) -> None:
        content = "".join(lines)
        pattern = (
            r"Progress\(([\d,]+)\) at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): "
            r"(.+) states generated.*, (.+) distinct states found.*, (.+) states left on queue"
        )
        match = re.search(pattern, content)
        if match:

            def parse_int(s: str) -> int:
                return int(s.replace(",", ""))

            item = InitialStateStatItem(
                timestamp=match.group(2),
                diameter=parse_int(match.group(1)),
                total=parse_int(match.group(3)),
                distinct=parse_int(match.group(4)),
                queue_size=parse_int(match.group(5)),
            )
            self.result.initial_states_stat.append(item)

    def _parse_error_trace_item(self, lines: list[str]) -> None:
        if not lines:
            return

        header = lines[0]
        # Example: 1: <Initial predicate> line 5, col 1 to line 5, col 10 of module M
        pattern = r"^(\d+): <(.*)> line (\d+), col (\d+) to line (\d+), col (\d+) of module (\w+).*$"
        match = re.match(pattern, header)
        if match:
            num = int(match.group(1))
            action = match.group(2)
            item = ErrorTraceItem(
                num=num,
                title=header,
                module=match.group(7),
                action=action,
                range_start_line=int(match.group(3)),
                range_start_col=int(match.group(4)),
                range_end_line=int(match.group(5)),
                range_end_col=int(match.group(6)),
            )
            # Parse variables
            self._parse_trace_variables(item, lines[1:])

            # Add to the last error
            if not self.result.errors:
                self.result.errors.append(ErrorInfo([], []))
            self.result.errors[-1].error_trace.append(item)

    def _parse_trace_variables(self, item: ErrorTraceItem, var_lines: list[str]) -> None:
        # Group lines by variable (starts with name = )
        current_var_name = None
        current_var_lines = []
        for line in var_lines:
            var_match = re.match(r"^(\w+) = (.*)$", line)
            if var_match:
                if current_var_name:
                    item.variables.append(parse_variable_value(current_var_name, current_var_lines))
                current_var_name = var_match.group(1)
                current_var_lines = [var_match.group(2)]
            else:
                current_var_lines.append(line)
        if current_var_name:
            item.variables.append(parse_variable_value(current_var_name, current_var_lines))

    def _parse_coverage(self, lines: list[str]) -> None:
        for line in lines:
            # Example: <Next line 10, col 5 to line 10, col 20 of module M>: 100:50
            pattern = r"<(\w+) line (\d+), col (\d+) to line (\d+), col (\d+) of module (\w+).*>: (\d+):(\d+)"
            match = re.search(pattern, line)
            if match:
                item = CoverageItem(
                    action=match.group(1),
                    range_start_line=int(match.group(2)),
                    range_start_col=int(match.group(3)),
                    range_end_line=int(match.group(4)),
                    range_end_col=int(match.group(5)),
                    module=match.group(6),
                    total=int(match.group(7)),
                    distinct=int(match.group(8)),
                    file_path=None,  # Not directly available in the coverage line
                )
                self.result.coverage_stat.append(item)

    def _parse_finished(self, lines: list[str]) -> None:
        content = "".join(lines)
        match = re.search(r"Finished in (\d+)ms at \((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)", content)
        if match:
            self.result.duration = int(match.group(1))
            self.result.end_date_time = datetime.strptime(match.group(2), "%Y-%m-%d %H:%M:%S")
