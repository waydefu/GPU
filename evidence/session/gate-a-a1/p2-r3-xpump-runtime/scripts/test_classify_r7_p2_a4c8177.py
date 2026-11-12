#!/usr/bin/env python3
"""Host mocks for a4c8177 R7-P2 present-renderer-exit classifier.

No ADB. Does not create runtime-a4c8177/r7-p2.
"""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
DESIGN = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design")
CLASSIFY = RUNTIME / "scripts" / "classify_r7_p2_a4c8177.py"
JUDGE = DESIGN / "judge-r7.py"

_cspec = importlib.util.spec_from_file_location("classify_r7_p2_a4c8177", CLASSIFY)
C = importlib.util.module_from_spec(_cspec)
assert _cspec.loader is not None
_cspec.loader.exec_module(C)


def ev(ts: str, seq: int, role: int, event: int, serial: int = 7, src: int = 0,
       dst: int = 0, generation: int = 1) -> str:
    return (
        f"{ts}  13115 13536 I gatea-telemetry: GATEA_EVENT seq={seq} role={role} "
        f"event={event} generation={generation} serial={serial} src={src} dst={dst}\n"
    )


def halt(ts: str, what: str, reason: int) -> str:
    return f"{ts}  13115 13536 F gatea-a1: GATEA_FATAL_HALT what={what} reason={reason}\n"


def summary(where: str = "x-hup", fatal: int = 6) -> str:
    return (
        f"09-17 23:00:00.200  13115 13536 I gatea-a1: GATEA_SUMMARY where={where} "
        f"nonce=1 generation=1 nextSequence=4 overflow=0 firstFailed=0 "
        f"generationFatal={fatal} fatalReason={fatal} c0=0 c1=0 c2=0 c3=0 c4=0 "
        f"c5=0 c6=1 c7=0 c8=0 c9=0 c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 "
        f"c16=1 c17=0 c18=0 c19=0 c20=0 c21=0 c22=0 c23=0 c24=0 c25=0 c26=0 c27=0\n"
    )


def construction() -> str:
    return (
        ev("09-17 23:00:00.000", 0, 1, 30, serial=7, src=4, dst=9)
        + ev("09-17 23:00:00.010", 1, 2, 35, serial=7, src=13, dst=2)
    )


def run_cli(follow: str) -> tuple[int, dict[str, str]]:
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        follow_path = tdir / "follow.txt"
        out_path = tdir / "classify.txt"
        follow_path.write_text(follow)
        rc = subprocess.run(
            [
                "python3", str(CLASSIFY),
                "--mode", "r7-p2-cell",
                "--follow", str(follow_path),
                "--env-captured", "1",
                "--env-exact", "1",
                "--out", str(out_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        rec: dict[str, str] = {}
        if out_path.is_file():
            for line in out_path.read_text().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    rec[k] = v
        return rc.returncode, rec


class ClassifyR7P2Abb27a65Tests(unittest.TestCase):
    def test_expected_present_renderer_exit_pass(self):
        follow = construction() + halt("09-17 23:00:00.100", "x-hup", 6) + summary()
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 0, msg=rec)
        self.assertEqual(rec["classification"], C.EXPECTED_PRESENT_RENDERER_EXIT)
        self.assertEqual(rec["product_fail"], "NO")
        self.assertEqual(rec["runner_invalid"], "NO")
        self.assertEqual(rec["last_halt"], "x-hup/6")
        self.assertEqual(rec["x_present_copy_wait_reason4"], "0")
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write(follow)
            path = f.name
        j = subprocess.run(
            ["python3", str(JUDGE), "present-renderer-exit", path,
             "--x-alive", "0", "--exit-signal", "0"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(j.returncode, 0, msg=j.stdout + j.stderr)
        self.assertTrue(j.stdout.startswith("R7_PASS present-renderer-exit"), j.stdout)

    def test_early_copyarea_cannot_consume_enum13(self):
        follow = (
            ev("09-17 23:00:00.000", 0, 1, 30, serial=1, src=1, dst=0)
            + ev("09-17 23:00:00.010", 1, 2, 35, serial=1, src=13, dst=2)
            + ev("09-17 23:00:00.200", 2, 1, 30, serial=7, src=4, dst=9)
            + halt("09-17 23:00:00.300", "x-hup", 6)
        )
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 9)
        self.assertEqual(rec["classification"], C.EARLY_COPY_CONSUME)
        self.assertEqual(rec["runner_invalid"], "YES")

    def test_timeout_after_exit_is_fail(self):
        follow = construction() + halt("09-17 23:00:02.050", "x-present-copy-wait", 4) + summary(
            where="x-present-copy-wait", fatal=4
        )
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 2)
        self.assertEqual(rec["product_fail"], "YES")
        self.assertEqual(rec["classification"], C.WRONG_TERMINAL)

    def test_rhup_not_substitute(self):
        follow = construction() + halt("09-17 23:00:00.100", "r-hup", 6) + summary(where="r-hup")
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 2)
        self.assertEqual(rec["classification"], C.RHUP_SUBSTITUTE)

    def test_event34_is_target_completed(self):
        follow = (
            construction()
            + ev("09-17 23:00:00.050", 2, 1, 34, src=0, dst=7)
            + halt("09-17 23:00:00.100", "x-hup", 6)
            + summary()
        )
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 2)
        self.assertEqual(rec["classification"], C.TARGET_COMPLETED)

    def test_wrong_serial(self):
        follow = (
            ev("09-17 23:00:00.000", 0, 1, 30, serial=7, src=4, dst=9)
            + ev("09-17 23:00:00.010", 1, 2, 35, serial=1, src=13, dst=2)
            + halt("09-17 23:00:00.100", "x-hup", 6)
        )
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 9)
        self.assertEqual(rec["classification"], C.SERIAL_MISMATCH)

    def test_pre_target_copyarea_unrelated_serial_ok(self):
        follow = (
            ev("09-17 23:00:00.000", 0, 1, 30, serial=1, src=1, dst=0)
            + ev("09-17 23:00:00.010", 1, 1, 30, serial=7, src=4, dst=9)
            + ev("09-17 23:00:00.020", 2, 2, 35, serial=7, src=13, dst=2)
            + halt("09-17 23:00:00.100", "x-hup", 6)
            + summary()
        )
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 0)
        self.assertEqual(rec["classification"], C.EXPECTED_PRESENT_RENDERER_EXIT)

    def test_direct_not_success_fail(self):
        follow = construction() + halt("09-17 23:00:00.100", "x-direct-not-success", 4)
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 2)
        self.assertEqual(rec["classification"], C.WRONG_REASON4_IDENTITY)


if __name__ == "__main__":
    unittest.main()
