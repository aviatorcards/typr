"""Word generation and settings."""

import random
import unittest

from typr.present import (
    HELP,
    HELP_COMPACT,
    digits,
    fit_config,
    help_lines,
    hint_line,
    sparkline,
    span_width,
    text_column,
)
from typr.font import FONT_ORDER, size_label
from typr.settings import (
    Settings,
    cycle_corpus,
    cycle_font,
    cycle_size,
    cycle_time,
    cycle_words,
    summary,
    to_config,
)
from typr.words import ENGLISH_200, ENGLISH_1K, generate, random_quote


class WordsTest(unittest.TestCase):
    def test_lists_are_everyday_words(self):
        self.assertEqual(len(ENGLISH_1K), 1000)
        self.assertEqual(len(ENGLISH_200), 200)
        self.assertIn("the", ENGLISH_200)
        self.assertIn("an", ENGLISH_200)
        self.assertTrue(all(word.isalpha() and word == word.lower() for word in ENGLISH_1K))

    def test_generation_is_deterministic_and_stays_in_the_list(self):
        first = generate("english", 40, False, False, random.Random(1))
        second = generate("english", 40, False, False, random.Random(1))
        self.assertEqual(first, second)
        self.assertEqual(len(first), 40)
        self.assertTrue(set(first) <= set(ENGLISH_200))
        self.assertTrue(all(a != b for a, b in zip(first, first[1:])))

    def test_wider_list_can_leave_the_common_200(self):
        words = generate("english1k", 400, False, False, random.Random(3))
        self.assertTrue(set(words) <= set(ENGLISH_1K))
        self.assertTrue(set(words) - set(ENGLISH_200))

    def test_punctuation_and_numbers(self):
        punct = generate("english", 80, True, False, random.Random(1), final=True)
        self.assertTrue(any(not char.isalpha() for word in punct for char in word))
        self.assertIn(punct[-1][-1], ".!?\"")
        numbers = generate("english", 80, False, True, random.Random(2))
        self.assertTrue(any(any(char.isdigit() for char in word) for word in numbers))

    def test_quotes_keep_their_own_punctuation(self):
        words = random_quote(random.Random(1))
        self.assertGreaterEqual(len(words), 3)
        self.assertTrue(any(not word.isalpha() for word in words))


class SettingsTest(unittest.TestCase):
    def test_time_cycle_wraps_and_leaves_quotes(self):
        settings = Settings(corpus="quotes")
        cycle_time(settings, 1)
        self.assertEqual(settings.corpus, "english")
        self.assertEqual(settings.limit, "time")
        self.assertEqual(settings.time_s, 60)
        cycle_time(settings, -1)
        self.assertEqual(settings.time_s, 30)

    def test_word_cycle_and_corpus_cycle(self):
        settings = Settings()
        cycle_words(settings, 1)
        self.assertEqual((settings.limit, settings.words_n), ("words", 50))
        cycle_corpus(settings, 1)
        self.assertEqual(settings.corpus, "english1k")
        self.assertEqual(to_config(settings).describe(), "50 words 1k")
        cycle_corpus(settings, -1)
        self.assertEqual(summary(settings), "50 words · english")
        cycle_font(settings, 1)
        self.assertEqual(settings.font, "plain")
        cycle_font(settings, 1)
        self.assertEqual(settings.font, "block")
        cycle_font(settings, -1)
        self.assertEqual(settings.font, "plain")
        self.assertEqual(len({len(name) for name in FONT_ORDER}), 1)
        self.assertEqual(settings.size, "small")
        cycle_size(settings, 1)
        self.assertEqual(settings.size, "medium")
        cycle_size(settings, 1)
        self.assertEqual(settings.size, "large")
        cycle_size(settings, 1)
        self.assertEqual(settings.size, "small")
        self.assertEqual(len({len(size_label(name)) for name in ("small", "medium", "large")}), 1)

    def test_config_line_fits_and_does_not_jump(self):
        settings = Settings()
        spans = fit_config(settings, 84)
        self.assertLessEqual(span_width(spans), 84)
        shown_wide = "".join(text for text, _ in spans)
        self.assertIn("typr", shown_wide)
        self.assertIn("small", shown_wide)
        self.assertLessEqual(span_width(fit_config(settings, 72)), 72)
        selected = Settings(time_s=60)
        idle = Settings(time_s=15)
        self.assertEqual(span_width(fit_config(selected, 90)), span_width(fit_config(idle, 90)))
        self.assertEqual(
            span_width(fit_config(Settings(size="small"), 100)),
            span_width(fit_config(Settings(size="medium"), 100)),
        )
        self.assertLessEqual(len(hint_line("idle", 40)), 40)
        self.assertIn("font", hint_line("idle", 72))
        self.assertIn("size", hint_line("idle", 72))
        self.assertLessEqual(len(hint_line("idle", 72)), 72)
        plain = Settings(font="plain")
        self.assertEqual(span_width(fit_config(settings, 90)), span_width(fit_config(plain, 90)))
        shown = "".join(text for text, _role in fit_config(settings, 90))
        self.assertIn("block", shown)
        self.assertIn("typr", shown)
        plain_line = "".join(text for text, _role in fit_config(plain, text_column(plain, 120)))
        self.assertIn("plain", plain_line)
        self.assertIn("serika", plain_line)
        self.assertLessEqual(text_column(settings, 200), 90)

    def test_digits_align_and_the_chart_has_one_column_per_cell(self):
        rows = digits(86)
        self.assertEqual(len(rows), 3)
        self.assertEqual(len({len(row) for row in rows}), 1)
        bars = sparkline([(0.0, 0), (1.0, 5), (2.0, 15)], 2.0, 8)
        self.assertEqual(len(bars), 8)

    def test_help_commands_share_one_column(self):
        wide = help_lines(90, 28)
        self.assertEqual(wide, HELP)
        narrow = help_lines(36, 12)
        self.assertEqual(narrow, HELP_COMPACT)
        self.assertLessEqual(len(narrow), 12)
        self.assertTrue(all(len(line) <= 36 for line in narrow))
        for lines in (wide, narrow):
            commands = [
                line
                for line in lines
                if line.startswith(("=", "<", "^", "[", "\\", ",", "tab", "ctrl", "esc"))
            ]
            columns = {_description_column(line) for line in commands}
            self.assertEqual(columns, {next(iter(columns))})
            self.assertGreaterEqual(len(commands), 8)


def _description_column(line: str) -> int:
    index = 0
    while index < len(line) and line[index] != " ":
        index += 1
    while index < len(line) and line[index] == " ":
        index += 1
    return index


if __name__ == "__main__":
    unittest.main()
