"""Test settings and the keys that change them before you start."""

from __future__ import annotations

from dataclasses import dataclass

from typr.engine import Config
from typr.font import FONT_ORDER, SIZE_ORDER, active_font, active_size
from typr.theme import THEME_ORDER

TIME_OPTIONS = (15, 30, 60, 120)
WORD_OPTIONS = (10, 25, 50, 100)


@dataclass
class Settings:
    limit: str = "time"
    time_s: int = 30
    words_n: int = 25
    corpus: str = "english"
    punct: bool = False
    numbers: bool = False
    theme: str = "serika"
    font: str = "block"
    size: str = "small"
    passage_name: str = ""
    base_corpus: str = "english"


def presets(settings: Settings) -> list[tuple[str, bool, bool, str]]:
    items = [
        ("english", False, False, "english"),
        ("english1k", False, False, "1k"),
        ("english", True, False, "punct"),
        ("english", False, True, "numbers"),
        ("english", True, True, "expert"),
        ("quotes", False, False, "quotes"),
    ]
    if settings.passage_name:
        items.append(("passage", False, False, settings.passage_name))
    return items


def corpus_label(settings: Settings) -> str:
    if settings.corpus == "quotes":
        return "quotes"
    if settings.corpus == "passage":
        return settings.passage_name or "passage"
    base = "1k" if settings.corpus == "english1k" else "english"
    if settings.punct and settings.numbers:
        return "expert" if base == "english" else "1k expert"
    if settings.punct:
        return "punct" if base == "english" else "1k punct"
    if settings.numbers:
        return "numbers" if base == "english" else "1k numbers"
    return base


def to_config(settings: Settings) -> Config:
    special = settings.corpus in ("quotes", "passage")
    if settings.corpus == "quotes":
        mode, count, label = "quote", 0, "quotes"
    elif settings.corpus == "passage":
        mode, count = "quote", 0
        label = settings.passage_name or "passage"
    elif settings.limit == "words":
        mode, count, label = "words", settings.words_n, corpus_label(settings)
    else:
        mode, count, label = "time", settings.time_s, corpus_label(settings)
    return Config(
        mode=mode,
        count=count,
        corpus=settings.corpus,
        punct=False if special else settings.punct,
        numbers=False if special else settings.numbers,
        label=label,
    )


def summary(settings: Settings) -> str:
    if settings.corpus == "quotes":
        return "quote"
    if settings.corpus == "passage":
        return settings.passage_name or "passage"
    head = f"{settings.time_s}s" if settings.limit == "time" else f"{settings.words_n} words"
    return f"{head} · {corpus_label(settings)}"


def _leave_special(settings: Settings) -> None:
    if settings.corpus in ("quotes", "passage"):
        settings.corpus = settings.base_corpus if settings.base_corpus in ("english", "english1k") else "english"
        settings.punct = False
        settings.numbers = False


def cycle_time(settings: Settings, direction: int) -> None:
    _leave_special(settings)
    settings.limit = "time"
    options = list(TIME_OPTIONS)
    index = options.index(settings.time_s) if settings.time_s in options else 0
    settings.time_s = options[(index + direction) % len(options)]


def cycle_words(settings: Settings, direction: int) -> None:
    _leave_special(settings)
    settings.limit = "words"
    options = list(WORD_OPTIONS)
    index = options.index(settings.words_n) if settings.words_n in options else 0
    settings.words_n = options[(index + direction) % len(options)]


def cycle_corpus(settings: Settings, direction: int) -> None:
    items = presets(settings)
    key = (settings.corpus, settings.punct, settings.numbers)
    index = next((i for i, item in enumerate(items) if item[:3] == key), -1)
    chosen = items[(index + direction) % len(items)]
    settings.corpus, settings.punct, settings.numbers = chosen[0], chosen[1], chosen[2]
    if settings.corpus in ("english", "english1k"):
        settings.base_corpus = settings.corpus


def cycle_theme(settings: Settings) -> None:
    index = THEME_ORDER.index(settings.theme) if settings.theme in THEME_ORDER else -1
    settings.theme = THEME_ORDER[(index + 1) % len(THEME_ORDER)]


def cycle_font(settings: Settings, direction: int = 1) -> None:
    name = active_font(settings.font)
    index = FONT_ORDER.index(name)
    settings.font = FONT_ORDER[(index + direction) % len(FONT_ORDER)]


def cycle_size(settings: Settings, direction: int = 1) -> None:
    name = active_size(settings.size)
    index = SIZE_ORDER.index(name)
    settings.size = SIZE_ORDER[(index + direction) % len(SIZE_ORDER)]
