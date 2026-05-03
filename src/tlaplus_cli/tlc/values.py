"""TLA+ value parser.

Ported from ts-output-parser/parsers/tlcValues.ts.
"""

import re
from enum import Enum, auto
from typing import ClassVar

from .models import TlaValue


class TokenType(Enum):
    Primitive = auto()
    Range = auto()
    Name = auto()
    SetStart = auto()
    SetEnd = auto()
    SequenceStart = auto()
    SequenceEnd = auto()
    StructureStart = auto()
    StructureEnd = auto()
    StructureItemSeparator = auto()
    FunctionStart = auto()
    FunctionEnd = auto()
    ColonBracket = auto()
    AtAt = auto()
    Comma = auto()
    End = auto()


class Token:
    def __init__(self, token_type: TokenType, string: str):
        self.type = token_type
        self.str = string


class Tokenizer:
    CONST_TOKENS: ClassVar[list[tuple[TokenType, str]]] = [
        (TokenType.SetStart, "{"),
        (TokenType.SetEnd, "}"),
        (TokenType.SequenceStart, "<<"),
        (TokenType.SequenceEnd, ">>"),
        (TokenType.StructureStart, "["),
        (TokenType.StructureEnd, "]"),
        (TokenType.FunctionStart, "("),
        (TokenType.FunctionEnd, ")"),
        (TokenType.StructureItemSeparator, "|->"),
        (TokenType.Comma, ","),
        (TokenType.ColonBracket, ":>"),
        (TokenType.AtAt, "@@"),
    ]

    def __init__(self, lines: list[str]):
        self.lines = lines
        self.line_idx = 0
        self.col_idx = 0

    def next_token(self) -> Token:
        string = self._next_str()
        if string is None:
            return Token(TokenType.End, "")

        for token_type, token_str in self.CONST_TOKENS:
            if string.startswith(token_str):
                self.col_idx += len(token_str)
                return Token(token_type, token_str)

        # Regexp tokens
        regexps = [
            (TokenType.Range, r"^(-?\d+\.\.-?\d+)"),
            (TokenType.Primitive, r"^(-?\d+)"),
            (TokenType.Primitive, r"^(TRUE|FALSE)"),
            (TokenType.Name, r"^(\w+)"),
        ]

        if string.startswith('"'):
            # String token
            match = re.match(r'^("([^"\\]|\\.)*")', string)
            if match:
                token_str = match.group(1)
                self.col_idx += len(token_str)
                return Token(TokenType.Primitive, token_str)

        for token_type, pattern in regexps:
            match = re.match(pattern, string)
            if match:
                token_str = match.group(1)
                self.col_idx += len(token_str)
                return Token(token_type, token_str)

        msg = f"Cannot parse variable value at line {self.line_idx + 1}, col {self.col_idx + 1}: {string}"
        raise ValueError(msg)

    def _next_str(self) -> str | None:
        while self.line_idx < len(self.lines):
            line = self.lines[self.line_idx]
            while self.col_idx < len(line) and line[self.col_idx] == " ":
                self.col_idx += 1

            if self.col_idx == len(line):
                self.line_idx += 1
                self.col_idx = 0
                continue

            return line[self.col_idx :]
        return None


def parse_variable_value(name: str, lines: list[str]) -> TlaValue:
    """Parse a TLA+ variable value from output lines."""
    tokenizer = Tokenizer(lines)
    try:
        return _parse_value(name, tokenizer.next_token(), tokenizer)
    except (ValueError, IndexError):
        # If parsing fails, return a simple value with the full string
        return TlaValue(name, " ".join(lines).strip())


def _parse_value(key: str | int, token: Token, tokenizer: Tokenizer) -> TlaValue:
    if token.type == TokenType.End:
        msg = "Unexpected end of tokens"
        raise ValueError(msg)

    if token.type in (TokenType.Primitive, TokenType.Range, TokenType.Name):
        return TlaValue(key, token.str)

    if token.type == TokenType.SetStart:
        return _parse_collection(key, "{", "}", TokenType.SetEnd, tokenizer)

    if token.type == TokenType.SequenceStart:
        return _parse_collection(key, "<<", ">>", TokenType.SequenceEnd, tokenizer)

    if token.type == TokenType.StructureStart:
        # Could be a structure [a |-> 1] or a function [S -> T]
        # Or a record [a |-> 1, b |-> 2]
        return _parse_structure(key, "[", "]", TokenType.StructureEnd, tokenizer)

    if token.type == TokenType.FunctionStart:
        return _parse_value(key, tokenizer.next_token(), tokenizer)

    # Fallback
    return TlaValue(key, token.str)


def _parse_collection(key: str | int, prefix: str, postfix: str, end_type: TokenType, tokenizer: Tokenizer) -> TlaValue:
    items: list[TlaValue] = []
    token = tokenizer.next_token()
    while token.type not in (end_type, TokenType.End):
        item = _parse_value(len(items) + 1, token, tokenizer)
        items.append(item)
        token = tokenizer.next_token()
        if token.type == TokenType.Comma:
            token = tokenizer.next_token()

    full_str = prefix + ", ".join(item.value for item in items) + postfix
    return TlaValue(key, full_str, items)


def _parse_structure(key: str | int, prefix: str, postfix: str, end_type: TokenType, tokenizer: Tokenizer) -> TlaValue:
    items: list[TlaValue] = []
    token = tokenizer.next_token()
    while token.type not in (end_type, TokenType.End):
        if token.type != TokenType.Name:
            # Not a standard structure item, just read as a collection?
            item = _parse_value(len(items) + 1, token, tokenizer)
            items.append(item)
        else:
            item_key = token.str
            token = tokenizer.next_token()
            if token.type in (TokenType.StructureItemSeparator, TokenType.ColonBracket):
                item_val = _parse_value(item_key, tokenizer.next_token(), tokenizer)
                items.append(item_val)
            else:
                # Just a name in a collection?
                items.append(TlaValue(len(items) + 1, item_key))
                # We already consumed the next token, so we need to be careful.
                # This parser is a bit simplified.
                continue

        token = tokenizer.next_token()
        if token.type in (TokenType.Comma, TokenType.AtAt):
            token = tokenizer.next_token()

    full_str = prefix + ", ".join(f"{item.key} |-> {item.value}" for item in items) + postfix
    return TlaValue(key, full_str, items)
