#!/usr/bin/env python3
"""Static verifier for dedicated run-r7-10-8545b26.sh.

Host-only. Does not ADB, install, launch X3, or create runtime-8545b26/r7-10.
Does not mutate frozen a07d66c runner, judge, timeout, or repair product source.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
RUNNER = RUNTIME / "run-r7-10-8545b26.sh"
GENERIC = RUNTIME / "run-r7-one-cell-a07d66c.sh"
CLASSIFY = RUNTIME / "scripts" / "classify_r7_10_hup_containment.py"
JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py")
TEST_JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py")
LEGAL_R710 = RUNTIME / "runtime-8545b26" / "r7-10"
HIST_R710 = RUNTIME / "runtime-a07d66c" / "r7-10"
REPAIR_WT = Path("/root/projects/GPU加速/src/f8-ahb-gatea-r7-10-hup")
SRC_INIT = REPAIR_WT / "lorie/src/main/cpp/lorie/InitOutput.c"
SRC_HDR = REPAIR_WT / "lorie/src/main/cpp/lorie/lorie.h"
SRC_CLASS = REPAIR_WT / "lorie/src/main/cpp/lorie/lorie_gatea_wait_wake_class.h"

EXPECTED_GENERIC_SHA = "36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded"
EXPECTED_JUDGE_SHA = "fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17"
EXPECTED_TEST_JUDGE_SHA = "4d7194cdf788b122c98b5d747cc5089283c154960d9ca846ef3faa0a66e53aa5"
EXPECTED_FIXTURE_DIRECT_SHA = "b424a6340aac9140114ef70b4eb80cdbaa17cf8762b730963b865cd947cd8c13"
EXPECTED_HOLDER_SHA = "3417abbf0855c10bfd2328e87f33518c2f7f59c42529ba157a847d3019f5b5ca"
EXPECTED_REPAIR_HEAD = "8545b26b308aa60b05685f48560285350e22ee8d"
EXPECTED_REPAIR_PARENT = "a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82"
EXPECTED_WAIT_CLASS_SHA = "50b6a19aa35f9157f5e869590bb32efd61f70781e6d05e31c30b1049cc83b397"
EXPECTED_INITOUTPUT_SHA = "97a7a70489865ee89fcdd296c1ef6baf489308a9d74410f7d5d1830b5d0d3205"
EXPECTED_LORIE_H_SHA = "4863175fc4411c0a5a2df564532afba629628e293324df41eb20296987d4a031"
EXPECTED_HIST_JUDGE_SHA = "c816d6c14e5a0f048e5873caf837c383a0b10eae8e9f3a61698a8e500356eef5"
EXPECTED_HIST_VERDICT_SHA = "5be8aab8ce0ee6ee9a46548d53ad8e2e50e0303befca965df5a3661284b1ca01"
FIXTURE_DIRECT = Path(
    "/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_r3_single_direct"
)
HOLDER = Path(
    "/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_b3a_hold"
)
HISTORICAL_RUNNERS = {
    "run-r7-one-cell-a07d66c.sh": EXPECTED_GENERIC_SHA,
    "run-r7-one-cell-fdfb1ce.sh": "f4fb89d66698af15caba8e02fa046b26a7f86934fb476fc49e41e9305cc4f471",
    "run-r7-05-requal-a07d66c.sh": "46c24fc94228bbc622886b51f45f1fcbd1580cc6a6ebbc9b64e09fc472096473",
    "run-r7-09-a07d66c.sh": "d6ec76c17b42403e426170ab4bbe7fe6800eb92b7a37a966a530255d6873f60d",
    "run-r7-11-a07d66c.sh": "74385947cbcef8dbeeb1deea9722b424828d9bf3780a4dd0279290df5310c453",
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

    need("EXPECT_SHA=8545b26b308aa60b05685f48560285350e22ee8d" in text, "missing EXPECT_SHA hard bind")
    need("CANDIDATE_HEAD=8545b26b308aa60b05685f48560285350e22ee8d" in text, "missing candidate HEAD")
    need("EXPECT_VERSION=1.03.01-8545b26-17.09.26" in text, "missing 8545b26 EXPECT_VERSION")
    need("EXPECT_VERSION_CODE=15" in text, "missing EXPECT_VERSION_CODE=15")
    need("EXPECT_PACKAGE=com.waydefu.x11gpu" in text, "missing EXPECT_PACKAGE")
    need("EXPECT_BUILD_ID=50a4078b940d982e1ca1484cac6dd2bf2abe7b0a" in text, "missing EXPECT_BUILD_ID")
    need("ALLOWED_ROOT_BASE=runtime-8545b26" in text, "missing runtime-8545b26 root bind")
    need("runtime-a07d66c*" in text, "must refuse runtime-a07d66c")
    need("runtime-fdfb1ce*" in text, "must refuse runtime-fdfb1ce")
    need("runtime-7549e36*" in text, "must refuse runtime-7549e36")
    need("ALLOWED_CELL=r7-10" in text, "missing ALLOWED_CELL=r7-10")
    need("ALLOWED_FAULT=renderer-exit-after-consume" in text, "missing ALLOWED_FAULT")
    need("ALLOWED_FIXTURE=direct" in text, "missing ALLOWED_FIXTURE=direct")
    need("CELL_ID must be $ALLOWED_CELL only" in text or "CELL_ID must be r7-10 only" in text,
         "must refuse other CELL_IDs")
    need("VALIDATE_ONLY" in text, "missing VALIDATE_ONLY")
    need("destination already exists" in text, "missing destination-exists refuse before write")
    need("FROZEN_WAIT_S=12" in text, "missing WAIT_S=12 freeze")
    need("WAIT_S must be" in text, "missing WAIT_S refuse")
    need("WAIT_S=30" not in text, "must not accept WAIT_S=30")
    need(str(JUDGE) in text, "runner must point at frozen judge-r7.py")
    need("classify_r7_10_hup_containment.py" in text, "runner must invoke dedicated classifier")
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
    need("holder_invocation_max=1" in text, "missing single holder invocation")
    need("LIVE_STATUS=ENABLED" in text, "dedicated live_status must be ENABLED")
    need("ENV_MISMATCH" in text and "got != need" in text, "missing exact env set equality")
    need("pre-cleanup-process.txt" in text, "missing pre-cleanup process observation")
    need("signal-audit.txt" in text, "missing PID-bound signal audit")
    need("not fabricate exit127" in text or "not fabricated as exit127" in text,
         "missing exit127 caveat")
    need("-P 5038" in text, "missing isolated ADB 5038")
    need("VALIDATE_ONLY_OK" in text, "VALIDATE_ONLY must print OK")
    need("p_r3_single_direct" in text, "must invoke frozen direct fixture")
    need("TERMUX_X11_GATEA_TEST_FAULT=$FAULT" in text, "missing exact TEST_FAULT export")
    need("timeout_ms=2000" in text, "must keep 2000 ms timeout oracle visible")
    need("reason4_globally_forbidden=NO" in text, "must not globally forbid timeout/4")
    need("r7-10-oracle.txt" in text, "missing R7-10 independent oracle file")
    need("x-hup" in text and "x-direct-not-success" in text, "missing repaired vs historical halt names")
    need("install_policy=this runner never installs" in text, "runner must not install")
    need("historical_root_write=0" in text, "must not write historical evidence")
    need("judge_mutation=0" in text, "must not mutate judge")
    need("timeout_mutation=0" in text, "must not mutate timeout")
    need("hup_precedence=" in text, "missing HUP precedence plan")
    need("SUCCESS wins" in text, "missing SUCCESS-wins precedence")
    need('"r7-01|' not in text, "dedicated runner must not enable r7-01")
    need('"r7-02|' not in text, "dedicated runner must not enable r7-02")
    need('"r7-03|' not in text, "dedicated runner must not enable r7-03")
    need('"r7-05|' not in text, "dedicated runner must not enable r7-05")
    need('"r7-06|' not in text, "dedicated runner must not enable r7-06")
    need('"r7-07|' not in text, "dedicated runner must not enable r7-07")
    need('"r7-08|' not in text, "dedicated runner must not enable r7-08")
    need('"r7-09|' not in text, "dedicated runner must not enable r7-09")
    need('"r7-11|' not in text, "dedicated runner must not enable r7-11")
    need('"r7-p1|' not in text, "dedicated runner must not enable r7-p1")
    need('"r7-p2|' not in text, "dedicated runner must not enable r7-p2")
    need("1.03.01-a07d66c-17.09.26" not in text, "must not bind a07d66c versionName")

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
    need(validate_idx != -1 and mkdir_idx != -1 and validate_idx < mkdir_idx,
         "VALIDATE_ONLY must return before mkdir")
    need(validate_idx != -1 and exists_idx != -1 and validate_idx < exists_idx,
         "VALIDATE_ONLY must return before live destination check")
    need(classify_idx != -1 and judge_idx != -1 and classify_idx < judge_idx,
         "classifier must run before frozen judge")

    need('"r7-10|renderer-exit-after-consume|direct"' in generic,
         "generic historical r7-10 mapping must remain")
    need("EXPECT_VERSION=1.03.01-a07d66c-17.09.26" in generic,
         "generic must remain a07d66c-bound")
    need("runtime-a07d66c" in generic, "generic root bind must remain a07d66c")

    need("EXPECTED_HUP" in classify, "classifier missing EXPECTED_HUP")
    need("HISTORICAL_REASON4" in classify, "classifier missing HISTORICAL_REASON4")
    need("GENUINE_TIMEOUT_NOT_R7_10" in classify, "classifier missing genuine-timeout class")
    need("HUP_PRECEDENCE_PRESERVE" in classify, "classifier missing HUP preserve")
    need("HUP_PRECEDENCE_OVERWRITE" in classify, "classifier missing HUP overwrite")
    need('reason4_globally_forbidden' in classify, "classifier must expose reason4 global policy")
    need("BUG_WHAT = \"x-direct-not-success\"" in classify, "classifier missing historical bug what")
    need("EXPECTED_WHAT = \"x-hup\"" in classify, "classifier missing expected what")
    need("adb" not in classify.lower() or "Does not ADB" in classify,
         "classifier must remain host-only")

    need(LEGAL_R710.exists() is False, f"legal cell dir must remain absent: {LEGAL_R710}")
    need(HIST_R710.is_dir(), f"historical FAIL cell missing {HIST_R710}")
    hist_judge = HIST_R710 / "judge.txt"
    hist_verdict = HIST_R710 / "primary-verdict.txt"
    need(hist_judge.is_file(), "historical judge.txt missing")
    need(hist_verdict.is_file(), "historical primary-verdict.txt missing")
    if hist_judge.is_file():
        got = sha256(hist_judge)
        need(got == EXPECTED_HIST_JUDGE_SHA, f"historical r7-10 judge.txt mutated {got}")
        jtxt = hist_judge.read_text(errors="replace")
        need("R7_FAIL halt_mismatch what=x-direct-not-success reason=4" in jtxt,
             "historical FAIL text drifted")
    if hist_verdict.is_file():
        got = sha256(hist_verdict)
        need(got == EXPECTED_HIST_VERDICT_SHA, f"historical r7-10 primary-verdict mutated {got}")

    got_generic = sha256(GENERIC)
    need(got_generic == EXPECTED_GENERIC_SHA, f"generic runner SHA drifted {got_generic}")
    if not JUDGE.is_file():
        errors.append(f"judge missing {JUDGE}")
    else:
        got = sha256(JUDGE)
        need(got == EXPECTED_JUDGE_SHA, f"judge SHA drifted {got}")
        jtxt = JUDGE.read_text(encoding="utf-8")
        need(
            '"renderer-exit-after-consume": {"cell": 10, "side": 2, "what": "x-hup", "reason": 6, "need": ("publish", "consume"), "hup": True}'
            in jtxt,
            "frozen judge renderer-exit-after-consume spec drifted",
        )
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
    if HOLDER.is_file():
        got = sha256(HOLDER)
        need(got == EXPECTED_HOLDER_SHA, f"holder SHA drifted {got}")
    else:
        errors.append(f"holder missing {HOLDER}")

    for name, expected in HISTORICAL_RUNNERS.items():
        path = RUNTIME / name
        if not path.is_file():
            errors.append(f"historical runner missing {path}")
            continue
        got = sha256(path)
        need(got == expected, f"historical runner mutated {name} {got}")

    if SRC_CLASS.is_file():
        got = sha256(SRC_CLASS)
        need(got == EXPECTED_WAIT_CLASS_SHA, f"wait-class header mutated {got}")
    else:
        errors.append(f"wait-class header missing {SRC_CLASS}")
    if SRC_INIT.is_file():
        got = sha256(SRC_INIT)
        need(got == EXPECTED_INITOUTPUT_SHA, f"InitOutput.c mutated {got}")
    else:
        errors.append(f"InitOutput.c missing {SRC_INIT}")
    if SRC_HDR.is_file():
        got = sha256(SRC_HDR)
        need(got == EXPECTED_LORIE_H_SHA, f"lorie.h mutated {got}")
    else:
        errors.append(f"lorie.h missing {SRC_HDR}")

    if REPAIR_WT.is_dir():
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPAIR_WT,
            check=False,
            capture_output=True,
            text=True,
        )
        parent = subprocess.run(
            ["git", "rev-parse", "HEAD^"],
            cwd=REPAIR_WT,
            check=False,
            capture_output=True,
            text=True,
        )
        st = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPAIR_WT,
            check=False,
            capture_output=True,
            text=True,
        )
        need(head.returncode == 0 and head.stdout.strip() == EXPECTED_REPAIR_HEAD,
             f"repair HEAD drifted {head.stdout.strip()}")
        need(parent.returncode == 0 and parent.stdout.strip() == EXPECTED_REPAIR_PARENT,
             f"repair parent drifted {parent.stdout.strip()}")
        if st.returncode == 0 and st.stdout.strip():
            errors.append(f"repair worktree dirty {REPAIR_WT}: {st.stdout.strip()[:200]}")

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
    print(f"holder_sha256={EXPECTED_HOLDER_SHA}")
    print(f"repair_head={EXPECTED_REPAIR_HEAD}")
    print("legal_r7_10_8545b26_absent=YES")
    print("historical_r7_10_frozen=YES")
    print("historical_runners_unmodified=YES")
    print("repair_worktree_clean=YES")
    print("reason4_globally_forbidden=NO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
