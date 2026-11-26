"""Wrap the prompt into lines of styled cells.

The caret is an overlay. Turning the blink off changes color, not width,
so the words do not shift every half second.

``measure`` is optional. Without it, every cell is one column, which is
how plain text wraps. Block letters pass the width of each glyph.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Cell:
    ch: str
    kind: str


@dataclass(frozen=True)
class Line:
    cells: tuple[Cell, ...]
    words: tuple[int, ...]


def layout(
    words: list[str],
    typed: list[str],
    current: int,
    width: int,
    caret_on: bool,
    measure: Callable[[str], int] | None = None,
    gap: int = 0,
) -> list[Line]:
    width = max(4, width)
    rendered: list[tuple[int, list[Cell], bool]] = []
    for index, target in enumerate(words):
        entered = typed[index] if index < len(typed) else ""
        cells, caret_after = _render_word(target, entered, index == current, caret_on)
        rendered.append((index, cells, caret_after))

    tokens: list[tuple[str, list[Cell], int | None]] = []
    for position, (index, cells, caret_after) in enumerate(rendered):
        if position > 0 and not rendered[position - 1][2]:
            tokens.append(("gap", [Cell(" ", "space")], None))
        tokens.append(("word", cells, index))
        if caret_after:
            tokens.append(("gap", [Cell(" ", "caret" if caret_on else "space")], None))
    return _wrap(tokens, width, measure, gap)


def window(lines: list[Line], current: int, rows: int = 3) -> list[Line]:
    start = 0
    for index, line in enumerate(lines):
        if current in line.words:
            start = index
            break
    visible = list(lines[start : start + rows])
    while len(visible) < rows:
        visible.append(Line((), ()))
    return visible


def plain(line: Line) -> str:
    return "".join(cell.ch for cell in line.cells)


def _render_word(
    target: str,
    typed: str,
    active: bool,
    caret_on: bool,
) -> tuple[list[Cell], bool]:
    cells: list[Cell] = []
    for index, char in enumerate(target):
        if index < len(typed):
            got = typed[index]
            kind = "correct" if got == char else "incorrect"
            cells.append(Cell(got, kind))
        else:
            kind = "untyped"
            if active and index == len(typed):
                kind = "caret" if caret_on else "untyped"
            cells.append(Cell(char, kind))
    for char in typed[len(target) :]:
        cells.append(Cell(char, "extra"))
    caret_after = active and len(typed) >= len(target)
    return cells, caret_after


def _token_width(cells: list[Cell], measure: Callable[[str], int] | None, gap: int) -> int:
    if measure is None:
        return len(cells)
    total = 0
    for index, cell in enumerate(cells):
        total += measure(cell.ch)
        if gap and index + 1 < len(cells) and cell.ch != " " and cells[index + 1].ch != " ":
            total += gap
    return total


def _wrap(
    tokens: list[tuple[str, list[Cell], int | None]],
    width: int,
    measure: Callable[[str], int] | None = None,
    gap: int = 0,
) -> list[Line]:
    lines: list[Line] = []
    cells: list[Cell] = []
    words: list[int] = []
    used = 0

    def flush() -> None:
        nonlocal cells, words, used
        if cells:
            lines.append(Line(tuple(cells), tuple(words)))
        cells = []
        words = []
        used = 0

    for kind, token_cells, index in tokens:
        need = _token_width(token_cells, measure, gap)
        is_caret_gap = kind == "gap" and token_cells and token_cells[0].kind == "caret"
        if kind == "gap" and not cells:
            if is_caret_gap:
                cells.extend(token_cells)
                used += need
            continue
        if used + need > width and cells:
            flush()
            if kind == "gap":
                if is_caret_gap:
                    cells.extend(token_cells)
                    used += need
                continue
        cells.extend(token_cells)
        used += need
        if index is not None:
            words.append(index)
    flush()
    if not lines:
        lines.append(Line((), ()))
    return lines
