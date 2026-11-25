"""Scoring and the rules of a test."""

import unittest

from typr.engine import Config, make_test, new_rng


def _words(mode="words", count=1, targets=None, **kwargs):
    config = Config(mode, count, "english", False, False, "english")
    rng, seed = new_rng(1)
    return make_test(config, rng, seed, words=targets, allow_burst=False, **kwargs)


class ScoringTest(unittest.TestCase):
    def test_wpm_is_correct_characters_over_five(self):
        test = _words(targets=["hello"])
        for offset, char in enumerate("hello"):
            test.type_char(char, 1000.0 + offset * 0.2)
        stats = test.stats(1000.8)
        self.assertTrue(test.finished)
        self.assertEqual(stats.correct, 5)
        self.assertAlmostEqual(stats.wpm, 75.0)
        self.assertAlmostEqual(stats.acc, 100.0)

    def test_space_early_counts_missed_characters(self):
        test = _words(targets=["hello"])
        test.type_char("h", 1000.0)
        test.type_char("e", 1000.2)
        test.space(1000.4)
        stats = test.stats(1000.4)
        self.assertTrue(test.finished)
        self.assertEqual((stats.correct, stats.incorrect, stats.extra, stats.missed), (2, 0, 0, 3))
        self.assertAlmostEqual(stats.acc, 40.0)

    def test_wrong_and_extra_characters(self):
        test = _words(targets=["hi"])
        test.type_char("h", 10.0)
        test.type_char("x", 10.2)
        test.type_char("z", 10.4)
        test.space(10.6)
        stats = test.stats(10.6)
        self.assertEqual((stats.correct, stats.incorrect, stats.extra, stats.missed), (1, 1, 1, 0))
        self.assertAlmostEqual(stats.acc, 100 / 3)

    def test_last_word_ends_when_it_matches(self):
        test = _words(count=2, targets=["ab", "cd"])
        for moment, char in ((1, "a"), (2, "b")):
            test.type_char(char, moment)
        test.space(3)
        self.assertFalse(test.finished)
        test.type_char("c", 4)
        test.type_char("d", 5)
        self.assertTrue(test.finished)
        self.assertEqual(test.stats(5).correct, 4)

    def test_space_accepts_a_wrong_last_word(self):
        test = _words(count=2, targets=["ab", "cd"])
        test.type_char("a", 1)
        test.type_char("b", 2)
        test.space(3)
        test.type_char("c", 4)
        test.type_char("x", 5)
        test.space(6)
        self.assertTrue(test.finished)
        stats = test.stats(6)
        self.assertEqual((stats.correct, stats.incorrect), (3, 1))

    def test_empty_space_does_not_start_or_advance(self):
        test = _words(count=2, targets=["ab", "cd"])
        test.space(1000)
        self.assertFalse(test.started)
        self.assertEqual(test.current, 0)

    def test_backspace_returns_to_the_previous_word(self):
        test = _words(count=2, targets=["ab", "cd"])
        test.type_char("a", 1)
        test.type_char("b", 2)
        test.space(3)
        test.backspace(4)
        self.assertEqual(test.current, 0)
        self.assertEqual(test.typed[0], "a")
        self.assertIsNone(test.submit_at[0])

    def test_clear_word_removes_only_the_current_word(self):
        test = _words(targets=["hello"])
        test.type_char("h", 1)
        test.type_char("x", 2)
        test.clear_word(3)
        self.assertEqual(test.typed[0], "")
        self.assertFalse(test.finished)

    def test_time_mode_rejects_input_after_the_limit(self):
        test = _words(mode="time", count=10, targets=["hello", "there"])
        test.type_char("h", 5000)
        test.type_char("i", 5010)
        self.assertTrue(test.finished)
        self.assertEqual(test.typed[0], "h")
        self.assertAlmostEqual(test.stats(5099).seconds, 10.0)
        self.assertAlmostEqual(test.stats(5099).wpm, 1.2)

    def test_time_mode_grows_more_words(self):
        config = Config("time", 60, "english", False, False, "english")
        rng, seed = new_rng(2)
        test = make_test(config, rng, seed, allow_burst=True)
        self.assertGreaterEqual(len(test.targets), 160)
        test.current = len(test.targets) - 10
        test.ensure_ahead()
        self.assertGreaterEqual(len(test.targets) - test.current, 40)

    def test_steady_pace_is_consistent(self):
        test = _words(count=2, targets=["aaaaa", "bbbbb"])
        start = 1000.0
        for index, char in enumerate("aaaaa"):
            test.type_char(char, start + index * 0.2)
        test.space(start + 1.0)
        for index, char in enumerate("bbbbb"):
            test.type_char(char, start + 1.2 + index * 0.2)
        stats = test.stats(start + 2.0)
        self.assertTrue(test.finished)
        self.assertAlmostEqual(stats.consistency, 100.0)

    def test_burst_input_is_disqualified(self):
        test = _words(targets=["hello"])
        now = 1000.0
        for _ in range(12):
            test.type_char("a", now)
            now += 0.01
        self.assertEqual(test.disqualify, "burst")

    def test_quote_bucket_is_shared(self):
        config = Config("quote", 0, "quotes", False, False, "quotes")
        self.assertEqual(config.bucket, "quote|quotes")
        self.assertEqual(config.describe(), "quote")


if __name__ == "__main__":
    unittest.main()
