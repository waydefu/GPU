#!/usr/bin/env python3
"""Host tests for R7-11 serial-wrap classifier and frozen judge no_serial0."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
DESIGN = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design")

_cspec = importlib.util.spec_from_file_location(
    "classify_r7_11_serial_wrap",
    RUNTIME / "scripts" / "classify_r7_11_serial_wrap.py",
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
        "I gatea-a1: GATEA_SUMMARY where=x-serial-wrap nonce=1 "
        "generation=1 nextSequence=3 overflow=0 firstFailed=0 generationFatal=6 "
        "fatalReason=6 c0=0 c1=0 c2=0 c3=0 c4=0 c5=0 c6=0 c7=0 c8=0 c9=0 "
        "c10=0 c11=0 c12=0 c13=0 c14=0 c15=0 c16=1 c17=0 c18=0 c19=0 "
        "c20=0 c21=0 c22=0 c23=0 c24=1 c25=0 c26=0 c27=0\n"
    )


def expected_follow():
    return "".join([
        ev(0, 1, 2, serial=0),
        ev(1, 1, 35, serial=0, src=11, dst=1),
        ev(2, 1, 16, serial=0),
        halt("x-serial-wrap", 6),
        summary(),
    ])


class ClassifyR711Tests(unittest.TestCase):
    def test_expected_wrap_accepts_qualification_path(self):
        r = C.classify(
            follow=expected_follow(),
            x_alive=0, env_captured=1, env_exact=1,
            fixture_reached=1, holder_reached=1,
        )
        self.assertEqual(r["classification"], C.EXPECTED_WRAP)
        self.assertEqual(r["continue_judge"], "YES")
        self.assertEqual(r["runner_invalid"], "NO")
        self.assertEqual(r["product_fail"], "NO")
        self.assertEqual(r["publish_serial0"], 0)
        self.assertEqual(r["event35_enum"], 11)
        self.assertEqual(r["event35_side"], 1)
        self.assertEqual(r["last_halt_what"], "x-serial-wrap")
        self.assertEqual(r["last_halt_reason"], 6)
        self.assertEqual(r["counter_value_device_observed"], "NOT_AVAILABLE")
        self.assertEqual(r["seed_value_device_observed"], "NOT_AVAILABLE")

    def test_serial0_leaked_is_product_fail_even_with_correct_halt(self):
        follow = "".join([
            ev(0, 1, 35, serial=0, src=11, dst=1),
            ev(1, 1, 6, serial=0),
            ev(2, 1, 16, serial=0),
            halt("x-serial-wrap", 6),
            summary(),
        ])
        r = C.classify(
            follow=follow,
            x_alive=0, env_captured=1, env_exact=1,
            fixture_reached=1, holder_reached=1,
        )
        self.assertEqual(r["classification"], C.SERIAL0_LEAKED)
        self.assertEqual(r["product_fail"], "YES")
        self.assertEqual(r["publish_serial0"], 1)
        self.assertEqual(r["continue_judge"], "YES")
        self.assertEqual(r["runner_invalid"], "NO")
        with self.assertRaises(J.JudgeFail) as ctx:
            J.judge("serial-wrap", follow)
        self.assertEqual(ctx.exception.code, "publish_serial_zero")

    def test_wrong_terminal_x_hup(self):
        follow = "".join([
            ev(0, 1, 35, serial=0, src=11, dst=1),
            ev(1, 1, 16, serial=0),
            halt("x-hup", 6),
            summary(),
        ])
        r = C.classify(
            follow=follow,
            x_alive=0, env_captured=1, env_exact=1,
            fixture_reached=1, holder_reached=1,
        )
        self.assertEqual(r["classification"], C.WRONG_TERMINAL)
        self.assertEqual(r["product_fail"], "YES")
        self.assertEqual(r["last_halt_what"], "x-hup")
        self.assertEqual(r["continue_judge"], "YES")

    def test_no_event35_with_halt_is_invalid(self):
        follow = "".join([
            ev(0, 1, 16, serial=0),
            halt("x-serial-wrap", 6),
            summary(),
        ])
        r = C.classify(
            follow=follow,
            x_alive=0, env_captured=1, env_exact=1,
            fixture_reached=1, holder_reached=1,
        )
        self.assertEqual(r["classification"], C.NO_EVENT35)
        self.assertEqual(r["runner_invalid"], "YES")
        with self.assertRaises(J.JudgeFail) as ctx:
            J.judge("serial-wrap", follow)
        self.assertEqual(ctx.exception.code, "fault_missing")

    def test_repeated_seed_invalid(self):
        follow = "".join([
            ev(0, 1, 35, serial=0, src=11, dst=1),
            ev(1, 1, 35, serial=0, src=11, dst=1),
            ev(2, 1, 16, serial=0),
            halt("x-serial-wrap", 6),
            summary(),
        ])
        r = C.classify(
            follow=follow,
            x_alive=0, env_captured=1, env_exact=1,
            fixture_reached=1, holder_reached=1,
        )
        self.assertEqual(r["classification"], C.REPEATED_SEED)
        self.assertEqual(r["runner_invalid"], "YES")
        self.assertEqual(r["event35_count"], 2)

    def test_early_death_without_event35_invalid(self):
        r = C.classify(
            follow="X disappeared\n",
            x_alive=0, env_captured=1, env_exact=1,
            died_before_startup_deadline=1,
            fixture_reached=0, holder_reached=0,
        )
        self.assertEqual(r["classification"], C.UNRELATED_EARLY_DEATH)
        self.assertEqual(r["died_during_8s_invalid"], "YES")
        self.assertEqual(r["runner_invalid"], "YES")

    def test_event35_without_fixture_is_unbound_invalid(self):
        r = C.classify(
            follow=expected_follow(),
            x_alive=0, env_captured=1, env_exact=1,
            fixture_reached=0, holder_reached=0,
        )
        self.assertEqual(r["classification"], C.FIXTURE_NOT_BOUND)
        self.assertEqual(r["runner_invalid"], "YES")

    def test_missing_env_invalid(self):
        r = C.classify(
            follow=expected_follow(),
            x_alive=0, env_captured=0, env_exact=0,
            fixture_reached=1, holder_reached=1,
        )
        self.assertEqual(r["classification"], C.INVALID_ENV)
        self.assertEqual(r["runner_invalid"], "YES")

    def test_frozen_judge_accepts_no_prior_publish(self):
        follow = expected_follow()
        self.assertTrue(
            J.judge("serial-wrap", follow, x_alive=0, exit_signal=0)
            .startswith("R7_PASS serial-wrap")
        )

    def test_pre_fault_nonzero_publish_is_not_serial0_fail(self):
        follow = "".join([
            ev(0, 1, 6, serial=5),
            ev(1, 1, 35, serial=0, src=11, dst=1),
            ev(2, 1, 16, serial=0),
            halt("x-serial-wrap", 6),
            summary(),
        ])
        r = C.classify(
            follow=follow,
            x_alive=0, env_captured=1, env_exact=1,
            fixture_reached=1, holder_reached=1,
        )
        self.assertEqual(r["classification"], C.EXPECTED_WRAP)
        self.assertEqual(r["pre_fault_publish"], 1)
        self.assertEqual(r["publish_serial0"], 0)
        self.assertTrue(
            J.judge("serial-wrap", follow, x_alive=0, exit_signal=0)
            .startswith("R7_PASS serial-wrap")
        )

    def test_later_publish_after_35_is_product_fail(self):
        follow = "".join([
            ev(0, 1, 35, serial=0, src=11, dst=1),
            ev(1, 1, 6, serial=5),
            ev(2, 1, 16, serial=5),
            halt("x-serial-wrap", 6),
            summary(),
        ])
        r = C.classify(
            follow=follow,
            x_alive=0, env_captured=1, env_exact=1,
            fixture_reached=1, holder_reached=1,
        )
        self.assertEqual(r["product_fail"], "YES")
        self.assertGreater(r["later_publish_after_35"], 0)
        self.assertEqual(r["publish_serial0"], 0)

    def test_does_not_invent_observed_counter(self):
        r = C.classify(
            follow=expected_follow(),
            x_alive=0, env_captured=1, env_exact=1,
            fixture_reached=1, holder_reached=1,
        )
        self.assertNotIn("UINT64_MAX", r["counter_value_device_observed"])
        self.assertEqual(r["seed_value_device_observed"], "NOT_AVAILABLE")
        self.assertIn("source-proven", r["seed_ordering"])


if __name__ == "__main__":
    unittest.main()
