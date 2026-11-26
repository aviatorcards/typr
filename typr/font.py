"""Block letters that stay readable instead of filling the window.

Each glyph is a small bitmap. Rows are packed two pixels to a cell with
half-blocks, so a pixel stays close to square. Scale 1 is the calm size.
A larger scale is opt-in, and only used when the window can hold it.
Letters are separated by one column. A word gap is wider than that.
"""

from __future__ import annotations

_ROWS = 6
# One column between letters, at every scale. Word gaps are wider.
_LETTER_GAP = 1

# Same width, so the option line does not jump when you switch.
FONT_ORDER = ("block", "plain")
SIZE_ORDER = ("small", "medium", "large")
_SIZE_CAP = {"small": 1, "medium": 2, "large": 3}


def active_font(name: str) -> str:
    return name if name in FONT_ORDER else FONT_ORDER[0]


def active_size(name: str) -> str:
    return name if name in SIZE_ORDER else SIZE_ORDER[0]


def size_label(name: str) -> str:
    """Fixed width, so switching small/medium/large does not shift the line."""
    return f"{active_size(name):<6}"


# Six rows. Lowercase sits on row 4; g, j, p, q, y use row 5 as a descender.
# Width follows the letter, so a line holds more words than a 5-wide cell.
_RAW = {
    "A": ".##. #..# #..# #### #..# ....",
    "B": "###. #..# ###. #..# ###. ....",
    "C": ".### #... #... #... .### ....",
    "D": "##.. #.#. #..# #.#. ##.. ....",
    "E": "#### #... ###. #... #### ....",
    "F": "#### #... ###. #... #... ....",
    "G": ".### #... #.## #..# .### ....",
    "H": "#..# #..# #### #..# #..# ....",
    "I": "### .#. .#. .#. ### ...",
    "J": "..## ...# ...# #..# .##. ....",
    "K": "#..# #.#. ##.. #.#. #..# ....",
    "L": "#... #... #... #... #### ....",
    "M": "#...# ##.## #.#.# #...# #...# .....",
    "N": "#..# ##.# #.## #..# #..# ....",
    "O": ".##. #..# #..# #..# .##. ....",
    "P": "###. #..# ###. #... #... ....",
    "Q": ".##. #..# #..# #.#. .##. ...#",
    "R": "###. #..# ###. #.#. #..# ....",
    "S": ".### #... .##. ...# ###. ....",
    "T": "##### ..#.. ..#.. ..#.. ..#.. .....",
    "U": "#..# #..# #..# #..# .##. ....",
    "V": "#...# .#.#. .#.#. ..#.. ..... .....",
    "W": "#...# #...# #.#.# #.#.# .#.#. .....",
    "X": "#...# .#.#. ..#.. .#.#. #...# .....",
    "Y": "#...# .#.#. ..#.. ..#.. ..#.. .....",
    "Z": "#### ...# ..#. .#.. #### ....",
    "a": ".... .##. ...# #..# .### ....",
    "b": "#... ##.. #..# #..# ###. ....",
    "c": ".... .##. #... #... .##. ....",
    "d": "...# ..## #..# #..# .### ....",
    "e": ".... .### #... ###. .### ....",
    "f": ".## #.. ##. #.. #.. ...",
    "g": ".... .### #..# .### ..## ##..",
    "h": "#... ###. #..# #..# #..# ....",
    "i": ". # . # # .",
    "j": "..# ..# ... ..# ..# ##.",
    "k": "#... #..# ##.. #.#. #..# ....",
    "l": "#. #. #. #. ## ..",
    "m": "..... ##.## #.#.# #.#.# #.#.# .....",
    "n": ".... ###. #..# #..# #..# ....",
    "o": ".... .##. #..# #..# .##. ....",
    "p": ".... ###. #..# ###. #... #...",
    "q": ".... .##. #..# #..# .### ...#",
    "r": "... ### #.. #.. #.. ...",
    "s": ".... .##. ##.. ..## .##. ....",
    "t": ".#. ### .#. .#. .## ...",
    "u": ".... #..# #..# #..# .### ....",
    "v": "... #.# #.# .#. .#. ...",
    "w": "..... #...# #...# #.#.# .#.#. .....",
    "x": ".... #..# .##. .##. #..# ....",
    "y": ".... #..# .##. .##. ..#. ..#.",
    "z": ".... #### ...# .##. #### ....",
    "0": ".##. #..# #.#. #..# .##. ....",
    "1": ".#. ##. .#. .#. ### ...",
    "2": ".##. #..# ..#. .#.. #### ....",
    "3": "###. ...# .##. ...# ###. ....",
    "4": "#..# #..# #### ...# ...# ....",
    "5": "#### #... ###. ...# ###. ....",
    "6": ".##. #... ###. #..# .##. ....",
    "7": "#### ...# ..#. .#.. .#.. ....",
    "8": ".##. #..# .##. #..# .##. ....",
    "9": ".##. #..# .### ...# .##. ....",
    ".": ".. .. .. ## ## ..",
    ",": ".. .. .. .# #. #.",
    "!": "# # # . # .",
    "?": ".##. #..# ..#. .... ..#. ....",
    "'": "# # . . . .",
    '"': "#.# #.# ... ... ... ...",
    "-": "... ... ### ... ... ...",
    ";": ".. .# .. .. .# #.",
    ":": ".. .# .. .. .# ..",
    "(": ".# #. #. #. .# ..",
    ")": "#. .# .# .# #. ..",
    "/": "..# ..# .#. .#. #.. #..",
}


def _rows(packed: str) -> tuple[str, ...]:
    parts = tuple(packed.split())
    widths = {len(part) for part in parts}
    if len(parts) != _ROWS or len(widths) != 1 or any(any(ch not in ".#" for ch in part) for part in parts):
        raise RuntimeError(f"bad glyph {packed!r}")
    return parts


GLYPHS = {char: _rows(packed) for char, packed in _RAW.items()}

_CACHE: dict[tuple[str, int], tuple[str, ...]] = {}


def line_height(scale: int) -> int:
    return (_ROWS * max(1, scale) + 1) // 2


def letter_gap(scale: int = 1) -> int:
    """Columns between two letters. Stays one column when the letters grow."""
    del scale
    return _LETTER_GAP


def word_space(scale: int) -> int:
    """Blank columns between words. Wider than the one-column letter gap."""
    return 3 * max(1, scale)


def glyph_width(char: str, scale: int) -> int:
    """Columns one character occupies, not counting the gap after it."""
    scale = max(1, scale)
    if char == " ":
        return word_space(scale)
    bits = GLYPHS.get(char)
    if bits is None:
        return 4 * scale
    return len(bits[0]) * scale


def places(chars: str, scale: int) -> list[tuple[int, int]]:
    """``(x, width)`` for each character. One column sits between letters."""
    out: list[tuple[int, int]] = []
    x = 0
    for index, char in enumerate(chars):
        width = glyph_width(char, scale)
        out.append((x, width))
        x += width
        if index + 1 < len(chars) and char != " " and chars[index + 1] != " ":
            x += letter_gap(scale)
    return out


def run_width(chars: str, scale: int) -> int:
    placed = places(chars, scale)
    if not placed:
        return 0
    origin, width = placed[-1]
    return origin + width


def caret_bars(chars: str, kinds, scale: int) -> list[tuple[int, str]]:
    """Underline under each caret cell. The glyph itself is left alone."""
    bars = []
    for (origin, width), kind in zip(places(chars, scale), kinds):
        if kind == "caret" and width > 0:
            bars.append((origin, "▀" * width))
    return bars


def block_rows(scale: int) -> int:
    """Terminal rows for the whole test: options, three word lines, stats, hint."""
    if scale <= 0:
        return 9
    return 6 + 3 * line_height(scale) + 2


def text_scale(width: int, height: int, longest: int | str = 8, size: str = "small") -> int:
    """Largest scale for ``size`` that fits, or 0 for ordinary text.

    ``longest`` is the longest word, or just its length. Small stays at the
    calm scale: a bigger window does not grow the letters to fill it. A word
    that does not fit steps the scale down.
    """
    cap = _SIZE_CAP[active_size(size)]
    word = longest if isinstance(longest, str) else "m" * max(0, int(longest))
    usable = max(0, width - 2)
    best = 0
    for scale in range(1, cap + 1):
        if block_rows(scale) > height:
            break
        if word and run_width(word, scale) > usable:
            break
        best = scale
    return best


def result_plan(height: int, figure_h: int, recent: bool, extra: bool) -> tuple[bool, bool, bool, bool, int]:
    """Which result rows fit under a figure of ``figure_h`` lines.

    The tuple is chars, sparkline, history, extra note, and the row count.
    """

    def total(chars: bool, spark: bool, history: bool, note: bool) -> int:
        rows = figure_h + 6
        if chars:
            rows += 2
        if spark:
            rows += 2
        if history:
            rows += 1 + (1 if recent else 0)
        if note:
            rows += 1
        return rows

    note = extra and total(False, False, False, True) <= height
    chars = total(True, False, False, note) <= height
    history = total(chars, False, True, note) <= height
    spark = total(chars, True, history, note) <= height
    return chars, spark, history, note, total(chars, spark, history, note)


def figure_scale(width: int, height: int, places_n: int = 4) -> int:
    """Scale for the result number. Budget four digits so 999 and 1000 match."""
    best = 0
    for scale in range(1, 9):
        height_px = line_height(scale)
        if 7 + height_px > height or height_px > max(4, height // 3):
            break
        if run_width("0" * places_n, scale) + 10 > width:
            break
        best = scale
    return best


def ink_rows(char: str, scale: int) -> tuple[str, ...]:
    """One character as terminal rows, without the gap that follows it."""
    scale = max(1, scale)
    key = (char, scale)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    if char == " ":
        blank = " " * word_space(scale)
        rows = tuple(blank for _ in range(line_height(scale)))
        _CACHE[key] = rows
        return rows
    bits = GLYPHS.get(char)
    width = glyph_width(char, scale)
    if bits is None:
        rows = _literal(char, scale, width)
    else:
        pixels: list[list[int]] = []
        for row in bits:
            expanded: list[int] = []
            for bit in row:
                expanded.extend([1 if bit == "#" else 0] * scale)
            pixels.extend([expanded] * scale)
        if len(pixels) % 2:
            pixels.append([0] * width)
        rows_list: list[str] = []
        for index in range(0, len(pixels), 2):
            chars = []
            for column in range(width):
                top = pixels[index][column]
                bottom = pixels[index + 1][column]
                chars.append(" ▄▀█"[bottom + top * 2])
            rows_list.append("".join(chars))
        rows = tuple(rows_list)
    _CACHE[key] = rows
    return rows


def write(text: str, scale: int) -> list[str]:
    """Join glyphs into one figure. A space in ``text`` is a blank word gap."""
    glyphs = [ink_rows(char, scale) for char in text]
    if not glyphs:
        return []
    gap = " " * letter_gap(scale)
    rows: list[str] = []
    for row in range(len(glyphs[0])):
        parts: list[str] = []
        for index, glyph in enumerate(glyphs):
            if index and text[index - 1] != " " and text[index] != " ":
                parts.append(gap)
            parts.append(glyph[row])
        rows.append("".join(parts))
    return rows


def _literal(char: str, scale: int, width: int) -> tuple[str, ...]:
    """Unknown characters stay their real shape, centered in the same box."""
    rows = [[" "] * width for _ in range(line_height(scale))]
    if char and char != " ":
        rows[len(rows) // 2][width // 2] = char[:1]
    return tuple("".join(row) for row in rows)
