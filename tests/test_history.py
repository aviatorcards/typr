"""Saved results."""

import json
import tempfile
import unittest
from pathlib import Path

from typr.history import History


class HistoryTest(unittest.TestCase):
    def test_round_trip_and_a_corrupt_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            history = History(path)
            self.assertTrue(history.add({"wpm": 80, "acc": 99}))
            again = History(path)
            self.assertEqual(again.tests, [{"wpm": 80, "acc": 99}])
            path.write_text("{not json", encoding="utf-8")
            reset = History(path)
            self.assertEqual(reset.tests, [])
            self.assertTrue(path.with_suffix(".bad.json").exists())

    def test_no_save_keeps_the_file_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            history = History(path, enabled=False)
            self.assertTrue(history.add({"wpm": 10}))
            self.assertFalse(path.exists())
            self.assertEqual(history.tests, [{"wpm": 10}])

    def test_only_real_records_are_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            path.write_text(json.dumps({"version": 1, "tests": [{"wpm": 1}, {"nope": True}, "x"]}), encoding="utf-8")
            self.assertEqual(History(path).tests, [{"wpm": 1}])


if __name__ == "__main__":
    unittest.main()
