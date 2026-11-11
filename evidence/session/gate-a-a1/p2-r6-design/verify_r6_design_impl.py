#!/usr/bin/env python3
"""Static proof that R6 design-complete source matches GATE-A-P2-R6-DESIGN-20260915."""
from __future__ import annotations

import re
import sys
from pathlib import Path


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
    dispatch = (xs / "dix/dispatch.c").read_text()
    present = (xs / "present/present_execute.c").read_text()
    vblank = (xs / "present/present_vblank.c").read_text()
    priv = (xs / "present/present_priv.h").read_text()
    patch = (repo / "lorie/src/main/cpp/patches/xserver.patch").read_text()

    need("LORIE_GATEA_EVENT_REQUEST_ARRIVED" in hdr, "hdr:request-arrived", failures)
    need("LORIE_GATEA_EVENT_CALLBACK_EXECUTED" in hdr, "hdr:callback", failures)
    need("LORIE_GATEA_EVENT_DIRECT_ADMIT_REJECT" in hdr, "hdr:admit-reject", failures)
    need("LORIE_GATEA_EVENT_PRESENT_EARLY_ACK" in hdr, "hdr:present-early-ack", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_EVENT_GENERATION_CLOSED == 28' in hdr,
         "hdr:event-28-frozen", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_EVENT_PRESENT_EARLY_ACK == 32' in hdr,
         "hdr:event-32-frozen-early-ack", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_EVENT_PRESENT_REQUEUE_FAILED == 33' in hdr,
         "hdr:event-33-requeue-failed", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_EVENT_PRESENT_ACK_AFTER_COMPLETED == 34' in hdr,
         "hdr:event-34-ack-after-completed", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_EVENT_MAX == 35' in hdr,
         "hdr:event-max-35", failures)
    need('LORIE_GATEA_STATIC_ASSERT(LORIE_GATEA_COUNTER_MAX == 28' in hdr,
         "hdr:counter-max-frozen", failures)
    need("void lorieGateATraceXRequest(" in hdr, "hdr:trace-request-proto", failures)
    need("TERMUX_X11_GATEA_TEST_FAULT" not in hdr, "hdr:must-not-add-r7-fault", failures)
    need("TERMUX_X11_GATEA_TEST_FAULT" not in init, "init:must-not-add-r7-fault", failures)

    need("lorieGateATraceXRequest(" in dispatch, "dispatch:request-hook", failures)
    need("client->majorOp == 62" in dispatch, "dispatch:copyarea-filter", failures)
    need("client->majorOp == 70" in dispatch, "dispatch:solid-filter", failures)
    need("client->majorOp == 73" in dispatch, "dispatch:getimage-filter", failures)
    need('"RENDER"' in dispatch and '"Present"' in dispatch, "dispatch:ext-filter", failures)
    req_pos = dispatch.find("lorieGateATraceXRequest")
    vec_pos = dispatch.find("requestVector[client->majorOp]")
    need(req_pos > 0 and vec_pos > req_pos, "dispatch:hook-before-procvector", failures)

    wait = section(init, "static LorieGateAResult gateAWaitTerminal(",
                   "\n__attribute__((noreturn)) static void gateAXFatal(")
    need("usleep(200)" in wait, "wait:still-usleep", failures)
    need("ReadRequestFromClient" not in wait, "wait:must-not-read-x-clients", failures)
    need("WaitForSomething" not in wait, "wait:must-not-waitforsomething", failures)

    need("TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL" in init,
         "init:oom-env", failures)
    wrap = section(init, "void lorieGpuCopyWaitForPresentOrFatal(",
                   "\nstatic struct {")
    need("lorieGpuCopyWait(serial, 2000)" in wrap, "wait-or-fatal:uses-bounded-wait", failures)
    need('gateAXFatal("x-present-copy-wait"' in wrap, "wait-or-fatal:fail-stop", failures)
    need("ReadRequestFromClient" not in wrap, "wait-or-fatal:must-not-read-x-clients", failures)
    need("WaitForSomething" not in wrap, "wait-or-fatal:must-not-waitforsomething", failures)
    need("usleep(200)" in init, "wait:still-usleep", failures)
    need("lorieGateAPresentRequeueShouldFail" in present,
         "present:one-shot-call", failures)
    need("lorieGateATracePresentRequeueFailed" in present,
         "present:requeue-failed-trace", failures)
    need("lorieGpuCopyWaitForPresentOrFatal" in vblank,
         "vblank:wait-or-fatal", failures)
    need("present_gpu_copy_retire_or_fatal(vblank)" in present,
         "present:retirement-helper", failures)
    need("lorieGateATracePresentAckAfterCompleted" in present,
         "present:ack-after-completed-trace", failures)
    need("lorieGateATracePresentEarlyAck" not in present,
         "present:must-not-early-ack-on-requeue-fail", failures)
    fail_blk = section(present, "lorieGateAPresentRequeueShouldFail",
                       "present_copy_region")
    rq = fail_blk.find("lorieGateATracePresentRequeueFailed")
    rt = fail_blk.find("present_gpu_copy_retire_or_fatal")
    tr = fail_blk.find("lorieGateATracePresentAckAfterCompleted")
    need(0 <= rq < rt < tr, "present:requeue-retirement-order", failures)
    need("lorieGateATraceXCallback(4u" in present or "lorieGateATraceXCallback(4," in present,
         "present:callback-xop-present", failures)
    top = section(present, "void\npresent_execute_copy(",
                  "lorieTryScheduleGpuCopy")
    need("lorieGateAPresentRequeueShouldFail" not in top,
         "present:one-shot-not-on-pre-copy-requeue", failures)
    schedule = present[present.find("lorieTryScheduleGpuCopy"):
                       present.find("present_copy_region(&window->drawable")]
    need("vblank->gpu_copy_pending = TRUE" in schedule,
         "present:pending-set-after-schedule", failures)
    need(schedule.find("vblank->gpu_copy_pending = TRUE")
         < schedule.find("queue_vblank"),
         "present:pending-before-requeue", failures)
    need("lorieGpuCopyAck(" not in present,
         "present:no-raw-ack-outside-helper", failures)
    pending_blk = section(
        present,
        "/* lorie: a GPU copy was already scheduled",
        "} else if (lorieTryScheduleGpuCopy",
    )
    pending_rq = pending_blk.find("lorieGateATracePresentRequeueFailed")
    pending_rt = pending_blk.find("present_gpu_copy_retire_or_fatal")
    pending_ack = pending_blk.find("lorieGateATracePresentAckAfterCompleted")
    need(0 <= pending_rq < pending_rt < pending_ack,
         "present:pending-natural-requeue-trace-retire-ack", failures)
    need("present_vblank_scrap" not in pending_blk,
         "present:renderer-loss-must-not-scrap", failures)

    helper = section(vblank, "present_gpu_copy_retire_or_fatal",
                     "\nvoid\npresent_vblank_scrap")
    need("lorieGpuCopyAck(" in helper,
         "vblank:helper-owns-raw-ack", failures)
    need("lorieGpuCopyAck(" not in vblank[vblank.find("\nvoid\npresent_vblank_scrap"):
                                            vblank.find("\nvoid\npresent_vblank_destroy")],
         "vblank:scrap-no-raw-ack", failures)
    destroy_start = vblank.find("present_vblank_destroy(present_vblank_ptr vblank)")
    destroy = vblank[destroy_start:] if destroy_start >= 0 else ""
    need("lorieGpuCopyAck(" not in destroy,
         "vblank:destroy-no-raw-ack", failures)
    ack = helper.find("lorieGpuCopyAck")
    done = helper.find("lorieGpuCopyIsDone")
    wait_for_done = helper.find("lorieGpuCopyWaitForPresentOrFatal")
    clear = helper.find("gpu_copy_pending = FALSE")
    need(0 <= done < wait_for_done < ack < clear,
         "vblank:completion-wait-before-ack-before-pending-clear", failures)
    for field in ("gpu_copy_dst_buffer = NULL", "gpu_copy_serial = 0"):
        need(ack < helper.find(field), f"vblank:{field}-after-ack", failures)
    scrap = section(vblank, "present_vblank_scrap(present_vblank_ptr vblank)",
                    "\nvoid\npresent_vblank_destroy")
    need(scrap.find("present_gpu_copy_retire_or_fatal")
         < scrap.find("present_pixmap_idle"),
         "vblank:scrap-retire-before-idle", failures)
    need(destroy.find("present_gpu_copy_retire_or_fatal")
         < destroy.find("dixDestroyPixmap"),
         "vblank:destroy-retire-before-pixmap-drop", failures)
    need("lorieGateATracePresentEarlyAck" not in vblank,
         "vblank:event-32-no-runtime-call", failures)

    need("gateATraceAdmitReject(LORIE_GATEA_REJECT_NOT_QUIESCENT" in init,
         "init:reject-not-quiescent", failures)
    need("lorieGateATraceXCallback(LORIE_GATEA_XOP_COMPOSITE" in init,
         "init:callback-composite", failures)
    need("lorieGateATraceXCallback(LORIE_GATEA_XOP_COPYAREA" in init,
         "init:callback-copy", failures)
    need("lorieGateATraceXCallback(LORIE_GATEA_XOP_SOLID" in init,
         "init:callback-solid", failures)
    need("LORIE_GATEA_XOP_PREPARE_ACCESS" in init, "init:callback-prepare-access", failures)

    need("lorieGpuCopyWaitForPresentOrFatal" in priv, "priv:wait-or-fatal-exported", failures)
    need("lorieGpuCopyWait(" not in priv, "priv:must-not-export-raw-wait", failures)
    need("void present_gpu_copy_retire_or_fatal" in priv,
         "priv:retirement-helper-proto", failures)
    need("lorieGateATracePresentRequeueFailed" in priv, "priv:requeue-failed-proto", failures)
    need("lorieGateATracePresentAckAfterCompleted" in priv, "priv:ack-after-proto", failures)
    need("lorieGateATraceXRequest" in patch, "patch:dispatch-tracked", failures)
    need("lorieGpuCopyWaitForPresentOrFatal" in patch, "patch:present-wait-tracked", failures)
    need("present_gpu_copy_retire_or_fatal" in patch,
         "patch:retirement-helper-tracked", failures)
    need(patch.count("+++ ./present/present_execute.c") == 1,
         "patch:present-execute-once", failures)
    need(patch.count("+++ ./present/present_vblank.c") == 1,
         "patch:present-vblank-once", failures)
    need(patch.count("+++ ./present/present_priv.h") == 1,
         "patch:present-priv-once", failures)
    execute_hunk_start = patch.find("+++ ./present/present_execute.c")
    execute_hunk_end = patch.find("+++ ./present/present_priv.h", execute_hunk_start + 1)
    execute_hunk = patch[execute_hunk_start:execute_hunk_end] if execute_hunk_end > 0 else ""
    need("lorieGpuCopyAck(" not in execute_hunk,
         "patch:execute-hunk-no-raw-ack", failures)
    need("present_gpu_copy_retire_or_fatal" in execute_hunk,
         "patch:execute-hunk-uses-helper", failures)
    need("+++ ./dix/dispatch.c" in patch, "patch:dispatch-file", failures)

    renderer = (lorie / "renderer.cpp").read_text()
    (lorie / "cmdentrypoint.cpp").read_text()
    need("gateAFencePublishGateA" in renderer, "renderer:present", failures)
    need("gateATraceLegacyCompleted" in renderer, "renderer:legacy-completed-helper", failures)
    need("gateATraceLegacyCompleted(state, out.lastSerial" in renderer,
         "renderer:standalone-legacy-completed", failures)
    need("gateATraceLegacyCompleted(state, gpuCopySerial" in renderer,
         "renderer:redraw-legacy-completed", failures)
    need("EGL_FOREVER" in renderer, "renderer:legacy-forever-unchanged", failures)
    return failures


def main() -> int:
    repo = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/root/projects/GPU加速/src/f8-ahb-gatea-r6")
    failures = verify(repo)
    if failures:
        print("R6_DESIGN_IMPL=FAIL")
        for item in failures:
            print(f"FAIL {item}")
        return 1
    print("R6_DESIGN_IMPL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
