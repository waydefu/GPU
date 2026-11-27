#!/usr/bin/env python3
"""Thin PRoot stdio-to-AF_UNIX MCP relay with safe PRoot fallback (Stage 7.2).

Intended to be invoked inside PRoot by Hermes (`mcp_servers.<name>.command`).
If `F8_NO_HYBRID=1` is set or the native daemon socket is unavailable at startup,
transparently executes the exact same read-only MCP tool engine in-process inside
PRoot (unless `--no-fallback` or `--probe` is requested).
"""

from __future__ import annotations

import argparse
import json
import os
import selectors
import signal
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

from f8_hybrid2_policy import Policy, validate_unix_sock_path
from f8_hybrid2_tools import MCPToolEngine, RequestCancelled, RequestContext

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
                "clientInfo": {"name": "f8-hybrid2-probe", "version": "0.1.0"},
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


def bridge_stdio_to_uds(sock: socket.socket) -> int:
    """Bidirectionally pump newline-delimited frames between stdin/stdout and UDS."""
    stop = threading.Event()
    in_fd = sys.stdin.fileno()
    out_fd = sys.stdout.fileno()
    os.set_blocking(in_fd, False)
    sock.setblocking(False)

    sel = selectors.DefaultSelector()
    sel.register(in_fd, selectors.EVENT_READ, "stdin")
    sel.register(sock, selectors.EVENT_READ, "uds")

    stdin_eof = False
    shut_wr_sent = False
    to_uds = bytearray()
    to_stdout = bytearray()

    def on_sig(_signum: int, _frame: Any) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, on_sig)
    signal.signal(signal.SIGINT, on_sig)

    try:
        while not stop.is_set():
            # Flush pending buffers non-blockingly when possible.
            if to_uds:
                try:
                    sent = sock.send(to_uds)
                    del to_uds[:sent]
                except BlockingIOError:
                    pass
                except OSError:
                    break
            elif stdin_eof and not shut_wr_sent:
                try:
                    sock.shutdown(socket.SHUT_WR)
                except OSError:
                    break
                shut_wr_sent = True

            if to_stdout:
                try:
                    wrote = os.write(out_fd, to_stdout)
                    del to_stdout[:wrote]
                except BlockingIOError:
                    pass
                except OSError:
                    break

            for key, _ in sel.select(timeout=0.01 if (to_uds or to_stdout) else 0.1):
                tag = key.data
                if tag == "stdin":
                    try:
                        chunk = os.read(in_fd, 65536)
                    except BlockingIOError:
                        continue
                    except OSError:
                        stdin_eof = True
                        break
                    if not chunk:
                        stdin_eof = True
                        try:
                            sel.unregister(in_fd)
                        except KeyError:
                            pass
                        break
                    to_uds.extend(chunk)
                    if len(to_uds) > MAX_FRAME_BYTES * 2:
                        stop.set()
                        break
                elif tag == "uds":
                    try:
                        chunk = sock.recv(65536)
                    except BlockingIOError:
                        continue
                    except OSError:
                        stop.set()
                        break
                    if not chunk:
                        stop.set()
                        break
                    to_stdout.extend(chunk)

        # Flush final stdout bytes cleanly if socket ended after writing response.
        while to_stdout:
            try:
                wrote = os.write(out_fd, to_stdout)
                del to_stdout[:wrote]
            except OSError:
                break
    finally:
        sel.close()
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass
    return 0


def run_local_fallback(maps: list[tuple[str, str]], git_bin: str, default_timeout_s: float) -> int:
    """Execute the same read-only MCP engine locally inside PRoot when fallback triggers."""
    home_dir = os.environ.get("HOME", "/tmp")
    tmp_dir = os.environ.get("TMPDIR", "/tmp")
    policy = Policy(maps=maps, home=home_dir, tmp=tmp_dir, path_env=os.environ.get("PATH", "/usr/bin:/bin"))
    engine = MCPToolEngine(policy=policy, git_bin=git_bin, default_timeout_s=default_timeout_s)

    send_lock = threading.Lock()
    active_lock = threading.Lock()
    active: dict[str, RequestContext] = {}
    workers: list[threading.Thread] = []
    stop = threading.Event()

    def write_resp(obj: dict[str, Any]) -> None:
        raw = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
        with send_lock:
            sys.stdout.buffer.write(raw)
            sys.stdout.buffer.flush()

    def worker(req_id: Any, rk: str, params: Any, ctx: RequestContext) -> None:
        try:
            resp = engine.call_tool(req_id, params, ctx)
            if not ctx.cancel_event.is_set() and not stop.is_set():
                write_resp(resp)
        except RequestCancelled:
            pass
        finally:
            with active_lock:
                active.pop(rk, None)

    def on_sig(_signum: int, _frame: Any) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, on_sig)
    signal.signal(signal.SIGINT, on_sig)

    try:
        while not stop.is_set():
            raw = sys.stdin.buffer.readline()
            if not raw:
                break
            line = raw.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                write_resp(engine.jsonrpc_err(None, -32700, "Parse error"))
                continue

            if isinstance(msg, dict) and msg.get("method") == "notifications/cancelled":
                params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
                if "requestId" in params:
                    rk = json.dumps(params["requestId"], sort_keys=True)
                    with active_lock:
                        ctx = active.get(rk)
                    if ctx is not None:
                        ctx.cancel()
                continue

            sync_resp, async_kind = engine.handle_sync_control(msg)
            if sync_resp is not None:
                write_resp(sync_resp)
            elif async_kind == "tools/call":
                req_id = msg.get("id")
                rk = json.dumps(req_id, sort_keys=True)
                ctx = RequestContext(req_id, default_timeout_s)
                with active_lock:
                    active[rk] = ctx
                    th = threading.Thread(target=worker, args=(req_id, rk, msg.get("params"), ctx), daemon=True)
                    workers[:] = [w for w in workers if w.is_alive()]
                    workers.append(th)
                th.start()
    finally:
        if stop.is_set():
            with active_lock:
                ctxs = list(active.values())
            for c in ctxs:
                c.cancel()
        for w in workers:
            w.join(timeout=10.0)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Stage 7.2 PRoot stdio-to-UDS MCP relay")
    ap.add_argument("--socket", required=True, help="Shared AF_UNIX socket path")
    ap.add_argument(
        "--map",
        action="append",
        default=[],
        help="Guest-side fallback map GUEST=LOCAL_PREFIX (defaults to /root/projects=/root/projects)",
    )
    ap.add_argument("--connect-timeout", type=float, default=2.0, help="UDS connect timeout seconds")
    ap.add_argument("--default-timeout", type=float, default=30.0, help="Fallback default tool timeout")
    ap.add_argument("--git-bin", default="/usr/bin/git", help="Fallback PRoot git binary")
    ap.add_argument("--probe", action="store_true", help="Run initialize+ping readiness probe and exit")
    ap.add_argument("--no-fallback", action="store_true", help="Fail instead of falling back to local PRoot")
    return ap.parse_args(argv)


def _fallback_maps(raw_maps: list[str]) -> list[tuple[str, str]]:
    if not raw_maps:
        return [("/root/projects", "/root/projects")]
    out: list[tuple[str, str]] = []
    for item in raw_maps:
        if "=" in item:
            g, h = item.split("=", 1)
            out.append((g, h))
        else:
            out.append((item, item))
    return out


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sock_path = Path(args.socket)

    if args.probe:
        ok, detail = probe_daemon(sock_path, timeout_s=args.connect_timeout)
        print(json.dumps({"ok": ok, "detail": detail, "socket": str(sock_path)}))
        return 0 if ok else 2

    if os.environ.get("F8_NO_HYBRID") == "1":
        print("[f8-hybrid2-relay] fallback=proot reason=F8_NO_HYBRID=1", file=sys.stderr, flush=True)
        if args.no_fallback:
            return 3
        return run_local_fallback(_fallback_maps(args.map), args.git_bin, args.default_timeout)

    try:
        validate_unix_sock_path(sock_path)
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(args.connect_timeout)
        s.connect(str(sock_path))
    except (OSError, ValueError) as exc:
        if args.no_fallback:
            print(f"[f8-hybrid2-relay] daemon-unavailable reason={exc}", file=sys.stderr, flush=True)
            return 2
        print(f"[f8-hybrid2-relay] fallback=proot reason=daemon-unavailable ({exc})", file=sys.stderr, flush=True)
        return run_local_fallback(_fallback_maps(args.map), args.git_bin, args.default_timeout)

    return bridge_stdio_to_uds(s)


if __name__ == "__main__":
    raise SystemExit(main())
