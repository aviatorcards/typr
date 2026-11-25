"""The terminal screen."""

from __future__ import annotations

import curses
import math
import time
from dataclasses import dataclass

from typr.engine import Config, Stats, Test, make_test, new_rng
from typr.history import History
from typr.layout import layout, window
from typr.present import (
    digits,
    fit_config,
    help_lines,
    hint_line,
    round_half_up,
    sparkline,
    span_width,
)
from typr.settings import (
    Settings,
    cycle_corpus,
    cycle_theme,
    cycle_time,
    cycle_words,
    to_config,
)
from typr.theme import apply_theme

_KIND = {
    "correct": "correct",
    "incorrect": "incorrect",
    "extra": "extra",
    "untyped": "untyped",
    "caret": "caret",
    "space": "space",
}


@dataclass
class ResultView:
    stats: Stats
    title: str
    new_best: bool
    best: float | None
    average: float | None
    tests: int
    recent: list[int]
    warning: str | None


class App:
    def __init__(
        self,
        settings: Settings,
        fixed_seed: int | None,
        passage: list[str] | None,
        history: History,
    ) -> None:
        self.settings = settings
        self.fixed_seed = fixed_seed
        self.passage = passage
        self.history = history
        self.phase = "test"
        self.return_phase = "test"
        self.result: ResultView | None = None
        self.dirty = True
        self.last_blink: bool | None = None
        self._attr_theme: str | None = None
        self._attr_cache: dict[str, int] = {}
        self.test = self._build(to_config(settings), fixed_seed)

    def run(self, stdscr) -> None:
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        stdscr.keypad(True)
        stdscr.timeout(100)
        try:
            stdscr.leaveok(True)
        except curses.error:
            pass
        self.dirty = True
        while True:
            now = time.perf_counter()
            if self.phase == "test" and self.test.expired(now):
                self.test.finish(self.test.started_at + self.test.config.count)  # type: ignore[operator]
                self._complete()
            blink = (int(now / 0.53) % 2) == 0
            blink_changed = self.phase == "test" and blink != self.last_blink
            if self.dirty or blink_changed or self._running():
                self._draw(stdscr, blink, now)
                self.last_blink = blink
                self.dirty = False
            key = _read_key(stdscr)
            if key is None:
                continue
            if not self._handle(key, time.perf_counter()):
                break
            self.dirty = True

    def _build(self, config: Config, seed: int | None) -> Test:
        rng, actual = new_rng(seed)
        passage = self.passage if config.corpus == "passage" else None
        return make_test(config, rng, actual, passage=passage)

    def _new(self) -> None:
        self.test = self._build(to_config(self.settings), self.fixed_seed)
        self.phase = "test"
        self.result = None

    def _retry(self) -> None:
        self.test = self._build(self.test.config, self.test.seed)
        self.phase = "test"
        self.result = None

    def _running(self) -> bool:
        return self.phase == "test" and self.test.started and not self.test.finished

    def _handle(self, key: str, now: float) -> bool:
        if key in ("ignore", "resize"):
            return True
        if key == "quit":
            return False
        if self.phase == "help":
            self.phase = self.return_phase
            return True
        if key == "esc":
            return False
        if key == "?" and not self._running():
            self.return_phase = self.phase
            self.phase = "help"
            return True
        if key == "\\" and not self._running():
            cycle_theme(self.settings)
            self._attr_theme = None
            return True
        if key == "tab":
            self._new()
            return True
        if key == "ctrl-r":
            self._retry()
            return True
        if self.phase == "results":
            if key in ("enter", "r", "R"):
                self._new()
            elif key in ("q", "Q"):
                return False
            return True
        if not self._running():
            if key == "left":
                cycle_time(self.settings, -1)
                self._new()
                return True
            if key == "right":
                cycle_time(self.settings, 1)
                self._new()
                return True
            if key == "up":
                cycle_words(self.settings, 1)
                self._new()
                return True
            if key == "down":
                cycle_words(self.settings, -1)
                self._new()
                return True
            if key == "[":
                cycle_corpus(self.settings, -1)
                self._new()
                return True
            if key == "]":
                cycle_corpus(self.settings, 1)
                self._new()
                return True
            if key == "enter":
                return True
        elif self.test.expired(now):
            self.test.finish(self.test.started_at + self.test.config.count)  # type: ignore[operator]
            self._complete()
            return True
        if key == "backspace":
            self.test.backspace(now)
        elif key == "ctrl-w":
            self.test.clear_word(now)
        elif key == " ":
            self.test.space(now)
        elif len(key) == 1 and key.isprintable():
            self.test.type_char(key, now)
        if self.test.finished:
            self._complete()
        return True

    def _complete(self) -> None:
        if self.phase == "results":
            return
        stats = self.test.stats(self.test.finished_at or time.perf_counter())
        bucket = self.test.config.bucket
        prior = [row for row in self.history.tests if row.get("bucket") == bucket]
        qualifying = [row["wpm"] for row in prior if row.get("acc", 0) >= 90]
        prior_best = max(qualifying) if qualifying else None
        qualifies = stats.acc >= 90 and not stats.disqualified and stats.correct > 0
        new_best = bool(qualifies and (prior_best is None or stats.wpm > prior_best))
        warning = None
        saved = False
        if stats.disqualified:
            warning = "not saved  ·  input was too fast to be human"
        elif stats.correct <= 0:
            warning = "not saved"
        else:
            record = {
                "at": int(time.time()),
                "bucket": bucket,
                "label": self.test.config.describe(),
                "wpm": round(stats.wpm, 2),
                "raw": round(stats.raw, 2),
                "acc": round(stats.acc, 2),
                "consistency": None if stats.consistency is None else round(stats.consistency, 2),
                "correct": stats.correct,
                "incorrect": stats.incorrect,
                "extra": stats.extra,
                "missed": stats.missed,
                "seconds": round(stats.seconds, 3),
            }
            saved = self.history.add(record)
            if not saved:
                warning = "couldn't write history"
        best = prior_best
        if qualifies and saved:
            best = stats.wpm if best is None else max(best, stats.wpm)
        scores = [row["wpm"] for row in prior]
        count = len(prior)
        recent = [round_half_up(value) for value in scores[-7:]]
        if saved:
            scores.append(stats.wpm)
            count += 1
            recent.append(round_half_up(stats.wpm))
            recent = recent[-8:]
        average = sum(scores) / len(scores) if scores else None
        title = self.test.config.describe()
        if self.test.config.mode != "time":
            title = f"{title}  ·  {stats.seconds:.1f}s"
        self.result = ResultView(
            stats=stats,
            title=title,
            new_best=new_best and saved,
            best=best,
            average=average,
            tests=count,
            recent=recent,
            warning=warning,
        )
        self.phase = "results"

    def _colors(self) -> dict[str, int]:
        if self._attr_theme != self.settings.theme or not self._attr_cache:
            self._attr_cache = apply_theme(self.settings.theme)
            self._attr_theme = self.settings.theme
        return self._attr_cache

    def _draw(self, stdscr, blink: bool, now: float) -> None:
        stdscr.erase()
        attrs = self._colors()
        height, width = stdscr.getmaxyx()
        if height < 12 or width < 36:
            _draw_too_small(stdscr, attrs)
        elif self.phase == "help":
            _draw_help(stdscr, attrs)
        elif self.phase == "results" and self.result is not None:
            _draw_results(stdscr, attrs, self.result, self.test)
        else:
            _draw_test(stdscr, attrs, self.settings, self.test, self.history, blink, now)
        stdscr.refresh()


def _draw_too_small(stdscr, attrs: dict[str, int]) -> None:
    height, width = stdscr.getmaxyx()
    message = "typr needs a bigger terminal"
    _put(stdscr, height // 2, max(0, (width - len(message)) // 2), message, attrs["dim"])


def _draw_help(stdscr, attrs: dict[str, int]) -> None:
    height, width = stdscr.getmaxyx()
    lines = help_lines(width, height)
    block = max((len(line) for line in lines), default=0)
    left = max(0, (width - block) // 2)
    top = max(0, (height - len(lines)) // 2)
    last = len(lines) - 1
    for index, line in enumerate(lines):
        role = "accent" if index == 0 else "dim" if index == last else "text"
        # Share one left edge so the command column stays straight.
        if index in (0, last):
            x = left + max(0, (block - len(line)) // 2)
        else:
            x = left
        _put(stdscr, top + index, x, line, attrs[role])


def _draw_test(stdscr, attrs, settings: Settings, test: Test, history: History, blink: bool, now: float) -> None:
    height, width = stdscr.getmaxyx()
    column = max(20, min(72, width - 4))
    left = max(0, (width - column) // 2)
    block = 9
    top = max(0, (height - block) // 2)
    phase = "run" if test.started and not test.finished else "idle"
    _paint(stdscr, top, left, fit_config(settings, column), attrs, mute=phase == "run")
    lines = window(
        layout(test.targets, test.typed, min(test.current, max(0, len(test.targets) - 1)), column, blink),
        min(test.current, max(0, len(test.targets) - 1)),
    )
    for index, line in enumerate(lines):
        _paint_cells(stdscr, top + 2 + index, left, line.cells, attrs, column)
    best = _best(history, test.config.bucket)
    _paint(stdscr, top + 6, left, _live_stats(test, best, column, now), attrs)
    hint = hint_line(phase, column)
    _put(stdscr, top + 8, left, hint, attrs["dim"])


def _draw_results(stdscr, attrs, view: ResultView, test: Test) -> None:
    height, width = stdscr.getmaxyx()
    column = max(20, min(72, width - 4))
    left = max(0, (width - column) // 2)
    show_digits = height >= 16 and column >= 24
    show_spark = height >= 22
    show_chars = height >= 18
    show_history = height >= 20
    rows = 1 + 1 + (3 if show_digits else 1) + 1 + 1
    if show_spark:
        rows += 2
    if show_chars:
        rows += 2
    if show_history:
        rows += 1 + (1 if view.recent else 0)
    if view.warning:
        rows += 1
    rows += 2
    top = max(0, (height - rows) // 2)
    y = top
    _put(stdscr, y, left, view.title, attrs["dim"])
    y += 2
    figure = digits(round_half_up(view.stats.wpm))
    number_role = "good" if view.new_best else "accent"
    if show_digits:
        for row in figure:
            _put(stdscr, y, left, row, attrs[number_role])
            y += 1
        label_x = left + len(figure[0]) + 2
        _put(stdscr, top + 3, label_x, "wpm", attrs["dim"])
        if view.new_best:
            _put(stdscr, top + 4, label_x, "new best", attrs["good"])
        elif view.warning:
            _put(stdscr, top + 4, label_x, view.warning, attrs["warn"])
        y += 1
    else:
        text = f"{round_half_up(view.stats.wpm)} wpm"
        if view.new_best:
            text += "   new best"
        _put(stdscr, y, left, text, attrs[number_role])
        y += 2
        if view.warning and not view.new_best:
            _put(stdscr, y - 1, left, view.warning, attrs["warn"])
    _paint(stdscr, y, left, _metrics(view.stats), attrs)
    y += 2
    if show_spark:
        bars = sparkline(test.samples, view.stats.seconds, min(column, 56))
        _paint_bars(stdscr, y, left, bars, attrs)
        y += 2
    if show_chars:
        spans = _chars(view.stats)
        if span_width(spans) > column:
            spans = _chars(view.stats, compact=True)
        _paint(stdscr, y, left, spans, attrs)
        y += 2
    if show_history:
        _paint(stdscr, y, left, _history_line(view), attrs)
        y += 1
        if view.recent:
            _paint_recent(stdscr, y, left, view.recent, attrs)
            y += 1
    y += 1
    _put(stdscr, y, left, hint_line("results", column), attrs["dim"])


def _live_stats(test: Test, best: float | None, width: int, now: float) -> list[tuple[str, str]]:
    if not test.started:
        if best is None:
            return []
        label = f"best {round_half_up(best)}"
        gap = max(1, width - len(label))
        return [(" " * gap, "dim"), (label, "dim")]
    stats = test.stats(now)
    wpm = "--" if stats.seconds < 0.5 else str(round_half_up(stats.wpm))
    acc_role = "good" if stats.acc >= 98 else "warn" if stats.acc < 95 else "text"
    clock_role = "dim"
    if test.config.mode == "time" and _remaining(test, now) <= 5:
        clock_role = "warn"
    spans = [
        (wpm, "accent"),
        (" wpm", "dim"),
        ("    ", "dim"),
        (f"{stats.acc:.0f}%", acc_role),
        ("    ", "dim"),
        (_clock(test, now), clock_role),
    ]
    if best is not None:
        label = f"best {round_half_up(best)}"
        used = span_width(spans)
        if used + 2 + len(label) <= width:
            spans.append((" " * (width - used - len(label)), "dim"))
            spans.append((label, "dim"))
    return spans


def _remaining(test: Test, now: float) -> int:
    left = test.config.count - test.elapsed(now)
    if left <= 0:
        return 0
    return int(math.ceil(left - 1e-9))


def _clock(test: Test, now: float) -> str:
    if test.config.mode == "time":
        return f"{_remaining(test, now)}s"
    total = len(test.targets) if test.config.mode == "quote" else test.config.count
    return f"{min(test.current, total)}/{total}"


def _metrics(stats: Stats) -> list[tuple[str, str]]:
    acc_role = "good" if stats.acc >= 98 else "warn" if stats.acc < 95 else "text"
    consistency = "--" if stats.consistency is None else f"{round_half_up(stats.consistency)}%"
    return [
        ("acc ", "dim"),
        (f"{stats.acc:.1f}%", acc_role),
        ("    raw ", "dim"),
        (str(round_half_up(stats.raw)), "text"),
        ("    cons ", "dim"),
        (consistency, "text"),
    ]


def _chars(stats: Stats, compact: bool = False) -> list[tuple[str, str]]:
    if compact:
        return [
            (str(stats.correct), "good"),
            ("/", "dim"),
            (str(stats.incorrect), "bad"),
            ("/", "dim"),
            (str(stats.extra), "bad"),
            ("/", "dim"),
            (str(stats.missed), "warn"),
            ("  correct/wrong/extra/missed", "dim"),
        ]
    return [
        (str(stats.correct), "good"),
        (" correct", "dim"),
        ("    ", "dim"),
        (str(stats.incorrect), "bad"),
        (" wrong", "dim"),
        ("    ", "dim"),
        (str(stats.extra), "bad"),
        (" extra", "dim"),
        ("    ", "dim"),
        (str(stats.missed), "warn"),
        (" missed", "dim"),
    ]


def _history_line(view: ResultView) -> list[tuple[str, str]]:
    best = "--" if view.best is None else str(round_half_up(view.best))
    average = "--" if view.average is None else str(round_half_up(view.average))
    return [
        ("best ", "dim"),
        (best, "good" if view.new_best else "text"),
        ("    avg ", "dim"),
        (average, "text"),
        ("    tests ", "dim"),
        (str(view.tests), "text"),
    ]


def _best(history: History, bucket: str) -> float | None:
    scores = [
        row["wpm"]
        for row in history.tests
        if row.get("bucket") == bucket and row.get("acc", 0) >= 90
    ]
    return max(scores) if scores else None


def _paint(stdscr, y: int, x: int, spans: list[tuple[str, str]], attrs, mute: bool = False) -> None:
    for text, role in spans:
        attr = attrs["dim"] if mute else attrs.get(role, 0)
        _put(stdscr, y, x, text, attr)
        x += len(text)


def _paint_cells(stdscr, y: int, x: int, cells, attrs, limit: int) -> None:
    index = 0
    column = x
    end = x + limit
    while index < len(cells) and column < end:
        kind = cells[index].kind
        nxt = index + 1
        while nxt < len(cells) and cells[nxt].kind == kind and column + (nxt - index) < end:
            nxt += 1
        text = "".join(cell.ch for cell in cells[index:nxt])
        room = end - column
        text = text[:room]
        _put(stdscr, y, column, text, attrs.get(_KIND.get(kind, "text"), 0))
        column += len(text)
        index = nxt


def _paint_bars(stdscr, y: int, x: int, bars: list[tuple[str, int]], attrs) -> None:
    index = 0
    column = x
    while index < len(bars):
        level = bars[index][1]
        nxt = index + 1
        while nxt < len(bars) and (bars[nxt][1] <= 2) == (level <= 2):
            nxt += 1
        text = "".join(char for char, _level in bars[index:nxt])
        role = "dim" if level <= 2 else "accent"
        _put(stdscr, y, column, text, attrs[role])
        column += len(text)
        index = nxt


def _paint_recent(stdscr, y: int, x: int, recent: list[int], attrs) -> None:
    for index, value in enumerate(recent):
        role = "accent" if index == len(recent) - 1 else "dim"
        text = str(value)
        _put(stdscr, y, x, text, attrs[role])
        x += len(text) + 2


def _put(stdscr, y: int, x: int, text: str, attr: int = 0) -> None:
    if not text:
        return
    height, width = stdscr.getmaxyx()
    if y < 0 or y >= height:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    room = width - x
    if y == height - 1:
        room -= 1
    if room <= 0:
        return
    text = text[:room]
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def _read_key(stdscr):
    try:
        key = stdscr.get_wch()
    except curses.error:
        return None
    return normalize(key)


def normalize(key) -> str:
    if isinstance(key, int):
        mapping = {
            curses.KEY_BACKSPACE: "backspace",
            curses.KEY_LEFT: "left",
            curses.KEY_RIGHT: "right",
            curses.KEY_UP: "up",
            curses.KEY_DOWN: "down",
            curses.KEY_RESIZE: "resize",
            curses.KEY_ENTER: "enter",
            curses.KEY_BTAB: "tab",
            27: "esc",
            127: "backspace",
            8: "backspace",
            10: "enter",
            13: "enter",
            9: "tab",
        }
        return mapping.get(key, "ignore")
    if key in ("\x7f", "\b", "\x08"):
        return "backspace"
    if key == "\t":
        return "tab"
    if key in ("\n", "\r"):
        return "enter"
    if key == "\x1b":
        return "esc"
    if key in ("\x03", "\x04"):
        return "quit"
    if key == "\x12":
        return "ctrl-r"
    if key == "\x17":
        return "ctrl-w"
    if key.isprintable():
        return key
    return "ignore"
