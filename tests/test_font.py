"""Block letters grow with the window and stay aligned."""

import unittest

from typr.font import (
    GLYPHS,
    advance,
    block_rows,
    figure_scale,
    ink_rows,
    line_height,
    result_plan,
    text_scale,
    write,
)


class FontTest(unittest.TestCase):
    def test_glyphs_are_5_by_7(self):
        needed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        needed.update(".,'\"?!-;:()/")
        self.assertTrue(needed <= set(GLYPHS))
        for char, rows in GLYPHS.items():
            self.assertEqual(len(rows), 7, char)
            self.assertTrue(all(len(row) == 5 for row in rows), char)

    def test_confusable_letters_differ(self):
        for scale in (1, 2):
            for pair in ("Il", "l1", "I1", "O0", "S5", "uv"):
                self.assertNotEqual(ink_rows(pair[0], scale), ink_rows(pair[1], scale), pair)

    def test_scaled_rows_share_one_width(self):
        for scale in (1, 2, 3):
            rows = write("there before", scale)
            self.assertEqual(len(rows), line_height(scale))
            self.assertEqual(len(set(map(len, rows))), 1)
            self.assertTrue(any(char != " " for row in rows for char in row))

    def test_T_keeps_its_shape_at_the_smallest_size(self):
        self.assertEqual(ink_rows("T", 1), ("▀▀█▀▀", "  █  ", "  █  ", "  ▀  "))

    def test_a_larger_window_picks_a_larger_scale(self):
        self.assertEqual(text_scale(36, 12, 8), 0)
        small = text_scale(80, 24, 13)
        medium = text_scale(160, 50, 13)
        large = text_scale(240, 80, 13)
        self.assertGreaterEqual(small, 1)
        self.assertGreater(medium, small)
        self.assertGreaterEqual(large, medium)
        for width, height in ((80, 24), (100, 32), (160, 50), (240, 80)):
            scale = text_scale(width, height, 13)
            self.assertLessEqual(block_rows(scale), height)
            if scale:
                self.assertGreaterEqual((width - 2) // advance(scale), 13)

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
