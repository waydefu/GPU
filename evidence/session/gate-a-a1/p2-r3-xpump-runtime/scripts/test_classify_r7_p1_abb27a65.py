#!/usr/bin/env python3
"""Host mocks for abb27a65 R7-P1 present-hold-complete classifier.

No ADB. Does not create runtime-abb27a65/r7-p1.
"""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
DESIGN = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design")
CLASSIFY = RUNTIME / "scripts" / "classify_r7_p1_abb27a65.py"
JUDGE = DESIGN / "judge-r7.py"

_cspec = importlib.util.spec_from_file_location("classify_r7_p1_abb27a65", CLASSIFY)
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


def summary(where: str = "x-present-copy-wait", fatal: int = 4) -> str:
    return (
        f"09-17 23:00:02.060  13115 13536 I gatea-a1: GATEA_SUMMARY where={where} "
        f"nonce=1 generation=1 nextSequence=4 overflow=0 firstFailed=0 "
        f"generationFatal={fatal} fatalReason={fatal} c0=0 c1=0 c2=0 c3=0 c4=1 "
        f"c5=0 c6=0 c7=0 c8=0 c9=0 c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 "
        f"c16=1 c17=0 c18=0 c19=0 c20=0 c21=0 c22=0 c23=0 c24=0 c25=0 c26=0 c27=0\n"
    )


def construction(include36: bool = True, present_serial: int = 7,
                 fault_serial: int = 7) -> str:
    parts = [
        ev("09-17 23:00:00.000", 0, 1, 30, serial=present_serial, src=4, dst=9),
        ev("09-17 23:00:00.010", 1, 2, 35, serial=fault_serial, src=12, dst=2),
    ]
    if include36:
        parts.append(ev("09-17 23:00:00.020", 2, 1, 36, serial=present_serial, src=1, dst=7))
    return "".join(parts)


def early_copy_then_present() -> str:
    return (
        ev("09-17 23:00:00.000", 0, 1, 30, serial=1, src=1, dst=0)
        + ev("09-17 23:00:00.010", 1, 2, 35, serial=1, src=12, dst=2)
        + ev("09-17 23:00:00.200", 2, 1, 30, serial=7, src=4, dst=9)
    )


def run_cli(follow: str, mode: str = "r7-p1-cell", renderer_alive: int = 1,
            activity_pre_cleanup: int = 1) -> tuple[int, dict[str, str]]:
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        follow_path = tdir / "follow.txt"
        out_path = tdir / "classify.txt"
        follow_path.write_text(follow)
        rc = subprocess.run(
            [
                "python3", str(CLASSIFY),
                "--mode", mode,
                "--follow", str(follow_path),
                "--env-captured", "1",
                "--env-exact", "1",
                "--renderer-alive", str(renderer_alive),
                "--activity-pre-cleanup", str(activity_pre_cleanup),
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


class ClassifyR7P1Abb27a65Tests(unittest.TestCase):
    def test_expected_present_timeout_pass(self):
        follow = (
            construction()
            + ev("09-17 23:00:02.040", 3, 1, 16, serial=7)
            + halt("09-17 23:00:02.050", "x-present-copy-wait", 4)
            + summary()
            + "09-17 23:00:02.080  12 12 I p_r6_d2_present: FAIL CompleteNotify timeout serial=1\n"
        )
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 0)
        self.assertEqual(rec["classification"], C.EXPECTED_PRESENT_TIMEOUT)
        self.assertEqual(rec["product_fail"], "NO")
        self.assertEqual(rec["runner_invalid"], "NO")
        self.assertEqual(rec["continue_judge"], "YES")
        self.assertEqual(rec["last_halt"], "x-present-copy-wait/4")
        self.assertEqual(rec["x_hup"], "0")
        elapsed = int(rec["elapsed_ms"])
        self.assertGreaterEqual(elapsed, 1500)
        self.assertLessEqual(elapsed, 4500)
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write(follow)
            path = f.name
        j = subprocess.run(
            ["python3", str(JUDGE), "present-hold-complete", path,
             "--x-alive", "0", "--exit-signal", "0"],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(j.returncode, 0, msg=j.stdout + j.stderr)
        self.assertTrue(j.stdout.startswith("R7_PASS present-hold-complete"), j.stdout)

    def test_early_copyarea_cannot_consume_enum12(self):
        follow = early_copy_then_present() + halt("09-17 23:00:02.050", "x-present-copy-wait", 4)
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 9)
        self.assertEqual(rec["classification"], C.EARLY_COPY_CONSUME)
        self.assertEqual(rec["runner_invalid"], "YES")

    def test_wrong_serial_cannot_consume(self):
        follow = construction(fault_serial=1) + halt("09-17 23:00:02.050", "x-present-copy-wait", 4)
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 9)
        self.assertEqual(rec["classification"], C.SERIAL_MISMATCH)

    def test_wrong_generation_cannot_consume(self):
        follow = (
            ev("09-17 23:00:00.000", 0, 1, 30, serial=7, src=4, dst=9, generation=1)
            + ev("09-17 23:00:00.010", 1, 2, 35, serial=7, src=12, dst=2, generation=2)
            + halt("09-17 23:00:02.050", "x-present-copy-wait", 4)
        )
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 9)
        self.assertEqual(rec["classification"], C.SERIAL_MISMATCH)

    def test_pre_target_copyarea_ok_if_unrelated_serial(self):
        follow = (
            ev("09-17 23:00:00.000", 0, 1, 30, serial=1, src=1, dst=0)
            + ev("09-17 23:00:00.010", 1, 1, 30, serial=7, src=4, dst=9)
            + ev("09-17 23:00:00.020", 2, 2, 35, serial=7, src=12, dst=2)
            + ev("09-17 23:00:00.030", 3, 1, 36, serial=7, src=1, dst=7)
            + ev("09-17 23:00:02.040", 4, 1, 16, serial=7)
            + halt("09-17 23:00:02.050", "x-present-copy-wait", 4)
            + summary()
        )
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 0)
        self.assertEqual(rec["classification"], C.EXPECTED_PRESENT_TIMEOUT)

    def test_peer_died_hup_not_valid_p1(self):
        follow = construction() + halt("09-17 23:00:00.100", "x-hup", 6)
        rc, rec = run_cli(follow, renderer_alive=0, activity_pre_cleanup=0)
        self.assertEqual(rc, 9)
        self.assertEqual(rec["classification"], C.PEER_DIED)
        self.assertNotEqual(rec["classification"], C.EXPECTED_PRESENT_TIMEOUT)

    def test_live_renderer_wrong_hup_is_product_fail(self):
        follow = construction() + halt("09-17 23:00:02.050", "x-hup", 6)
        rc, rec = run_cli(follow, renderer_alive=1, activity_pre_cleanup=1)
        self.assertEqual(rc, 2)
        self.assertEqual(rec["product_fail"], "YES")
        self.assertIn(rec["classification"], (C.WRONG_TERMINAL, C.PEER_DIED))

    def test_wrong_reason4_direct_not_success(self):
        follow = construction() + halt("09-17 23:00:02.050", "x-direct-not-success", 4)
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 2)
        self.assertEqual(rec["classification"], C.WRONG_REASON4_IDENTITY)

    def test_target_completed_event34_then_timeout(self):
        follow = (
            construction()
            + ev("09-17 23:00:01.000", 3, 1, 34, src=0, dst=7)
            + halt("09-17 23:00:02.050", "x-present-copy-wait", 4)
            + summary()
        )
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 2)
        self.assertEqual(rec["classification"], C.TARGET_COMPLETED)

    def test_no_present_callback(self):
        follow = ev("09-17 23:00:00.010", 0, 2, 35, src=12, dst=2)
        follow += halt("09-17 23:00:02.050", "x-present-copy-wait", 4)
        rc, rec = run_cli(follow)
        self.assertEqual(rc, 9)
        self.assertEqual(rec["classification"], C.NO_PRESENT_CALLBACK)

    def test_wait_architecture_hup_still_works(self):
        follow = halt("09-17 23:00:00.100", "x-hup", 6)
        rc, rec = run_cli(follow, mode="wait-architecture")
        self.assertEqual(rc, 0)
        self.assertEqual(rec["classification"], C.WAIT_ARCHITECTURE_HUP)

    def test_wait_architecture_timeout_still_works(self):
        follow = construction() + halt("09-17 23:00:02.050", "x-present-copy-wait", 4)
        rc, rec = run_cli(follow, mode="wait-architecture")
        self.assertEqual(rc, 0)
        self.assertEqual(rec["classification"], C.WAIT_ARCHITECTURE_TIMEOUT)


if __name__ == "__main__":
    unittest.main()
