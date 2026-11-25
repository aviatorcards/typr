"""Word lists, quotes, and test generation."""

from __future__ import annotations

import random
from pathlib import Path

_DATA = Path(__file__).resolve().parent / "data" / "english_1k.txt"

QUOTES: tuple[str, ...] = (
    "To be, or not to be, that is the question.",
    "All the world's a stage, and all the men and women merely players.",
    "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
    "It was the best of times, it was the worst of times.",
    "Call me Ishmael.",
    "I went to the woods because I wished to live deliberately, to front only the essential facts of life.",
    "The report of my death was an exaggeration.",
    "Beware; for I am fearless, and therefore powerful.",
    "I have been a stranger in a strange land.",
    "There is nothing either good or bad, but thinking makes it so.",
    "We are such stuff as dreams are made on.",
    "Whatever our souls are made of, his and mine are the same.",
    "You must allow me to tell you how ardently I admire and love you.",
    "I can resist everything except temptation.",
    "Give every man thy ear, but few thy voice.",
    "Please, sir, I want some more.",
    "It is a far, far better thing that I do, than I have ever done.",
    "I am no bird; and no net ensnares me.",
)

_CONTRACTIONS = {
    ("do", "not"): "don't",
    ("did", "not"): "didn't",
    ("does", "not"): "doesn't",
    ("is", "not"): "isn't",
    ("was", "not"): "wasn't",
    ("were", "not"): "weren't",
    ("can", "not"): "can't",
    ("could", "not"): "couldn't",
    ("would", "not"): "wouldn't",
    ("should", "not"): "shouldn't",
    ("i", "am"): "I'm",
    ("you", "are"): "you're",
    ("they", "are"): "they're",
    ("we", "are"): "we're",
    ("it", "is"): "it's",
    ("that", "is"): "that's",
    ("what", "is"): "what's",
    ("let", "us"): "let's",
    ("i", "have"): "I've",
    ("i", "will"): "I'll",
    ("you", "will"): "you'll",
    ("we", "will"): "we'll",
    ("they", "will"): "they'll",
}


def load_word_list() -> list[str]:
    words: list[str] = []
    for line in _DATA.read_text(encoding="utf-8").splitlines():
        word = line.strip().lower()
        if not word or word.startswith("#"):
            continue
        if word.isalpha():
            words.append(word)
    if len(words) < 200:
        raise RuntimeError(f"word list at {_DATA} is incomplete")
    return words


ENGLISH_1K = load_word_list()
ENGLISH_200 = ENGLISH_1K[:200]


def load_passage(path: Path, limit: int = 3000) -> list[str]:
    text = path.read_text(encoding="utf-8")
    words: list[str] = []
    for raw in text.split():
        cleaned = "".join(ch for ch in raw if ch.isascii() and ch.isprintable())
        if cleaned:
            words.append(cleaned)
    if not words:
        raise ValueError(f"no ASCII words in {path}")
    return words[:limit]


def random_quote(rng: random.Random) -> list[str]:
    return rng.choice(QUOTES).split()


def generate(
    corpus: str,
    n: int,
    punct: bool,
    numbers: bool,
    rng: random.Random,
    *,
    final: bool = False,
) -> list[str]:
    """Build ``n`` tokens. ``final`` closes punctuation mode with a period."""
    bank = ENGLISH_1K if corpus == "english1k" else ENGLISH_200
    words: list[str] = []
    while len(words) < n:
        chunk = _sample(bank, (n - len(words)) + (40 if punct else 0), rng)
        if punct:
            chunk = _contract(chunk, rng)
        if numbers:
            chunk = _numbers(chunk, rng)
        if punct:
            chunk = _sprinkle_punct(chunk, rng)
        if not chunk:
            break
        words.extend(chunk)
    if len(words) > n:
        words = words[:n]
    if final and punct and words:
        words[-1] = _close_sentence(words[-1])
    return words


def _sample(bank: list[str], n: int, rng: random.Random) -> list[str]:
    out: list[str] = []
    previous: str | None = None
    for _ in range(n):
        word = rng.choice(bank)
        guard = 0
        while word == previous and len(bank) > 1 and guard < 5:
            word = rng.choice(bank)
            guard += 1
        out.append(word)
        previous = word
    return out


def _contract(words: list[str], rng: random.Random) -> list[str]:
    out: list[str] = []
    index = 0
    while index < len(words):
        pair = (words[index], words[index + 1]) if index + 1 < len(words) else None
        if pair in _CONTRACTIONS and rng.random() < 0.75:
            out.append(_CONTRACTIONS[pair])
            index += 2
        else:
            out.append(words[index])
            index += 1
    return out


def _numbers(words: list[str], rng: random.Random) -> list[str]:
    out: list[str] = []
    for word in words:
        if word.isalpha() and rng.random() < 0.15:
            out.append(_rand_number(rng))
        else:
            out.append(word)
    return out


def _rand_number(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.45:
        return str(rng.randint(0, 9))
    if roll < 0.8:
        return str(rng.randint(10, 99))
    if roll < 0.95:
        return str(rng.randint(100, 999))
    return str(rng.randint(1000, 9999))


def _sprinkle_punct(words: list[str], rng: random.Random) -> list[str]:
    out: list[str] = []
    capitalize = True
    for index, word in enumerate(words):
        if word == "i":
            word = "I"
        elif capitalize and word[:1].isalpha():
            word = word[:1].upper() + word[1:]
        capitalize = False
        if index < len(words) - 1:
            roll = rng.random()
            if roll < 0.055:
                word += ","
            elif roll < 0.09:
                word += "."
                capitalize = True
            elif roll < 0.11:
                word += "?"
                capitalize = True
            elif roll < 0.125:
                word += "!"
                capitalize = True
            elif roll < 0.16 and word.isalpha():
                word = f'"{word}"'
        out.append(word)
    return out


def _close_sentence(word: str) -> str:
    word = word.rstrip(",")
    if not word or word[-1] in ".!?":
        return word
    if word.endswith('"') and len(word) > 1:
        return word[:-1] + '."'
    return word + "."
