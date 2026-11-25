"""Local result history."""

from __future__ import annotations

import json
import os
from pathlib import Path


def default_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / "typr"


class History:
    def __init__(self, path: Path | None, enabled: bool = True) -> None:
        self.path = path
        self.enabled = enabled
        self.tests: list[dict] = load(path) if path is not None else []

    def add(self, record: dict) -> bool:
        self.tests.append(record)
        if len(self.tests) > 1000:
            del self.tests[:-1000]
        if not self.enabled or self.path is None:
            return True
        try:
            self._write()
        except OSError:
            return False
        return True

    def _write(self) -> None:
        assert self.path is not None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "tests": self.tests}
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)


def load(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        backup = path.with_suffix(".bad.json")
        try:
            path.replace(backup)
        except OSError:
            pass
        return []
    rows = data.get("tests", []) if isinstance(data, dict) else []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict) and "wpm" in row]
