"""Block letters stay modest, aligned, and distinct."""

import unittest

from typr.font import (
    GLYPHS,
    SIZE_ORDER,
    block_rows,
    caret_bars,
    figure_scale,
    ink_rows,
    letter_gap,
    line_height,
    places,
    result_plan,
    run_width,
    text_scale,
    word_space,
    write,
)


class FontTest(unittest.TestCase):
    def test_glyphs_share_one_height(self):
        needed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        needed.update(".,'\"?!-;:()/")
        self.assertTrue(needed <= set(GLYPHS))
        for char, rows in GLYPHS.items():
            self.assertEqual(len(rows), 6, char)
            self.assertEqual(len({len(row) for row in rows}), 1, char)

    def test_confusable_letters_differ(self):
        pairs = (
            "ae",
            "ao",
            "ce",
            "g9",
            "gq",
            "gy",
            "s5",
            "sS",
            "yv",
            "uv",
            "nh",
            "Il",
            "l1",
            "I1",
            "O0",
            "pq",
        )
        for scale in (1, 2):
            for pair in pairs:
                self.assertNotEqual(ink_rows(pair[0], scale), ink_rows(pair[1], scale), (pair, scale))

    def test_letter_gap_is_one_column_and_words_are_wider(self):
        for scale in (1, 2, 3):
            self.assertEqual(letter_gap(scale), 1)
            self.assertGreaterEqual(word_space(scale), letter_gap(scale) + 2)
        spots = places("ab", 1)
        self.assertEqual(spots[1][0], spots[0][0] + spots[0][1] + 1)
        spaced = places("a b", 1)
        between = spaced[2][0] - (spaced[0][0] + spaced[0][1])
        self.assertEqual(between, word_space(1))
        self.assertGreater(between, 1)

    def test_a_120_column_line_holds_several_words(self):
        phrase = "there before wanted for why"
        self.assertGreaterEqual(phrase.count(" ") + 1, 5)
        self.assertLessEqual(run_width(phrase, 1), 118)
        shorter = "the you and that it is"
        self.assertGreaterEqual(shorter.count(" ") + 1, 6)
        self.assertLessEqual(run_width(shorter, 1), 118)
        scale = text_scale(120, 40, "something", "small")
        self.assertEqual(scale, 1)
        self.assertLessEqual(block_rows(scale), 40)

    def test_size_caps_the_scale_instead_of_filling_the_window(self):
        self.assertEqual(text_scale(36, 12, 8), 0)
        self.assertEqual(text_scale(240, 80, "something", "small"), 1)
        self.assertEqual(text_scale(120, 40, "something", "small"), 1)
        medium = text_scale(120, 40, "something", "medium")
        large = text_scale(200, 60, "something", "large")
        self.assertGreater(medium, 1)
        self.assertGreater(large, medium)
        for size in SIZE_ORDER:
            scale = text_scale(120, 40, "something", size)
            self.assertLessEqual(block_rows(scale), 40)
            self.assertLessEqual(run_width("something", scale), 118)

    def test_scaled_rows_share_one_width(self):
        for scale in (1, 2, 3):
            rows = write("there before", scale)
            self.assertEqual(len(rows), line_height(scale))
            self.assertEqual(len(set(map(len, rows))), 1)
            self.assertEqual(len(rows[0]), run_width("there before", scale))
            self.assertTrue(any(char != " " for row in rows for char in row))

    def test_T_keeps_its_shape_at_the_smallest_size(self):
        self.assertEqual(ink_rows("T", 1), ("▀▀█▀▀", "  █  ", "  ▀  "))

    def test_the_caret_is_an_underline_under_the_glyph(self):
        bars = caret_bars("cat", ["correct", "caret", "untyped"], 1)
        self.assertEqual(len(bars), 1)
        origin, bar = bars[0]
        self.assertEqual(origin, places("cat", 1)[1][0])
        self.assertEqual(bar, "▀" * places("cat", 1)[1][1])
        self.assertEqual(caret_bars("cat", ["untyped", "untyped", "untyped"], 1), [])

    def test_the_result_number_stays_on_the_screen(self):
        scale = figure_scale(80, 24)
        self.assertGreaterEqual(scale, 1)
        self.assertLessEqual(line_height(scale), 24 // 3)
        chars, spark, history, note, rows = result_plan(24, line_height(scale), True, False)
        self.assertLessEqual(rows, 24)
        self.assertTrue(chars)
        self.assertTrue(history)
        self.assertTrue(spark)
        tight, _, _, _, tight_rows = result_plan(12, 4, False, True)
        self.assertLessEqual(tight_rows, 12)
        self.assertFalse(tight)


if __name__ == "__main__":
    unittest.main()
