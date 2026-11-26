"""Command line entry for typr."""

from __future__ import annotations

import argparse
import curses
import locale
import os
import sys
from pathlib import Path

from typr import __version__
from typr.history import History, default_dir
from typr.font import FONT_ORDER
from typr.settings import Settings
from typr.theme import THEME_ORDER
from typr.ui import App
from typr.words import load_passage


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    passage = None
    if args.passage is not None:
        if not args.passage.is_file():
            sys.stderr.write(f"typr: no such file: {args.passage}\n")
            return 1
        try:
            passage = load_passage(args.passage)
        except (OSError, UnicodeError, ValueError) as exc:
            sys.stderr.write(f"typr: {exc}\n")
            return 1
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        sys.stderr.write("typr needs an interactive terminal\n")
        return 1
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass
    os.environ.setdefault("ESCDELAY", "25")
    settings = Settings(theme=args.theme, font=args.font)
    if args.words is not None:
        settings.limit = "words"
        settings.words_n = args.words
    elif args.time is not None:
        settings.limit = "time"
        settings.time_s = args.time
    if args.corpus == "english1k":
        settings.corpus = "english1k"
        settings.base_corpus = "english1k"
    elif args.corpus == "quotes":
        settings.corpus = "quotes"
    settings.punct = args.punct
    settings.numbers = args.numbers
    if passage is not None:
        settings.corpus = "passage"
        settings.passage_name = args.passage.stem[:24]
        settings.punct = False
        settings.numbers = False
    directory = args.data_dir if args.data_dir is not None else default_dir()
    history = History(directory / "history.json", enabled=not args.no_save)
    app = App(settings, args.seed, passage, history)
    try:
        curses.wrapper(app.run)
    except KeyboardInterrupt:
        return 0
    except curses.error as exc:
        sys.stderr.write(f"typr could not start: {exc}\n")
        return 1
    return 0


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="typr",
        description="A terminal typing test.",
        epilog=(
            "Inside the test, arrow keys change the length, [ ] change the text, "
            "\\ changes the theme, = changes the font, tab starts a new test, and esc quits."
        ),
    )
    limit = parser.add_mutually_exclusive_group()
    limit.add_argument("-t", "--time", type=int, choices=(15, 30, 60, 120), help="seconds")
    limit.add_argument("-w", "--words", type=int, choices=(10, 25, 50, 100), help="word count")
    parser.add_argument(
        "-c",
        "--corpus",
        choices=("english", "english1k", "quotes"),
        default="english",
        help="english is the common 200, english1k is wider, quotes are short passages",
    )
    parser.add_argument("-p", "--punct", action="store_true", help="add capitalization and punctuation")
    parser.add_argument("-n", "--numbers", action="store_true", help="mix numbers into the words")
    parser.add_argument("--theme", choices=THEME_ORDER, default="serika")
    parser.add_argument(
        "--font",
        choices=FONT_ORDER,
        default="block",
        help="block letters grow with the window; plain uses the terminal font",
    )
    parser.add_argument("--seed", type=int, help="repeat the same words every restart")
    parser.add_argument("--passage", type=Path, help="type this text file instead of random words")
    parser.add_argument("--data-dir", type=Path, help="where history.json is stored")
    parser.add_argument("--no-save", action="store_true", help="do not write the result to history")
    parser.add_argument("--version", action="version", version=f"typr {__version__}")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
