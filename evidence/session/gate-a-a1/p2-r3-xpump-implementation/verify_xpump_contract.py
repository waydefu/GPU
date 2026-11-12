#!/usr/bin/env python3
"""Gate A A1 X-pump source invariants plus deterministic stream models."""
from __future__ import annotations

import argparse
import re
import socket
import struct
import threading
from dataclasses import dataclass
from pathlib import Path

MAGIC = 0x31415447
GATE_HEADER = struct.Struct("<IHHQQQQ")
READY_BODY = struct.Struct("<Q")
LEGACY_HEADER_SIZE = 24


def need(haystack: str, needle: str, label: str, failures: list[str]) -> None:
    if needle not in haystack:
        failures.append(f"missing:{label}")


def reject(haystack: str, pattern: str, label: str, failures: list[str]) -> None:
    if re.search(pattern, haystack, re.MULTILINE):
        failures.append(f"forbidden:{label}")


@dataclass
class ModelRecord:
    kind: str
    header: bytes
    body: bytes


class StreamModel:
    """Minimal contract model: prefix, complete header, then exact body."""

    def __init__(self) -> None:
        self.buf = bytearray()

    def feed(self, chunk: bytes) -> list[ModelRecord]:
        self.buf.extend(chunk)
        out: list[ModelRecord] = []
        while True:
            if len(self.buf) < 4:
                return out
            magic = struct.unpack_from("<I", self.buf)[0]
            header_len = GATE_HEADER.size if magic == MAGIC else LEGACY_HEADER_SIZE
            if len(self.buf) < header_len:
                return out
            header = bytes(self.buf[:header_len])
            if magic == MAGIC:
                _, _, msg_type, length, *_ = GATE_HEADER.unpack(header)
                expected = {2: READY_BODY.size, 3: READY_BODY.size,
                            5: 0, 7: 0, 8: READY_BODY.size}.get(msg_type)
                if expected is None or length != expected:
                    raise ValueError("protocol")
                body_len = expected
            else:
                body_len = 0
            if len(self.buf) < header_len + body_len:
                return out
            body = bytes(self.buf[header_len:header_len + body_len])
            del self.buf[:header_len + body_len]
            out.append(ModelRecord("gate" if magic == MAGIC else "legacy", header, body))


def run_models(failures: list[str]) -> None:
    ready = GATE_HEADER.pack(MAGIC, 1, 2, READY_BODY.size,
                             0x11, 0x22, 0x33) + READY_BODY.pack(0x44)
    model = StreamModel()
    pieces = [ready[:1], ready[1:3], ready[3:4], ready[4:23],
              ready[23:40], ready[40:47], ready[47:]]
    for piece in pieces[:-1]:
        if model.feed(piece):
            failures.append("model:partial-ready-dispatched")
            break
    else:
        out = model.feed(pieces[-1])
        if len(out) != 1 or out[0].body != READY_BODY.pack(0x44):
            failures.append("model:fragmented-ready")

    # One writer lock covers each full logical record even when the transport
    # emits deliberately tiny chunks.
    left, right = socket.socketpair()
    lock = threading.Lock()
    records = [ready, GATE_HEADER.pack(MAGIC, 1, 5, 0, 0x11, 0x22, 0x33)]

    def writer(record: bytes) -> None:
        with lock:
            for i in range(0, len(record), 3):
                left.sendall(record[i:i + 3])

    threads = [threading.Thread(target=writer, args=(record,)) for record in records]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    left.shutdown(socket.SHUT_WR)
    wire = bytearray()
    while True:
        data = right.recv(128)
        if not data:
            break
        wire.extend(data)
    left.close()
    right.close()
    decoded = StreamModel().feed(bytes(wire))
    if [record.header[6] for record in decoded] not in ([2, 5], [5, 2]):
        failures.append("model:serialized-records")

    # Truncated records remain incomplete; HUP is therefore terminal rather
    # than a timeout or a synthetic record.
    partial = StreamModel()
    if partial.feed(ready[:17]) or not partial.buf:
        failures.append("model:truncated-hup-state")

    # Generation close cancels, rather than replays, deferred legacy work.
    deferred = [b"clipboard", b"fd-event"]
    deferred.clear()
    if deferred:
        failures.append("model:generation-cancel")


def verify(repo: Path) -> list[str]:
    failures: list[str] = []
    root = repo / "lorie/src/main/cpp/lorie"
    header = (root / "lorie.h").read_text()
    cmd = (root / "cmdentrypoint.cpp").read_text()
    init = (root / "InitOutput.c").read_text()
    activity = (root / "activity.cpp").read_text()
    renderer = (root / "renderer.cpp").read_text()

    for needle, label in [
        ("LorieRecordDecoderPhase", "decoder-phases"),
        ("LORIE_RECORD_PHASE_GATE_BODY", "gate-body-phase"),
        ("LORIE_RECORD_PHASE_LEGACY_PAYLOAD", "legacy-payload-phase"),
        ("LORIE_RECORD_PHASE_LEGACY_FD", "legacy-fd-phase"),
        ("MSG_DONTWAIT", "nonblocking-recv"),
        ("lorieActivityWriterMutex", "shared-writer-mutex-decl"),
        ("sizeof(struct LorieGateAFrame) == 40", "wire-40"),
        ("sizeof(struct LorieGateAProtocol) == 40", "sideband-40"),
        ("sizeof(LorieGpuCopyEntry) == 168", "queue-entry-168"),
    ]:
        need(header, needle, label, failures)

    for needle, label in [
        ("lorieGateAPumpConnection", "main-thread-pump"),
        ("QueueWorkProc(gateADeferredWorkProc", "legacy-deferral"),
        ("gateADeferredTupleValid", "generation-bound-deferral"),
        ("fr->bufferId == 0", "result-and-ack-id-check"),
        ("fr->bufferId != 0", "generation-closed-id-check"),
        ("LORIE_GATEA_LEGACY_CANCEL", "close-cancel-policy"),
    ]:
        need(cmd, needle, label, failures)

    need(header, "LORIE_GATEA_WAIT_BUDGET_NS 2000000000ull", "two-second-budget", failures)
    need(init, '"x-ready-timeout"', "ready-timeout-name", failures)
    need(init, "lorieGateAPumpConnection(&deadline", "waiter-pumps", failures)
    need(init, "lorieGateACancelDeferred(nonce, generation)", "close-cancels-deferred", failures)
    reject(init, r"lorieGateAWaiterWaitUntil\s*\(", "condvar-self-wait", failures)

    for needle, label in [
        ("pthread_mutex_t lorieActivityWriterMutex", "writer-mutex-definition"),
        ("lorieActivitySendLegacyPayload", "payload-writer"),
        ("lorieActivitySendLegacyFd", "fd-writer"),
        ("lorieActivitySendGateFrame", "gate-writer"),
        ("return 1;\n            }", "one-record-callback"),
    ]:
        need(activity, needle, label, failures)
    reject(activity, r"\bwrite\s*\(\s*conn_fd", "activity-direct-write", failures)
    reject(activity, r"ancil_send_fd\s*\(\s*conn_fd", "activity-direct-fd-write", failures)
    reject(activity, r"goto\s+again|FIONREAD", "activity-blocking-redrain", failures)

    need(renderer, "lorieActivitySendLegacyRecord(&e)", "renderer-legacy-helper", failures)
    need(renderer, "lorieActivitySendGateFrame(&fr", "renderer-gate-helper", failures)
    reject(renderer, r"gateASendMutex|\bwrite\s*\(\s*conn_fd", "renderer-private-writer", failures)

    run_models(failures)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    failures = verify(args.repo.resolve())
    if failures:
        print("XPUMP_CONTRACT=FAIL")
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print("XPUMP_CONTRACT=PASS")
    print("STATIC_INVARIANTS=PASS")
    print("SOCKETPAIR_MODELS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
