#!/usr/bin/env python3
"""Static verifier for dedicated run-r7-p1-8545b26.sh.

Host-only. Does not ADB, install, launch X3, or create runtime-8545b26/r7-p1.
Does not mutate frozen a07d66c runner, r7-10 runner, judge, timeout, or product source.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
RUNNER = RUNTIME / "run-r7-p1-8545b26.sh"
R710 = RUNTIME / "run-r7-10-8545b26.sh"
GENERIC = RUNTIME / "run-r7-one-cell-a07d66c.sh"
CLASSIFY = RUNTIME / "scripts" / "classify_r7_p1_present_hold.py"
JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py")
TEST_JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py")
LEGAL_R7P1 = RUNTIME / "runtime-8545b26" / "r7-p1"
LEGAL_R710 = RUNTIME / "runtime-8545b26" / "r7-10"
HIST_R710 = RUNTIME / "runtime-a07d66c" / "r7-10"
REPAIR_WT = Path("/root/projects/GPU加速/src/f8-ahb-gatea-r7-10-hup")
SRC_INIT = REPAIR_WT / "lorie/src/main/cpp/lorie/InitOutput.c"
SRC_HDR = REPAIR_WT / "lorie/src/main/cpp/lorie/lorie.h"
SRC_CLASS = REPAIR_WT / "lorie/src/main/cpp/lorie/lorie_gatea_wait_wake_class.h"
SRC_RENDER = REPAIR_WT / "lorie/src/main/cpp/lorie/renderer.cpp"
WAIT_TEST = REPAIR_WT / "scripts" / "test_gatea_wait_wake_class.c"

EXPECTED_GENERIC_SHA = "36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded"
EXPECTED_R710_RUNNER_SHA = "690a865d1bce410cabe10dd7d1da27be89a1f53302ac932f64cc50980afc54cd"
EXPECTED_JUDGE_SHA = "fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17"
EXPECTED_TEST_JUDGE_SHA = "4d7194cdf788b122c98b5d747cc5089283c154960d9ca846ef3faa0a66e53aa5"
EXPECTED_FIXTURE_PRESENT_SHA = "fec8f46d25614732b136dda03aa7ffaa309d373d4b285591d7322ba040bcba86"
EXPECTED_HOLDER_SHA = "3417abbf0855c10bfd2328e87f33518c2f7f59c42529ba157a847d3019f5b5ca"
EXPECTED_REPAIR_HEAD = "8545b26b308aa60b05685f48560285350e22ee8d"
EXPECTED_REPAIR_PARENT = "a07d66c48b7fe276b0b1fbfa1fa8eaf08ed68b82"
EXPECTED_WAIT_CLASS_SHA = "50b6a19aa35f9157f5e869590bb32efd61f70781e6d05e31c30b1049cc83b397"
EXPECTED_INITOUTPUT_SHA = "97a7a70489865ee89fcdd296c1ef6baf489308a9d74410f7d5d1830b5d0d3205"
EXPECTED_LORIE_H_SHA = "4863175fc4411c0a5a2df564532afba629628e293324df41eb20296987d4a031"
EXPECTED_RENDERER_SHA = "d7f0489d72d32e6f6a8ef71ff5592be6140986ff76094d6240cfce78d0eaaa63"
EXPECTED_HIST_JUDGE_SHA = "c816d6c14e5a0f048e5873caf837c383a0b10eae8e9f3a61698a8e500356eef5"
EXPECTED_R710_CELL_JUDGE_SHA = "bdd9cf8f412c023fc9988bc3dc6c070c38b256113b54372cb0685cb26d35eb77"
FIXTURE_PRESENT = Path(
    "/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_r6_d2_present"
)
HOLDER = Path(
    "/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_b3a_hold"
)
PATCH_SRC = Path("/root/projects/GPU加速/patches/p_r6_d2_present.c")
HISTORICAL_RUNNERS = {
    "run-r7-one-cell-a07d66c.sh": EXPECTED_GENERIC_SHA,
    "run-r7-10-8545b26.sh": EXPECTED_R710_RUNNER_SHA,
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
    hdr = SRC_HDR.read_text(encoding="utf-8") if SRC_HDR.is_file() else ""
    init = SRC_INIT.read_text(encoding="utf-8") if SRC_INIT.is_file() else ""
    rend = SRC_RENDER.read_text(encoding="utf-8") if SRC_RENDER.is_file() else ""
    wait = SRC_CLASS.read_text(encoding="utf-8") if SRC_CLASS.is_file() else ""

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
    need("ALLOWED_CELL=r7-p1" in text, "missing ALLOWED_CELL=r7-p1")
    need("ALLOWED_FAULT=present-hold-complete" in text, "missing ALLOWED_FAULT")
    need("ALLOWED_FIXTURE=present" in text, "missing ALLOWED_FIXTURE=present")
    need("CELL_ID must be $ALLOWED_CELL only" in text or "CELL_ID must be r7-p1 only" in text,
         "must refuse other CELL_IDs")
    need("VALIDATE_ONLY" in text, "missing VALIDATE_ONLY")
    need("destination already exists" in text, "missing destination-exists refuse before write")
    need("FROZEN_WAIT_S=12" in text, "missing WAIT_S=12 freeze")
    need("WAIT_S must be" in text, "missing WAIT_S refuse")
    need("WAIT_S=30" not in text, "must not accept WAIT_S=30")
    need(str(JUDGE) in text, "runner must point at frozen judge-r7.py")
    need("classify_r7_p1_present_hold.py" in text, "runner must invoke dedicated classifier")
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
    need("holder_required=YES" in text, "P1 requires holder for surfaceAvailable")
    need("LIVE_STATUS=ENABLED" in text, "dedicated live_status must be ENABLED")
    need("ENV_MISMATCH" in text and "got != need" in text, "missing exact env set equality")
    need("pre-cleanup-process.txt" in text, "missing pre-cleanup process observation")
    need("signal-audit.txt" in text, "missing PID-bound signal audit")
    need("renderer-liveness.txt" in text, "missing renderer liveness sampling")
    need("-P 5038" in text, "missing isolated ADB 5038")
    need("VALIDATE_ONLY_OK" in text, "VALIDATE_ONLY must print OK")
    need("p_r6_d2_present" in text, "must invoke frozen present fixture")
    need('" inflight' in text or " inflight >>" in text, "must invoke inflight mode")
    need("TERMUX_X11_GATEA_TEST_FAULT=$FAULT" in text, "missing exact TEST_FAULT export")
    need("timeout_ms=2000" in text, "must keep 2000 ms timeout oracle visible")
    need("reason4_globally_forbidden=NO" in text, "must not globally forbid timeout/4")
    need("r7-p1-oracle.txt" in text, "missing R7-P1 independent oracle file")
    need("x-present-copy-wait" in text, "missing Present timeout identity")
    need("install_policy=this runner never installs" in text, "runner must not install")
    need("historical_root_write=0" in text, "must not write historical evidence")
    need("judge_mutation=0" in text, "must not mutate judge")
    need("timeout_mutation=0" in text, "must not mutate timeout")
    need("hup_precedence=" in text, "missing wait-wake precedence plan")
    need("SUCCESS wins" in text, "missing SUCCESS-wins precedence")
    need("fault12_trigger=0" in text, "VALIDATE_ONLY must not trigger fault12")
    need("r7_p2=0" in text, "must not run R7-P2")
    need('"r7-01|' not in text, "dedicated runner must not enable r7-01")
    need('"r7-10|' not in text, "dedicated runner must not enable r7-10")
    need('"r7-p2|' not in text, "dedicated runner must not enable r7-p2")
    need("1.03.01-a07d66c-17.09.26" not in text, "must not bind a07d66c versionName")
    need("_exit(127)" not in text, "must not synthesize renderer death")
    need("timeout_ms=2000" in text, "must not replace product timeout with runner sleep")

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

    need('"r7-p1|present-hold-complete|present"' in generic,
         "generic historical r7-p1 mapping must remain")
    need("LIVE_STATUS=REVIEW_REQUIRED" in generic, "generic r7-p1 must remain REVIEW_REQUIRED")
    need("EXPECT_VERSION=1.03.01-a07d66c-17.09.26" in generic,
         "generic must remain a07d66c-bound")
    need("runtime-a07d66c" in generic, "generic root bind must remain a07d66c")

    need("EXPECTED_PRESENT_TIMEOUT" in classify, "classifier missing EXPECTED_PRESENT_TIMEOUT")
    need("PEER_DIED" in classify, "classifier missing PEER_DIED")
    need("WRONG_REASON4_IDENTITY" in classify, "classifier missing WRONG_REASON4_IDENTITY")
    need("TARGET_COMPLETED" in classify, "classifier missing TARGET_COMPLETED")
    need("NO_PRESENT_CALLBACK" in classify, "classifier missing NO_PRESENT_CALLBACK")
    need("NO_EVENT35" in classify, "classifier missing NO_EVENT35")
    need("REPEATED_FAULT" in classify, "classifier missing REPEATED_FAULT")
    need("WRONG_TERMINAL" in classify, "classifier missing WRONG_TERMINAL")
    need("TRACE_INCOMPLETE" in classify, "classifier missing TRACE_INCOMPLETE")
    need("WAIT_ARCHITECTURE_HUP" in classify, "classifier missing wait-architecture HUP")
    need("WAIT_ARCHITECTURE_TIMEOUT" in classify, "classifier missing wait-architecture TIMEOUT")
    need('EXPECTED_WHAT = "x-present-copy-wait"' in classify, "classifier missing expected what")
    need("reason4_globally_forbidden" in classify, "classifier must expose reason4 global policy")
    need("PRODUCT_TIMEOUT_MS = 2000" in classify, "classifier must freeze 2000 ms")
    need("adb" not in classify.lower() or "Does not ADB" in classify,
         "classifier must remain host-only")

    need(LEGAL_R7P1.exists() is False, f"legal P1 cell dir must remain absent: {LEGAL_R7P1}")
    need(LEGAL_R710.is_dir(), f"frozen 8545b26 r7-10 cell missing {LEGAL_R710}")
    need(HIST_R710.is_dir(), f"historical FAIL cell missing {HIST_R710}")
    hist_judge = HIST_R710 / "judge.txt"
    r710_judge = LEGAL_R710 / "judge.txt"
    need(hist_judge.is_file(), "historical judge.txt missing")
    need(r710_judge.is_file(), "frozen 8545b26 r7-10 judge.txt missing")
    if hist_judge.is_file():
        got = sha256(hist_judge)
        need(got == EXPECTED_HIST_JUDGE_SHA, f"historical r7-10 judge.txt mutated {got}")
        jtxt = hist_judge.read_text(errors="replace")
        need("R7_FAIL halt_mismatch what=x-direct-not-success reason=4" in jtxt,
             "historical FAIL text drifted")
    if r710_judge.is_file():
        got = sha256(r710_judge)
        need(got == EXPECTED_R710_CELL_JUDGE_SHA, f"8545b26 r7-10 judge.txt mutated {got}")
        jtxt = r710_judge.read_text(errors="replace")
        need("R7_PASS renderer-exit-after-consume" in jtxt, "8545b26 r7-10 PASS text drifted")

    got_generic = sha256(GENERIC)
    need(got_generic == EXPECTED_GENERIC_SHA, f"generic runner SHA drifted {got_generic}")
    got_r710 = sha256(R710)
    need(got_r710 == EXPECTED_R710_RUNNER_SHA, f"r7-10 runner SHA drifted {got_r710}")
    if not JUDGE.is_file():
        errors.append(f"judge missing {JUDGE}")
    else:
        got = sha256(JUDGE)
        need(got == EXPECTED_JUDGE_SHA, f"judge SHA drifted {got}")
        jtxt = JUDGE.read_text(encoding="utf-8")
        need(
            '"present-hold-complete": {"cell": 12, "side": 2, "what": "x-present-copy-wait", "reason": 4, "need": ("present_cb",), "present": True}'
            in jtxt,
            "frozen judge present-hold-complete spec drifted",
        )
    if not TEST_JUDGE.is_file():
        errors.append(f"test-judge missing {TEST_JUDGE}")
    else:
        got = sha256(TEST_JUDGE)
        need(got == EXPECTED_TEST_JUDGE_SHA, f"test-judge SHA drifted {got}")
    if FIXTURE_PRESENT.is_file():
        got = sha256(FIXTURE_PRESENT)
        need(got == EXPECTED_FIXTURE_PRESENT_SHA, f"present fixture SHA drifted {got}")
        need(FIXTURE_PRESENT.stat().st_size == 72536, "present fixture size drifted")
    else:
        errors.append(f"present fixture missing {FIXTURE_PRESENT}")
    if HOLDER.is_file():
        got = sha256(HOLDER)
        need(got == EXPECTED_HOLDER_SHA, f"holder SHA drifted {got}")
    else:
        errors.append(f"holder missing {HOLDER}")
    need(PATCH_SRC.is_file(), f"present fixture source missing {PATCH_SRC}")

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
        need("LORIE_GATEA_WAIT_WAKE_X_HUP" in wait, "wait-wake missing HUP class")
        need("LORIE_GATEA_WAIT_WAKE_TIMEOUT" in wait, "wait-wake missing TIMEOUT class")
        need("if (timeoutExpired)" in wait, "wait-wake must keep live-peer timeout")
        need("if (!connectionAlive)" in wait, "wait-wake must keep peer-dead HUP")
    else:
        errors.append(f"wait-class header missing {SRC_CLASS}")
    if SRC_INIT.is_file():
        got = sha256(SRC_INIT)
        need(got == EXPECTED_INITOUTPUT_SHA, f"InitOutput.c mutated {got}")
        need('lorieGpuCopyWait(serial, 2000)' in init, "Present wait must stay 2000 ms")
        need('gateAXFatal("x-present-copy-wait", LORIE_GATEA_FAIL_TIMEOUT, serial)' in init,
             "missing x-present-copy-wait/4 emit")
        need("present-hold-complete" in init, "missing present-hold-complete cell name")
    else:
        errors.append(f"InitOutput.c missing {SRC_INIT}")
    if SRC_HDR.is_file():
        got = sha256(SRC_HDR)
        need(got == EXPECTED_LORIE_H_SHA, f"lorie.h mutated {got}")
        need("LORIE_GATEA_TEST_PRESENT_HOLD_COMPLETE = 12" in hdr, "fault enum 12 drifted")
        need("sizeof(struct LorieGateAProtocol) == 40" in hdr, "protocol size drifted")
        need("offsetof(struct LorieGateAProtocol, generationFatal) == 4" in hdr,
             "generationFatal offset drifted")
        need("p->protocolVersion = 1u" in hdr, "protocol version drifted")
        need("LORIE_GATEA_EVENT_MAX == 37" in hdr, "EVENT_MAX drifted")
        need("LORIE_GATEA_COUNTER_MAX == 28" in hdr, "COUNTER_MAX drifted")
        need("LORIE_RENDERER_FRAME_WAIT_NS 8000000L" in hdr, "CASE_LOOP 8 ms drifted")
        need("LORIE_GATEA_FAIL_TIMEOUT = 4" in hdr, "FAIL_TIMEOUT drifted")
    else:
        errors.append(f"lorie.h missing {SRC_HDR}")
    if SRC_RENDER.is_file():
        got = sha256(SRC_RENDER)
        need(got == EXPECTED_RENDERER_SHA, f"renderer.cpp mutated {got}")
        need("LORIE_GATEA_TEST_PRESENT_HOLD_COMPLETE" in rend, "missing fault12 consume")
        need("lorieGateAPublishCompleted" in rend, "missing completedSerial publish")
        hold_idx = rend.find("LORIE_GATEA_TEST_PRESENT_HOLD_COMPLETE")
        exit_idx = rend.find("LORIE_GATEA_TEST_PRESENT_RENDERER_EXIT")
        need(hold_idx != -1 and "_exit(127)" not in rend[hold_idx:hold_idx + 500],
             "fault12 must not _exit")
        need(exit_idx != -1 and "_exit(127)" in rend[exit_idx:exit_idx + 800],
             "P2 exit hook must remain a separate cell")
    else:
        errors.append(f"renderer.cpp missing {SRC_RENDER}")

    if REPAIR_WT.is_dir():
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPAIR_WT, check=False, capture_output=True, text=True,
        )
        parent = subprocess.run(
            ["git", "rev-parse", "HEAD^"],
            cwd=REPAIR_WT, check=False, capture_output=True, text=True,
        )
        st = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPAIR_WT, check=False, capture_output=True, text=True,
        )
        need(head.returncode == 0 and head.stdout.strip() == EXPECTED_REPAIR_HEAD,
             f"repair HEAD drifted {head.stdout.strip()}")
        need(parent.returncode == 0 and parent.stdout.strip() == EXPECTED_REPAIR_PARENT,
             f"repair parent drifted {parent.stdout.strip()}")
        if st.returncode == 0 and st.stdout.strip():
            errors.append(f"repair worktree dirty {REPAIR_WT}: {st.stdout.strip()[:200]}")

    if WAIT_TEST.is_file():
        out_bin = Path("/tmp/test_gatea_wait_wake_class_r7p1")
        cc = subprocess.run(
            ["cc", "-O0", "-o", str(out_bin), str(WAIT_TEST)],
            check=False, capture_output=True, text=True,
        )
        need(cc.returncode == 0, f"wait-wake compile failed {cc.stderr[-200:]}")
        if cc.returncode == 0:
            run = subprocess.run([str(out_bin)], check=False, capture_output=True, text=True)
            need(run.returncode == 0 and "GATEA_WAIT_WAKE_CLASS=PASS" in run.stdout,
                 f"wait-wake host test failed {run.stdout} {run.stderr}")

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
    print(f"r7_10_runner_sha256={EXPECTED_R710_RUNNER_SHA}")
    print(f"judge_sha256={EXPECTED_JUDGE_SHA}")
    print(f"test_judge_sha256={EXPECTED_TEST_JUDGE_SHA}")
    print(f"fixture_present_sha256={EXPECTED_FIXTURE_PRESENT_SHA}")
    print(f"holder_sha256={EXPECTED_HOLDER_SHA}")
    print(f"repair_head={EXPECTED_REPAIR_HEAD}")
    print("legal_r7_p1_8545b26_absent=YES")
    print("frozen_r7_10_8545b26=YES")
    print("historical_r7_10_frozen=YES")
    print("historical_runners_unmodified=YES")
    print("repair_worktree_clean=YES")
    print("reason4_globally_forbidden=NO")
    print("timeout_ms=2000")
    return 0


if __name__ == "__main__":
    sys.exit(main())
