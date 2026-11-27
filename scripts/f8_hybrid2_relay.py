#!/usr/bin/env python3
"""Universal PRoot stdio-to-AF_UNIX MCP relay with safe PRoot fallback (Stage 7.2).

Works with any standard MCP stdio client (Hermes, Codex CLI, Claude Code,
Claude Desktop, Antigravity, OpenCode).

Features:
- Global disable aware (`F8_NO_HYBRID=1` or `<sock_dir>/disabled.flag`)
- Optional `--auto-start` delegating safely to `f8_hybrid2_ctl.ensure_running`
  (never crashes with rc=4 when MCP client strips Android 7-env vars!)
- Early-EOF retry/fallback if daemon idle-exits right as `connect()` finishes
- Non-blocking selector EVENT_WRITE bridge without 100Hz busy spinning
- Wakeup-pipe `select.poll()` in PRoot fallback so SIGTERM aborts in <5ms
"""

from __future__ import annotations

import argparse
import json
import os
import select
import selectors
import shutil
import signal
import socket
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

from f8_hybrid2_policy import (
    DEFAULT_FALLBACK_MAPS,
    DEFAULT_SOCK_PATH,
    Policy,
    parse_map_specs,
    read_tracer_pid,
    validate_unix_sock_path,
)
from f8_hybrid2_tools import MCPToolEngine, RequestCancelled, RequestContext, canonical_req_key

MAX_FRAME_BYTES = 4 * 1024 * 1024


def probe_daemon(sock_path: Path, timeout_s: float = 2.0) -> tuple[bool, str]:
    """Connect to the native UDS daemon and perform an MCP initialize + ping probe."""
    try:
        validate_unix_sock_path(sock_path)
    except ValueError as exc:
        return False, str(exc)
    if not sock_path.exists():
        return False, "socket-missing"
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout_s)
    try:
        s.connect(str(sock_path))
        init_req = {
            "jsonrpc": "2.0",
            "id": "probe-1",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "f8-hybrid2-probe", "version": "0.2.0"},
            },
        }
        s.sendall((json.dumps(init_req) + "\n").encode("utf-8"))
        f = s.makefile("rb")
        line1 = f.readline()
        if not line1:
            return False, "eof-on-init"
        r1 = json.loads(line1.decode("utf-8"))
        if "result" not in r1:
            return False, f"init-error: {r1.get('error')}"
        s.sendall((json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n").encode("utf-8"))
        s.sendall((json.dumps({"jsonrpc": "2.0", "id": "probe-2", "method": "ping"}) + "\n").encode("utf-8"))
        line2 = f.readline()
        if not line2:
            return False, "eof-on-ping"
        r2 = json.loads(line2.decode("utf-8"))
        if "result" not in r2:
            return False, f"ping-error: {r2.get('error')}"
        return True, "ok"
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"probe-failed: {exc}"
    finally:
        try:
            s.close()
        except OSError:
            pass


def bridge_stdio_to_uds(sock: socket.socket) -> tuple[int, bool, bytes]:
    """Bridge stdio <-> UDS cleanly. Returns (exit_rc, early_eof_no_reply, initial_sent_bytes)."""
    stop = threading.Event()
    in_fd = sys.stdin.fileno()
    out_fd = sys.stdout.fileno()
    in_was_blocking = os.get_blocking(in_fd)
    out_was_blocking = os.get_blocking(out_fd)
    os.set_blocking(in_fd, False)
    os.set_blocking(out_fd, False)
    sock.setblocking(False)

    sel = selectors.DefaultSelector()
    stdin_eof = False
    shut_wr_sent = False
    to_uds = bytearray()
    to_stdout = bytearray()
    sent_to_uds = bytearray()
    received_from_uds = 0
    uds_closed_early = False
    sig_r, sig_w = os.pipe()
    os.set_blocking(sig_r, False)
    os.set_blocking(sig_w, False)
    sel.register(sig_r, selectors.EVENT_READ, "sig")

    def _set_interest(fd_or_sock: Any, desired_events: int | None, tag: str) -> None:
        try:
            key = sel.get_key(fd_or_sock)
        except KeyError:
            key = None
        if desired_events is None:
            if key is not None:
                sel.unregister(fd_or_sock)
            return
        if key is None:
            sel.register(fd_or_sock, desired_events, tag)
        elif key.events != desired_events:
            sel.modify(fd_or_sock, desired_events, tag)

    def _refresh_sel() -> None:
        _set_interest(in_fd, None if stdin_eof else selectors.EVENT_READ, "stdin")
        uds_ev = selectors.EVENT_READ | (selectors.EVENT_WRITE if to_uds else 0)
        _set_interest(sock, uds_ev, "uds")
        _set_interest(out_fd, selectors.EVENT_WRITE if to_stdout else None, "stdout")

    def on_sig(_signum: int, _frame: Any) -> None:
        stop.set()
        try:
            os.write(sig_w, b"\x01")
        except OSError:
            pass

    prev_sigterm = signal.signal(signal.SIGTERM, on_sig)
    prev_sigint = signal.signal(signal.SIGINT, on_sig)

    try:
        while not stop.is_set():
            _refresh_sel()
            for key, mask in sel.select(timeout=0.5):
                tag = key.data
                if tag == "sig":
                    stop.set()
                    break
                if tag == "stdin" and (mask & selectors.EVENT_READ):
                    try:
                        chunk = os.read(in_fd, 65536)
                    except BlockingIOError:
                        continue
                    except OSError:
                        stdin_eof = True
                        break
                    if not chunk:
                        stdin_eof = True
                        if not to_uds and not shut_wr_sent:
                            try:
                                sock.shutdown(socket.SHUT_WR)
                                shut_wr_sent = True
                            except OSError:
                                stop.set()
                        break
                    to_uds.extend(chunk)
                    if len(sent_to_uds) < MAX_FRAME_BYTES:
                        sent_to_uds.extend(chunk[: MAX_FRAME_BYTES - len(sent_to_uds)])
                    if len(to_uds) > MAX_FRAME_BYTES * 2:
                        stop.set()
                        break
                elif tag == "uds":
                    if (mask & selectors.EVENT_WRITE) and to_uds:
                        try:
                            sent = sock.send(to_uds)
                            del to_uds[:sent]
                        except BlockingIOError:
                            pass
                        except OSError:
                            stop.set()
                            break
                        if stdin_eof and not to_uds and not shut_wr_sent:
                            try:
                                sock.shutdown(socket.SHUT_WR)
                                shut_wr_sent = True
                            except OSError:
                                stop.set()
                                break
                    if mask & selectors.EVENT_READ:
                        try:
                            chunk = sock.recv(65536)
                        except BlockingIOError:
                            continue
                        except OSError:
                            if received_from_uds == 0:
                                uds_closed_early = True
                            stop.set()
                            break
                        if not chunk:
                            if received_from_uds == 0:
                                uds_closed_early = True
                            stop.set()
                            break
                        received_from_uds += len(chunk)
                        to_stdout.extend(chunk)
                elif tag == "stdout" and (mask & selectors.EVENT_WRITE) and to_stdout:
                    try:
                        wrote = os.write(out_fd, to_stdout)
                        del to_stdout[:wrote]
                    except BlockingIOError:
                        pass
                    except OSError:
                        stop.set()
                        break

        # Flush remaining stdout cleanly if pipe is still open.
        if to_stdout:
            os.set_blocking(out_fd, True)
            while to_stdout:
                try:
                    wrote = os.write(out_fd, to_stdout)
                    del to_stdout[:wrote]
                except OSError:
                    break
    finally:
        signal.signal(signal.SIGTERM, prev_sigterm)
        signal.signal(signal.SIGINT, prev_sigint)
        sel.close()
        for fd in (sig_r, sig_w):
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.set_blocking(in_fd, in_was_blocking)
        except OSError:
            pass
        try:
            os.set_blocking(out_fd, out_was_blocking)
        except OSError:
            pass
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass
    return 0, (uds_closed_early and received_from_uds == 0), bytes(sent_to_uds)


def run_local_fallback(
    maps: list[tuple[str, str]],
    git_bin: str,
    default_timeout_s: float,
    prebuffered: bytes = b"",
) -> int:
    """Execute the same read-only MCP engine locally inside PRoot with fast SIGTERM wakeup."""
    home_dir = os.environ.get("HOME", tempfile.gettempdir())
    tmp_dir = os.environ.get("TMPDIR", tempfile.gettempdir())
    policy = Policy(maps=maps, home=home_dir, tmp=tmp_dir, path_env=os.environ.get("PATH", "/usr/bin:/bin"))
    engine = MCPToolEngine(policy=policy, git_bin=git_bin, default_timeout_s=default_timeout_s)

    send_lock = threading.Lock()
    active_lock = threading.Lock()
    active: dict[str, RequestContext] = {}
    workers: list[threading.Thread] = []
    state = {"initialized": False}
    stop = threading.Event()
    sig_r, sig_w = os.pipe()
    os.set_blocking(sig_r, False)
    os.set_blocking(sig_w, False)

    def write_resp(obj: dict[str, Any], *, ctx: RequestContext | None = None) -> None:
        raw = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
        with send_lock:
            if ctx is not None and ctx.cancel_event.is_set():
                return
            try:
                sys.stdout.buffer.write(raw)
                sys.stdout.buffer.flush()
            except OSError:
                stop.set()

    def worker(req_id: Any, rk: str, params: Any, ctx: RequestContext) -> None:
        try:
            resp = engine.call_tool(req_id, params, ctx)
            if not stop.is_set():
                write_resp(resp, ctx=ctx)
        except RequestCancelled:
            pass
        except Exception as exc:
            if not stop.is_set():
                write_resp(engine.jsonrpc_err(req_id, -32603, f"Internal error: {type(exc).__name__}"), ctx=ctx)
        finally:
            with active_lock:
                active.pop(rk, None)

    def handle_line(raw: bytes) -> None:
        if len(raw) > MAX_FRAME_BYTES:
            write_resp(engine.jsonrpc_err(None, -32600, "Frame too large"))
            return
        line = raw.strip()
        if not line:
            return
        try:
            msg = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            write_resp(engine.jsonrpc_err(None, -32700, "Parse error"))
            return

        if isinstance(msg, dict) and msg.get("method") == "notifications/cancelled":
            params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
            if "requestId" in params:
                rk = canonical_req_key(params["requestId"])
                if rk is not None:
                    with active_lock:
                        ctx = active.get(rk)
                    if ctx is not None:
                        ctx.cancel()
            return

        sync_resp, action = engine.handle_sync_control(msg, initialized=state["initialized"])
        if action == "initialized":
            state["initialized"] = True
        if sync_resp is not None:
            write_resp(sync_resp)
        elif action == "tools/call":
            req_id = msg.get("id")
            rk = canonical_req_key(req_id)
            if rk is None:
                write_resp(engine.jsonrpc_err(None, -32600, "Invalid Request id"))
                return
            with active_lock:
                if rk in active:
                    write_resp(engine.jsonrpc_err(req_id, -32600, "Duplicate active request id"))
                    return
                ctx = RequestContext(req_id, default_timeout_s)
                active[rk] = ctx
                th = threading.Thread(target=worker, args=(req_id, rk, msg.get("params"), ctx), daemon=True)
                workers[:] = [w for w in workers if w.is_alive()]
                workers.append(th)
            th.start()

    def on_sig(_signum: int, _frame: Any) -> None:
        stop.set()
        try:
            os.write(sig_w, b"\x01")
        except OSError:
            pass

    signal.signal(signal.SIGTERM, on_sig)
    signal.signal(signal.SIGINT, on_sig)

    in_fd = sys.stdin.fileno()
    poller = select.poll()
    poller.register(in_fd, select.POLLIN | select.POLLHUP)
    poller.register(sig_r, select.POLLIN)
    buf = bytearray(prebuffered)

    try:
        while True:
            nl = buf.find(b"\n")
            if nl >= 0:
                one = bytes(buf[:nl]).rstrip(b"\r")
                del buf[: nl + 1]
                handle_line(one)
                continue
            if stop.is_set():
                break
            events = poller.poll(500)
            if stop.is_set():
                break
            eof_hit = False
            for fd, ev in events:
                if fd == sig_r:
                    stop.set()
                    break
                if fd == in_fd and (ev & (select.POLLIN | select.POLLHUP)):
                    chunk = os.read(in_fd, 65536)
                    if not chunk:
                        eof_hit = True
                        break
                    buf.extend(chunk)
                    if len(buf) > MAX_FRAME_BYTES * 2:
                        write_resp(engine.jsonrpc_err(None, -32600, "Line buffer overflow"))
                        stop.set()
                        break
            if stop.is_set() or eof_hit:
                break
    finally:
        if stop.is_set():
            with active_lock:
                ctxs = list(active.values())
            for c in ctxs:
                c.cancel()
        join_wait = max(default_timeout_s + 2.0, 10.0)
        for w in workers:
            w.join(timeout=join_wait)
        for fd in (sig_r, sig_w):
            try:
                os.close(fd)
            except OSError:
                pass
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Stage 7.2 universal PRoot stdio-to-UDS MCP relay")
    ap.add_argument("--socket", default=DEFAULT_SOCK_PATH, help="Shared AF_UNIX socket path")
    ap.add_argument("--disabled-flag", default="", help="Optional global disable flag path")
    ap.add_argument(
        "--map",
        action="append",
        default=[],
        help="Fallback map GUEST=LOCAL_PREFIX (defaults to /root/projects=/root/projects)",
    )
    ap.add_argument(
        "--daemon-map",
        action="append",
        default=[],
        help="Optional GUEST=HOST map forwarded to ctl.ensure_running on --auto-start",
    )
    ap.add_argument("--connect-timeout", type=float, default=3.0, help="UDS connect timeout seconds")
    ap.add_argument("--default-timeout", type=float, default=30.0, help="Fallback default tool timeout")
    ap.add_argument("--git-bin", default=shutil.which("git") or "/usr/bin/git", help="Fallback git binary")
    ap.add_argument("--probe", action="store_true", help="Run initialize+ping readiness probe and exit")
    ap.add_argument("--auto-start", action="store_true", help="Try single-flight auto-start via controller if socket down")
    ap.add_argument("--no-fallback", action="store_true", help="Fail instead of falling back to local PRoot")
    return ap.parse_args(argv)


def _try_connect_with_optional_autostart(
    sock_path: Path,
    timeout_s: float,
    auto_start: bool,
    daemon_maps: list[str] | None = None,
) -> socket.socket:
    validate_unix_sock_path(sock_path)
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout_s)
        s.connect(str(sock_path))
        return s
    except OSError as first_exc:
        try:
            s.close()
        except OSError:
            pass
        if not auto_start:
            raise first_exc
        try:
            import f8_hybrid2_ctl as ctl

            res = ctl.ensure_running(
                runtime_dir=sock_path.parent,
                maps=daemon_maps,
                timeout_s=max(3.0, timeout_s),
            )
            if not res.get("ok"):
                raise OSError(f"autostart-unavailable:{res.get('reason')}")
        except Exception as exc:
            raise OSError(str(exc)) from exc
        s2 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s2.settimeout(timeout_s)
        s2.connect(str(sock_path))
        return s2


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sock_path = Path(args.socket)
    disabled_flag = Path(args.disabled_flag) if args.disabled_flag else (sock_path.parent / "disabled.flag")
    autostart_maps = args.daemon_map or (args.map if read_tracer_pid() == 0 else [])

    if args.probe:
        if os.environ.get("F8_NO_HYBRID") == "1" or disabled_flag.exists():
            print(json.dumps({"ok": False, "detail": "global-disabled", "socket": str(sock_path)}))
            return 3
        ok, detail = probe_daemon(sock_path, timeout_s=args.connect_timeout)
        print(json.dumps({"ok": ok, "detail": detail, "socket": str(sock_path)}))
        return 0 if ok else 2

    if os.environ.get("F8_NO_HYBRID") == "1":
        print("[f8-hybrid2-relay] fallback=proot reason=F8_NO_HYBRID=1", file=sys.stderr, flush=True)
        if args.no_fallback:
            return 3
        return run_local_fallback(parse_map_specs(args.map, DEFAULT_FALLBACK_MAPS), args.git_bin, args.default_timeout)

    if disabled_flag.exists():
        print("[f8-hybrid2-relay] fallback=proot reason=global-disabled", file=sys.stderr, flush=True)
        if args.no_fallback:
            return 3
        return run_local_fallback(parse_map_specs(args.map, DEFAULT_FALLBACK_MAPS), args.git_bin, args.default_timeout)

    try:
        s = _try_connect_with_optional_autostart(sock_path, args.connect_timeout, args.auto_start, autostart_maps)
    except (OSError, ValueError) as exc:
        if args.no_fallback:
            print(f"[f8-hybrid2-relay] daemon-unavailable reason={exc}", file=sys.stderr, flush=True)
            return 2
        print(f"[f8-hybrid2-relay] fallback=proot reason=daemon-unavailable ({exc})", file=sys.stderr, flush=True)
        return run_local_fallback(parse_map_specs(args.map, DEFAULT_FALLBACK_MAPS), args.git_bin, args.default_timeout)

    rc, early_eof, initial_bytes = bridge_stdio_to_uds(s)
    if early_eof:
        # Idle-exit or transient close before any reply arrived: retry connect once or fall back.
        try:
            s_retry = _try_connect_with_optional_autostart(sock_path, args.connect_timeout, args.auto_start, autostart_maps)
            if initial_bytes:
                s_retry.sendall(initial_bytes)
            rc2, early2, _ = bridge_stdio_to_uds(s_retry)
            if not early2:
                return rc2
        except (OSError, ValueError):
            pass
        if args.no_fallback:
            return 2
        print("[f8-hybrid2-relay] fallback=proot reason=early-eof-on-connect", file=sys.stderr, flush=True)
        return run_local_fallback(
            parse_map_specs(args.map, DEFAULT_FALLBACK_MAPS),
            args.git_bin,
            args.default_timeout,
            prebuffered=initial_bytes,
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
