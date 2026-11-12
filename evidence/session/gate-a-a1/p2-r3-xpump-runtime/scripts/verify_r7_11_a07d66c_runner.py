#!/usr/bin/env python3
"""Static verifier for dedicated run-r7-11-a07d66c.sh.

Host-only. Does not ADB, install, launch X3, or create runtime-a07d66c/r7-11.
Does not lift generic-runner REVIEW_REQUIRED.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

RUNTIME = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime")
RUNNER = RUNTIME / "run-r7-11-a07d66c.sh"
GENERIC = RUNTIME / "run-r7-one-cell-a07d66c.sh"
CLASSIFY = RUNTIME / "scripts" / "classify_r7_11_serial_wrap.py"
JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py")
TEST_JUDGE = Path("/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py")
LEGAL_R711 = RUNTIME / "runtime-a07d66c" / "r7-11"
HUP_WT = Path("/root/projects/GPU加速/src/f8-ahb-gatea-r7-hup-preserve")
SRC_INIT = HUP_WT / "lorie/src/main/cpp/lorie/InitOutput.c"
SRC_HDR = HUP_WT / "lorie/src/main/cpp/lorie/lorie.h"

EXPECTED_GENERIC_SHA = "36d66f17dc78673c931b91db67778ba1767e548eecb0a85c3acb0e2d3e758ded"
EXPECTED_JUDGE_SHA = "fba3c10f83fc3309151ca62d12dbe9dda4aabde2a040a131dcab116f0bd4cc17"
EXPECTED_TEST_JUDGE_SHA = "4d7194cdf788b122c98b5d747cc5089283c154960d9ca846ef3faa0a66e53aa5"
EXPECTED_FIXTURE_DIRECT_SHA = "b424a6340aac9140114ef70b4eb80cdbaa17cf8762b730963b865cd947cd8c13"
EXPECTED_HOLDER_SHA = "3417abbf0855c10bfd2328e87f33518c2f7f59c42529ba157a847d3019f5b5ca"
FIXTURE_DIRECT = Path(
    "/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_r3_single_direct"
)
HOLDER = Path(
    "/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/p_b3a_hold"
)
HISTORICAL = {
    "run-r7-one-cell-fdfb1ce.sh": "f4fb89d66698af15caba8e02fa046b26a7f86934fb476fc49e41e9305cc4f471",
    "run-r7-05-requal-a07d66c.sh": "46c24fc94228bbc622886b51f45f1fcbd1580cc6a6ebbc9b64e09fc472096473",
    "run-r7-09-a07d66c.sh": "d6ec76c17b42403e426170ab4bbe7fe6800eb92b7a37a966a530255d6873f60d",
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
    init = SRC_INIT.read_text(encoding="utf-8") if SRC_INIT.is_file() else ""
    hdr = SRC_HDR.read_text(encoding="utf-8") if SRC_HDR.is_file() else ""

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
    need("fixture_required=YES" in text, "R7-11 must require one direct publish attempt")
    need("holder_required=YES" in text, "R7-11 must require holder construction")
    need("no_serial0=YES" in text, "missing no_serial0 oracle marker")
    need("prior_publish_required=NO" in text, "must not invent prior PUBLISH requirement")
    need("seed_after_event35=YES" in text, "missing seed-after-event35 marker")
    need("production_serial_default_unmodified=YES" in text, "must not modify production serial default")
    need('"r7-11|serial-wrap|direct"' in text, "missing frozen R7-11 tuple")
    need("LIVE_STATUS=ENABLED" in text, "dedicated live_status must be ENABLED")
    need("CELL_ID not r7-11" in text or "is not this dedicated R7-11 runner" in text,
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
    need("died_during_8s_without_fixture=INVALID" in text, "8s death without fixture must be INVALID")
    need("injection_reachability=YES_GATEA_DIRECT_PUBLISH_RECT" in text,
         "missing source-proven injection reachability marker")
    need("no-serial0-oracle.txt" in text, "missing dedicated serial0 oracle file")
    need("serial-state-audit.txt" in text, "missing serial-state audit")
    need("do_not_invent_observed_UINT64_MAX=YES" in text, "must not invent observed UINT64_MAX")
    need("p_r3_single_direct" in text, "must invoke frozen direct fixture")
    need("TERMUX_X11_GATEA_TEST_FAULT=$FAULT" in text, "missing exact TEST_FAULT export")
    need("WAIT_S=30" not in text, "must not accept WAIT_S=30")

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
    need('"r7-09|' not in text, "dedicated runner must not enable r7-09")
    need('"r7-10|' not in text, "dedicated runner must not enable r7-10")
    need('"r7-p1|' not in text, "dedicated runner must not enable r7-p1")
    need('"r7-p2|' not in text, "dedicated runner must not enable r7-p2")

    need("LIVE_STATUS=REVIEW_REQUIRED" in generic, "generic REVIEW_REQUIRED must remain")
    need('"r7-11|serial-wrap|direct"' in generic, "generic must keep r7-11 mapping")
    need("DIED_DURING_8S" in generic, "generic DIED_DURING_8S path must remain unmodified")

    need("EXPECTED_WRAP" in classify, "classifier missing EXPECTED_WRAP")
    need("SERIAL0_LEAKED" in classify, "classifier missing SERIAL0_LEAKED")
    need("NO_EVENT35" in classify, "classifier missing NO_EVENT35")
    need("REPEATED_SEED" in classify, "classifier missing REPEATED_SEED")
    need("cannot fabricate ENV_EXACT" in classify, "classifier missing unread-env fail-closed")
    need('"fixture_required": "YES"' in classify, "classifier must keep fixture_required=YES")
    need("NOT_AVAILABLE" in classify, "classifier must not invent observed counter")
    need("publish_serial0" in classify, "classifier missing publish_serial0")
    need("Never upgrades missing evidence to PASS" in classify,
         "classifier must not upgrade missing evidence")

    need(LEGAL_R711.exists() is False, f"legal cell dir must remain absent: {LEGAL_R711}")

    need("LORIE_GATEA_TEST_SERIAL_WRAP" in init, "source missing SERIAL_WRAP enum consume site")
    need("gpuCopySerialCounter = UINT64_MAX" in init, "source missing post-event35 seed")
    need('gateAXFatal("x-serial-wrap"' in init, "source missing x-serial-wrap fatal")
    need("gateADirectPublishRect" in init, "source missing publish-rect host")
    consume_idx = init.find("lorieGateATestFaultConsume(pvfb->state, LORIE_GATEA_TEST_SERIAL_WRAP")
    seed_idx = init.find("pvfb->gpuCopySerialCounter = UINT64_MAX")
    wrap_idx = init.find('gateAXFatal("x-serial-wrap"')
    publish_idx = init.find("LORIE_GATEA_EVENT_PUBLISH")
    need(consume_idx != -1 and seed_idx != -1 and consume_idx < seed_idx,
         "source: consume/event35 must precede UINT64_MAX seed")
    need(seed_idx != -1 and wrap_idx != -1 and seed_idx < wrap_idx,
         "source: seed must precede wrap fatal")
    need(wrap_idx != -1 and publish_idx != -1 and wrap_idx < publish_idx,
         "source: wrap fatal must precede EVENT_PUBLISH")
    need("LORIE_GATEA_TEST_SERIAL_WRAP = 11" in hdr, "header enum 11")
    need("CAS consumed 0→1, then event 35, then the caller injects" in hdr
         or "CAS consumed 0->1, then event 35" in hdr
         or "then event 35, then the caller injects" in hdr,
         "header one-shot consume-then-35 contract")

    got_generic = sha256(GENERIC)
    need(got_generic == EXPECTED_GENERIC_SHA, f"generic runner SHA drifted {got_generic}")
    if not JUDGE.is_file():
        errors.append(f"judge missing {JUDGE}")
    else:
        got = sha256(JUDGE)
        need(got == EXPECTED_JUDGE_SHA, f"judge SHA drifted {got}")
        jtxt = JUDGE.read_text(encoding="utf-8")
        need('"serial-wrap": {"cell": 11, "side": 1, "what": "x-serial-wrap", "reason": 6, "need": (), "no_serial0": True}' in jtxt,
             "frozen judge serial-wrap spec drifted")
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
    print(f"holder_sha256={EXPECTED_HOLDER_SHA}")
    print("legal_r7_11_absent=YES")
    print("generic_review_required_unlifted=YES")
    print("historical_runners_unmodified=YES")
    print("product_worktree_clean=YES")
    print("source_seed_after_event35=YES")
    print("source_wrap_before_publish=YES")
    return 0


if __name__ == "__main__":
    sys.exit(main())
