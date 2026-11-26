"""Block letters that grow with the terminal.

Each glyph is a 5×7 bitmap. Rows are packed two pixels to a cell with
half-blocks, so a cell's tall shape stays close to square. ``scale`` 2
draws every pixel as a 2×2 block, and so on. Scale 0 is normal text.
"""

from __future__ import annotations

INK = 5
_GAP = 1

# Same width, so the option line does not jump when you switch.
FONT_ORDER = ("block", "plain")


def active_font(name: str) -> str:
    return name if name in FONT_ORDER else FONT_ORDER[0]

# Rows use '#' for ink. Lowercase sits lower than capitals; g, j, p, q, y drop.
_RAW = {
    "A": ".###. #...# #...# ##### #...# #...# #...#",
    "B": "####. #...# #...# ####. #...# #...# ####.",
    "C": ".###. #...# #.... #.... #.... #...# .###.",
    "D": "####. #...# #...# #...# #...# #...# ####.",
    "E": "##### #.... #.... ####. #.... #.... #####",
    "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .###.",
    "H": "#...# #...# #...# ##### #...# #...# #...#",
    "I": "##### ..#.. ..#.. ..#.. ..#.. ..#.. #####",
    "J": "..### ...#. ...#. ...#. #..#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #...# #...# #...# #...#",
    "N": "#...# ##..# #.#.# #..## #...# #...# #...#",
    "O": ".###. #...# #...# #...# #...# #...# .###.",
    "P": "####. #...# #...# ####. #.... #.... #....",
    "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#",
    "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".#### #.... #.... .###. ....# ....# ####.",
    "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# .###.",
    "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
    "W": "#...# #...# #...# #...# #.#.# ##.## .#.#.",
    "X": "#...# .#.#. ..#.. ..#.. ..#.. .#.#. #...#",
    "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    "a": "..... ..... .###. ....# .###. #...# .####",
    "b": "#.... #.... ####. #...# #...# #...# ####.",
    "c": "..... ..... .###. #.... #.... #.... .###.",
    "d": "....# ....# .#### #...# #...# #...# .####",
    "e": "..... ..... .###. #...# ####. #.... .###.",
    "f": "..##. .#... ####. .#... .#... .#... .#...",
    "g": "..... ..... .#### #...# .#### ....# .###.",
    "h": "#.... #.... ####. #...# #...# #...# #...#",
    "i": "..... ..#.. ..... ..#.. ..#.. ..#.. ..#..",
    "j": "..... ...#. ..... ...#. ...#. #..#. .##..",
    "k": "#.... #.... #..#. #.#.. ##... #.#.. #..#.",
    "l": "..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "m": "..... ..... ##.## #.#.# #.#.# #.#.# #.#.#",
    "n": "..... ..... ####. #...# #...# #...# #...#",
    "o": "..... ..... .###. #...# #...# #...# .###.",
    "p": "..... ..... ####. #...# ####. #.... #....",
    "q": "..... ..... .#### #...# .#### ....# ....#",
    "r": "..... ..... #.##. ##... #.... #.... #....",
    "s": "..... ..... .###. #.... .###. ....# ####.",
    "t": "..#.. ..#.. ##### ..#.. ..#.. ..#.. ..##.",
    "u": "..... ..... #...# #...# #...# #...# .####",
    "v": "..... ..... #...# #...# #...# .#.#. ..#..",
    "w": "..... ..... #...# #...# #.#.# #.#.# .#.#.",
    "x": "..... ..... #...# .#.#. ..#.. .#.#. #...#",
    "y": "..... ..... #...# #...# .#### ....# .###.",
    "z": "..... ..... ##### ...#. ..#.. .#... #####",
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.",
    "1": "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    "2": ".###. #...# ....# ..##. .#... #.... #####",
    "3": ".###. #...# ....# ..##. ....# #...# .###.",
    "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": ".###. #.... #.... ####. #...# #...# .###.",
    "7": "##### ....# ...#. ..#.. .#... .#... .#...",
    "8": ".###. #...# #...# .###. #...# #...# .###.",
    "9": ".###. #...# #...# .#### ....# ....# .###.",
    ".": "..... ..... ..... ..... ..... ..#.. ..#..",
    ",": "..... ..... ..... ..... ..#.. ..#.. .#...",
    "!": "..#.. ..#.. ..#.. ..#.. ..... ..#.. ..#..",
    "?": ".###. #...# ....# ..#.. ..#.. ..... ..#..",
    "'": "..#.. ..#.. .#... ..... ..... ..... .....",
    '"': ".#.#. .#.#. #.#.. ..... ..... ..... .....",
    "-": "..... ..... ..... ##### ..... ..... .....",
    ";": "..... ..#.. ..#.. ..... ..#.. ..#.. .#...",
    ":": "..... ..#.. ..#.. ..... ..#.. ..#.. .....",
    "(": "..##. .#... #.... #.... #.... .#... ..##.",
    ")": ".##.. ...#. ....# ....# ....# ...#. .##..",
    "/": "....# ....# ...#. ..#.. .#... #.... #....",
}


def _rows(packed: str) -> tuple[str, ...]:
    parts = tuple(packed.split())
    if len(parts) != 7 or any(len(part) != INK or any(ch not in ".#" for ch in part) for part in parts):
        raise RuntimeError(f"bad glyph {packed!r}")
    return parts


GLYPHS = {char: _rows(packed) for char, packed in _RAW.items()}

_CACHE: dict[tuple[str, int], tuple[str, ...]] = {}


def line_height(scale: int) -> int:
    return (7 * scale + 1) // 2


def advance(scale: int) -> int:
    """Columns one character takes, including the gap before the next one."""
    return (INK + _GAP) * scale


def block_rows(scale: int) -> int:
    """Terminal rows for the whole test: options, three word lines, stats, hint."""
    if scale <= 0:
        return 9
    return 6 + 3 * line_height(scale) + 2


def text_scale(width: int, height: int, longest: int = 8) -> int:
    """Largest glyph scale that fits, or 0 for ordinary one-cell text.

    ``longest`` is the longest word on the test. The line has to hold it,
    so a wider window grows the letters instead of only adding more words.
    """
    need = min(16, max(longest, 8))
    usable = max(0, width - 2)
    best = 0
    for scale in range(1, 8):
        if block_rows(scale) > height:
            break
        if usable // advance(scale) < need:
            break
        best = scale
    return best


def char_columns(width: int, scale: int) -> int:
    return max(1, (width - 2) // advance(scale))


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


def figure_scale(width: int, height: int, places: int = 4) -> int:
    """Scale for the result number. Budget four digits so 999 and 1000 match."""
    best = 0
    for scale in range(1, 9):
        if 7 + line_height(scale) > height or line_height(scale) > max(4, height // 3):
            break
        figure = places * INK * scale + max(0, places - 1) * scale
        if figure + 10 > width:
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
    bits = GLYPHS.get(char)
    width = INK * scale
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
    """Join glyphs into one figure. A space in ``text`` is a blank letter."""
    glyphs = [ink_rows(char if char != " " else " ", scale) for char in text]
    if not glyphs:
        return []
    gap = " " * scale
    return [gap.join(glyph[row] for glyph in glyphs) for row in range(len(glyphs[0]))]


def _literal(char: str, scale: int, width: int) -> tuple[str, ...]:
    """Unknown characters stay their real shape, centered in the same box."""
    rows = [[" "] * width for _ in range(line_height(scale))]
    if char and char != " ":
        rows[len(rows) // 2][width // 2] = char[:1]
    return tuple("".join(row) for row in rows)
