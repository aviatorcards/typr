"""Typing-test state, scoring, and the rules for each key."""

from __future__ import annotations

import os
import random
import statistics
from dataclasses import dataclass, field

from typr.words import generate, random_quote


@dataclass(frozen=True)
class Config:
    mode: str  # "time", "words", or "quote"
    count: int
    corpus: str
    punct: bool
    numbers: bool
    label: str

    @property
    def bucket(self) -> str:
        if self.corpus == "quotes":
            return "quote|quotes"
        if self.corpus == "passage":
            return f"passage|{self.label}"
        return f"{self.mode}|{self.count}|{self.label}|{int(self.punct)}|{int(self.numbers)}"

    def describe(self) -> str:
        if self.corpus == "quotes":
            return "quote"
        if self.corpus == "passage":
            return self.label
        head = f"{self.count}s" if self.mode == "time" else f"{self.count} words"
        return f"{head} {self.label}"


@dataclass(frozen=True)
class Stats:
    wpm: float
    raw: float
    acc: float
    consistency: float | None
    correct: int
    incorrect: int
    extra: int
    missed: int
    seconds: float
    disqualified: str | None


def new_rng(seed: int | None) -> tuple[random.Random, int]:
    if seed is None:
        seed = random.SystemRandom().randrange(1, 2_000_000_000)
    return random.Random(seed), seed


@dataclass
class Test:
    config: Config
    rng: random.Random
    seed: int
    targets: list[str]
    typed: list[str]
    submit_at: list[float | None]
    current: int = 0
    started_at: float | None = None
    finished_at: float | None = None
    samples: list[tuple[float, int]] = field(default_factory=list)
    disqualify: str | None = None
    last_key_at: float | None = None
    fast: int = 0
    allow_burst: bool = False

    @property
    def started(self) -> bool:
        return self.started_at is not None

    @property
    def finished(self) -> bool:
        return self.finished_at is not None

    def elapsed(self, now: float) -> float:
        if self.started_at is None:
            return 0.0
        end = self.finished_at if self.finished_at is not None else now
        if self.config.mode == "time":
            end = min(end, self.started_at + self.config.count)
        return max(0.0, end - self.started_at)

    def expired(self, now: float) -> bool:
        if self.finished or self.started_at is None or self.config.mode != "time":
            return False
        return now >= self.started_at + self.config.count

    def finish(self, now: float) -> None:
        if self.finished:
            return
        if self.started_at is None:
            self.started_at = now
        if self.config.mode == "time":
            now = min(now, self.started_at + self.config.count)
        self.finished_at = now
        self._sample(now)

    def type_char(self, ch: str, now: float) -> None:
        if self.finished or len(ch) != 1 or not ch.isascii() or not ch.isprintable() or ch == " ":
            return
        if self.expired(now):
            self.finish(now)
            return
        self._speed(now)
        if self.started_at is None:
            self.started_at = now
            self.samples.append((0.0, 0))
        self.typed[self.current] += ch
        self._sample(now)
        self._complete_if_exact(now)
        self.ensure_ahead()

    def space(self, now: float) -> None:
        if self.finished:
            return
        if self.expired(now):
            self.finish(now)
            return
        if not self.typed[self.current] or self.started_at is None:
            return
        self._speed(now)
        self.submit_at[self.current] = self.elapsed(now)
        self.current += 1
        self._sample(now)
        if self.current >= len(self.targets):
            if self.config.mode == "time":
                self.ensure_ahead()
            if self.current >= len(self.targets):
                self.finish(now)
                return
        self.ensure_ahead()

    def backspace(self, now: float) -> None:
        if self.finished:
            return
        if self.expired(now):
            self.finish(now)
            return
        if self.typed[self.current]:
            self.typed[self.current] = self.typed[self.current][:-1]
            if self.started:
                self._sample(now)
            return
        if self.current == 0:
            return
        self.current -= 1
        self.submit_at[self.current] = None
        if self.typed[self.current]:
            self.typed[self.current] = self.typed[self.current][:-1]
        if self.started:
            self._sample(now)

    def clear_word(self, now: float) -> None:
        if self.finished:
            return
        if self.expired(now):
            self.finish(now)
            return
        if self.typed[self.current]:
            self.typed[self.current] = ""
            if self.started:
                self._sample(now)

    def ensure_ahead(self) -> None:
        if self.config.mode != "time" or self.config.corpus in ("quotes", "passage"):
            return
        if len(self.targets) - self.current >= 40:
            return
        more = generate(
            self.config.corpus,
            80,
            self.config.punct,
            self.config.numbers,
            self.rng,
            final=False,
        )
        if not more:
            return
        self.targets.extend(more)
        self.typed.extend([""] * len(more))
        self.submit_at.extend([None] * len(more))

    def counts(self) -> tuple[int, int, int, int]:
        correct = incorrect = extra = missed = 0
        for index, target in enumerate(self.targets):
            if index > self.current:
                break
            typed = self.typed[index]
            submitted = index < self.current
            for position, char in enumerate(target):
                if position < len(typed):
                    if typed[position] == char:
                        correct += 1
                    else:
                        incorrect += 1
                elif submitted:
                    missed += 1
            if len(typed) > len(target):
                extra += len(typed) - len(target)
        return correct, incorrect, extra, missed

    def stats(self, now: float) -> Stats:
        correct, incorrect, extra, missed = self.counts()
        seconds = self.elapsed(now)
        if seconds < 0.001:
            wpm = 0.0
            raw = 0.0
        else:
            minutes = seconds / 60.0
            # One "word" is five characters, the usual typing-test definition.
            wpm = (correct / 5) / minutes
            raw = ((correct + incorrect + extra) / 5) / minutes
        total = correct + incorrect + extra + missed
        accuracy = 100.0 if total == 0 else 100.0 * correct / total
        return Stats(
            wpm=wpm,
            raw=raw,
            acc=accuracy,
            consistency=self._consistency(),
            correct=correct,
            incorrect=incorrect,
            extra=extra,
            missed=missed,
            seconds=seconds,
            disqualified=self.disqualify,
        )

    def _consistency(self) -> float | None:
        marks: list[tuple[float, int]] = []
        for index, stamp in enumerate(self.submit_at):
            if stamp is not None:
                marks.append((stamp, len(self.typed[index])))
        if len(marks) < 2:
            return None
        speeds: list[float] = []
        previous = 0.0
        for stamp, chars in marks:
            delta = stamp - previous
            previous = stamp
            if delta > 0.001 and chars > 0:
                speeds.append((chars / 5) / (delta / 60))
        if len(speeds) < 2:
            return None
        mean = statistics.fmean(speeds)
        if mean <= 0:
            return 0.0
        spread = statistics.pstdev(speeds)
        return max(0.0, min(100.0, 100 * (1 - spread / mean)))

    def _sample(self, now: float) -> None:
        if self.started_at is None:
            return
        self.samples.append((self.elapsed(now), self.counts()[0]))

    def _speed(self, now: float) -> None:
        if self.allow_burst:
            return
        if self.last_key_at is not None and (now - self.last_key_at) < 0.02:
            self.fast += 1
        else:
            self.fast = 1
        self.last_key_at = now
        # A dozen characters, each under 20ms apart, is not a person typing.
        if self.fast >= 12:
            self.disqualify = "burst"

    def _complete_if_exact(self, now: float) -> None:
        if self.config.mode == "time":
            return
        if self.current != len(self.targets) - 1:
            return
        if self.typed[self.current] != self.targets[self.current]:
            return
        self.submit_at[self.current] = self.elapsed(now)
        self.current += 1
        self.finish(now)


def make_test(
    config: Config,
    rng: random.Random,
    seed: int,
    words: list[str] | None = None,
    passage: list[str] | None = None,
    allow_burst: bool | None = None,
) -> Test:
    if allow_burst is None:
        allow_burst = os.environ.get("TYPR_ALLOW_BURST") == "1"
    if words is None:
        if config.corpus == "passage":
            if not passage:
                raise ValueError("passage is empty")
            words = list(passage)
        elif config.corpus == "quotes":
            words = random_quote(rng)
        else:
            count = 160 if config.mode == "time" else config.count
            words = generate(
                config.corpus,
                count,
                config.punct,
                config.numbers,
                rng,
                final=config.mode != "time",
            )
    return Test(
        config=config,
        rng=rng,
        seed=seed,
        targets=list(words),
        typed=[""] * len(words),
        submit_at=[None] * len(words),
        allow_burst=allow_burst,
    )
