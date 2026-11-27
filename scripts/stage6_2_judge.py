#!/usr/bin/env python3
"""Judge for Stage 6.2 Power Mode Comparison (STAGE6-2-POWER-MODE-FREEZE-20261127.md).

Implements sections 4-7 of the frozen spec:
  - Block-level validity gates V1-V6 (section 5)
  - Series-level schedule/retry rules, V4 spread, V7 resolution, V8 red control (section 5)
  - Primary metric, A/A noise, guardrails G1-G6, and GO / PAUSE / RETIRE / INVALID verdict (section 6)

Missing or null critical telemetry fails closed (null is never treated as 0).
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
from pathlib import Path
from typing import Any

SCHEDULE = ("B1", "P1", "P2", "B2", "B3", "P3", "P4", "B4", "S1")
PAIRS = (("B1-P1", "B1", "P1"), ("P2-B2", "B2", "P2"), ("B3-P3", "B3", "P3"), ("P4-B4", "B4", "P4"))
SLOT_MODES = {
    "B1": "balanced", "B2": "balanced", "B3": "balanced", "B4": "balanced",
    "P1": "performance", "P2": "performance", "P3": "performance", "P4": "performance",
    "S1": "power_saver",
}

EXPECTED_FLAGS = {
    "balanced": {"low_power": 0, "POWER_PERFORMANCE_MODE_OPEN": 0, "speed_mode": 0},
    "performance": {"low_power": 0, "POWER_PERFORMANCE_MODE_OPEN": 1, "speed_mode": 0},
    "power_saver": {"low_power": 1, "POWER_PERFORMANCE_MODE_OPEN": 0, "speed_mode": 0},
}

EXPECTED_MAX_FREQ_KHZ = {
    "balanced": {**{f"cpu{i}": 2745600 for i in range(6)}, "cpu6": 2880000, "cpu7": 2880000},
    "performance": {**{f"cpu{i}": 3628800 for i in range(6)}, "cpu6": 4608000, "cpu7": 4608000},
    "power_saver": {"cpu6": 768000, "cpu7": 768000},
}

EARLY_WINDOW = (0.0, 30.0)
LATE_WINDOW = (90.0, 180.0)
DEFAULT_CHARGE_STEP_UAH = 16000  # Measured in 30s dry-run (ticks of 15,000-16,000 uAh)


def _is_num(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val)


def _median(vals: list[float]) -> float | None:
    if not vals:
        return None
    return float(st.median(vals))


def _spread_ratio(vals: list[float]) -> float | None:
    if not vals:
        return None
    med = st.median(vals)
    if med <= 0:
        return None
    return (max(vals) - min(vals)) / med


def _check_flags(flags: Any, mode: str, label: str, why: list[str]) -> bool:
    if not isinstance(flags, dict):
        why.append(f"V1: {label} power_flags missing")
        return False
    exp = EXPECTED_FLAGS[mode]
    ok = True
    for k, want in exp.items():
        got = flags.get(k)
        if got != want:
            why.append(f"V1: {label} {k}={got!r} != {want}")
            ok = False
    return ok


def _check_freqs(freqs: Any, mode: str, label: str, why: list[str]) -> bool:
    if not isinstance(freqs, dict):
        why.append(f"V2: {label} scaling_max_freq missing")
        return False
    exp = EXPECTED_MAX_FREQ_KHZ[mode]
    ok = True
    for cpu, want in exp.items():
        got = freqs.get(cpu)
        if got != want:
            why.append(f"V2: {label} {cpu} scaling_max_freq={got!r} != {want}")
            ok = False
    return ok


def _compute_power_w(pre: dict, post: dict, duration_s: float | None, step_uah: int) -> float | None:
    c0 = pre.get("charge_counter_uah")
    c1 = post.get("charge_counter_uah")
    v0 = pre.get("battery_voltage_mv")
    v1 = post.get("battery_voltage_mv")
    if not (_is_num(c0) and _is_num(c1) and _is_num(v0) and _is_num(v1) and _is_num(duration_s) and duration_s > 0):
        return None
    delta_uah = abs(c0 - c1)
    if step_uah <= 0 or delta_uah < 5 * step_uah:
        return None
    avg_mv = 0.5 * (v0 + v1)
    return round(delta_uah * avg_mv * 3600.0 / (duration_s * 1e9), 3)


def validate_block(block: dict[str, Any], is_dryrun: bool = False, charge_step_uah: int = DEFAULT_CHARGE_STEP_UAH) -> dict[str, Any]:
    """Validate one measurement block against V1-V6 and summarize its metrics."""
    why: list[str] = []
    v_gates: dict[str, bool] = {}

    mode = block.get("mode")
    slot = block.get("slot")
    if mode not in EXPECTED_FLAGS:
        why.append(f"unknown mode {mode!r}")
        return {"valid": False, "why": why, "v_gates": {"V1": False}, "metrics": {}}
    if not is_dryrun and slot in SLOT_MODES and SLOT_MODES[slot] != mode:
        why.append(f"slot {slot} requires mode {SLOT_MODES[slot]}, got {mode}")

    pre = block.get("pre")
    post = block.get("post")
    samples = block.get("samples")
    batches = block.get("batches")
    if not isinstance(pre, dict) or not isinstance(post, dict) or not isinstance(samples, list) or not isinstance(batches, list):
        why.append("missing pre/post/samples/batches structure")
        return {"valid": False, "why": why, "v_gates": {}, "metrics": {}}

    # V1: power flags at start and end
    v1_pre = _check_flags(pre.get("power_flags"), mode, "start", why)
    v1_post = _check_flags(post.get("power_flags"), mode, "end", why)
    v_gates["V1"] = v1_pre and v1_post

    # V2: scaling_max_freq at start
    v_gates["V2"] = _check_freqs(pre.get("scaling_max_freq_khz"), mode, "start", why)

    # V3: start temperatures (real cpu-* max <= 55.0 C, battery <= 36.0 C)
    cpu_t0 = pre.get("cpu_real_max_c")
    bat_t0 = pre.get("battery_temp_c")
    v3_ok = True
    if not _is_num(cpu_t0) or cpu_t0 > 55.0:
        why.append(f"V3: start cpu_real_max_c={cpu_t0!r} > 55.0 or missing")
        v3_ok = False
    if not _is_num(bat_t0) or bat_t0 > 36.0:
        why.append(f"V3: start battery_temp_c={bat_t0!r} > 36.0 or missing")
        v3_ok = False
    v_gates["V3"] = v3_ok

    # V4 (per-block): discharging (status == 3) and 40 <= level <= 90 throughout
    # V5: mWakefulness == Awake throughout
    v4_ok = True
    v5_ok = True
    checkpoints = [("start", pre), *[(f"t={s.get('t_s')}", s) for s in samples], ("end", post)]
    for lbl, cp in checkpoints:
        st_val = cp.get("battery_status")
        lvl = cp.get("battery_level")
        wake = cp.get("wakefulness")
        if st_val != 3:
            why.append(f"V4: {lbl} battery_status={st_val!r} != 3 (not discharging)")
            v4_ok = False
        if not _is_num(lvl) or lvl < 40 or lvl > 90:
            why.append(f"V4: {lbl} battery_level={lvl!r} outside [40, 90]")
            v4_ok = False
        if wake != "Awake":
            why.append(f"V5: {lbl} wakefulness={wake!r} != 'Awake'")
            v5_ok = False
    v_gates["V4_block"] = v4_ok
    v_gates["V5"] = v5_ok

    # V6: ADB sample fail ratio <= 10%, bad batch ratio <= 10%
    adb_results = [cp.get("adb_ok") for _, cp in checkpoints]
    adb_total = len(adb_results)
    adb_fails = sum(1 for x in adb_results if x is not True)
    adb_fail_ratio = adb_fails / adb_total if adb_total else 1.0

    batch_total = len(batches)
    bad_batches = sum(1 for b in batches if b.get("rc") != 0 or b.get("orphan_pids") != 0)
    bad_batch_ratio = bad_batches / batch_total if batch_total else 1.0

    v6_ok = True
    if not samples:
        why.append("V6: zero 5s samples recorded")
        v6_ok = False
    if batch_total == 0:
        why.append("V6: zero batches executed")
        v6_ok = False
    if adb_fail_ratio > 0.10:
        why.append(f"V6: adb_fail_ratio={adb_fail_ratio:.3f} > 0.10 ({adb_fails}/{adb_total})")
        v6_ok = False
    if bad_batch_ratio > 0.10:
        why.append(f"V6: bad_batch_ratio={bad_batch_ratio:.3f} > 0.10 ({bad_batches}/{batch_total})")
        v6_ok = False

    valid_batches = [b for b in batches if b.get("rc") == 0 and b.get("orphan_pids") == 0]
    early_batches = [b for b in valid_batches if _is_num(b.get("start_offset_s")) and EARLY_WINDOW[0] <= b["start_offset_s"] < EARLY_WINDOW[1]]
    late_batches = [b for b in valid_batches if _is_num(b.get("start_offset_s")) and LATE_WINDOW[0] <= b["start_offset_s"] <= LATE_WINDOW[1]]

    if not early_batches:
        why.append("V6: no valid batches in early window (0-30s)")
        v6_ok = False
    if not is_dryrun and not late_batches:
        why.append("V6: no valid batches in late window (90-180s)")
        v6_ok = False
    v_gates["V6"] = v6_ok

    # Guardrail data extraction
    g4_ok = True
    max_bat_c = None
    max_cpu_c = None
    for lbl, cp in checkpoints:
        bt = cp.get("battery_temp_c")
        ct = cp.get("cpu_real_max_c")
        if not _is_num(bt) or not _is_num(ct):
            g4_ok = False
        else:
            max_bat_c = bt if max_bat_c is None else max(max_bat_c, bt)
            max_cpu_c = ct if max_cpu_c is None else max(max_cpu_c, ct)
            if bt > 42.0 or ct > 85.0:
                g4_ok = False

    late_samples = [s for s in samples if _is_num(s.get("t_s")) and LATE_WINDOW[0] <= s["t_s"] <= LATE_WINDOW[1]]
    g3_late_thermal_ok = bool(late_samples) and all(s.get("thermal_status") == 0 for s in late_samples)

    termux_kills = block.get("termux_kills")
    has_termux_kill = bool(termux_kills) if isinstance(termux_kills, list) else True
    g5_ok = (bad_batches == 0) and (not has_termux_kill)

    def _batch_vals(sub: list[dict], key: str) -> list[float]:
        return [float(b[key]) for b in sub if _is_num(b.get(key))]

    early_wall_med = _median(_batch_vals(early_batches, "wall_ms"))
    late_wall_med = _median(_batch_vals(late_batches, "wall_ms"))
    late_click_p95_med = _median(_batch_vals(late_batches, "click_p95_ms"))
    late_raf_p95_med = _median(_batch_vals(late_batches, "raf_p95_ms"))
    late_drop33_vals = [int(b["drop_gt33ms"]) for b in late_batches if isinstance(b.get("drop_gt33ms"), int)]
    late_drop33_total = sum(late_drop33_vals) if len(late_drop33_vals) == len(late_batches) and late_batches else None

    late_early_ratio = None
    if early_wall_med and late_wall_med and early_wall_med > 0:
        late_early_ratio = late_wall_med / early_wall_med

    mem_avail_vals = [float(cp["mem_avail_mb"]) for _, cp in checkpoints if _is_num(cp.get("mem_avail_mb"))]

    metrics = {
        "slot": slot,
        "mode": mode,
        "start_battery_level": pre.get("battery_level"),
        "adb_fail_ratio": round(adb_fail_ratio, 4),
        "bad_batch_ratio": round(bad_batch_ratio, 4),
        "batches_total": batch_total,
        "batches_valid": len(valid_batches),
        "early_batches": len(early_batches),
        "late_batches": len(late_batches),
        "early_wall_ms_median": early_wall_med,
        "late_wall_ms_median": late_wall_med,
        "late_early_ratio": late_early_ratio,
        "late_click_p95_ms_median": late_click_p95_med,
        "late_raf_p95_ms_median": late_raf_p95_med,
        "late_drop_gt33ms_total": late_drop33_total,
        "max_battery_temp_c": max_bat_c,
        "max_cpu_real_c": max_cpu_c,
        "g3_late_thermal_status_0": g3_late_thermal_ok,
        "g4_temp_safe": g4_ok,
        "g5_clean": g5_ok,
        "mem_avail_min_mb": min(mem_avail_vals) if mem_avail_vals else None,
        "power_w": _compute_power_w(pre, post, block.get("duration_s"), charge_step_uah),
        "vmstat_delta": block.get("vmstat_delta"),
        "zram_before": pre.get("zram"),
        "zram_after": post.get("zram"),
        "psi": None,
        "secondary": {
            "launch_ms_median": _median(_batch_vals(valid_batches, "launch_ms")),
            "tracer_cpu_ms_median": _median(_batch_vals(valid_batches, "tracer_cpu_ms")),
            "inner_total_ms_median": _median(_batch_vals(valid_batches, "inner_total_ms")),
            "click_p50_ms_median": _median(_batch_vals(valid_batches, "click_p50_ms")),
            "peak_pss_mb_median": _median(_batch_vals(valid_batches, "peak_pss_mb")),
        },
    }
    return {"valid": not why, "why": why, "v_gates": v_gates, "metrics": metrics}


def judge_series(series: dict[str, Any], charge_step_uah: int = DEFAULT_CHARGE_STEP_UAH) -> dict[str, Any]:
    """Judge a complete Stage 6.2 series and return GO / PAUSE / RETIRE / INVALID."""
    raw_blocks = series.get("blocks")
    why: list[str] = []
    if not isinstance(raw_blocks, list):
        return {"verdict": "INVALID", "why": ["blocks list missing"], "v_gates": {}, "g_gates": {}}

    slot_records: dict[str, list[dict[str, Any]]] = {}
    chosen_valid: dict[str, dict[str, Any]] = {}
    evaluated: list[dict[str, Any]] = []

    for idx, blk in enumerate(raw_blocks):
        if not isinstance(blk, dict):
            why.append(f"block[{idx}] is not a dict")
            continue
        slot = blk.get("slot")
        attempt = blk.get("attempt", 1)
        if slot not in SLOT_MODES:
            why.append(f"unknown slot {slot!r} at index {idx}")
            continue
        res = validate_block(blk, is_dryrun=False, charge_step_uah=charge_step_uah)
        entry = {"slot": slot, "attempt": attempt, "mode": blk.get("mode"), **res}
        evaluated.append(entry)
        slot_records.setdefault(slot, []).append(entry)

        if len(slot_records[slot]) > 2:
            why.append(f"slot {slot} has >2 attempts")
        if attempt not in (1, 2) or attempt != len(slot_records[slot]):
            why.append(f"slot {slot} invalid attempt numbering ({attempt})")
        if attempt == 2 and slot_records[slot][0]["valid"]:
            why.append(f"slot {slot} re-run despite attempt 1 already valid (no cherry-picking)")
        if res["valid"]:
            chosen_valid[slot] = entry

    # Verify slot order and completeness
    seen_slots_first_pass = [e["slot"] for e in evaluated if e["attempt"] == 1]
    if tuple(seen_slots_first_pass) != SCHEDULE:
        why.append(f"schedule first-pass order {seen_slots_first_pass} != {list(SCHEDULE)}")

    missing_slots = [s for s in SCHEDULE if s not in chosen_valid]
    if missing_slots:
        why.append(f"missing valid block for slots: {missing_slots}")

    v_gates: dict[str, Any] = {}
    if missing_slots or why:
        return {
            "verdict": "INVALID",
            "why": why,
            "blocks": evaluated,
            "v_gates": v_gates,
            "g_gates": {},
        }

    # Series-level V4: start battery level spread <= 5 percentage points across all 9 valid blocks
    start_levels = [chosen_valid[s]["metrics"]["start_battery_level"] for s in SCHEDULE]
    if any(not _is_num(x) for x in start_levels):
        v_gates["V4_series"] = False
        why.append("V4: missing start_battery_level in one or more blocks")
    else:
        lvl_spread = max(start_levels) - min(start_levels)
        v_gates["V4_series"] = lvl_spread <= 5.0
        if not v_gates["V4_series"]:
            why.append(f"V4: start battery level spread={lvl_spread} > 5 percentage points")

    b_slots = ("B1", "B2", "B3", "B4")
    p_slots = ("P1", "P2", "P3", "P4")
    b_late_walls = [chosen_valid[s]["metrics"]["late_wall_ms_median"] for s in b_slots]
    p_late_walls = [chosen_valid[s]["metrics"]["late_wall_ms_median"] for s in p_slots]
    s1_late_wall = chosen_valid["S1"]["metrics"]["late_wall_ms_median"]

    spread_b = _spread_ratio(b_late_walls)
    spread_p = _spread_ratio(p_late_walls)
    v7_ok = (spread_b is not None and spread_b <= 0.04) and (spread_p is not None and spread_p <= 0.04)
    v_gates["V7"] = v7_ok
    if not v7_ok:
        why.append(f"V7: intra-mode late wall_ms spread exceeded 4% (B={spread_b}, P={spread_p})")

    b_4block_med = _median(b_late_walls)
    red_slowdown = None
    if b_4block_med and s1_late_wall and b_4block_med > 0:
        red_slowdown = (s1_late_wall - b_4block_med) / b_4block_med
    v8_ok = red_slowdown is not None and red_slowdown >= 0.02
    v_gates["V8"] = v8_ok
    if not v8_ok:
        why.append(f"V8: red control S1 slowdown={red_slowdown} < 0.02 (2.0%)")

    if why:
        return {
            "verdict": "INVALID",
            "why": why,
            "blocks": evaluated,
            "v_gates": v_gates,
            "g_gates": {},
            "spread_b": spread_b,
            "spread_p": spread_p,
            "red_slowdown": red_slowdown,
        }

    aa_noise = max(spread_b, spread_p)

    # Pair comparisons
    pair_rows = []
    imp_late_list: list[float] = []
    imp_early_list: list[float] = []
    for pair_name, b_slot, p_slot in PAIRS:
        bm = chosen_valid[b_slot]["metrics"]
        pm = chosen_valid[p_slot]["metrics"]
        b_late = bm["late_wall_ms_median"]
        p_late = pm["late_wall_ms_median"]
        b_early = bm["early_wall_ms_median"]
        p_early = pm["early_wall_ms_median"]
        imp_late = (b_late - p_late) / b_late
        imp_early = (b_early - p_early) / b_early
        imp_late_list.append(imp_late)
        imp_early_list.append(imp_early)
        pair_rows.append({
            "pair": pair_name,
            "b_late_wall_ms": b_late,
            "p_late_wall_ms": p_late,
            "imp_late": round(imp_late, 6),
            "b_early_wall_ms": b_early,
            "p_early_wall_ms": p_early,
            "imp_early": round(imp_early, 6),
        })

    imp_late_med = float(st.median(imp_late_list))
    wins_ge_2pct = sum(1 for x in imp_late_list if x >= 0.02)
    early_wins_ge_2pct = sum(1 for x in imp_early_list if x >= 0.02)

    # Guardrails G1-G6 across B1..B4 and P1..P4 (G4/G5 also check S1 safety, wait: G4 says "所有取樣", G5 says "區塊內")
    b_clicks = [chosen_valid[s]["metrics"]["late_click_p95_ms_median"] for s in b_slots]
    p_clicks = [chosen_valid[s]["metrics"]["late_click_p95_ms_median"] for s in p_slots]
    if any(not _is_num(x) for x in b_clicks + p_clicks):
        g1_ok = False
    else:
        g1_ok = st.median(p_clicks) <= 1.15 * st.median(b_clicks)

    b_rafs = [chosen_valid[s]["metrics"]["late_raf_p95_ms_median"] for s in b_slots]
    p_rafs = [chosen_valid[s]["metrics"]["late_raf_p95_ms_median"] for s in p_slots]
    b_drops = [chosen_valid[s]["metrics"]["late_drop_gt33ms_total"] for s in b_slots]
    p_drops = [chosen_valid[s]["metrics"]["late_drop_gt33ms_total"] for s in p_slots]
    if any(not _is_num(x) for x in b_rafs + p_rafs) or any(x is None for x in b_drops + p_drops):
        g2_ok = False
    else:
        g2_ok = (st.median(p_rafs) <= st.median(b_rafs) + 1.0) and (sum(p_drops) <= sum(b_drops))

    g3_ok = all(chosen_valid[s]["metrics"]["g3_late_thermal_status_0"] for s in p_slots)
    g4_ok = all(chosen_valid[s]["metrics"]["g4_temp_safe"] for s in SCHEDULE)
    g5_ok = all(chosen_valid[s]["metrics"]["g5_clean"] for s in SCHEDULE)

    b_ratios = [chosen_valid[s]["metrics"]["late_early_ratio"] for s in b_slots]
    p_ratios = [chosen_valid[s]["metrics"]["late_early_ratio"] for s in p_slots]
    if any(not _is_num(x) for x in b_ratios + p_ratios):
        g6_ok = False
    else:
        g6_ok = st.median(p_ratios) <= st.median(b_ratios) + 0.03

    g_gates = {
        "G1": g1_ok, "G2": g2_ok, "G3": g3_ok,
        "G4": g4_ok, "G5": g5_ok, "G6": g6_ok,
    }

    # Verdict logic (section 6)
    reasons: list[str] = []
    if imp_late_med < 0.005:
        reasons.append(f"median late improvement {imp_late_med:.4f} < 0.005 (0.5%)")
    if any(x <= -0.02 for x in imp_late_list):
        reasons.append(f"at least one pair regressed <= -2.0%: {imp_late_list}")
    if not g5_ok:
        reasons.append("G5 failed (am_kill/lmk on com.termux, orphan_pids!=0, or rc!=0)")

    if reasons:
        verdict = "RETIRE"
    elif wins_ge_2pct == 4 and imp_late_med >= 2.0 * aa_noise and all(g_gates.values()):
        verdict = "GO"
        reasons.append("all GO criteria and G1-G6 guardrails satisfied")
    else:
        verdict = "PAUSE"
        if early_wins_ge_2pct == 4 and wins_ge_2pct < 4:
            reasons.append("early window 4/4 >= 2.0% but late window fell short (thermal throttling / drift)")
        if wins_ge_2pct < 4:
            reasons.append(f"only {wins_ge_2pct}/4 pairs achieved >= 2.0% late improvement")
        if imp_late_med < 2.0 * aa_noise:
            reasons.append(f"median improvement {imp_late_med:.4f} < 2 * aa_noise ({2.0 * aa_noise:.4f})")
        failed_g = [k for k, ok in g_gates.items() if not ok]
        if failed_g:
            reasons.append(f"guardrails failed: {failed_g}")

    return {
        "verdict": verdict,
        "why": reasons,
        "aa_noise": round(aa_noise, 6),
        "spread_b": round(spread_b, 6),
        "spread_p": round(spread_p, 6),
        "red_slowdown": round(red_slowdown, 6),
        "imp_late_median": round(imp_late_med, 6),
        "wins_ge_2pct": f"{wins_ge_2pct}/4",
        "early_wins_ge_2pct": f"{early_wins_ge_2pct}/4",
        "pairs": pair_rows,
        "v_gates": v_gates,
        "g_gates": g_gates,
        "blocks": evaluated,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stage 6.2 power-mode judge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b_p = sub.add_parser("block", help="Validate a single block JSON")
    b_p.add_argument("path", type=Path)
    b_p.add_argument("--dryrun", action="store_true")
    b_p.add_argument("--charge-step-uah", type=int, default=DEFAULT_CHARGE_STEP_UAH)
    s_p = sub.add_parser("series", help="Judge a full 9-slot series JSON")
    s_p.add_argument("path", type=Path)
    s_p.add_argument("--charge-step-uah", type=int, default=DEFAULT_CHARGE_STEP_UAH)
    args = ap.parse_args(argv)

    data = json.loads(args.path.read_text(encoding="utf-8"))
    if args.cmd == "block":
        res = validate_block(data, is_dryrun=args.dryrun, charge_step_uah=args.charge_step_uah)
        rc = 0 if res["valid"] else 1
    else:
        res = judge_series(data, charge_step_uah=args.charge_step_uah)
        rc = 1 if res["verdict"] == "INVALID" else 0
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main())
