"""Terminal color themes. Typed text uses the accent; mistakes use red."""

from __future__ import annotations

import curses
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    typed: int
    error: int
    extra: int
    untyped: int
    dim: int
    text: int
    good: int
    warn: int
    basic: int


THEMES = {
    "serika": Theme("serika", 220, 196, 167, 241, 245, 254, 114, 214, curses.COLOR_YELLOW),
    "nord": Theme("nord", 110, 196, 167, 241, 245, 254, 150, 222, curses.COLOR_CYAN),
    "dracula": Theme("dracula", 141, 196, 168, 241, 245, 254, 120, 222, curses.COLOR_MAGENTA),
    "gruvbox": Theme("gruvbox", 208, 196, 167, 241, 245, 254, 142, 214, curses.COLOR_YELLOW),
    "mono": Theme("mono", 255, 196, 245, 241, 245, 255, 255, 255, curses.COLOR_WHITE),
}

THEME_ORDER = ["serika", "nord", "dracula", "gruvbox", "mono"]


def apply_theme(name: str) -> dict[str, int]:
    theme = THEMES.get(name, THEMES["serika"])
    if not curses.has_colors():
        return _mono()
    try:
        curses.start_color()
    except curses.error:
        return _mono()
    default_bg = -1
    try:
        curses.use_default_colors()
    except curses.error:
        default_bg = curses.COLOR_BLACK
    rich = curses.COLORS >= 256
    if rich:
        _pair(1, theme.untyped, default_bg)
        _pair(2, theme.typed, default_bg)
        _pair(3, theme.error, default_bg)
        _pair(4, theme.extra, default_bg)
        _pair(5, theme.dim, default_bg)
        _pair(6, theme.text, default_bg)
        _pair(7, theme.good, default_bg)
        _pair(8, theme.warn, default_bg)
        _pair(9, 16, theme.typed)
    else:
        _pair(1, curses.COLOR_WHITE, default_bg)
        _pair(2, theme.basic, default_bg)
        _pair(3, curses.COLOR_RED, default_bg)
        _pair(4, curses.COLOR_RED, default_bg)
        _pair(5, curses.COLOR_WHITE, default_bg)
        _pair(6, curses.COLOR_WHITE, default_bg)
        _pair(7, curses.COLOR_GREEN, default_bg)
        _pair(8, curses.COLOR_YELLOW, default_bg)
        _pair(9, curses.COLOR_BLACK, theme.basic)
    bold = curses.A_BOLD
    dim = curses.A_DIM if not rich else 0
    return {
        "untyped": curses.color_pair(1) | (curses.A_DIM if not rich else 0),
        "correct": curses.color_pair(2) | bold,
        "accent": curses.color_pair(2) | bold,
        "selected": curses.color_pair(2) | bold,
        "incorrect": curses.color_pair(3),
        "bad": curses.color_pair(3),
        "extra": curses.color_pair(4) | dim,
        "dim": curses.color_pair(5) | (curses.A_DIM if not rich else 0),
        "idle": curses.color_pair(5) | (curses.A_DIM if not rich else 0),
        "text": curses.color_pair(6),
        "good": curses.color_pair(7) | bold,
        "warn": curses.color_pair(8),
        "caret": curses.color_pair(9),
        "space": curses.color_pair(1),
    }


def _pair(number: int, fg: int, bg: int) -> None:
    try:
        curses.init_pair(number, fg, bg)
    except curses.error:
        curses.init_pair(number, curses.COLOR_WHITE, curses.COLOR_BLACK)


def _mono() -> dict[str, int]:
    return {
        "untyped": curses.A_DIM,
        "correct": curses.A_BOLD,
        "accent": curses.A_BOLD,
        "selected": curses.A_BOLD,
        "incorrect": curses.A_BOLD,
        "bad": curses.A_BOLD,
        "extra": curses.A_DIM,
        "dim": curses.A_DIM,
        "idle": curses.A_DIM,
        "text": 0,
        "good": curses.A_BOLD,
        "warn": curses.A_BOLD,
        "caret": curses.A_REVERSE,
        "space": 0,
    }
