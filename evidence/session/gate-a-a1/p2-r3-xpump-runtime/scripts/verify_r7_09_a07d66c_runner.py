#!/usr/bin/env python3
"""Static verifier for dedicated run-r7-09-a07d66c.sh.

Host-only. Does not ADB, install, launch X3, or create runtime-a07d66c/r7-09.
Does not lift generic-runner REVIEW_REQUIRED.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
RUNNER = RUNTIME / "run-r7-09-a07d66c.sh"
GENERIC = RUNTIME / "run-r7-one-cell-a07d66c.sh"
CLASSIFY = RUNTIME / "scripts" / "classify_r7_09_early_fail.py"
JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py")
TEST_JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py")
LEGAL_R709 = RUNTIME / "runtime-a07d66c" / "r7-09"
HUP_WT = Path("/root/projects/GPU加速/src/f8-ahb-gatea-r7-hup-preserve")

EXPECTED_GENERIC_SHA = "36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded"
EXPECTED_JUDGE_SHA = "fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17"
EXPECTED_TEST_JUDGE_SHA = "4d7194cdf788b122c98b5d747cc5089283c154960d9ca846ef3faa0a66e53aa5"
EXPECTED_FIXTURE_DIRECT_SHA = "b424a6340aac9140114ef70b4eb80cdbaa17cf8762b730963b865cd947cd8c13"
FIXTURE_DIRECT = Path(
    "/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_r3_single_direct"
)
HISTORICAL = {
    "run-r7-one-cell-fdfb1ce.sh": "f4fb89d66698af15caba8e02fa046b26a7f86934fb476fc49e41e9305cc4f471",
    "run-r7-05-requal-a07d66c.sh": "46c24fc94228bbc622886b51f45f1fcbd1580cc6a6ebbc9b64e09fc472096473",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def fail(msg: str) -> None:
    print(f"VERIFIER_FAIL {msg}")
    raise SystemExit(2)


def main() -> int:
    errors: list[str] = []

    def need(cond: bool, msg: str) -> None:
        if not cond:
            errors.append(msg)

    if not RUNNER.is_file():
        fail(f"dedicated runner missing {RUNNER}")
    if not GENERIC.is_file():
        fail(f"generic runner missing {GENERIC}")
    if not CLASSIFY.is_file():
        fail(f"classifier missing {CLASSIFY}")

    text = RUNNER.read_text(encoding="utf-8")
    generic = GENERIC.read_text(encoding="utf-8")
    classify = CLASSIFY.read_text(encoding="utf-8")

    need("EXPECT_VERSION=1.03.01-a07d66c-17.09.26" in text, "missing a07d66c EXPECT_VERSION")
    need("EXPECT_VERSION_CODE=15" in text, "missing EXPECT_VERSION_CODE=15")
    need("CANDIDATE_HEAD=a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82" in text, "missing candidate HEAD")
    need("runtime-a07d66c" in text, "missing runtime-a07d66c root policy")
    need("runtime-fdfb1ce*" in text, "missing refuse of runtime-fdfb1ce")
    need("runtime-7549e36*" in text, "missing refuse of runtime-7549e36")
    need("VALIDATE_ONLY" in text, "missing VALIDATE_ONLY")
    need("destination already exists" in text, "missing destination-exists refuse before write")
    need("FROZEN_WAIT_S=12" in text, "missing WAIT_S=12 freeze")
    need("WAIT_S must be" in text, "missing WAIT_S refuse")
    need(str(JUDGE) in text, "runner must point at frozen judge-r7.py")
    need(str(CLASSIFY) in text, "runner must invoke dedicated classifier")
    need("set -euo pipefail" in text, "missing set -euo pipefail")
    need("stable_policy=read-only" in text, "missing Stable read-only policy")
    need("termux-x11gpu com.waydefu.x11gpu :3" in text, "missing experimental X3 cmdline guard")
    need("am force-stop com.waydefu.x11gpu" in text, "missing experimental Activity cleanup")
    need("pkill" not in text, "pkill is forbidden")
    need("force-stop com.termux.x11" not in text, "must not force-stop Stable")
    need("kill com.termux.x11" not in text, "must not kill Stable by name")
    need("adb install" not in text.lower(), "runner must not adb install")
    need("for attempt" not in text, "retry loop forbidden")
    need("auto_next=0" in text, "missing auto_next=0")
    need("retry=0" in text, "missing retry=0")
    need("fixture_invocation_max=1" in text, "missing single fixture invocation")
    need("fixture_required=NO" in text, "R7-09 must not require fixture success")
    need("holder_required=NO" in text, "R7-09 must not require holder HOLD READY")
    need('"r7-09|wrong-generation-frame|direct"' in text, "missing frozen R7-09 tuple")
    need("LIVE_STATUS=ENABLED" in text, "dedicated live_status must be ENABLED")
    need("CELL_ID not r7-09" in text or "is not this dedicated R7-09 runner" in text,
         "must refuse other CELL_IDs")
    need("ENV_MISMATCH" in text and "got != need" in text, "missing exact env set equality")
    need("cannot fabricate ENV_EXACT" in text, "missing fail-closed unread-environ policy")
    need("immediate_on_pid_discovery" in text, "missing immediate environ capture")
    need("pre-cleanup-process.txt" in text, "missing pre-cleanup process observation")
    need("signal-audit.txt" in text, "missing PID-bound signal audit")
    need("not fabricate exit127" in text or "not fabricated as exit127" in text,
         "missing exit127 caveat")
    need("-P 5038" in text, "missing isolated ADB 5038")
    need("VALIDATE_ONLY_OK" in text, "VALIDATE_ONLY must print OK")
    need("died_during_8s_alone=NOT_INVALID" in text, "missing early-fail policy marker")
    need("expected-fatal-aware" in text, "missing expected-fatal-aware policy")
    need('echo "DIED_DURING_8S pid=$X3"' not in text,
         "dedicated runner must not reuse generic DIED_DURING_8S INVALID path")
    need("injection_reachability=YES_READY_SETUP_BEFORE_HOLDER_FIXTURE" in text,
         "missing source-proven injection reachability marker")
    need("NOT_REACHED" in text, "must allow fixture/holder NOT_REACHED")

    mkdir_idx = text.find('mkdir -p "$CELL"')
    exists_idx = text.find("destination already exists")
    validate_idx = text.find('if [ "$VALIDATE_ONLY" = 1 ]')
    source_idx = text.find("source \"$ROOT_HARNESS/harness-lib.sh\"")
    classify_idx = text.find('python3 "$CLASSIFY"')
    judge_idx = text.find('python3 "$JUDGE"')
    need(exists_idx != -1 and mkdir_idx != -1 and exists_idx < mkdir_idx,
         "destination exists check must precede mkdir")
    need(validate_idx != -1 and source_idx != -1 and validate_idx < source_idx,
         "VALIDATE_ONLY must return before sourcing harness/ADB")
    need(validate_idx < mkdir_idx, "VALIDATE_ONLY must return before mkdir")
    need(classify_idx != -1 and judge_idx != -1 and classify_idx < judge_idx,
         "classifier must run before frozen judge")

    need('"r7-08|' not in text, "dedicated runner must not enable r7-08")
    need('"r7-11|' not in text, "dedicated runner must not enable r7-11")
    need('"r7-10|' not in text, "dedicated runner must not enable r7-10")
    need('"r7-p1|' not in text, "dedicated runner must not enable r7-p1")
    need('"r7-p2|' not in text, "dedicated runner must not enable r7-p2")

    need("LIVE_STATUS=REVIEW_REQUIRED" in generic, "generic REVIEW_REQUIRED must remain")
    need('"r7-09|wrong-generation-frame|direct"' in generic, "generic must keep r7-09 mapping")
    need("DIED_DURING_8S" in generic, "generic DIED_DURING_8S path must remain unmodified")

    need("EXPECTED_EARLY_FAIL" in classify, "classifier missing EXPECTED_EARLY_FAIL")
    need("UNRELATED_EARLY_DEATH" in classify, "classifier missing UNRELATED_EARLY_DEATH")
    need("cannot fabricate ENV_EXACT" in classify, "classifier missing unread-env fail-closed")
    need("died_during_8s_invalid" in classify, "classifier missing died_during_8s_invalid field")
    need('"fixture_required": "NO"' in classify,
         "classifier must keep fixture_required=NO")
    need("arbitrary" not in classify.lower() or "Never upgrades missing evidence to PASS" in classify,
         "classifier must not upgrade missing evidence")

    need(LEGAL_R709.exists() is False, f"legal cell dir must remain absent: {LEGAL_R709}")

    got_generic = sha256(GENERIC)
    need(got_generic == EXPECTED_GENERIC_SHA, f"generic runner SHA drifted {got_generic}")
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
    if FIXTURE_DIRECT.is_file():
        got = sha256(FIXTURE_DIRECT)
        need(got == EXPECTED_FIXTURE_DIRECT_SHA, f"direct fixture SHA drifted {got}")
    else:
        errors.append(f"direct fixture missing {FIXTURE_DIRECT}")

    for name, expected in HISTORICAL.items():
        path = RUNTIME / name
        if not path.is_file():
            errors.append(f"historical runner missing {path}")
            continue
        got = sha256(path)
        need(got == expected, f"historical runner mutated {name} {got}")

    if HUP_WT.is_dir():
        st = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=HUP_WT,
            check=False,
            capture_output=True,
            text=True,
        )
        if st.returncode == 0 and st.stdout.strip():
            errors.append(f"product worktree dirty {HUP_WT}: {st.stdout.strip()[:200]}")

    if errors:
        for e in errors:
            print(f"VERIFIER_FAIL {e}")
        return 2

    print("VERIFIER_PASS")
    print(f"dedicated_runner={RUNNER}")
    print(f"dedicated_runner_sha256={sha256(RUNNER)}")
    print(f"dedicated_runner_size={RUNNER.stat().st_size}")
    print(f"classifier_sha256={sha256(CLASSIFY)}")
    print(f"generic_runner_sha256={EXPECTED_GENERIC_SHA}")
    print(f"generic_runner_size={GENERIC.stat().st_size}")
    print(f"judge_sha256={EXPECTED_JUDGE_SHA}")
    print(f"test_judge_sha256={EXPECTED_TEST_JUDGE_SHA}")
    print(f"fixture_direct_sha256={EXPECTED_FIXTURE_DIRECT_SHA}")
    print("legal_r7_09_absent=YES")
    print("generic_review_required_unlifted=YES")
    print("historical_runners_unmodified=YES")
    print("product_worktree_clean=YES")
    return 0


if __name__ == "__main__":
    sys.exit(main())
