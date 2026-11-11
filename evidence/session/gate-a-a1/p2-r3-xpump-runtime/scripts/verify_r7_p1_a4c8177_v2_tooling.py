#!/usr/bin/env python3
"""Static tooling verifier for a4c8177 liveness-oracle v2.

Proves: no product source mutation, no APK rebuild requirement, frozen
runners/evidence/judge/timeout/ABI intact, no workstation Android PID
death authority in v2 classifiers/runners.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

WT = Path("/root/projects/GPU加速/src/f8-ahb-gatea-r7-p1-arm")
RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
DESIGN = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design")
EXPECT_SHA = "a4c8177f4b059fddd111717255e9d23cf0e15e1e"
JUDGE_SHA = "fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17"
V1_P1 = "4cbb1394c7b714bb4fb570dff352539ad179b8e5b39d174b8f325c9ec33e1b47"
V1_P2 = "6b0a9bdbcbf71a3cbe43f8da80d13d2b7a1c4f5331ada69feb8800969b90d55e"
ABB_P1 = "95900a2d22a37877c065b007feefe07895d8dcb37661e0d3b52b27e9d4ba7098"
ABB_P2 = "d36a4ccca7b7b148d77433b376c994ae435cec92e5dc4ed09604ab653901d8cc"
A4_CLASSIFY = "246832f2733d0c27bcdcf716615fdaf4431680b6320542893a69c19e8bcc84f6"
ABB_CLASSIFY = "a135c79c5599d00424dbbdf46c0e2edb703987f54653898dc226ee523c58f19b"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(msg: str) -> None:
    print(f"FAIL {msg}")
    raise SystemExit(2)


def main() -> int:
    head = subprocess.check_output(["git", "-C", str(WT), "rev-parse", "HEAD"], text=True).strip()
    if head != EXPECT_SHA:
        fail(f"worktree HEAD {head} != {EXPECT_SHA}")
    dirty = subprocess.check_output(["git", "-C", str(WT), "status", "--short"], text=True)
    if dirty.strip():
        fail(f"product worktree dirty:\n{dirty}")
    print("PASS product-source-unmodified", head)

    judge = DESIGN / "judge-r7.py"
    if sha256(judge) != JUDGE_SHA:
        fail("judge SHA drifted")
    print("PASS judge-unmodified")

    if sha256(RUNTIME / "run-r7-p1-a4c8177.sh") != V1_P1:
        fail("v1 p1 runner overwritten")
    if sha256(RUNTIME / "run-r7-p2-a4c8177.sh") != V1_P2:
        fail("v1 p2 runner overwritten")
    if sha256(RUNTIME / "run-r7-p1-abb27a65.sh") != ABB_P1:
        fail("abb27a65 p1 runner overwritten")
    if sha256(RUNTIME / "run-r7-p2-abb27a65.sh") != ABB_P2:
        fail("abb27a65 p2 runner overwritten")
    print("PASS historical-runners-unmodified")

    if sha256(RUNTIME / "runtime-a4c8177/r7-p1/r7-p1-classify.txt") != A4_CLASSIFY:
        fail("frozen a4c8177 r7-p1 classify mutated")
    if sha256(RUNTIME / "runtime-abb27a65/r7-p1/r7-p1-classify.txt") != ABB_CLASSIFY:
        fail("frozen abb27a65 r7-p1 classify mutated")
    # Pre-device: validity-02 / r7-p2 must be absent. After the authorized
    # one-shot, existence is expected; frozen first-attempt r7-p1 stays immutable.
    v02 = RUNTIME / "runtime-a4c8177/r7-p1-validity-02"
    if v02.exists():
        initial = v02 / "r7-p1-classify.runner-initial.txt"
        if not initial.is_file():
            fail("validity-02 exists without runner-initial classify snapshot")
        if "TARGET_COMPLETED" not in initial.read_text():
            fail("runner-initial snapshot lost the false-red TARGET_COMPLETED")
        print("PASS validity-02-present-frozen-first-classify")
    else:
        print("PASS validity-02-absent-pre-device")
    print("PASS frozen-evidence-unmodified")

    for name in ("run-r7-p1-a4c8177-v2.sh", "run-r7-p2-a4c8177-v2.sh"):
        text = (RUNTIME / name).read_text()
        if "timeout_ms=2000" not in text:
            fail(f"{name} timeout drifted")
        if "EXPECT_SHA=a4c8177f4b059fddd111717255e9d23cf0e15e1e" not in text:
            fail(f"{name} source SHA bind drifted")
        if "CANDIDATE_CI=35295094951" not in text:
            fail(f"{name} CI bind drifted")
        if 'this runner never installs' not in text:
            fail(f"{name} install policy missing")
        if 'liveness_oracle=phase-scoped-v2' not in text:
            fail(f"{name} missing phase-scoped oracle")
        # host /proc of Android Activity must not be death/life authority
        if '[ -d "/proc/$ACT_PID" ] && [ -d "/proc/$X3" ]' in text:
            fail(f"{name} still uses host /proc Activity+X3 conjunction as alive")
        if "ADB shell \"test -d /proc/$ACT_PID\"" not in text:
            fail(f"{name} missing device /proc probe")
        print(f"PASS {name}-binds")

    p1c = (RUNTIME / "scripts/classify_r7_p1_a4c8177_v2.py").read_text()
    if "activity_pre_cleanup != 1" in p1c and "PEER_DIED" in p1c:
        # v2 must not classify PEER_DIED from post-terminal pre-cleanup
        if "Activity not ALIVE at pre-cleanup" in p1c:
            fail("v2 classifier still PEER_DIED on pre-cleanup")
    if 'e["event"] == EV_SUCCESS and e["serial"] == target_serial' not in p1c:
        fail("v2 p1 success class is not target-serial scoped")
    if "open(\"/proc/" in p1c or "Path(\"/proc/" in p1c:
        fail("v2 p1 classifier opens /proc")
    p2c = (RUNTIME / "scripts/classify_r7_p2_a4c8177_v2.py").read_text()
    if 'e["event"] == EV_SUCCESS and e["serial"] == target_serial' not in p2c:
        fail("v2 p2 success class is not target-serial scoped")
    if "Path(\"/proc/" in p2c:
        fail("v2 p2 classifier opens /proc")
    print("PASS classifiers-no-host-proc")

    print("R7_P1_A4C8177_V2_TOOLING_STATIC=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
