# typr

A typing test in the terminal. Words on screen, a caret, and a result when you finish. On a larger window the words are drawn as block letters, kept small enough that several words fit on a line. `,` and `.` change that size (`small`, `medium`, `large`). Press `=` if you want the terminal's own font.

```bash
python3 -m typr
```

The clock starts on the first character you type. Backspace fixes the current word and can step back into the previous one.

## Keys

| Key | Before you start | During the test | On the result |
| --- | --- | --- | --- |
| letters | start the test | type | |
| `←` `→` | 15s, 30s, 60s, 120s | | |
| `↑` `↓` | 10, 25, 50, 100 words | | |
| `[` `]` | english, 1k, punct, numbers, expert, quotes | | |
| `\` | color theme | | color theme |
| `=` `-` | block or plain letters | | block or plain letters |
| `,` `.` | letter size | | letter size |
| `tab` | new words | restart | new test |
| `ctrl+r` | retry these words | retry these words | retry these words |
| `ctrl+w` | | clear the current word | |
| `enter` | | | new test |
| `?` | help | | help |
| `esc` | quit | quit | quit |

`english` is the 200 most common words. `1k` is a wider everyday list. `punct` adds capitals and punctuation, `numbers` mixes in digits, and `expert` uses both. `quotes` is one short public-domain passage.

```bash
python3 -m typr -t 15
python3 -m typr -w 50 --punct
python3 -m typr -c quotes
python3 -m typr --passage speech.txt
python3 -m typr --theme nord
python3 -m typr --font plain
python3 -m typr --size medium
```

`small` is the default block size. `medium` and `large` draw the same letters bigger, and step down when the window cannot hold them. The caret in block mode is an underline in the theme color, so the current letter stays readable.

`--seed 1` repeats the same words every restart.

## Scoring

WPM is correct characters divided by five, per minute. Raw WPM also counts mistyped and extra characters. Accuracy is correct characters divided by correct, wrong, extra, and skipped characters. Consistency is how even your pace was from word to word.

A result becomes your best for that mode only at 90% accuracy or above. History is stored in `~/.local/share/typr/history.json` (or `$XDG_DATA_HOME/typr`).

## Word list

The list is everyday English in spoken-frequency order, limited to general-service vocabulary and real inflections. Frequency comes from OpenSubtitles via [FrequencyWords](https://github.com/hermitdave/FrequencyWords). The vocabulary filter follows the [New General Service List](https://www.newgeneralservicelist.com/) by Browne, Culligan, and Phillips, released under Creative Commons.
