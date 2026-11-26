#!/usr/bin/env python3
"""Unit tests for autoshard_judge.py exit codes on PASS, FAIL, and INVALID."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import autoshard_judge as AJ  # noqa: E402


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def make_fixture(out: Path, r1_tracer: str = "100", drop_f1: bool = False) -> None:
    work = out / "fakeprefix"
    w(out / "work", str(work))
    for s in ("main", "f1", "f2", "r1"):
        w(out / f"{s}.inner_done", "done")
        w(out / f"{s}.inner_f8_env", "")
    w(out / "main.test_tracer", "100")
    w(out / "f1.test_tracer", "100")
    w(out / "f2.test_tracer", "100")
    w(out / "r1.test_tracer", "100")

    def cell(rel: str, tracer: str, exe: str = "", sharded: str = "", argv: str = ""):
        d = out / "cells" / rel
        w(d / "tracer", tracer)
        if exe:
            w(d / "shard_exe", exe)
        if sharded:
            w(d / "sharded", sharded)
        if argv:
            w(d / "tracer.argv", argv)

    cell("main-e1", "200", exe=f"{work}/fakeapp/fakeelectron", sharded="1", argv="proot-fast8\n-0\n")
    for c in ("e2", "e3", "e4", "e5", "e6", "e7", "e10", "e12"):
        cell(f"main-{c}", "100")
    for c in ("e8", "e9"):
        cell(f"main-e1/{c}", "200")
    cell("main-e1/e11", "201")
    cell("main-t1", "300")
    w(out / "cells/main-t1/orphan.txt",
      "orphan_alive_after_1s=yes orphan_comm=sleep orphan_tracer=300 t1_tracer_alive=yes\n"
      "t1_tracer_gone_after_kill=yes after_ds=1\n")

    cell("f1-f1", "100")
    w(out / "f1-f1.rc", "0" if drop_f1 else "7")
    w(out / "f1-f1.stderr", "F8_SHARD_REFUSE: test\n")

    cell("f2-f2", "100")
    w(out / "f2-f2.rc", "7")

    cell("r1-r1", r1_tracer)

    def write_log(name: str, counts: dict[tuple[str, str], int]):
        lines = []
        for (act, exe), n in counts.items():
            for _ in range(n):
                lines.append(f"00:00:00 pid=1 {act} /tmp/{exe}")
        w(out / f"{name}.autoshard.log", "\n".join(lines) + ("\n" if lines else ""))

    for s, exp in AJ.EXPECTED_LOG.items():
        write_log(s, exp)


class AutoshardJudgeExitCode(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="autoshard-judge-"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_pass_fail_invalid_exit_codes(self):
        d_pass = self.tmp / "pass"
        d_fail = self.tmp / "fail"
        d_inv = self.tmp / "inv"
        make_fixture(d_pass)
        make_fixture(d_fail, drop_f1=True)
        make_fixture(d_inv, r1_tracer="999")

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(AJ.main([str(d_pass)]), 0)
            self.assertEqual(AJ.main([str(d_fail)]), 1)
            self.assertEqual(AJ.main([str(d_inv)]), 1)

        p_pass = subprocess.run([sys.executable, str(HERE / "autoshard_judge.py"), str(d_pass)],
                                capture_output=True, text=True)
        p_fail = subprocess.run([sys.executable, str(HERE / "autoshard_judge.py"), str(d_fail)],
                                capture_output=True, text=True)
        p_inv = subprocess.run([sys.executable, str(HERE / "autoshard_judge.py"), str(d_inv)],
                               capture_output=True, text=True)
        self.assertEqual(p_pass.returncode, 0, p_pass.stdout)
        self.assertIn("AUTOSHARD_RULES_PASS", p_pass.stdout)
        self.assertEqual(p_fail.returncode, 1, p_fail.stdout)
        self.assertIn("AUTOSHARD_RULES_FAIL", p_fail.stdout)
        self.assertEqual(p_inv.returncode, 1, p_inv.stdout)
        self.assertIn("AUTOSHARD_INVALID", p_inv.stdout)


if __name__ == "__main__":
    unittest.main()
