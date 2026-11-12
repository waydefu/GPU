#!/usr/bin/env python3
"""Host tests for R7-09 early-fail classifier and frozen judge need=()."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
DESIGN = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design")

_cspec = importlib.util.spec_from_file_location(
    "classify_r7_09_early_fail",
    RUNTIME / "scripts" / "classify_r7_09_early_fail.py",
)
C = importlib.util.module_from_spec(_cspec)
assert _cspec.loader is not None
_cspec.loader.exec_module(C)

_jspec = importlib.util.spec_from_file_location("judge_r7", DESIGN / "judge-r7.py")
J = importlib.util.module_from_spec(_jspec)
assert _jspec.loader is not None
_jspec.loader.exec_module(J)


def ev(seq, role, event, gen=1, serial=0, src=0, dst=0):
    return (
        f"I gatea-telemetry: GATEA_EVENT seq={seq} role={role} event={event} "
        f"generation={gen} serial={serial} src={src} dst={dst}\n"
    )


def halt(what, reason):
    return f"F gatea-a1: GATEA_FATAL_HALT what={what} reason={reason}\n"


def summary():
    return (
        "I gatea-a1: GATEA_SUMMARY where=x-wrong-generation nonce=1 "
        "generation=1 nextSequence=2 overflow=0 firstFailed=0 generationFatal=6 "
        "fatalReason=6 c0=0 c1=0 c2=0 c3=0 c4=0 c5=0 c6=0 c7=0 c8=0 c9=0 "
        "c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 c16=1 c17=0 c18=0 c19=0 "
        "c20=0 c21=0 c22=0 c23=0 c24=1 c25=0 c26=0 c27=0\n"
    )


def expected_follow():
    return "".join([
        ev(0, 1, 35, serial=0, src=9, dst=1),
        ev(1, 1, 16, serial=0),
        halt("x-wrong-generation", 6),
        summary(),
    ])


class ClassifyR709Tests(unittest.TestCase):
    def test_expected_early_fatal_not_died_during_8s_invalid(self):
        r = C.classify(
            follow=expected_follow(),
            x_alive=0, env_captured=1, env_exact=1,
            died_before_startup_deadline=1,
        )
        self.assertEqual(r["classification"], C.EXPECTED_EARLY_FAIL)
        self.assertEqual(r["died_during_8s_invalid"], "NO")
        self.assertEqual(r["continue_judge"], "YES")
        self.assertEqual(r["runner_invalid"], "NO")
        self.assertEqual(r["fixture_required"], "NO")
        self.assertEqual(r["event35_enum"], 9)
        self.assertEqual(r["event35_side"], 1)
        self.assertEqual(r["last_halt_what"], "x-wrong-generation")
        self.assertEqual(r["last_halt_reason"], 6)

    def test_unrelated_early_death_invalid(self):
        follow = "X disappeared\n"
        r = C.classify(
            follow=follow,
            x_alive=0, env_captured=1, env_exact=1,
            died_before_startup_deadline=1,
        )
        self.assertEqual(r["classification"], C.UNRELATED_EARLY_DEATH)
        self.assertEqual(r["died_during_8s_invalid"], "YES")
        self.assertEqual(r["continue_judge"], "NO")
        self.assertEqual(r["runner_invalid"], "YES")

    def test_wrong_enum_early_death_invalid(self):
        follow = "".join([
            ev(0, 2, 35, serial=5, src=8, dst=2),
            ev(1, 2, 16, serial=5),
            halt("r-test-fatal-pre-fence", 6),
            summary(),
        ])
        r = C.classify(
            follow=follow,
            x_alive=0, env_captured=1, env_exact=1,
            died_before_startup_deadline=1,
        )
        self.assertEqual(r["classification"], C.UNRELATED_EARLY_DEATH)
        self.assertEqual(r["runner_invalid"], "YES")

    def test_missing_env_invalid_even_with_expected_fatal(self):
        r = C.classify(
            follow=expected_follow(),
            x_alive=0, env_captured=0, env_exact=0,
            died_before_startup_deadline=1,
        )
        self.assertEqual(r["classification"], C.INVALID_ENV)
        self.assertEqual(r["runner_invalid"], "YES")
        self.assertEqual(r["continue_judge"], "NO")

    def test_env_mismatch_invalid(self):
        r = C.classify(
            follow=expected_follow(),
            x_alive=0, env_captured=1, env_exact=0,
            died_before_startup_deadline=1,
        )
        self.assertEqual(r["classification"], C.INVALID_ENV)
        self.assertEqual(r["runner_invalid"], "YES")

    def test_survived_startup_continues_to_judge(self):
        r = C.classify(
            follow=expected_follow(),
            x_alive=0, env_captured=1, env_exact=1,
            died_before_startup_deadline=0,
        )
        self.assertEqual(r["classification"], C.CONTINUE_TO_JUDGE)
        self.assertEqual(r["continue_judge"], "YES")
        self.assertEqual(r["fixture_required"], "NO")

    def test_frozen_judge_accepts_no_publish(self):
        follow = expected_follow()
        self.assertTrue(
            J.judge("wrong-generation-frame", follow, x_alive=0, exit_signal=0)
            .startswith("R7_PASS wrong-generation-frame")
        )

    def test_frozen_judge_rejects_missing_fault(self):
        follow = "".join([ev(0, 1, 16), halt("x-wrong-generation", 6), summary()])
        with self.assertRaises(J.JudgeFail) as ctx:
            J.judge("wrong-generation-frame", follow)
        self.assertEqual(ctx.exception.code, "fault_missing")

    def test_dump_only_event35_still_expected(self):
        r = C.classify(
            follow="",
            dump=expected_follow(),
            x_alive=0, env_captured=1, env_exact=1,
            died_before_startup_deadline=1,
        )
        self.assertEqual(r["classification"], C.EXPECTED_EARLY_FAIL)
        self.assertEqual(r["died_during_8s_invalid"], "NO")

    def test_covering_halt_not_expected_early_fail(self):
        follow = expected_follow() + halt("x-hup", 6)
        r = C.classify(
            follow=follow,
            x_alive=0, env_captured=1, env_exact=1,
            died_before_startup_deadline=1,
        )
        self.assertEqual(r["classification"], C.UNRELATED_EARLY_DEATH)
        self.assertEqual(r["runner_invalid"], "YES")
        self.assertEqual(r["last_halt_what"], "x-hup")
        self.assertEqual(r["continue_judge"], "NO")

    def test_frozen_judge_rejects_wrong_side(self):
        follow = "".join([
            ev(0, 2, 35, serial=0, src=9, dst=2),
            ev(1, 1, 16),
            halt("x-wrong-generation", 6),
            summary(),
        ])
        with self.assertRaises(J.JudgeFail) as ctx:
            J.judge("wrong-generation-frame", follow)
        self.assertEqual(ctx.exception.code, "fault_cell_or_side")


if __name__ == "__main__":
    unittest.main()
