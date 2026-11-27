#!/usr/bin/env python3
"""Synthetic unit tests for stage6_2_judge.py (including required failing [RED] cases)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage6_2_judge as J  # noqa: E402
import stage6_2_power_bench as B  # noqa: E402


def _checkpoint(mode: str, t_s: float | None = None, battery_level: int = 80,
                battery_status: int = 3, wakefulness: str = "Awake",
                cpu_temp: float = 50.0, bat_temp: float = 34.0,
                thermal_status: int = 0, adb_ok: bool = True,
                charge_counter: int = 5000000, voltage_mv: int = 4150) -> dict:
    cp = {
        "power_flags": dict(J.EXPECTED_FLAGS[mode]),
        "scaling_max_freq_khz": dict(J.EXPECTED_MAX_FREQ_KHZ[mode]),
        "cpu_real_max_c": cpu_temp,
        "battery_temp_c": bat_temp,
        "battery_status": battery_status,
        "battery_level": battery_level,
        "wakefulness": wakefulness,
        "thermal_status": thermal_status,
        "adb_ok": adb_ok,
        "mem_avail_mb": 3200.0,
        "charge_counter_uah": charge_counter,
        "battery_voltage_mv": voltage_mv,
        "zram": {"physical_kb": 3000000, "swap_kb": 9000000, "total_swap_kb": 16777212},
    }
    if t_s is not None:
        cp["t_s"] = t_s
    return cp


def _make_batch(offset_s: float, wall_ms: float, click_p95: float = 12.0,
                raf_p95: float = 16.7, drop33: int = 0, rc: int = 0,
                orphan_pids: int = 0) -> dict:
    return {
        "start_offset_s": offset_s,
        "wall_ms": wall_ms,
        "inner_total_ms": wall_ms * 0.9,
        "tracer_cpu_ms": 800.0,
        "launch_ms": 400.0,
        "click_p50_ms": 8.0,
        "click_p95_ms": click_p95,
        "raf_p50_ms": 16.5,
        "raf_p95_ms": raf_p95,
        "raf_p99_ms": raf_p95 + 1.0,
        "drop_gt20ms": 0,
        "drop_gt33ms": drop33,
        "peak_pss_mb": 420.0,
        "rc": rc,
        "orphan_pids": orphan_pids,
    }


def _make_block(slot: str, attempt: int = 1, early_wall: float = 2500.0,
                late_wall: float = 2500.0, click_p95: float = 12.0,
                raf_p95: float = 16.7, drop33: int = 0,
                start_level: int = 80, end_level: int = 79,
                thermal_status_late: int = 0, termux_kills: list | None = None,
                bad_batch_count: int = 0, start_cpu_temp: float = 52.0,
                max_cpu_temp: float = 70.0, max_bat_temp: float = 38.0,
                adb_fail_samples: int = 0, end_flags_override: dict | None = None) -> dict:
    mode = J.SLOT_MODES[slot]
    pre = _checkpoint(mode, battery_level=start_level, cpu_temp=start_cpu_temp, bat_temp=34.5, charge_counter=5100000)
    post = _checkpoint(mode, battery_level=end_level, cpu_temp=max_cpu_temp, bat_temp=max_bat_temp, charge_counter=5000000)
    if end_flags_override:
        post["power_flags"] = end_flags_override

    samples = []
    for i in range(1, 37):
        t = float(i * 5)
        ts = thermal_status_late if 90.0 <= t <= 180.0 else 0
        ok = i > adb_fail_samples
        samples.append(_checkpoint(mode, t_s=t, battery_level=start_level, cpu_temp=max_cpu_temp,
                                   bat_temp=max_bat_temp, thermal_status=ts, adb_ok=ok))

    batches = []
    # 5 early (0..30s), 5 mid (30..90s), 10 late (90..180s)
    for i in range(5):
        batches.append(_make_batch(i * 5.0, early_wall, click_p95=click_p95, raf_p95=raf_p95, drop33=drop33))
    for i in range(5):
        batches.append(_make_batch(35.0 + i * 10.0, (early_wall + late_wall) / 2.0, click_p95=click_p95, raf_p95=raf_p95))
    for i in range(10):
        is_bad = i < bad_batch_count
        batches.append(_make_batch(92.0 + i * 8.0, late_wall, click_p95=click_p95, raf_p95=raf_p95,
                                   drop33=drop33, rc=1 if is_bad else 0, orphan_pids=1 if is_bad else 0))

    return {
        "slot": slot,
        "attempt": attempt,
        "mode": mode,
        "duration_s": 180.0,
        "pre": pre,
        "post": post,
        "samples": samples,
        "batches": batches,
        "termux_kills": [] if termux_kills is None else termux_kills,
        "vmstat_delta": {"pswpin": 0, "pswpout": 0, "pgmajfault": 2, "compact_stall": 0},
    }


def _make_series(b_walls=(2500.0, 2500.0, 2500.0, 2500.0),
                 p_walls=(2350.0, 2350.0, 2350.0, 2350.0),
                 s_wall=2800.0, b_early=None, p_early=None, **kw) -> dict:
    b_early = b_early or b_walls
    p_early = p_early or p_walls
    b_map = {f"B{i+1}": (b_early[i], b_walls[i]) for i in range(4)}
    p_map = {f"P{i+1}": (p_early[i], p_walls[i]) for i in range(4)}
    blocks = []
    for slot in J.SCHEDULE:
        if slot in b_map:
            ew, lw = b_map[slot]
            blocks.append(_make_block(slot, early_wall=ew, late_wall=lw, **kw.get("b_kw", {})))
        elif slot in p_map:
            ew, lw = p_map[slot]
            blocks.append(_make_block(slot, early_wall=ew, late_wall=lw, **kw.get("p_kw", {})))
        else:
            blocks.append(_make_block(slot, early_wall=s_wall, late_wall=s_wall, **kw.get("s_kw", {})))
    return {"blocks": blocks}


class Stage62JudgeTests(unittest.TestCase):
    def test_clear_win_go(self):
        # 6% improvement across 4/4 pairs, low intra-mode noise, S1 +12% slower -> GO
        res = J.judge_series(_make_series(b_walls=(2500, 2510, 2495, 2505),
                                          p_walls=(2350, 2360, 2345, 2355), s_wall=2800))
        self.assertEqual(res["verdict"], "GO", res)
        self.assertTrue(all(res["g_gates"].values()))

    def test_no_difference_retire(self):  # [RED]
        # 0.2% difference (< 0.5%) -> RETIRE
        res = J.judge_series(_make_series(b_walls=(2500, 2500, 2500, 2500),
                                          p_walls=(2495, 2495, 2495, 2495), s_wall=2800))
        self.assertEqual(res["verdict"], "RETIRE", res)

    def test_regression_retire(self):  # [RED]
        # One pair regresses by -2.4% even if median is +1.0% (and intra-mode spread <= 4%) -> RETIRE
        res = J.judge_series(_make_series(b_walls=(2500, 2500, 2500, 2500),
                                          p_walls=(2470, 2470, 2480, 2560), s_wall=2800))
        self.assertEqual(res["verdict"], "RETIRE", res)

    def test_g5_termux_kill_retire(self):  # [RED]
        res = J.judge_series(_make_series(p_kw={"termux_kills": ["am_kill com.termux"]}))
        self.assertEqual(res["verdict"], "RETIRE", res)
        self.assertFalse(res["g_gates"]["G5"])

    def test_intra_mode_spread_too_large_invalid(self):  # [RED]
        # Balanced spread = (2620 - 2450) / 2500 = 6.8% > 4% -> INVALID (V7)
        res = J.judge_series(_make_series(b_walls=(2450, 2500, 2500, 2620),
                                          p_walls=(2300, 2300, 2300, 2300), s_wall=2800))
        self.assertEqual(res["verdict"], "INVALID", res)
        self.assertFalse(res["v_gates"]["V7"])

    def test_early_win_late_collapse_pause(self):  # [RED]
        # Early 4/4 >= 2.0% (2500->2300 = +8%), late only +1.2% -> PAUSE
        res = J.judge_series(_make_series(b_early=(2500, 2500, 2500, 2500),
                                          p_early=(2300, 2300, 2300, 2300),
                                          b_walls=(2500, 2500, 2500, 2500),
                                          p_walls=(2470, 2470, 2470, 2470), s_wall=2800))
        self.assertEqual(res["verdict"], "PAUSE", res)
        self.assertEqual(res["early_wins_ge_2pct"], "4/4")

    def test_red_control_not_slow_enough_invalid(self):  # [RED]
        # S1 only +1.0% slower (< 2.0%) -> INVALID (V8)
        res = J.judge_series(_make_series(b_walls=(2500, 2500, 2500, 2500),
                                          p_walls=(2350, 2350, 2350, 2350), s_wall=2525))
        self.assertEqual(res["verdict"], "INVALID", res)
        self.assertFalse(res["v_gates"]["V8"])

    def test_guardrails_g1_g3_g4_g6_pause(self):  # [RED]
        # G1 click_p95 > 1.15x
        r1 = J.judge_series(_make_series(b_kw={"click_p95": 10.0}, p_kw={"click_p95": 12.0}))
        self.assertEqual(r1["verdict"], "PAUSE")
        self.assertFalse(r1["g_gates"]["G1"])
        # G3 thermal_status != 0 in late window
        r3 = J.judge_series(_make_series(p_kw={"thermal_status_late": 1}))
        self.assertEqual(r3["verdict"], "PAUSE")
        self.assertFalse(r3["g_gates"]["G3"])
        # G4 cpu temp > 85 C
        r4 = J.judge_series(_make_series(p_kw={"max_cpu_temp": 86.0}))
        self.assertEqual(r4["verdict"], "PAUSE")
        self.assertFalse(r4["g_gates"]["G4"])
        # G6 late/early drift worse by > 0.03
        r6 = J.judge_series(_make_series(b_early=(2500, 2500, 2500, 2500), b_walls=(2500, 2500, 2500, 2500),
                                         p_early=(2200, 2200, 2200, 2200), p_walls=(2350, 2350, 2350, 2350)))
        self.assertEqual(r6["verdict"], "PAUSE")
        self.assertFalse(r6["g_gates"]["G6"])

    def test_null_never_zero_fails_closed(self):  # [RED]
        blk = _make_block("P1")
        blk["samples"][20]["thermal_status"] = None  # inside 90-180s
        res = J.validate_block(blk)
        self.assertFalse(res["metrics"]["g3_late_thermal_status_0"])

        blk2 = _make_block("B1")
        blk2["pre"]["cpu_real_max_c"] = None
        res2 = J.validate_block(blk2)
        self.assertFalse(res2["valid"])
        self.assertFalse(res2["v_gates"]["V3"])

    def test_retry_attempt_2_allowed_only_when_attempt_1_invalid(self):
        s = _make_series()
        # Replace B1 with invalid attempt 1 (high start temp) + valid attempt 2
        bad_b1 = _make_block("B1", attempt=1, start_cpu_temp=58.0)
        good_b1 = _make_block("B1", attempt=2, early_wall=2500, late_wall=2500)
        s["blocks"] = [bad_b1, good_b1, *s["blocks"][1:]]
        res = J.judge_series(s)
        self.assertEqual(res["verdict"], "GO", res)

        # Cherry-picking a valid attempt 1 with attempt 2 -> INVALID
        s2 = _make_series()
        s2["blocks"] = [_make_block("B1", attempt=1), _make_block("B1", attempt=2), *s2["blocks"][1:]]
        self.assertEqual(J.judge_series(s2)["verdict"], "INVALID")

    def test_cli_exit_codes(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "series.json"
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                p.write_text(json.dumps(_make_series()))
                self.assertEqual(J.main(["series", str(p)]), 0)
                p.write_text(json.dumps(_make_series(s_wall=2500)))
                self.assertEqual(J.main(["series", str(p)]), 1)

    def test_battery_voltage_parser_ignores_max_charging_voltage(self):
        sample = (
            "  Max charging voltage: 0\n"
            "  Charge counter: 4642000\n"
            "  status: 3\n"
            "  level: 76\n"
            "  voltage: 4165\n"
            "  temperature: 327\n"
        )
        bat = B.parse_battery_fields(sample)
        self.assertEqual(bat["battery_voltage_mv"], 4165)
        self.assertEqual(bat["charge_counter_uah"], 4642000)
        self.assertEqual(bat["battery_temp_c"], 32.7)

    def test_power_w_uses_5x_step_threshold(self):
        blk_small = _make_block("B1")
        blk_small["pre"]["charge_counter_uah"] = 5070000
        blk_small["post"]["charge_counter_uah"] = 5000000  # 70,000 < 5 * 16,000 = 80,000 -> None
        self.assertIsNone(J.validate_block(blk_small)["metrics"]["power_w"])
        blk_big = _make_block("B1")
        blk_big["pre"]["charge_counter_uah"] = 5160000
        blk_big["post"]["charge_counter_uah"] = 5000000  # 160,000 >= 80,000 -> valid float
        self.assertIsNotNone(J.validate_block(blk_big)["metrics"]["power_w"])


if __name__ == "__main__":
    unittest.main()
