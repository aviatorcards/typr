"""Word wrapping and the caret."""

import unittest

from typr.layout import layout, plain, window


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

    def test_the_window_starts_at_the_active_line(self):
        words = ["aa", "bb", "cc", "dd", "ee"]
        lines = layout(words, [""] * 5, 2, 2, True)
        visible = window(lines, 2)
        self.assertEqual([line.words for line in visible], [(2,), (3,), (4,)])


if __name__ == "__main__":
    unittest.main()
