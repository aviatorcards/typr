"""Plain-text pieces of the screen: digits, the chart, and the option line."""

from __future__ import annotations

from typr.font import active_font, size_label
from typr.settings import Settings, corpus_label, summary

# Three rows, each glyph three columns. A space separates digits.
_FONT = {
    "0": ("█▀█", "█ █", "▀▀▀"),
    "1": ("▀█ ", " █ ", "▀▀▀"),
    "2": ("▀▀█", "█▀▀", "▀▀▀"),
    "3": ("▀▀█", " ▀█", "▀▀▀"),
    "4": ("█ █", "▀▀█", "  ▀"),
    "5": ("█▀▀", "▀▀█", "▀▀▀"),
    "6": ("█▀▀", "█▀█", "▀▀▀"),
    "7": ("▀▀█", " ▄▀", "  ▀"),
    "8": ("█▀█", "█▀█", "▀▀▀"),
    "9": ("█▀█", "▀▀█", " ▀▀"),
}

_BARS = "▁▂▃▄▅▆▇█"


def round_half_up(value: float) -> int:
    return int(value + 0.5)


def digits(number: int) -> list[str]:
    text = str(max(0, number))
    rows = ["", "", ""]
    for index, char in enumerate(text):
        glyph = _FONT.get(char, _FONT["0"])
        gap = "" if index == len(text) - 1 else " "
        for row in range(3):
            rows[row] += glyph[row] + gap
    return rows


def sparkline(
    samples: list[tuple[float, int]],
    elapsed: float,
    columns: int,
) -> list[tuple[str, int]]:
    """Return (character, level 0-7) bars of correct-character pace."""
    if columns <= 0:
        return []
    if elapsed <= 0 or not samples:
        return [(_BARS[0], 0) for _ in range(columns)]

    def correct_at(moment: float) -> int:
        value = 0
        for stamp, count in samples:
            if stamp <= moment + 1e-9:
                value = count
            else:
                break
        return value

    levels: list[float] = []
    for index in range(columns):
        start = elapsed * index / columns
        end = elapsed * (index + 1) / columns
        chars = max(0, correct_at(end) - correct_at(start))
        delta = end - start
        pace = (chars / 5) / (delta / 60) if delta > 0 else 0.0
        levels.append(pace)
    peak = max(levels) or 1.0
    bars: list[tuple[str, int]] = []
    for pace in levels:
        if pace <= 0:
            bars.append((_BARS[0], 0))
            continue
        level = int(round(pace / peak * (len(_BARS) - 1)))
        level = max(1, min(len(_BARS) - 1, level))
        bars.append((_BARS[level], level))
    return bars


def span_width(spans: list[tuple[str, str]]) -> int:
    return sum(len(text) for text, _role in spans)


def _chip(value: str, selected: bool) -> tuple[str, str]:
    # Brackets and spaces are the same width, so the line does not jump.
    text = f"[{value}]" if selected else f" {value} "
    return text, "selected" if selected else "idle"


def config_spans(
    settings: Settings,
    show_name: bool,
    show_theme: bool,
    show_font: bool = True,
) -> list[tuple[str, str]]:
    live = settings.corpus not in ("quotes", "passage")
    spans: list[tuple[str, str]] = []
    if show_name:
        spans.append(("typr", "accent"))
        spans.append(("  ", "dim"))
    for index, value in enumerate((15, 30, 60, 120)):
        if index:
            spans.append((" ", "dim"))
        selected = live and settings.limit == "time" and settings.time_s == value
        spans.append(_chip(str(value), selected))
    spans.append(("  ", "dim"))
    for index, value in enumerate((10, 25, 50, 100)):
        if index:
            spans.append((" ", "dim"))
        selected = live and settings.limit == "words" and settings.words_n == value
        spans.append(_chip(str(value), selected))
    spans.append(("  ", "dim"))
    spans.append((corpus_label(settings), "selected"))
    if show_font:
        spans.append(("  ", "dim"))
        spans.append((active_font(settings.font), "text"))
        spans.append(("  ", "dim"))
        spans.append((size_label(settings.size), "text"))
    if show_theme:
        spans.append(("  ", "dim"))
        spans.append((settings.theme, "dim"))
    return spans


def text_column(settings: Settings, width: int) -> int:
    """Centered reading column for the terminal font.

    A wide window stays at 72 columns, or up to 80 if the option line needs
    the room. A narrower window uses what it has.
    """
    room = max(20, width - 4)
    if room <= 72:
        return room
    needed = span_width(config_spans(settings, True, True, True))
    return min(room, max(72, min(needed, 80)))


def plain_body_rows() -> int:
    """Rows for options, three word lines with a blank between, stats, and the hint."""
    return 11


def plain_word_y(top: int, index: int) -> int:
    """Screen row of word line ``index``. A blank row sits between lines."""
    return top + 2 + index * 2


def fit_config(settings: Settings, width: int) -> list[tuple[str, str]]:
    # Drop the theme, then the name, before the font. The font name is how
    # you turn block letters on.
    for show_name, show_theme, show_font in (
        (True, True, True),
        (True, False, True),
        (False, False, True),
        (False, False, False),
    ):
        spans = config_spans(settings, show_name, show_theme, show_font)
        if span_width(spans) <= width:
            return spans
    return [(summary(settings), "selected")]


def hint_line(phase: str, width: int) -> str:
    full = {
        "idle": "<> time  ^v words  [] text  \\ theme  = font  ,. size  tab  esc quit",
        "run": "tab restart    esc quit",
        "results": "tab new   = font   ,. size   ctrl+r retry   esc quit",
    }[phase]
    if len(full) <= width:
        return full
    short = {
        "idle": "arrows config    tab restart    esc quit",
        "run": "tab restart    esc quit",
        "results": "tab new    esc quit",
    }[phase]
    if len(short) <= width:
        return short
    return "esc quit"


HELP = (
    "typr",
    "",
    "Type the words. The clock starts on your first key.",
    "",
    "<>         time: 15s, 30s, 60s, 120s",
    "^v         words: 10, 25, 50, 100",
    "[]         text: english, 1k, punct, numbers, expert, quotes",
    "\\          color theme",
    "=          letters: plain or block",
    ",.         size: small, medium, large",
    "tab        new test",
    "ctrl+r     retry the same words",
    "ctrl+w     clear the current word",
    "esc        quit",
    "",
    "WPM counts correct characters, five to a word.",
    "Accuracy counts wrong, extra, and skipped characters.",
    "A personal best needs at least 90% accuracy.",
    "",
    "any key to return",
)

# Fits the smallest screen the app will draw (36 columns, 12 rows).
HELP_COMPACT = (
    "typr",
    "<>      time",
    "^v      words",
    "[]      text",
    "\\       theme",
    "=       plain or block",
    ",.      letter size",
    "tab     new test",
    "ctrl+r  retry these words",
    "ctrl+w  clear this word",
    "esc     quit",
    "any key to return",
)


def help_lines(width: int, height: int) -> tuple[str, ...]:
    """Pick a help block that fits. Command rows stay left-aligned."""
    if len(HELP) <= height and all(len(line) <= width for line in HELP):
        return HELP
    return HELP_COMPACT
