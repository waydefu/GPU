#!/usr/bin/env python3
"""Native Termux persistent MCP JSON-RPC 2.0 daemon over AF_UNIX (Stage 7.2).

Intended to run outside PRoot (TracerPid == 0) via `termux-bg-run`.
Enforces 0700 socket dir, 0600 socket mode, <=107-byte AF_UNIX path check,
single-instance flock pidfile, SO_PEERCRED UID verification, per-request
cancellation (`notifications/cancelled`), per-call timeout with process-group
SIGKILL, clean client disconnect teardown, and zero-residue SIGTERM shutdown.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import select
import signal
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

from f8_hybrid2_policy import Policy, Refuse, read_tracer_pid, validate_unix_sock_path, verify_peercred
from f8_hybrid2_tools import MCPToolEngine, RequestCancelled, RequestContext

MAX_LINE_BYTES = 4 * 1024 * 1024
CONN_IDLE_READ_TIMEOUT = 1.0


class ClientSession:
    """Tracks one connected UDS client and its active request workers."""

    def __init__(self, conn: socket.socket, engine: MCPToolEngine, default_timeout_s: float) -> None:
        self.conn = conn
        self.engine = engine
        self.default_timeout_s = default_timeout_s
        self._send_lock = threading.Lock()
        self._active_lock = threading.Lock()
        self._active: dict[str, RequestContext] = {}
        self._workers: list[threading.Thread] = []
        self.closed = threading.Event()

    @staticmethod
    def _req_key(req_id: Any) -> str:
        return json.dumps(req_id, sort_keys=True)

    def send_json(self, obj: dict[str, Any]) -> bool:
        if self.closed.is_set():
            return False
        raw = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
        with self._send_lock:
            if self.closed.is_set():
                return False
            try:
                self.conn.sendall(raw)
                return True
            except OSError:
                return False

    def cancel_all(self) -> None:
        self.closed.set()
        with self._active_lock:
            ctxs = list(self._active.values())
        for ctx in ctxs:
            ctx.cancel()
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.conn.close()
        except OSError:
            pass

    def join_workers(self, timeout_s: float = 5.0) -> None:
        deadline = time.monotonic() + timeout_s
        with self._active_lock:
            threads = list(self._workers)
        for th in threads:
            rem = max(0.05, deadline - time.monotonic())
            th.join(timeout=rem)

    def _run_tool_worker(self, req_id: Any, req_key: str, params: Any, ctx: RequestContext) -> None:
        try:
            resp = self.engine.call_tool(req_id, params, ctx)
            if not ctx.cancel_event.is_set() and not self.closed.is_set():
                self.send_json(resp)
        except RequestCancelled:
            pass
        except Exception as exc:
            if not ctx.cancel_event.is_set() and not self.closed.is_set():
                self.send_json(self.engine.jsonrpc_err(req_id, -32603, f"Internal error: {type(exc).__name__}"))
        finally:
            with self._active_lock:
                self._active.pop(req_key, None)

    def _handle_message(self, raw_line: bytes) -> None:
        if len(raw_line) > MAX_LINE_BYTES:
            self.send_json(self.engine.jsonrpc_err(None, -32600, "Frame too large"))
            return
        try:
            msg = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(self.engine.jsonrpc_err(None, -32700, "Parse error"))
            return

        if isinstance(msg, dict) and msg.get("method") == "notifications/cancelled":
            params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
            if "requestId" in params:
                rk = self._req_key(params["requestId"])
                with self._active_lock:
                    ctx = self._active.get(rk)
                if ctx is not None:
                    ctx.cancel()
            return

        sync_resp, async_kind = self.engine.handle_sync_control(msg)
        if sync_resp is not None:
            self.send_json(sync_resp)
            return
        if async_kind == "tools/call":
            req_id = msg.get("id")
            rk = self._req_key(req_id)
            ctx = RequestContext(req_id, self.default_timeout_s)
            with self._active_lock:
                self._active[rk] = ctx
                th = threading.Thread(
                    target=self._run_tool_worker,
                    args=(req_id, rk, msg.get("params"), ctx),
                    daemon=True,
                )
                self._workers = [w for w in self._workers if w.is_alive()]
                self._workers.append(th)
            th.start()

    def serve(self) -> None:
        self.conn.settimeout(CONN_IDLE_READ_TIMEOUT)
        buf = bytearray()
        poller = select.poll()
        poller.register(self.conn.fileno(), select.POLLIN | select.POLLHUP | getattr(select, "POLLRDHUP", 0))
        read_eof = False
        try:
            while not self.closed.is_set():
                events = poller.poll(50 if read_eof else 500)
                hup = any(ev & (select.POLLHUP | select.POLLERR | select.POLLNVAL) for _, ev in events)
                if hup:
                    # Peer closed whole socket or was killed -> abort active workers immediately.
                    self.cancel_all()
                    break
                if read_eof:
                    with self._active_lock:
                        still_running = any(w.is_alive() for w in self._workers)
                    if not still_running:
                        break
                    continue
                if not any(ev & select.POLLIN for _, ev in events):
                    continue
                try:
                    chunk = self.conn.recv(65536)
                except BlockingIOError:
                    continue
                except OSError:
                    self.cancel_all()
                    break
                if not chunk:
                    # Half-close (SHUT_WR): let already-dispatched requests finish while watching for POLLHUP.
                    read_eof = True
                    poller.modify(self.conn.fileno(), select.POLLHUP | select.POLLERR)
                    continue
                buf.extend(chunk)
                if len(buf) > MAX_LINE_BYTES:
                    self.send_json(self.engine.jsonrpc_err(None, -32600, "Line buffer overflow"))
                    break
                while True:
                    nl = buf.find(b"\n")
                    if nl < 0:
                        break
                    line = bytes(buf[:nl]).rstrip(b"\r")
                    del buf[: nl + 1]
                    if line:
                        self._handle_message(line)
        finally:
            try:
                poller.unregister(self.conn.fileno())
            except (OSError, KeyError):
                pass
            if not read_eof:
                self.cancel_all()
            self.join_workers(timeout_s=5.0)
            self.closed.set()
            try:
                self.conn.close()
            except OSError:
                pass


class Hybrid2Daemon:
    """Single-instance AF_UNIX MCP server."""

    def __init__(
        self,
        sock_path: Path,
        pidfile: Path,
        log_path: Path | None,
        engine: MCPToolEngine,
        default_timeout_s: float,
    ) -> None:
        self.sock_path = sock_path
        self.pidfile = pidfile
        self.log_path = log_path
        self.engine = engine
        self.default_timeout_s = default_timeout_s
        self._stop_event = threading.Event()
        self._lock_fh: Any = None
        self._srv_sock: socket.socket | None = None
        self._sess_lock = threading.Lock()
        self._sessions: set[ClientSession] = set()
        self._log_lock = threading.Lock()

    def write_audit(self, entry: dict[str, Any]) -> None:
        if self.log_path is None:
            return
        payload = {"ts": round(time.time(), 3), **entry}
        line = json.dumps(payload, ensure_ascii=False) + "\n"
        with self._log_lock:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(line)

    def _acquire_pidfile(self) -> None:
        self.pidfile.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.pidfile, "a+", encoding="utf-8")
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            fh.close()
            raise RuntimeError("pidfile-locked") from exc
        fh.seek(0)
        fh.truncate()
        fh.write(f"{os.getpid()}\n")
        fh.flush()
        self._lock_fh = fh

    def _bind_socket(self) -> None:
        sdir = self.sock_path.parent
        sdir.mkdir(parents=True, exist_ok=True)
        os.chmod(sdir, 0o700)
        if self.sock_path.exists() or self.sock_path.is_symlink():
            self.sock_path.unlink()
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        old_umask = os.umask(0o177)
        try:
            srv.bind(str(self.sock_path))
        finally:
            os.umask(old_umask)
        os.chmod(self.sock_path, 0o600)
        srv.listen(64)
        srv.settimeout(0.5)
        self._srv_sock = srv

    def request_stop(self) -> None:
        self._stop_event.set()

    def _handle_client(self, conn: socket.socket) -> None:
        sess: ClientSession | None = None
        try:
            verify_peercred(conn)
            sess = ClientSession(conn, self.engine, self.default_timeout_s)
            with self._sess_lock:
                self._sessions.add(sess)
            sess.serve()
        except Refuse as exc:
            self.write_audit({"ev": "conn", "decision": "refuse", "reason": str(exc)})
            try:
                conn.close()
            except OSError:
                pass
        except OSError:
            try:
                conn.close()
            except OSError:
                pass
        finally:
            if sess is not None:
                with self._sess_lock:
                    self._sessions.discard(sess)

    def run(self) -> int:
        self._acquire_pidfile()
        self._bind_socket()
        self.write_audit({"ev": "daemon", "action": "start", "pid": os.getpid(), "tracer_pid": read_tracer_pid()})
        client_threads: list[threading.Thread] = []
        try:
            assert self._srv_sock is not None
            while not self._stop_event.is_set():
                try:
                    conn, _ = self._srv_sock.accept()
                except socket.timeout:
                    client_threads = [t for t in client_threads if t.is_alive()]
                    continue
                except OSError:
                    break
                th = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
                client_threads.append(th)
                th.start()
        finally:
            if self._srv_sock is not None:
                try:
                    self._srv_sock.close()
                except OSError:
                    pass
            with self._sess_lock:
                sessions = list(self._sessions)
            for sess in sessions:
                sess.cancel_all()
            for sess in sessions:
                sess.join_workers(timeout_s=5.0)
            for th in client_threads:
                th.join(timeout=2.0)
            try:
                if self.sock_path.exists() or self.sock_path.is_symlink():
                    self.sock_path.unlink()
            except OSError:
                pass
            if self._lock_fh is not None:
                try:
                    fcntl.flock(self._lock_fh.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
                try:
                    self._lock_fh.close()
                except OSError:
                    pass
            try:
                if self.pidfile.exists():
                    self.pidfile.unlink()
            except OSError:
                pass
            self.write_audit({"ev": "daemon", "action": "stop", "pid": os.getpid()})
        return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Stage 7.2 Native Hybrid 2.0 MCP UDS daemon")
    ap.add_argument("--socket", required=True, help="AF_UNIX socket path (<=107 bytes)")
    ap.add_argument(
        "--map",
        action="append",
        required=True,
        help="Path map GUEST_PREFIX=HOST_PREFIX (may repeat)",
    )
    ap.add_argument("--home", required=True, help="Clean HOME dir for native git subprocesses")
    ap.add_argument("--tmp", required=True, help="Clean TMPDIR for native git subprocesses")
    ap.add_argument("--pidfile", required=True, help="Pidfile path for single-instance flock")
    ap.add_argument("--log", default="", help="Optional sanitized audit JSONL log path")
    ap.add_argument("--git-bin", default="/data/data/com.termux/files/usr/bin/git", help="Native git binary path")
    ap.add_argument("--default-timeout", type=float, default=30.0, help="Default per-tool timeout (seconds)")
    ap.add_argument(
        "--skip-tracer-check",
        action="store_true",
        help="Skip TracerPid==0 assertion (ONLY for off-device/PRoot synthetic tests)",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        sock_path = validate_unix_sock_path(args.socket)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4

    if not args.skip_tracer_check:
        tpid = read_tracer_pid()
        if tpid != 0:
            print(f"error: daemon requires native execution (TracerPid={tpid}, expected 0)", file=sys.stderr)
            return 5

    maps: list[tuple[str, str]] = []
    for item in args.map:
        if "=" not in item:
            print(f"error: invalid --map {item!r}, expected GUEST=HOST", file=sys.stderr)
            return 2
        g, h = item.split("=", 1)
        maps.append((g, h))

    os.makedirs(args.home, exist_ok=True)
    os.makedirs(args.tmp, exist_ok=True)
    log_path = Path(args.log) if args.log else None
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    policy = Policy(maps=maps, home=args.home, tmp=args.tmp)
    daemon_holder: dict[str, Hybrid2Daemon] = {}

    def audit_cb(entry: dict[str, Any]) -> None:
        d = daemon_holder.get("d")
        if d is not None:
            d.write_audit(entry)

    engine = MCPToolEngine(
        policy=policy,
        git_bin=args.git_bin,
        default_timeout_s=args.default_timeout,
        audit_cb=audit_cb,
    )
    daemon = Hybrid2Daemon(
        sock_path=sock_path,
        pidfile=Path(args.pidfile),
        log_path=log_path,
        engine=engine,
        default_timeout_s=args.default_timeout,
    )
    daemon_holder["d"] = daemon

    def _on_sig(signum: int, _frame: Any) -> None:
        daemon.request_stop()

    signal.signal(signal.SIGTERM, _on_sig)
    signal.signal(signal.SIGINT, _on_sig)

    try:
        return daemon.run()
    except RuntimeError as exc:
        if str(exc) == "pidfile-locked":
            print(f"error: another daemon holds pidfile {args.pidfile}", file=sys.stderr)
            return 3
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
