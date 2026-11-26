"""Word wrapping and the caret."""

import curses
import unittest

from typr.layout import layout, plain, window
from typr.ui import cell_attr


def kinds(words, typed, current, width, caret=True):
    lines = layout(words, typed, current, width, caret)
    return [cell.kind for line in lines for cell in line.cells], "".join(plain(line) for line in lines)


class LayoutTest(unittest.TestCase):
    def test_caret_sits_on_the_next_untyped_letter(self):
        got, text = kinds(["cat", "dog"], ["ca", ""], 0, 20)
        self.assertEqual(text, "cat dog")
        self.assertEqual(got, ["correct", "correct", "caret", "space", "untyped", "untyped", "untyped"])

    def test_finished_word_puts_the_caret_on_the_following_space(self):
        got, text = kinds(["cat", "dog"], ["cat", ""], 0, 20)
        self.assertEqual(text, "cat dog")
        self.assertEqual(got[3], "caret")
        self.assertEqual(got.count("caret"), 1)

    def test_mistakes_show_what_was_typed(self):
        got, text = kinds(["cat"], ["cx"], 0, 20)
        self.assertEqual(text, "cxt")
        self.assertEqual(got, ["correct", "incorrect", "caret"])

    def test_extra_characters_and_a_trailing_caret(self):
        got, text = kinds(["ab"], ["abXY"], 0, 20)
        self.assertEqual(text, "abXY ")
        self.assertEqual(got, ["correct", "correct", "extra", "extra", "caret"])

    def test_blink_does_not_change_the_width(self):
        words = ["hello", "world", "again"]
        typed = ["hello", "wor", ""]
        on = layout(words, typed, 1, 40, True)
        off = layout(words, typed, 1, 40, False)
        self.assertEqual([len(line.cells) for line in on], [len(line.cells) for line in off])
        off_kinds = [cell.kind for line in off for cell in line.cells]
        self.assertNotIn("caret", off_kinds)

    def test_words_wrap_on_spaces(self):
        lines = layout(["hello", "world", "again"], ["", "", ""], 0, 11, True)
        self.assertEqual([plain(line) for line in lines], ["hello world", "again"])

    def test_a_measured_line_wraps_on_glyph_width(self):
        def measure(char):
            return 4 if char != " " else 3

        lines = layout(["aa", "bb"], ["", ""], 0, 11, True, measure=measure, gap=1)
        # "aa" is 4+1+4 = 9. The space is 3, so 9+3 does not fit in 11 and the word wraps.
        self.assertEqual([plain(line) for line in lines], ["aa", "bb"])
        wide = layout(["aa", "bb"], ["", ""], 0, 30, True, measure=measure, gap=1)
        self.assertEqual([plain(line) for line in wide], ["aa bb"])

    def test_typing_ahead_does_not_reflow_the_lines(self):
        words = ["there", "before", "wanted", "for", "why", "but"]
        before = layout(words, [""] * len(words), 0, 72, True)
        after = layout(words, ["there", "bef", "", "", "", ""], 1, 72, True)
        self.assertEqual([plain(line) for line in before], [plain(line) for line in after])
        self.assertEqual(window(before, 0)[0].words, window(after, 1)[0].words)

    def test_the_window_shifts_one_line_when_the_first_is_done(self):
        words = ["aa", "bb", "cc", "dd", "ee", "ff"]
        lines = layout(words, [""] * len(words), 0, 5, True)
        self.assertEqual([plain(line) for line in lines], ["aa bb", "cc dd", "ee ff"])
        self.assertEqual([plain(line) for line in window(lines, 0)], ["aa bb", "cc dd", "ee ff"])
        self.assertEqual([plain(line) for line in window(lines, 2)], ["cc dd", "ee ff", ""])

    def test_the_plain_caret_underlines_the_letter(self):
        attrs = {
            "accent": 1,
            "untyped": 2,
            "caret": 4,
            "correct": 8,
            "incorrect": 16,
            "extra": 32,
            "space": 2,
        }
        marked = cell_attr("caret", attrs)
        self.assertEqual(marked & curses.A_UNDERLINE, curses.A_UNDERLINE)
        self.assertEqual(marked & ~curses.A_UNDERLINE, attrs["accent"])
        self.assertNotEqual(marked, attrs["caret"])
        self.assertEqual(cell_attr("correct", attrs), attrs["correct"])
        self.assertEqual(cell_attr("incorrect", attrs), attrs["incorrect"])
        self.assertEqual(cell_attr("untyped", attrs), attrs["untyped"])

    def test_the_window_starts_at_the_active_line(self):
        words = ["aa", "bb", "cc", "dd", "ee"]
        lines = layout(words, [""] * 5, 2, 2, True)
        visible = window(lines, 2)
        self.assertEqual([line.words for line in visible], [(2,), (3,), (4,)])


if __name__ == "__main__":
    unittest.main()
