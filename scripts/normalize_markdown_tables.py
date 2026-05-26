#!/usr/bin/env python3
"""Normalize Markdown tables for markdownlint MD060 compact style.

The script is intentionally narrow:
- only rewrites pipe tables outside fenced code blocks
- preserves blockquote prefixes
- keeps table cell text unchanged except for surrounding spacing
- aligns delimiter rows to the header row for MD060 aligned_delimiter
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DELIMITER_RE = re.compile(r"^:?-+:?$")
FENCE_RE = re.compile(r"^ {0,3}(```|~~~)")
BLOCKQUOTE_PREFIX_RE = re.compile(r"^((?:>\s*)*)(.*)$")


def split_prefix(line: str) -> tuple[str, str]:
    match = BLOCKQUOTE_PREFIX_RE.match(line.rstrip("\n"))
    if not match:
        return "", line.rstrip("\n")
    return match.group(1), match.group(2)


def is_table_row(content: str) -> bool:
    stripped = content.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def split_cells(content: str) -> list[str]:
    stripped = content.strip()
    return [cell.strip() for cell in stripped.removeprefix("|").removesuffix("|").split("|")]


def is_delimiter_row(content: str) -> bool:
    if not is_table_row(content):
        return False
    cells = split_cells(content)
    return bool(cells) and all(DELIMITER_RE.match(cell) for cell in cells)


def delimiter_cell(original: str, width: int) -> str:
    left = original.startswith(":")
    right = original.endswith(":")
    width = max(width, 1)

    if left and right:
        return ":" + ("-" * max(width - 2, 1)) + ":"
    if left:
        return ":" + ("-" * max(width - 1, 1))
    if right:
        return ("-" * max(width - 1, 1)) + ":"
    return "-" * width


def render_row(prefix: str, cells: list[str]) -> str:
    # MD060 compact style wants one space padding for non-empty cells and
    # one blank space total for empty cells: "| value | | value |".
    rendered_cells = [" " if cell == "" else f" {cell} " for cell in cells]
    return prefix + "|" + "|".join(rendered_cells) + "|\n"


def render_delimiter(prefix: str, header: list[str], delimiter: list[str]) -> str:
    cells = [
        delimiter_cell(delimiter_cell_text, len(header_cell))
        for header_cell, delimiter_cell_text in zip(header, delimiter, strict=True)
    ]
    return prefix + "| " + " | ".join(cells) + " |\n"


def normalize_text(text: str) -> str:
    lines = text.splitlines(keepends=True)
    changed = False
    in_fence = False
    index = 0

    while index < len(lines):
        prefix, content = split_prefix(lines[index])

        if FENCE_RE.match(content):
            in_fence = not in_fence
            index += 1
            continue

        if in_fence or index + 1 >= len(lines):
            index += 1
            continue

        next_prefix, next_content = split_prefix(lines[index + 1])
        if not (
            prefix == next_prefix
            and is_table_row(content)
            and is_delimiter_row(next_content)
        ):
            index += 1
            continue

        header = split_cells(content)
        delimiter = split_cells(next_content)
        if len(header) != len(delimiter):
            index += 1
            continue

        new_header = render_row(prefix, header)
        new_delimiter = render_delimiter(prefix, header, delimiter)
        if lines[index] != new_header:
            lines[index] = new_header
            changed = True
        if lines[index + 1] != new_delimiter:
            lines[index + 1] = new_delimiter
            changed = True

        row_index = index + 2
        while row_index < len(lines):
            row_prefix, row_content = split_prefix(lines[row_index])
            if row_prefix != prefix or not is_table_row(row_content):
                break

            cells = split_cells(row_content)
            new_row = render_row(prefix, cells)
            if lines[row_index] != new_row:
                lines[row_index] = new_row
                changed = True
            row_index += 1

        index = row_index

    return "".join(lines) if changed else text


def normalize_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    normalized = normalize_text(original)
    if normalized == original:
        return False
    path.write_text(normalized, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=Path)
    args = parser.parse_args()

    for path in args.files:
        if path.suffix.lower() != ".md" or not path.is_file():
            continue
        normalize_file(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
