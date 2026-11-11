#!/usr/bin/env python3
"""Gate A R5 backpressure regression: source ordering plus kernel capacity."""
from __future__ import annotations

import argparse
import fcntl
import socket
import struct
from pathlib import Path

FIONREAD = 0x541B
TIOCOUTQ = 0x5411
LEGACY_RECORD_BYTES = 24


def section(text: str, start: str, end: str) -> str:
    begin = text.find(start)
    if begin < 0:
        raise ValueError(f"missing section start: {start}")
    finish = text.find(end, begin)
    if finish < 0:
        raise ValueError(f"missing section end: {end}")
    return text[begin:finish]


def need(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def probe_tiny_write_capacity(failures: list[str]) -> dict[str, int]:
    sender, receiver = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    sender.setblocking(False)
    writes = 0
    try:
        while True:
            try:
                sender.sendall(b"x" * LEGACY_RECORD_BYTES)
                writes += 1
            except BlockingIOError:
                break
        inq = struct.unpack("I", fcntl.ioctl(receiver.fileno(), FIONREAD,
                                             struct.pack("I", 0)))[0]
        outq = struct.unpack("I", fcntl.ioctl(sender.fileno(), TIOCOUTQ,
                                              struct.pack("I", 0)))[0]
        sndbuf = sender.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    finally:
        sender.close()
        receiver.close()
    need(writes < 815, "kernel:tiny-writes-must-fill-before-r5-first-stall", failures)
    need(inq == writes * LEGACY_RECORD_BYTES, "kernel:fionread-payload", failures)
    need(outq >= sndbuf, "kernel:outq-reaches-accounting-limit", failures)
    return {"sndbuf": sndbuf, "writes": writes, "payload": inq, "outq": outq}


def verify(repo: Path) -> tuple[list[str], dict[str, int]]:
    failures: list[str] = []
    root = repo / "lorie/src/main/cpp/lorie"
    cmd = (root / "cmdentrypoint.cpp").read_text()
    renderer = (root / "renderer.cpp").read_text()

    callback = section(cmd, "static void handleLorieEventsProto(",
                       "\nvoid handleLorieEvents(")
    need("for (;;)" in callback, "callback:missing-drain-loop", failures)
    need("result == LORIE_RECORD_INCOMPLETE" in callback,
         "callback:incomplete-phase-not-continued", failures)
    need("result == LORIE_RECORD_WOULD_BLOCK" in callback,
         "callback:would-block-not-terminal", failures)
    need(callback.count("lorieRecordDecoderNext(") == 1,
         "callback:decoder-call-shape", failures)
    if "for (;;)" in callback and "lorieRecordDecoderNext(" in callback:
        need(callback.find("for (;;)") < callback.find("lorieRecordDecoderNext("),
             "callback:decoder-call-outside-loop", failures)

    gate_publish = section(renderer, "gateAFencePublishGateA(",
                           "\nvoid Renderer::bindTexture(")
    need("notifyGpuCopyDone()" not in gate_publish,
         "renderer:gate-helper-notifies-under-lock", failures)
    need("return true;" in gate_publish,
         "renderer:gate-helper-does-not-report-publication", failures)

    standalone = section(renderer, "void Renderer::applyPendingGpuCopies()",
                         "\nstatic float panToCursor(")
    need("gateANotify" in standalone, "renderer:standalone-missing-notify-state", failures)
    need(standalone.find("notifyGpuCopyDone()")
         < standalone.rfind("lorie_mutex_unlock(&state->lock"),
         "renderer:standalone-legacy-notify-placement-changed", failures)
    need(standalone.rfind("lorie_mutex_unlock(&state->lock")
         < standalone.rfind("notifyGpuCopyDone()"),
         "renderer:standalone-gatea-notify-before-unlock", failures)

    redraw = section(renderer, "void Renderer::redrawLocked(",
                     "\nbool Renderer::shouldWait(")
    need("gateANotify" in redraw, "renderer:redraw-missing-notify-state", failures)
    need(redraw.rfind("lorie_mutex_unlock(&state->lock")
         < redraw.rfind("notifyGpuCopyDone()"),
         "renderer:redraw-gatea-notify-before-unlock", failures)
    need("if (!gpuCopyOut.gateASeen)" in redraw,
         "renderer:redraw-legacy-placement-not-explicit", failures)

    capacity = probe_tiny_write_capacity(failures)
    return failures, capacity


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args()
    try:
        failures, capacity = verify(args.repo.resolve())
    except (OSError, ValueError) as exc:
        print(f"R5_BACKPRESSURE=ERROR {exc}")
        return 2
    print("KERNEL_CAPACITY=" + " ".join(f"{key}={value}" for key, value in capacity.items()))
    if failures:
        print("R5_BACKPRESSURE=FAIL")
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("R5_BACKPRESSURE=PASS")
    print("CALLBACK_DRAIN=PASS")
    print("GATEA_NOTIFY_AFTER_UNLOCK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
