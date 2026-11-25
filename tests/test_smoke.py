"""Drive the real screen through a pseudoterminal."""

import os
import select
import signal
import struct
import sys
import tempfile
import termios
import time
import unittest
import fcntl
from pathlib import Path

from typr.words import generate
import random


ROOT = Path(__file__).resolve().parents[1]


def _run(args, send, ready, timeout=6):
    import pty

    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(ROOT)
        os.environ["TERM"] = "xterm-256color"
        os.environ["TYPR_ALLOW_BURST"] = "1"
        os.environ["ESCDELAY"] = "25"
        size = struct.pack("HHHH", 32, 100, 0, 0)
        fcntl.ioctl(0, termios.TIOCSWINSZ, size)
        os.execv(sys.executable, [sys.executable, "-m", "typr", *args])
    output = b""
    sent = False
    status = None
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            readable, _, _ = select.select([fd], [], [], 0.05)
            if readable:
                try:
                    output += os.read(fd, 65536)
                except OSError:
                    break
            if not sent and ready in output:
                sent = True
                for chunk in send:
                    os.write(fd, chunk)
                    time.sleep(0.01)
            ended, code = os.waitpid(pid, os.WNOHANG)
            if ended:
                status = code
                while True:
                    readable, _, _ = select.select([fd], [], [], 0.05)
                    if not readable:
                        break
                    try:
                        chunk = os.read(fd, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    output += chunk
                break
        if status is None:
            os.kill(pid, signal.SIGTERM)
            _, status = os.waitpid(pid, 0)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    return status, output, sent


class SmokeTest(unittest.TestCase):
    def test_escape_quits(self):
        with tempfile.TemporaryDirectory() as directory:
            status, output, sent = _run(
                ["--no-save", "--seed", "1", "--data-dir", directory],
                [b"\x1b"],
                b"esc quit",
            )
        self.assertTrue(sent, output[-400:])
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)

    def test_a_short_test_reaches_the_result(self):
        words = generate("english", 10, False, False, random.Random(1), final=True)
        payload = "".join(word + (" " if index < len(words) - 1 else "") for index, word in enumerate(words))
        with tempfile.TemporaryDirectory() as directory:
            status, output, sent = _run(
                ["--no-save", "--seed", "1", "-w", "10", "--data-dir", directory],
                [payload.encode(), b"\x1b"],
                b"esc quit",
                timeout=8,
            )
        self.assertTrue(sent, output[-400:])
        self.assertIn(b"wpm", output)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)

    def test_help_and_version_do_not_need_a_screen(self):
        import subprocess

        for flag in ("--help", "--version"):
            done = subprocess.run(
                [sys.executable, "-m", "typr", flag],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("typr", subprocess.run(
            [sys.executable, "-m", "typr", "--version"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        ).stdout)


if __name__ == "__main__":
    unittest.main()
