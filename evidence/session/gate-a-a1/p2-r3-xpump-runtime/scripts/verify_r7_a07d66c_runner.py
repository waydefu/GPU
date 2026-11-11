#!/usr/bin/env python3
"""Static verifier for run-r7-one-cell-a07d66c.sh.

Host-only. Does not ADB, install, launch X3, or create runtime-a07d66c/r7-01.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
RUNNER = RUNTIME / "run-r7-one-cell-a07d66c.sh"
JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py")
TEST_JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py")
LEGAL_R701 = RUNTIME / "runtime-a07d66c" / "r7-01"
HISTORICAL = {
    "run-r7-one-cell-fdfb1ce.sh": "f4fb89d66698af15caba8e02fa046b26a7f86934fb476fc49e41e9305cc4f471",
    "run-r7-05-requal-a07d66c.sh": "46c24fc94228bbc622886b51f45f1fcbd1580cc6a6ebbc9b64e09fc472096473",
}

EXPECTED_JUDGE_SHA = "fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17"
EXPECTED_TEST_JUDGE_SHA = "4d7194cdf788b122c98b5d747cc5089283c154960d9ca846ef3faa0a66e53aa5"

ENABLED = {
    ("r7-01", "src-ready-miss", "direct"),
    ("r7-02", "dst-ready-miss", "direct"),
    ("r7-03", "tuple-mismatch", "direct"),
    ("r7-06", "fence-create-fail", "direct"),
    ("r7-07", "fence-timeout", "direct"),
    ("r7-08", "renderer-fatal-pre-fence", "direct"),
    ("r7-10", "renderer-exit-after-consume", "direct"),
}
REVIEW = {
    ("r7-09", "wrong-generation-frame", "direct"),
    ("r7-11", "serial-wrap", "direct"),
    ("r7-p1", "present-hold-complete", "present"),
    ("r7-p2", "present-renderer-exit", "present"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def fail(msg: str) -> None:
    print(f"VERIFIER_FAIL {msg}")
    raise SystemExit(2)


def main() -> int:
    if not RUNNER.is_file():
        fail(f"runner missing {RUNNER}")
    text = RUNNER.read_text(encoding="utf-8")
    errors: list[str] = []

    def need(cond: bool, msg: str) -> None:
        if not cond:
            errors.append(msg)

    need("EXPECT_VERSION=1.03.01-a07d66c-17.09.26" in text, "missing a07d66c EXPECT_VERSION")
    need("EXPECT_VERSION_CODE=15" in text, "missing EXPECT_VERSION_CODE=15")
    need("CANDIDATE_HEAD=a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82" in text, "missing candidate HEAD")
    need("runtime-a07d66c" in text, "missing runtime-a07d66c root policy")
    need("runtime-fdfb1ce" in text and "forbidden" in text.lower() or "runtime-fdfb1ce*" in text,
         "missing refuse of runtime-fdfb1ce")
    need("VALIDATE_ONLY" in text, "missing VALIDATE_ONLY")
    need("destination already exists" in text, "missing destination-exists refuse before write")
    need("FROZEN_WAIT_S=12" in text, "missing WAIT_S=12 freeze")
    need("WAIT_S must be" in text, "missing WAIT_S refuse")
    need(str(JUDGE) in text, "runner must point at frozen judge-r7.py")
    need("judge-r7.py" in text, "missing frozen judge path")
    need("set -euo pipefail" in text, "missing set -euo pipefail")
    need("com.termux.x11" in text and "read-only" in text.lower() or "stable_policy=read-only" in text,
         "missing Stable read-only policy")
    need("termux-x11gpu com.waydefu.x11gpu :3" in text, "missing experimental X3 cmdline guard")
    need("am force-stop com.waydefu.x11gpu" in text, "missing experimental Activity cleanup")
    need("pkill" not in text, "pkill is forbidden")
    need("force-stop com.termux.x11" not in text, "must not force-stop Stable")
    need("kill com.termux.x11" not in text, "must not kill Stable by name")
    need("adb install" not in text.lower(), "runner must not adb install")
    need("for attempt" not in text, "retry loop forbidden")
    need("while qualification" not in text, "qualification retry forbidden")
    need("retry fixture" not in text, "fixture retry forbidden")
    need("auto_next=0" in text, "missing auto_next=0")
    need("fixture_invocation_max=1" in text, "missing single fixture invocation")
    need('"r7-01|src-ready-miss|direct"' in text, "r7-01 tuple must be enabled")
    need("LIVE_STATUS=ENABLED" in text, "missing ENABLED live status")
    need("CELL_ID=$CELL_ID is a completed frozen cell" in text, "missing completed-cell refuse")
    need("SUPPORTED_BY_MAPPING_BUT_REQUIRES_PACKET_REVIEW" in text, "missing review-required marker")
    need("TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL" in text or "TERMUX_X11_GATEA_" in text,
         "missing Gate A env hygiene")
    need("ENV_MISMATCH" in text and "got != need" in text, "missing exact env set equality")
    need("GATEA_HUP_PRESERVE" in text, "missing HUP-preserve-era logging")
    need("pre-cleanup-process.txt" in text, "missing pre-cleanup process observation")
    need("signal-audit.txt" in text, "missing PID-bound signal audit")
    need("must not fabricate exit127" in text or "not fabricated as exit127" in text,
         "missing exit127 caveat")
    need("versionName/versionCode/lastUpdateTime are live package checks only" in text,
         "missing provenance caveat")
    need("-P 5038" in text, "missing isolated ADB 5038")
    need("exit 0" in text and "VALIDATE_ONLY_OK" in text, "VALIDATE_ONLY must exit 0 after plan")

    mkdir_idx = text.find('mkdir -p "$CELL"')
    exists_idx = text.find("destination already exists")
    validate_idx = text.find('if [ "$VALIDATE_ONLY" = 1 ]')
    source_idx = text.find("source \"$ROOT_HARNESS/harness-lib.sh\"")
    need(exists_idx != -1 and mkdir_idx != -1 and exists_idx < mkdir_idx,
         "destination exists check must precede mkdir")
    need(validate_idx != -1 and source_idx != -1 and validate_idx < source_idx,
         "VALIDATE_ONLY must return before sourcing harness/ADB")
    need(validate_idx < mkdir_idx, "VALIDATE_ONLY must return before mkdir")

    for cell, fault, fixture in ENABLED:
        needle = f'"{cell}|{fault}|{fixture}"'
        need(needle in text, f"missing ENABLED mapping {needle}")
    for cell, fault, fixture in REVIEW:
        needle = f'"{cell}|{fault}|{fixture}"'
        need(needle in text, f"missing REVIEW mapping {needle}")

    need(LEGAL_R701.exists() is False, f"legal cell dir must remain absent: {LEGAL_R701}")

    if not JUDGE.is_file():
        errors.append(f"judge missing {JUDGE}")
    else:
        got = sha256(JUDGE)
        need(got == EXPECTED_JUDGE_SHA, f"judge SHA drifted {got}")
    if not TEST_JUDGE.is_file():
        errors.append(f"test-judge missing {TEST_JUDGE}")
    else:
        got = sha256(TEST_JUDGE)
        need(got == EXPECTED_TEST_JUDGE_SHA, f"test-judge SHA drifted {got}")

    for name, expected in HISTORICAL.items():
        path = RUNTIME / name
        if not path.is_file():
            errors.append(f"historical runner missing {path}")
            continue
        got = sha256(path)
        need(got == expected, f"historical runner mutated {name} {got}")

    if errors:
        for e in errors:
            print(f"VERIFIER_FAIL {e}")
        return 2

    print("VERIFIER_PASS")
    print(f"runner={RUNNER}")
    print(f"runner_sha256={sha256(RUNNER)}")
    print(f"runner_size={RUNNER.stat().st_size}")
    print(f"judge_sha256={EXPECTED_JUDGE_SHA}")
    print(f"test_judge_sha256={EXPECTED_TEST_JUDGE_SHA}")
    print("legal_r7_01_absent=YES")
    print("historical_runners_unmodified=YES")
    return 0


if __name__ == "__main__":
    sys.exit(main())
