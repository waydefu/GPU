#!/usr/bin/env python3
"""Static proof that Artifact B / R7 support matches GATE-A-P2-R7-R10-SUPPORT-DESIGN-20260916."""
from __future__ import annotations

import sys
from pathlib import Path


CELLS = (
    "src-ready-miss",
    "dst-ready-miss",
    "tuple-mismatch",
    "fbo-incomplete",
    "post-draw-gl",
    "fence-create-fail",
    "fence-timeout",
    "renderer-fatal-pre-fence",
    "wrong-generation-frame",
    "renderer-exit-after-consume",
    "serial-wrap",
    "present-hold-complete",
    "present-renderer-exit",
    "destroy-while-gpu-owned",
    "close-while-lease",
    "stale-ready-replay",
)


def need(cond: bool, label: str, failures: list[str]) -> None:
    if not cond:
        failures.append(label)


def section(text: str, start: str, end: str) -> str:
    begin = text.find(start)
    if begin < 0:
        raise ValueError(f"missing section start: {start}")
    finish = text.find(end, begin + 1)
    if finish < 0:
        return text[begin:]
    return text[begin:finish]


def verify(repo: Path) -> list[str]:
    failures: list[str] = []
    lorie = repo / "lorie/src/main/cpp/lorie"
    xs = repo / "lorie/src/main/cpp/xserver"
    hdr = (lorie / "lorie.h").read_text()
    init = (lorie / "InitOutput.c").read_text()
    renderer = (lorie / "renderer.cpp").read_text()
    cmd = (lorie / "cmdentrypoint.cpp").read_text()
    activity = (lorie / "activity.cpp").read_text()
    patch = (repo / "lorie/src/main/cpp/patches/xserver.patch").read_text()
    vblank = (xs / "present/present_vblank.c").read_text()
    priv = (xs / "present/present_priv.h").read_text()

    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_EVENT_PRESENT_EARLY_ACK == 32' in hdr,
         "hdr:event-32-frozen", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_EVENT_TEST_FAULT_FIRED == 35' in hdr,
         "hdr:event-35", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_EVENT_PRESENT_RETIRE == 36' in hdr,
         "hdr:event-36", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_EVENT_MAX == 37' in hdr,
         "hdr:event-max-37", failures)
    need("LORIE_GATEA_EVENT_MAX == 35" not in hdr, "hdr:must-not-keep-max-35", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_COUNTER_MAX == 28' in hdr,
         "hdr:counter-max-frozen", failures)
    need("0x47374146" in hdr, "hdr:test-fault-magic", failures)
    need('sizeof(struct LorieGateATestFault) == 40' in hdr, "hdr:test-fault-size", failures)
    need("offsetof(struct LorieGateATestFault, targetGeneration) == 24" in hdr,
         "hdr:test-fault-gen-off", failures)
    need("TERMUX_X11_GATEA_TEST_FAULT" in hdr, "hdr:test-fault-env-name", failures)
    need("lorieGateATestFaultConsume" in hdr, "hdr:consume-helper", failures)
    need("lorieGateADumpSummary" in hdr, "hdr:dump-decl", failures)
    need("lorieGateATracePresentRetire" in hdr, "hdr:retire-trace-decl", failures)

    consume = section(hdr, "static inline __always_inline int lorieGateATestFaultConsume(",
                      "\n#ifdef __cplusplus")
    cas = consume.find("__atomic_compare_exchange_n(&st->gateATestFault.consumed")
    fired = consume.find("LORIE_GATEA_EVENT_TEST_FAULT_FIRED")
    need(0 <= cas < fired, "hdr:cas-before-event-35", failures)
    armed = section(hdr, "static inline __always_inline int lorieGateATestFaultArmed(",
                    "static inline __always_inline int lorieGateATestFaultConsume(")
    need("__atomic_load_n(&st->gateATestFault.armed" in armed, "hdr:armed-load-first", failures)
    need("fopen" not in armed and "getenv" not in armed, "hdr:armed-no-io", failures)

    need("TERMUX_X11_GATEA_TEST_FAULT" in init, "init:fault-env", failures)
    need("TERMUX_X11_GATEA_TEST_ARM" in init, "init:arm-env", failures)
    need("x-test-fault-env" in init, "init:env-refuse", failures)
    need("lorieGateADumpSummary" in init, "init:dump-def", failures)
    need("GATEA_SUMMARY where=" in init, "init:summary-format", failures)
    need("/data/data/com.termux/files/usr/tmp/gatea-summary.txt" in hdr,
         "hdr:summary-path", failures)
    need("lorieGateATestFaultPublishFromEnv(lorieScreen.state)" in init,
         "init:publish-from-env", failures)
    need("UINT64_MAX" in init and "LORIE_GATEA_TEST_SERIAL_WRAP" in init,
         "init:serial-wrap-seed", failures)
    need("x-destroy-in-lease" in init and "LORIE_GATEA_TEST_DESTROY_WHILE_GPU_OWNED" in init,
         "init:destroy-hook", failures)
    need("LORIE_GATEA_TEST_CLOSE_WHILE_LEASE" in init, "init:close-hook", failures)
    mmap_init = init.find("mmap(NULL, sizeof(*lorieScreen.state)")
    mmap_act = activity.find("mmap(NULL, sizeof(*state)")
    need(mmap_init > 0 and mmap_act > 0, "mmap:sizeof-state-both-sides", failures)

    need("getenv" not in renderer or "TERMUX_X11_GATEA_TEST_FAULT" not in renderer,
         "renderer:must-not-getenv-fault", failures)
    need("TERMUX_X11_GATEA_TEST_FAULT" not in renderer, "renderer:no-fault-env-token", failures)
    need("TERMUX_X11_GATEA_TEST_FAULT" not in activity, "activity:no-fault-env-token", failures)
    need("lorieGateATestFaultConsume" in renderer, "renderer:consume-sites", failures)
    need("r-test-fatal-pre-fence" in renderer, "renderer:r7-08-what", failures)
    need("_exit(127)" in renderer, "renderer:exit-cells", failures)
    need("LORIE_GATEA_TEST_PRESENT_HOLD_COMPLETE" in renderer, "renderer:p1-hold", failures)
    need("LORIE_GATEA_TEST_STALE_READY_REPLAY" in renderer, "renderer:r7-14-hook", failures)

    need("LORIE_GATEA_TEST_WRONG_GENERATION_FRAME" in cmd, "cmd:r7-09", failures)
    need("lorieGateADumpSummary" in cmd, "cmd:dump-on-input-fatal", failures)

    for name in CELLS:
        need(f'"{name}"' in init, f"init:cell-name-{name}", failures)

    helper = section(vblank, "present_gpu_copy_retire_or_fatal",
                     "\nvoid\npresent_vblank_scrap")
    tr = helper.find("lorieGateATracePresentRetire")
    wait = helper.find("lorieGpuCopyWaitForPresentOrFatal")
    ack = helper.find("lorieGpuCopyAck")
    need(0 <= tr < wait < ack, "vblank:event-36-before-wait-before-ack", failures)
    need("lorieGateACopyBufferId" in helper, "vblank:copy-buffer-id", failures)
    need("lorieGateATracePresentEarlyAck" not in vblank, "vblank:event-32-unused", failures)
    present_exec = (xs / "present/present_execute.c").read_text()
    need("lorieGateATracePresentEarlyAck" not in present_exec, "present:event-32-unused", failures)
    need("extern uint64_t lorieGateACopyBufferId(void *buf)" in priv,
         "priv:copy-buffer-id", failures)
    need("lorieGateATracePresentRetire" in patch, "patch:event-36", failures)
    need("lorieGateACopyBufferId" in patch, "patch:copy-buffer-id", failures)

    return failures


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_r7_support.py WORKTREE")
        return 2
    repo = Path(sys.argv[1])
    failures = verify(repo)
    if failures:
        print("R7_SUPPORT=FAIL")
        for item in failures:
            print(f"FAIL {item}")
        return 1
    print("R7_SUPPORT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
