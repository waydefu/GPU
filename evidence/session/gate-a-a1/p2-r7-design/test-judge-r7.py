#!/usr/bin/env python3
"""Host negatives and positives for judge-r7.py. No ADB. No source mutation."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("judge_r7", HERE / "judge-r7.py")
J = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(J)

SRC, DST, GEN, SERIAL = 7, 5, 1, 3


def ev(seq, role, event, gen=GEN, serial=SERIAL, src=SRC, dst=DST):
    return (
        f"I gatea-telemetry: GATEA_EVENT seq={seq} role={role} event={event} "
        f"generation={gen} serial={serial} src={src} dst={dst}\n"
    )


def halt(what, reason):
    return f"F gatea-a1: GATEA_FATAL_HALT what={what} reason={reason}\n"


def summary():
    return (
        "I gatea-a1: GATEA_SUMMARY where=r-gatea-DIRECT_LOOKUP_FAIL nonce=1 "
        "generation=1 nextSequence=8 overflow=0 firstFailed=0 generationFatal=2 "
        "fatalReason=2 c0=1 c1=1 c2=0 c3=1 c4=0 c5=0 c6=0 c7=0 c8=0 c9=0 "
        "c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 c16=0 c17=0 c18=0 c19=0 "
        "c20=0 c21=0 c22=0 c23=0 c24=1 c25=0 c26=0 c27=0\n"
    )


def fatal_cell(cell_event_src, side, what, reason, extra_before="", extra_after=""):
    return "".join([
        extra_before,
        ev(0, 1, 6),
        ev(1, 2, 7),
        ev(2, side, 35, serial=SERIAL, src=cell_event_src, dst=side),
        extra_after,
        ev(3, 2, 16, serial=SERIAL, src=SRC, dst=DST),
        halt(what, reason),
        summary(),
    ])


class JudgeR7Tests(unittest.TestCase):
    def fail_code(self, cell, follow, **kw):
        with self.assertRaises(J.JudgeFail) as ctx:
            J.judge(cell, follow, **kw)
        return ctx.exception.code

    def test_zero_faults_fail(self):
        follow = "".join([ev(0, 1, 6), ev(1, 2, 7), halt("r-gatea-DIRECT_LOOKUP_FAIL", 2), summary()])
        self.assertEqual(self.fail_code("src-ready-miss", follow), "fault_missing")

    def test_two_faults_fail(self):
        follow = "".join([
            ev(0, 1, 6),
            ev(1, 2, 7),
            ev(2, 2, 35, src=1, dst=2),
            ev(3, 2, 35, src=1, dst=2),
            halt("r-gatea-DIRECT_LOOKUP_FAIL", 2),
            summary(),
        ])
        self.assertEqual(self.fail_code("src-ready-miss", follow), "fault_not_one_shot")

    def test_success_after_35_fail(self):
        follow = fatal_cell(1, 2, "r-gatea-DIRECT_LOOKUP_FAIL", 2,
                            extra_after=ev(3, 1, 17))
        # extra_after shares seq 3 with fatal; use seq 4
        follow = "".join([
            ev(0, 1, 6),
            ev(1, 2, 7),
            ev(2, 2, 35, src=1, dst=2),
            ev(3, 1, 17),
            ev(4, 2, 16),
            halt("r-gatea-DIRECT_LOOKUP_FAIL", 2),
            summary(),
        ])
        self.assertEqual(self.fail_code("src-ready-miss", follow), "progress_after_fault")

    def test_wrong_what_fail(self):
        follow = fatal_cell(1, 2, "r-other", 2)
        self.assertEqual(self.fail_code("src-ready-miss", follow), "halt_mismatch")

    def test_signal_fail(self):
        follow = fatal_cell(1, 2, "r-gatea-DIRECT_LOOKUP_FAIL", 2)
        self.assertEqual(self.fail_code("src-ready-miss", follow, exit_signal=11), "exit_was_signal")

    def test_x_alive_fail(self):
        follow = fatal_cell(1, 2, "r-gatea-DIRECT_LOOKUP_FAIL", 2)
        self.assertEqual(self.fail_code("src-ready-miss", follow, x_alive=1), "x_still_alive")

    def test_missing_construction_fail(self):
        follow = "".join([
            ev(0, 2, 35, src=1, dst=2),
            ev(1, 2, 16),
            halt("r-gatea-DIRECT_LOOKUP_FAIL", 2),
            summary(),
        ])
        self.assertEqual(self.fail_code("src-ready-miss", follow), "missing_construction_publish")

    def test_gap_without_ring_incomplete(self):
        follow = "".join([
            ev(0, 1, 6),
            ev(2, 2, 7),
            ev(3, 2, 35, src=1, dst=2),
            ev(4, 2, 16),
            halt("r-gatea-DIRECT_LOOKUP_FAIL", 2),
            summary(),
        ])
        self.assertEqual(self.fail_code("src-ready-miss", follow), "telemetry_seq_gap")

    def test_event_32_fail(self):
        follow = "".join([
            ev(0, 1, 6),
            ev(1, 1, 32),
            ev(2, 2, 7),
            ev(3, 2, 35, src=1, dst=2),
            ev(4, 2, 16),
            halt("r-gatea-DIRECT_LOOKUP_FAIL", 2),
            summary(),
        ])
        self.assertEqual(self.fail_code("src-ready-miss", follow), "event_32_present")

    def test_fatal_sample_pass(self):
        follow = fatal_cell(1, 2, "r-gatea-DIRECT_LOOKUP_FAIL", 2)
        self.assertTrue(J.judge("src-ready-miss", follow).startswith("R7_PASS"))

    def test_fbo_needs_lookup_ok(self):
        follow = "".join([
            ev(0, 1, 6),
            ev(1, 2, 7),
            ev(2, 2, 8),
            ev(3, 2, 35, src=4, dst=2),
            ev(4, 2, 16),
            halt("r-gatea-DIRECT_LOOKUP_FAIL", 2),
            summary(),
        ])
        self.assertTrue(J.judge("fbo-incomplete", follow).startswith("R7_PASS"))

    def test_quiesced_sample_pass(self):
        follow = "".join([
            ev(0, 1, 6),
            ev(1, 2, 7),
            ev(2, 2, 10),
            ev(3, 2, 35, src=5, dst=2),
            ev(4, 2, 15),
            ev(5, 1, 16),
            halt("x-direct-not-success", 2),
            summary(),
        ])
        self.assertTrue(J.judge("post-draw-gl", follow).startswith("R7_PASS"))

    def test_wrap_sample_pass(self):
        follow = "".join([
            ev(0, 1, 2, serial=0),
            ev(1, 1, 35, serial=0, src=11, dst=1),
            ev(2, 1, 16, serial=0),
            halt("x-serial-wrap", 6),
            summary(),
        ])
        self.assertTrue(J.judge("serial-wrap", follow).startswith("R7_PASS"))

    def test_wrap_serial0_publish_fail(self):
        follow = "".join([
            ev(0, 1, 35, serial=0, src=11, dst=1),
            ev(1, 1, 6, serial=0),
            ev(2, 1, 16, serial=0),
            halt("x-serial-wrap", 6),
            summary(),
        ])
        self.assertEqual(self.fail_code("serial-wrap", follow), "publish_serial_zero")

    def test_present_hold_pass(self):
        follow = "".join([
            ev(0, 1, 30, serial=SERIAL, src=4, dst=9),
            ev(1, 2, 35, src=12, dst=2),
            ev(2, 1, 36, serial=SERIAL, src=1, dst=DST),
            ev(3, 1, 16, serial=SERIAL),
            halt("x-present-copy-wait", 4),
            summary(),
        ])
        self.assertTrue(J.judge("present-hold-complete", follow).startswith("R7_PASS"))

    def test_present_event_34_fail(self):
        follow = "".join([
            ev(0, 1, 30, serial=SERIAL, src=4, dst=9),
            ev(1, 2, 35, src=12, dst=2),
            ev(2, 1, 34, serial=SERIAL, src=0, dst=DST),
            halt("x-present-copy-wait", 4),
            summary(),
        ])
        self.assertEqual(self.fail_code("present-hold-complete", follow), "event_34_on_present_cell")


if __name__ == "__main__":
    unittest.main()
