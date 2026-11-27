#!/usr/bin/env python3
"""Stage 7.5 tiered cooperative resource governance for Native Hybrid 2.0.

One module holds every governed quantity so the 2/4/6/8-way modes differ only
by a row in PROFILES:

- relay leases (independent relay clients) and daemon sessions: ``Profile.mode``
- group-wide tool executions (daemon native workers plus relay local workers),
  managed separately from client count: ``Profile.exec_slots``
- per relay/session queued native calls: ``Profile.session_queue``
- byte and parse limits shared by every governed process: ``GOVERNED``

All quotas are cooperative. They bind the daemon, relays and fallbacks that
receive the same ``F8_HYBRID2_BUDGET_DIR``; they are not kernel limits and do
not bind an independently launched program, a different directory, or the
working set of an external child such as git.
"""

from __future__ import annotations

import fcntl
import json
import os
import stat
import sys
from dataclasses import asdict, dataclass

BUDGET_DIR_ENV = "F8_HYBRID2_BUDGET_DIR"
MAX_MODE = 8
MiB = 1024 * 1024


@dataclass(frozen=True)
class Profile:
    mode: int
    exec_slots: int
    session_queue: int


# exec_slots come from the capacity arithmetic in budget_report(); see the Stage 7.5 report.
PROFILES: dict[int, Profile] = {
    2: Profile(mode=2, exec_slots=2, session_queue=4),
    4: Profile(mode=4, exec_slots=3, session_queue=4),
    6: Profile(mode=6, exec_slots=2, session_queue=4),
    8: Profile(mode=8, exec_slots=1, session_queue=4),
}


@dataclass(frozen=True)
class Limits:
    request_frame: int  # max request frame, excluding LF
    input_buffer: int  # incomplete stdin frame that ends the stream
    parse_budget: int | None  # max parse_cost() of one frame
    response_frame: int  # max UDS response frame at the relay
    out_watermark: int  # relay stops reading upstream / daemon stops reading requests
    to_uds_watermark: int  # selective relay stops reading stdin
    replay_bytes: int  # early-EOF replay copy
    daemon_out_cap: int | None  # daemon worker waits for output space instead of closing
    raw_buffer: int  # raw passthrough per direction
    tool_parse_budget: int | None  # python_json_summary parse estimate
    native_pending: int  # selective relay native requests awaiting replies


LEGACY = Limits(
    request_frame=4 * MiB, input_buffer=8 * MiB, parse_budget=None, response_frame=16 * MiB,
    out_watermark=8 * MiB, to_uds_watermark=4 * MiB, replay_bytes=4 * MiB, daemon_out_cap=None,
    raw_buffer=8 * MiB, tool_parse_budget=None, native_pending=16,
)

# The largest daemon response is a tool result whose 1 MiB text at most doubles
# when JSON-escaped again (the inner JSON has no raw control characters), or an
# error echoing a request string, which is shorter than request_frame.
_RESPONSE = 2 * MiB + 64 * 1024
GOVERNED = Limits(
    request_frame=512 * 1024, input_buffer=512 * 1024, parse_budget=2 * MiB, response_frame=_RESPONSE,
    out_watermark=256 * 1024, to_uds_watermark=256 * 1024, replay_bytes=64 * 1024, daemon_out_cap=_RESPONSE,
    raw_buffer=1 * MiB, tool_parse_budget=24 * MiB, native_pending=4,
)

_STRUCTURAL = (b"{", b"[", b",", b":")


def parse_cost_parts(data: bytes) -> tuple[int, bool]:
    """Structural character count and ASCII flag; additive over byte chunks."""
    return sum(data.count(c) for c in _STRUCTURAL), data.isascii()


def parse_cost_total(size: int, tokens: int, ascii_only: bool) -> int:
    return (3 if ascii_only else 9) * size + 128 * tokens + 4096


def parse_cost(data: bytes) -> int:
    """Upper estimate of the Python heap json.loads(data.decode()) needs, plus data.

    Calibrated with tracemalloc on CPython 3.12 and 3.14 against container-,
    number- and string-dense documents (worst observed ratio 1.00 for strings).
    Characters inside strings are counted as structure, which only overestimates.
    """
    return parse_cost_total(len(data), *parse_cost_parts(data))


def _open_private_dir(directory: str) -> int:
    dfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    st = os.fstat(dfd)
    if st.st_uid != os.getuid() or st.st_mode & 0o077:
        os.close(dfd)
        raise ValueError("budget directory must be owned by the user and private")
    return dfd


def _open_private_file(name: str, dfd: int, flags: int = os.O_RDWR | os.O_CREAT) -> int:
    fd = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=dfd)
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077 or st.st_nlink != 1:
        os.close(fd)
        raise ValueError(f"invalid budget file {name}")
    return fd


def _try_lock(name: str, dfd: int) -> int | None:
    fd = _open_private_file(name, dfd)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    except BaseException:
        os.close(fd)
        raise
    return fd


def _read_profile(dfd: int) -> Profile:
    try:
        fd = _open_private_file("profile", dfd, os.O_RDONLY)
    except FileNotFoundError as exc:
        raise ValueError("budget profile missing; run f8_hybrid2_budget.py init") from exc
    try:
        raw = os.read(fd, 64)
    finally:
        os.close(fd)
    try:
        mode = int(raw.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("invalid budget profile") from exc
    if mode not in PROFILES:
        raise ValueError(f"unsupported budget mode {mode}")
    return PROFILES[mode]


def _all_lock_names() -> list[str]:
    return ["daemon", *(f"slot-{i}" for i in range(MAX_MODE)), *(f"exec-{i}" for i in range(MAX_MODE))]


def init_budget_dir(directory: str, mode: int) -> Profile:
    """Create or re-profile a budget directory while no governed process holds it."""
    if mode not in PROFILES:
        raise ValueError(f"unsupported budget mode {mode}")
    os.makedirs(directory, mode=0o700, exist_ok=True)
    dfd = _open_private_dir(directory)
    held: list[int] = []
    try:
        for name in _all_lock_names():
            fd = _try_lock(name, dfd)
            if fd is None:
                raise ValueError("budget directory in use")
            held.append(fd)
        tmp = ".profile.tmp"
        try:
            os.unlink(tmp, dir_fd=dfd)
        except FileNotFoundError:
            pass
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dfd)
        try:
            os.write(fd, f"{mode}\n".encode("ascii"))
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, "profile", src_dir_fd=dfd, dst_dir_fd=dfd)
        return PROFILES[mode]
    finally:
        for fd in held:
            os.close(fd)
        os.close(dfd)


def acquire_lease(directory: str, *, daemon: bool = False) -> tuple[int, Profile]:
    """Hold the daemon lease or one of ``mode`` relay slots for the process lifetime.

    The profile is re-read after locking, so a lease never exceeds the mode that
    init_budget_dir() wrote while holding every lock.
    """
    dfd = _open_private_dir(directory)
    try:
        profile = _read_profile(dfd)
        names = ["daemon"] if daemon else [f"slot-{i}" for i in range(profile.mode)]
        for name in names:
            fd = _try_lock(name, dfd)
            if fd is None:
                continue
            try:
                current = _read_profile(dfd)
            except BaseException:
                os.close(fd)
                raise
            if current != profile:
                os.close(fd)
                raise ValueError("budget profile changed during admission")
            return fd, profile
        raise ValueError("budget exhausted")
    finally:
        os.close(dfd)


class ExecPool:
    """Group-wide execution tokens shared by daemon workers and relay local workers."""

    def __init__(self, directory: str, slots: int) -> None:
        self.directory = directory
        self.slots = slots

    def try_acquire(self) -> int | None:
        dfd = _open_private_dir(self.directory)
        try:
            for i in range(self.slots):
                fd = _try_lock(f"exec-{i}", dfd)
                if fd is not None:
                    return fd
            return None
        finally:
            os.close(dfd)

    @staticmethod
    def release(fd: int | None) -> None:
        if fd is not None and fd >= 0:
            os.close(fd)


@dataclass(frozen=True)
class Governance:
    lease_fd: int
    profile: Profile
    pool: ExecPool
    limits: Limits = GOVERNED


def governance_from_env(*, daemon: bool = False) -> Governance | None:
    """Return None outside budget mode; raise OSError/ValueError on refused admission."""
    directory = os.environ.get(BUDGET_DIR_ENV)
    if not directory:
        return None
    fd, profile = acquire_lease(directory, daemon=daemon)
    return Governance(lease_fd=fd, profile=profile, pool=ExecPool(directory, profile.exec_slots))


# Capacity arithmetic --------------------------------------------------------

def relay_buffer_bound(limits: Limits = GOVERNED) -> int:
    """Byte ceiling of one selective relay's enforced buffers plus one frame parse."""
    chunk = 65536
    return (
        limits.input_buffer + chunk  # stdin_buf
        + limits.replay_bytes
        + limits.to_uds_watermark + limits.request_frame + chunk  # to_uds
        + limits.response_frame + chunk  # incomplete uds_buf
        + limits.out_watermark + limits.response_frame + chunk  # to_stdout
        + limits.response_frame  # one finished local response
        + (limits.parse_budget or 0)  # one frame parse at a time
    )


def daemon_session_bound(limits: Limits = GOVERNED) -> int:
    """Byte ceiling of one daemon session: input, one parse, retained requests, output."""
    chunk = 65536
    out = max(limits.daemon_out_cap or 0, limits.out_watermark + limits.request_frame + chunk)
    # Admitted requests share one parse_budget per session (ClientSession._active_cost).
    return limits.request_frame + chunk + 2 * (limits.parse_budget or 0) + out


def budget_report(mode: int, *, daemon_idle_kib: int, relay_idle_kib: int,
                  exec_envelope_kib: int, child_envelope_kib: int,
                  child_threads: int = 1, child_fds: int = 8) -> dict[str, object]:
    """Theoretical aggregate for one mode from enforced limits plus measured envelopes.

    Measured inputs (idle PSS, per-execution Python working set, external child
    PSS/threads/FDs) are assumptions taken from device runs; the byte limits are
    enforced by code. The sum is an accounting bound, not a kernel limit.
    """
    p = PROFILES[mode]
    lim = GOVERNED
    kib = lambda b: (b + 1023) // 1024  # noqa: E731
    memory = {
        "idle_daemon": daemon_idle_kib,
        "idle_relays": mode * relay_idle_kib,
        "relay_buffers": mode * kib(relay_buffer_bound(lim)),
        "daemon_sessions": mode * kib(daemon_session_bound(lim)),
        "executions": p.exec_slots * exec_envelope_kib,
        "external_children": p.exec_slots * child_envelope_kib,
    }
    # daemon: main + sessions + workers; relay: main + local worker + fallback output thread.
    threads = 1 + mode + p.exec_slots + 3 * mode + p.exec_slots * child_threads
    # daemon: stdio 3, pidfile, listener, lease, audit append; per session socket + wake pipe.
    # relay: stdio 3, socket, wake pipe 2, selector, lease, one transient file.
    # per execution: token, wake pipe 2, pidfd, stdout/stderr pipes, stdin temp, one file; plus child FDs.
    fds = (7 + 3 * mode) + 9 * mode + p.exec_slots * (8 + child_fds)
    return {
        "mode": mode,
        "profile": asdict(p),
        "memory_kib": memory,
        "memory_total_kib": sum(memory.values()),
        "threads_total": threads,
        "fds_total": fds,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Stage 7.5 cooperative budget directory and capacity table")
    sub = ap.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init", help="write a mode while no governed process is running")
    init.add_argument("directory")
    init.add_argument("--mode", type=int, required=True, choices=sorted(PROFILES))
    table = sub.add_parser("table", help="print theoretical capacity for every mode")
    for name in ("daemon-idle-kib", "relay-idle-kib", "exec-envelope-kib", "child-envelope-kib"):
        table.add_argument(f"--{name}", type=int, required=True)
    table.add_argument("--child-threads", type=int, default=1)
    table.add_argument("--child-fds", type=int, default=8)
    args = ap.parse_args(argv)
    if args.cmd == "init":
        try:
            profile = init_budget_dir(args.directory, args.mode)
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3
        print(json.dumps(asdict(profile)))
        return 0
    rows = [budget_report(m, daemon_idle_kib=args.daemon_idle_kib, relay_idle_kib=args.relay_idle_kib,
                          exec_envelope_kib=args.exec_envelope_kib, child_envelope_kib=args.child_envelope_kib,
                          child_threads=args.child_threads, child_fds=args.child_fds) for m in sorted(PROFILES)]
    print(json.dumps({"limits": asdict(GOVERNED), "relay_buffer_bound": relay_buffer_bound(),
                      "daemon_session_bound": daemon_session_bound(), "modes": rows}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
