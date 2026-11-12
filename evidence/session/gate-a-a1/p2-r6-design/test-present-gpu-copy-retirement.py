#!/usr/bin/env python3
"""RED/GREEN source checks for the R6 Present GPU-copy retirement contract."""
from __future__ import annotations

import re
import sys
from pathlib import Path


ACK_CALL = re.compile(r"\blorieGpuCopyAck\s*\(")


def function_body(source: str, signature: str, next_signature: str | None = None) -> str:
    start = source.find(signature)
    if start < 0:
        return ""
    end = source.find(next_signature, start) if next_signature else len(source)
    return source[start:end if end >= 0 else len(source)]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: test-present-gpu-copy-retirement.py WORKTREE")
        return 2

    repo = Path(sys.argv[1])
    present = repo / "lorie/src/main/cpp/xserver/present"
    execute = (present / "present_execute.c").read_text()
    vblank = (present / "present_vblank.c").read_text()
    priv = (present / "present_priv.h").read_text()
    scmd = (present / "present_scmd.c").read_text()
    failures: list[str] = []

    c_sources = sorted(present.glob("*.c"))
    callsites = [
        (path.name, match.start())
        for path in c_sources
        for match in ACK_CALL.finditer(path.read_text())
    ]
    helper_sig = "present_gpu_copy_retire_or_fatal(present_vblank_ptr vblank)"
    helper_start = vblank.find(helper_sig)
    helper_end = vblank.find("\n}\n", helper_start) + 3 if helper_start >= 0 else -1
    helper = vblank[helper_start:helper_end] if helper_start >= 0 and helper_end > 0 else ""

    if len(callsites) != 1:
        failures.append(f"raw-ack-count expected=1 actual={len(callsites)}")
    for filename, _ in callsites:
        if filename != "present_vblank.c" or ACK_CALL.search(helper) is None:
            failures.append(f"raw-ack-outside-retirement-helper file={filename}")

    if "void present_gpu_copy_retire_or_fatal" not in priv:
        failures.append("missing-retirement-helper-declaration")
    if helper_start < 0:
        failures.append("missing-retirement-helper-definition")
    else:
        done = helper.find("lorieGpuCopyIsDone")
        wait = helper.find("lorieGpuCopyWaitForPresentOrFatal")
        ack = helper.find("lorieGpuCopyAck")
        clear_pending = helper.find("gpu_copy_pending = FALSE")
        clear_dst = helper.find("gpu_copy_dst_buffer = NULL")
        clear_serial = helper.find("gpu_copy_serial = 0")
        if done < 0 or wait < 0 or ack < 0:
            failures.append("helper-missing-completion-proof-or-ack")
        elif not (done < wait < ack < clear_pending):
            failures.append("helper-order-must-prove-and-wait-before-ack-clear")
        if clear_dst >= 0 and clear_dst < ack:
            failures.append("helper-clears-destination-before-ack")
        if clear_serial >= 0 and clear_serial < ack:
            failures.append("helper-clears-serial-before-ack")
        if "lorieGpuCopyAck(vblank->pixmap, vblank->gpu_copy_dst_buffer)" not in helper:
            failures.append("helper-must-pass-nullable-destination-through")

    scrap = function_body(
        vblank,
        "present_vblank_scrap(present_vblank_ptr vblank)",
        "\nvoid\npresent_vblank_destroy",
    )
    destroy = function_body(vblank, "present_vblank_destroy(present_vblank_ptr vblank)")
    if "present_gpu_copy_retire_or_fatal(vblank)" not in scrap:
        failures.append("scrap-must-use-retirement-helper")
    elif "present_gpu_copy_retire_or_fatal(vblank)" in scrap and (
        scrap.find("present_gpu_copy_retire_or_fatal(vblank)")
        > scrap.find("present_pixmap_idle")
    ):
        failures.append("scrap-retires-after-idle")
    if "present_gpu_copy_retire_or_fatal(vblank)" not in destroy:
        failures.append("destroy-must-use-retirement-helper")
    elif "present_gpu_copy_retire_or_fatal(vblank)" in destroy and (
        destroy.find("present_gpu_copy_retire_or_fatal(vblank)")
        > destroy.find("dixDestroyPixmap")
    ):
        failures.append("destroy-drops-pixmap-before-retirement")

    if "present_gpu_copy_retire_or_fatal(vblank)" not in execute:
        failures.append("execute-must-use-retirement-helper")
    if "lorieGpuCopyAck(" in execute:
        failures.append("execute-must-have-no-raw-ack")
    schedule = execute[
        execute.find("lorieTryScheduleGpuCopy"):execute.find(
            "present_copy_region(&window->drawable"
        )
    ]
    if "gpu_copy_pending = TRUE" not in schedule:
        failures.append("schedule-must-publish-pending-state")
    else:
        pending_pos = schedule.find("gpu_copy_pending = TRUE")
        for marker in ("lorieGateAPixmapBufferId", "GetCurrentClient", "queue_vblank"):
            if schedule.find(marker) >= 0 and pending_pos > schedule.find(marker):
                failures.append(f"schedule-pending-state-after-{marker}")
    if "lorieGateATracePresentEarlyAck" in execute:
        failures.append("event-32-must-remain-unreachable")

    pending_block = execute[
        execute.find("/* lorie: a GPU copy was already scheduled"):
        execute.find("} else if (lorieTryScheduleGpuCopy")
    ]
    requeue_failed = pending_block.find("lorieGateATracePresentRequeueFailed")
    retire = pending_block.find("present_gpu_copy_retire_or_fatal")
    ack_after = pending_block.find("lorieGateATracePresentAckAfterCompleted")
    if not (0 <= requeue_failed < retire < ack_after):
        failures.append("pending-natural-requeue-must-trace-fail-retire-ack")
    if "present_vblank_scrap" in pending_block:
        failures.append("renderer-loss-must-not-scrap-before-fail-stop")

    pending_clears = [
        (path.name, match.start())
        for path in c_sources
        for match in re.finditer(r"\bgpu_copy_pending\s*=\s*FALSE\b", path.read_text())
    ]
    if len(pending_clears) != 1:
        failures.append(
            f"pending-clear-count expected=1 actual={len(pending_clears)}"
        )
    elif pending_clears[0][0] != "present_vblank.c" or (
        helper_start < 0
        or not (helper_start <= pending_clears[0][1] < helper_end)
    ):
        failures.append("pending-clear-outside-retirement-helper")

    recheck = function_body(scmd, "lorieRecheckGpuCopies(void)")
    if "present_re_execute(vblank)" not in recheck:
        failures.append("recheck-must-reexecute-pending-vblank")

    if failures:
        print("PRESENT_RETIREMENT=FAIL")
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("PRESENT_RETIREMENT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
