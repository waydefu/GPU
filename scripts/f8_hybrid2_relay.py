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
import collections
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
from f8_hybrid2_tools import MCPToolEngine, RequestCancelled, RequestContext, TOOL_DEFS, canonical_req_key

MAX_FRAME_BYTES = 4 * 1024 * 1024
DEFAULT_MAX_LOCAL_INFLIGHT = 8
ALL_TOOL_NAMES: frozenset[str] = frozenset(str(d["name"]) for d in TOOL_DEFS)
DEFAULT_NATIVE_TOOLS: frozenset[str] = frozenset({"repo_tree_scan", "repo_text_search", "git_ro"})


def parse_native_tools(spec: str | None) -> frozenset[str]:
    if spec is None:
        return DEFAULT_NATIVE_TOOLS
    cleaned = spec.strip()
    if not cleaned or cleaned.lower() == "none":
        return frozenset()
    if cleaned.lower() == "all":
        return ALL_TOOL_NAMES
    chosen = frozenset(tok.strip() for tok in cleaned.split(",") if tok.strip())
    unknown = chosen - ALL_TOOL_NAMES
    if unknown:
        raise ValueError(f"Unknown --native-tools entries: {sorted(unknown)}")
    return chosen


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


def bridge_stdio_to_uds(
    sock: socket.socket,
    *,
    native_tools: frozenset[str] = DEFAULT_NATIVE_TOOLS,
    local_maps: list[tuple[str, str]] | None = None,
    git_bin: str = "/usr/bin/git",
    default_timeout_s: float = 30.0,
    max_local_inflight: int = DEFAULT_MAX_LOCAL_INFLIGHT,
    route_log_path: Path | None = None,
    prebuffered: bytes = b"",
) -> tuple[int, bool, bytes]:
    """Bridge stdio <-> UDS with selective Stage 7.4 tool routing (native UDS vs PRoot local)."""
    if native_tools >= ALL_TOOL_NAMES:
        return _bridge_raw_passthrough(sock, prebuffered=prebuffered)

    max_local = max(1, min(16, int(max_local_inflight)))
    home_dir = os.environ.get("HOME", tempfile.gettempdir())
    tmp_dir = os.environ.get("TMPDIR", tempfile.gettempdir())
    maps = list(local_maps) if local_maps is not None else list(DEFAULT_FALLBACK_MAPS)
    policy = Policy(maps=maps, home=home_dir, tmp=tmp_dir, path_env=os.environ.get("PATH", "/usr/bin:/bin"))
    local_engine = MCPToolEngine(policy=policy, git_bin=git_bin, default_timeout_s=default_timeout_s)

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
    stdin_buf = bytearray(prebuffered)
    uds_buf = bytearray()
    to_uds = bytearray()
    to_stdout = bytearray()
    sent_to_uds = bytearray(prebuffered[:MAX_FRAME_BYTES])

    session_state: dict[str, Any] = {
        "init_seen": False,
        "initialized": False,
        "init_rk": None,
        "local_replies": 0,
        "received_from_uds": 0,
        "uds_closed": False,
        "uds_closed_early": False,
        "sig_abort": False,
    }
    native_inflight: set[str] = set()
    local_active_lock = threading.Lock()
    local_active: dict[str, RequestContext] = {}
    deferred_local: list[tuple[Any, str, Any]] = []
    workers: list[threading.Thread] = []
    local_out_lock = threading.Lock()
    local_out_q: collections.deque[tuple[bytes, str | None]] = collections.deque()

    sig_r, sig_w = os.pipe()
    local_r, local_w = os.pipe()
    for pfd in (sig_r, sig_w, local_r, local_w):
        os.set_blocking(pfd, False)
    sel.register(sig_r, selectors.EVENT_READ, "sig")
    sel.register(local_r, selectors.EVENT_READ, "local")

    def _record_route(tool_name: str, target: str) -> None:
        if route_log_path is None:
            return
        try:
            route_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(route_log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ev": "route", "tool": tool_name, "target": target}, separators=(",", ":")) + "\n")
        except OSError:
            pass

    def _wake_local() -> None:
        try:
            os.write(local_w, b"\x01")
        except OSError:
            pass

    def _queue_local_bytes(raw_bytes: bytes, rk: str | None = None, *, wake: bool = True) -> None:
        with local_out_lock:
            local_out_q.append((raw_bytes, rk))
        if wake:
            _wake_local()

    def _local_worker(req_id: Any, rk: str, params: Any, ctx: RequestContext) -> None:
        raw_out: bytes | None = None
        try:
            resp = local_engine.call_tool(req_id, params, ctx)
            if not stop.is_set() and not ctx.cancel_event.is_set():
                raw_out = (json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8")
        except RequestCancelled:
            pass
        except Exception as exc:
            if not stop.is_set() and not ctx.cancel_event.is_set():
                err = local_engine.jsonrpc_err(req_id, -32603, f"Internal error: {type(exc).__name__}")
                raw_out = (json.dumps(err, ensure_ascii=False) + "\n").encode("utf-8")
        finally:
            if raw_out is not None:
                _queue_local_bytes(raw_out, rk, wake=False)
            with local_active_lock:
                local_active.pop(rk, None)
            _wake_local()

    def _start_local_call(req_id: Any, rk: str, params: Any) -> bool:
        ctx = RequestContext(req_id, default_timeout_s)
        with local_active_lock:
            if len(local_active) >= max_local:
                return False
            local_active[rk] = ctx
            workers[:] = [w for w in workers if w.is_alive()]
            th = threading.Thread(target=_local_worker, args=(req_id, rk, params, ctx), daemon=True)
            workers.append(th)
        th.start()
        return True

    def _emit_local_err(req_id: Any, code: int, msg: str) -> None:
        to_stdout.extend((json.dumps(local_engine.jsonrpc_err(req_id, code, msg), ensure_ascii=False) + "\n").encode("utf-8"))
        session_state["local_replies"] += 1

    def _fail_deferred_uninitialized() -> None:
        while deferred_local:
            req_id, _rk, _params = deferred_local.pop(0)
            _emit_local_err(req_id, -32002, "Server not initialized")

    def _mark_uds_closed() -> None:
        session_state["uds_closed"] = True
        native_inflight.clear()
        if session_state["received_from_uds"] == 0 and session_state["local_replies"] == 0:
            session_state["uds_closed_early"] = True
            deferred_local.clear()
            stop.set()
            return
        if not session_state["initialized"] and deferred_local:
            _fail_deferred_uninitialized()
        if not stdin_eof:
            stop.set()

    def _handle_stdin_line(raw_line: bytes) -> None:
        if len(raw_line) > MAX_FRAME_BYTES:
            _emit_local_err(None, -32600, "Frame too large")
            return
        stripped = raw_line.strip()
        if not stripped:
            return
        try:
            msg = json.loads(stripped.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _emit_local_err(None, -32700, "Parse error")
            return

        # Strict JSON-RPC 2.0 validation before routing either local or UDS.
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            raw_id = msg.get("id") if isinstance(msg, dict) else None
            _emit_local_err(raw_id if canonical_req_key(raw_id) is not None else None, -32600, "Invalid Request")
            return

        has_id = "id" in msg
        req_id = msg.get("id")
        rk = canonical_req_key(req_id) if has_id else None
        if has_id and rk is None:
            _emit_local_err(None, -32600, "Invalid Request id")
            return

        method = msg.get("method")
        if not isinstance(method, str) or not method:
            if has_id:
                _emit_local_err(req_id, -32600, "Missing method")
            return

        if method == "notifications/cancelled":
            params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
            if "requestId" in params:
                cancel_rk = canonical_req_key(params["requestId"])
                if cancel_rk is not None:
                    with local_active_lock:
                        ctx = local_active.get(cancel_rk)
                    if ctx is not None:
                        ctx.cancel()
                        return
                    for idx, (_rid, drk, _dp) in enumerate(deferred_local):
                        if drk == cancel_rk:
                            deferred_local.pop(idx)
                            return
                    native_inflight.discard(cancel_rk)
            if not session_state["uds_closed"]:
                to_uds.extend(stripped + b"\n")
            return

        if method == "tools/call":
            if not has_id or rk is None:
                return
            with local_active_lock:
                local_busy = rk in local_active
                live_local_cnt = len(local_active)
            deferred_busy = any(drk == rk for _rid, drk, _dp in deferred_local)
            if local_busy or deferred_busy or rk in native_inflight:
                _emit_local_err(req_id, -32600, "Duplicate active request id")
                return
            params = msg.get("params")
            if not isinstance(params, dict):
                _emit_local_err(req_id, -32602, "Invalid params")
                return
            tool_name = params.get("name")
            if not isinstance(tool_name, str):
                _emit_local_err(req_id, -32602, "Invalid tool call params")
                return
            if tool_name in native_tools:
                if session_state["uds_closed"]:
                    _emit_local_err(req_id, -32000, "Native daemon disconnected")
                    return
                native_inflight.add(rk)
                _record_route(tool_name, "native_uds")
                to_uds.extend(stripped + b"\n")
                return
            if not session_state["initialized"]:
                if not session_state["init_seen"]:
                    _emit_local_err(req_id, -32002, "Server not initialized")
                    return
                if session_state["uds_closed"]:
                    _emit_local_err(req_id, -32002, "Server not initialized")
                    return
                if live_local_cnt + len(deferred_local) >= max_local:
                    _emit_local_err(req_id, -32000, "Server busy: max local inflight requests reached")
                    return
                _record_route(tool_name, "proot_local")
                deferred_local.append((req_id, rk, params))
                return
            if live_local_cnt + len(deferred_local) >= max_local:
                _emit_local_err(req_id, -32000, "Server busy: max local inflight requests reached")
                return
            _record_route(tool_name, "proot_local")
            if not _start_local_call(req_id, rk, params):
                _emit_local_err(req_id, -32000, "Server busy: max local inflight requests reached")
            return

        if method == "initialize" and has_id:
            session_state["init_seen"] = True
            session_state["init_rk"] = rk
        if has_id and rk is not None:
            if session_state["uds_closed"]:
                _emit_local_err(req_id, -32000, "Native daemon disconnected")
                return
            native_inflight.add(rk)
        if not session_state["uds_closed"]:
            to_uds.extend(stripped + b"\n")

    def _handle_uds_line(raw_line: bytes) -> None:
        stripped = raw_line.strip()
        if not stripped:
            return
        try:
            resp = json.loads(stripped.decode("utf-8"))
            if isinstance(resp, dict) and "id" in resp:
                rk = canonical_req_key(resp.get("id"))
                if rk is not None:
                    native_inflight.discard(rk)
                    if session_state["init_rk"] is not None and rk == session_state["init_rk"]:
                        if "result" in resp:
                            session_state["initialized"] = True
                            while deferred_local:
                                d_rid, d_rk, d_params = deferred_local.pop(0)
                                if not _start_local_call(d_rid, d_rk, d_params):
                                    _emit_local_err(d_rid, -32000, "Server busy: max local inflight requests reached")
                        else:
                            _fail_deferred_uninitialized()
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        to_stdout.extend(stripped + b"\n")

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
        out_paused = len(to_stdout) >= MAX_FRAME_BYTES * 2
        _set_interest(in_fd, None if (stdin_eof or out_paused) else selectors.EVENT_READ, "stdin")
        _set_interest(local_r, None if out_paused else selectors.EVENT_READ, "local")
        if session_state["uds_closed"]:
            _set_interest(sock, None, "uds")
        else:
            uds_ev = (0 if out_paused else selectors.EVENT_READ) | (selectors.EVENT_WRITE if to_uds else 0)
            _set_interest(sock, uds_ev if uds_ev else None, "uds")
        _set_interest(out_fd, selectors.EVENT_WRITE if to_stdout else None, "stdout")

    def on_sig(_signum: int, _frame: Any) -> None:
        session_state["sig_abort"] = True
        stop.set()
        try:
            os.write(sig_w, b"\x01")
        except OSError:
            pass

    prev_sigterm = signal.signal(signal.SIGTERM, on_sig)
    prev_sigint = signal.signal(signal.SIGINT, on_sig)

    try:
        while True:
            nl = stdin_buf.find(b"\n")
            if nl < 0:
                break
            one = bytes(stdin_buf[:nl]).rstrip(b"\r")
            del stdin_buf[: nl + 1]
            _handle_stdin_line(one)
        while not stop.is_set():
            if len(to_stdout) > MAX_FRAME_BYTES * 4:
                session_state["sig_abort"] = True
                stop.set()
                break
            with local_active_lock:
                local_busy_now = bool(local_active)
            with local_out_lock:
                local_queued = bool(local_out_q)
            if stdin_eof and session_state["uds_closed"] and not local_busy_now and not deferred_local and not local_queued and not to_stdout:
                break
            _refresh_sel()
            for key, mask in sel.select(timeout=0.5):
                tag = key.data
                if tag == "sig":
                    session_state["sig_abort"] = True
                    stop.set()
                    break
                if tag == "local":
                    try:
                        os.read(local_r, 4096)
                    except OSError:
                        pass
                    with local_out_lock:
                        while local_out_q:
                            raw_resp, _rk = local_out_q.popleft()
                            to_stdout.extend(raw_resp)
                            session_state["local_replies"] += 1
                elif tag == "stdin" and (mask & selectors.EVENT_READ):
                    try:
                        chunk = os.read(in_fd, 65536)
                    except BlockingIOError:
                        continue
                    except OSError:
                        stdin_eof = True
                        break
                    if not chunk:
                        stdin_eof = True
                        while True:
                            nl = stdin_buf.find(b"\n")
                            if nl < 0:
                                break
                            one = bytes(stdin_buf[:nl]).rstrip(b"\r")
                            del stdin_buf[: nl + 1]
                            _handle_stdin_line(one)
                        if stdin_buf.strip():
                            _handle_stdin_line(bytes(stdin_buf))
                            stdin_buf.clear()
                        if not to_uds and not shut_wr_sent and not session_state["uds_closed"]:
                            try:
                                sock.shutdown(socket.SHUT_WR)
                                shut_wr_sent = True
                            except OSError:
                                _mark_uds_closed()
                        break
                    if (
                        session_state["received_from_uds"] == 0
                        and session_state["local_replies"] == 0
                        and len(sent_to_uds) < MAX_FRAME_BYTES
                    ):
                        sent_to_uds.extend(chunk[: MAX_FRAME_BYTES - len(sent_to_uds)])
                    stdin_buf.extend(chunk)
                    while True:
                        nl = stdin_buf.find(b"\n")
                        if nl < 0:
                            break
                        one = bytes(stdin_buf[:nl]).rstrip(b"\r")
                        del stdin_buf[: nl + 1]
                        _handle_stdin_line(one)
                    if len(stdin_buf) > MAX_FRAME_BYTES * 2:
                        _emit_local_err(None, -32600, "Line buffer overflow")
                        stop.set()
                        break
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
                            _mark_uds_closed()
                            break
                        if stdin_eof and not to_uds and not shut_wr_sent and not session_state["uds_closed"]:
                            try:
                                sock.shutdown(socket.SHUT_WR)
                                shut_wr_sent = True
                            except OSError:
                                _mark_uds_closed()
                                break
                    if (mask & selectors.EVENT_READ) and not session_state["uds_closed"]:
                        try:
                            chunk = sock.recv(65536)
                        except BlockingIOError:
                            continue
                        except OSError:
                            _mark_uds_closed()
                            break
                        if not chunk:
                            _mark_uds_closed()
                            break
                        session_state["received_from_uds"] += len(chunk)
                        uds_buf.extend(chunk)
                        while True:
                            nl = uds_buf.find(b"\n")
                            if nl < 0:
                                break
                            one = bytes(uds_buf[:nl]).rstrip(b"\r")
                            del uds_buf[: nl + 1]
                            _handle_uds_line(one)
                elif tag == "stdout" and (mask & selectors.EVENT_WRITE) and to_stdout:
                    try:
                        wrote = os.write(out_fd, to_stdout)
                        del to_stdout[:wrote]
                    except BlockingIOError:
                        pass
                    except OSError:
                        session_state["sig_abort"] = True
                        stop.set()
                        break

    finally:
        signal.signal(signal.SIGTERM, prev_sigterm)
        signal.signal(signal.SIGINT, prev_sigint)
        if stop.is_set():
            with local_active_lock:
                ctxs = list(local_active.values())
            for c in ctxs:
                c.cancel()
        for w in workers:
            w.join(timeout=max(default_timeout_s + 2.0, 10.0))
        sel.close()
        for fd in (sig_r, sig_w, local_r, local_w):
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
    return (
        0,
        bool(session_state["uds_closed_early"] and session_state["received_from_uds"] == 0 and session_state["local_replies"] == 0),
        bytes(sent_to_uds),
    )


def _bridge_raw_passthrough(sock: socket.socket, *, prebuffered: bytes = b"") -> tuple[int, bool, bytes]:
    """Raw passthrough stdio <-> UDS (used only when --native-tools all)."""
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
    to_uds = bytearray(prebuffered)
    to_stdout = bytearray()
    sent_to_uds = bytearray(prebuffered[:MAX_FRAME_BYTES])
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

        # Drain without switching stdout to blocking mode; signal remains actionable.
        while to_stdout and not stop.is_set():
            ready = select.poll()
            ready.register(out_fd, select.POLLOUT | select.POLLERR | select.POLLHUP)
            ready.register(sig_r, select.POLLIN)
            for fd, ev in ready.poll(500):
                if fd == sig_r or (fd == out_fd and ev & (select.POLLERR | select.POLLHUP)):
                    stop.set()
                    break
                if fd == out_fd and ev & select.POLLOUT:
                    try:
                        del to_stdout[:os.write(out_fd, to_stdout)]
                    except BlockingIOError:
                        pass
                    except OSError:
                        stop.set()
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
    max_inflight: int = DEFAULT_MAX_LOCAL_INFLIGHT,
) -> int:
    """Execute the same read-only MCP engine locally inside PRoot with fast SIGTERM wakeup."""
    max_local = max(1, min(16, int(max_inflight)))
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
    out_fd = sys.stdout.fileno()
    out_was_blocking = os.get_blocking(out_fd)
    os.set_blocking(out_fd, False)
    out_buf = bytearray()
    out_done = threading.Event()

    def write_resp(obj: dict[str, Any], *, ctx: RequestContext | None = None) -> None:
        raw = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
        with send_lock:
            if stop.is_set() or (ctx is not None and ctx.cancel_event.is_set()):
                return
            if len(out_buf) + len(raw) > MAX_FRAME_BYTES * 4:
                stop.set()
                return
            out_buf.extend(raw)

    def output_worker() -> None:
        poller = select.poll()
        poller.register(out_fd, select.POLLOUT | select.POLLERR | select.POLLHUP)
        while not stop.is_set():
            with send_lock:
                pending = bool(out_buf)
            if not pending:
                if out_done.wait(0.05):
                    with send_lock:
                        if not out_buf:
                            break
                continue
            for _fd, ev in poller.poll(100):
                if ev & (select.POLLERR | select.POLLHUP):
                    stop.set()
                    break
                if ev & select.POLLOUT:
                    try:
                        with send_lock:
                            del out_buf[:os.write(out_fd, out_buf)]
                    except BlockingIOError:
                        pass
                    except OSError:
                        stop.set()
                        break

    output_thread = threading.Thread(target=output_worker, daemon=True)
    output_thread.start()

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
                if len(active) >= max_local:
                    write_resp(engine.jsonrpc_err(req_id, -32000, "Server busy: max local inflight requests reached"))
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
        out_done.set()
        output_thread.join()
        try:
            os.set_blocking(out_fd, out_was_blocking)
        except OSError:
            pass
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
    ap.add_argument(
        "--native-tools",
        default=os.environ.get("F8_HYBRID2_NATIVE_TOOLS"),
        help="Comma-separated tools routed to native UDS daemon (default: repo_tree_scan,repo_text_search,git_ro; 'all' for passthrough)",
    )
    ap.add_argument(
        "--route-log",
        default=os.environ.get("F8_HYBRID2_ROUTE_LOG", ""),
        help="Optional JSONL route audit log path (records tool->native_uds/proot_local)",
    )
    ap.add_argument(
        "--max-local-inflight",
        type=int,
        default=int(os.environ.get("F8_HYBRID2_MAX_LOCAL_INFLIGHT", str(DEFAULT_MAX_LOCAL_INFLIGHT))),
        help="Max concurrent locally routed/fallback requests in relay",
    )
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
    try:
        native_tools = parse_native_tools(args.native_tools)
    except ValueError as exc:
        print(f"[f8-hybrid2-relay] invalid --native-tools: {exc}", file=sys.stderr, flush=True)
        return 2
    route_log_path = Path(args.route_log) if args.route_log else None
    local_maps = parse_map_specs(args.map, DEFAULT_FALLBACK_MAPS)
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
        return run_local_fallback(local_maps, args.git_bin, args.default_timeout, max_inflight=args.max_local_inflight)

    if disabled_flag.exists():
        print("[f8-hybrid2-relay] fallback=proot reason=global-disabled", file=sys.stderr, flush=True)
        if args.no_fallback:
            return 3
        return run_local_fallback(local_maps, args.git_bin, args.default_timeout, max_inflight=args.max_local_inflight)

    try:
        s = _try_connect_with_optional_autostart(sock_path, args.connect_timeout, args.auto_start, autostart_maps)
    except (OSError, ValueError) as exc:
        if args.no_fallback:
            print(f"[f8-hybrid2-relay] daemon-unavailable reason={exc}", file=sys.stderr, flush=True)
            return 2
        print(f"[f8-hybrid2-relay] fallback=proot reason=daemon-unavailable ({exc})", file=sys.stderr, flush=True)
        return run_local_fallback(local_maps, args.git_bin, args.default_timeout, max_inflight=args.max_local_inflight)

    rc, early_eof, initial_bytes = bridge_stdio_to_uds(
        s,
        native_tools=native_tools,
        local_maps=local_maps,
        git_bin=args.git_bin,
        default_timeout_s=args.default_timeout,
        max_local_inflight=args.max_local_inflight,
        route_log_path=route_log_path,
    )
    if early_eof:
        # Idle-exit or transient close before any reply arrived: retry connect once or fall back.
        try:
            s_retry = _try_connect_with_optional_autostart(sock_path, args.connect_timeout, args.auto_start, autostart_maps)
            rc2, early2, _ = bridge_stdio_to_uds(
                s_retry,
                native_tools=native_tools,
                local_maps=local_maps,
                git_bin=args.git_bin,
                default_timeout_s=args.default_timeout,
                max_local_inflight=args.max_local_inflight,
                route_log_path=route_log_path,
                prebuffered=initial_bytes,
            )
            if not early2:
                return rc2
        except (OSError, ValueError):
            pass
        if args.no_fallback:
            return 2
        print("[f8-hybrid2-relay] fallback=proot reason=early-eof-on-connect", file=sys.stderr, flush=True)
        return run_local_fallback(
            local_maps,
            args.git_bin,
            args.default_timeout,
            prebuffered=initial_bytes,
            max_inflight=args.max_local_inflight,
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
