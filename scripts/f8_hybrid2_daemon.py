#!/usr/bin/env python3
"""Native Termux persistent universal MCP JSON-RPC 2.0 daemon over AF_UNIX (Stage 7.2).

Intended to run outside PRoot (`TracerPid == 0`).
Supports multiple concurrent MCP clients with per-connection isolation,
backpressure (`--max-clients` / `--max-inflight`), duplicate active req_id
rejection, MCP `initialize` gating, atomic `.ready` marker, inode-verified
socket/pidfile self-check (`TermuxService` wipe defense), and race-free idle
auto-shutdown (`unlink` socket -> drain `accept()` backlog -> clean exit).
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

from f8_hybrid2_policy import (
    DEFAULT_DAEMON_MAPS,
    DEFAULT_PID_PATH,
    DEFAULT_READY_PATH,
    DEFAULT_SOCK_PATH,
    Policy,
    Refuse,
    parse_map_specs,
    read_tracer_pid,
    validate_unix_sock_path,
    verify_peercred,
)
from f8_hybrid2_tools import MCPToolEngine, RequestCancelled, RequestContext, cancellation_req_key, canonical_req_key

MAX_LINE_BYTES = 4 * 1024 * 1024
MAX_OUTBUF_BYTES = 4 * 1024 * 1024
MAX_OUTBUF_HARD_BYTES = 16 * 1024 * 1024
AUDIT_ROTATE_BYTES = 5 * 1024 * 1024


class ClientSession:
    """Tracks one connected UDS client, its initialization state, and non-blocking I/O loop."""

    def __init__(
        self,
        conn: socket.socket,
        daemon: Hybrid2Daemon,
        conn_id: int,
        peer_pid: int,
    ) -> None:
        self.conn = conn
        self.daemon = daemon
        self.engine = daemon.engine
        self.default_timeout_s = daemon.default_timeout_s
        self.conn_id = conn_id
        self.peer_pid = peer_pid
        self.initialized = False
        self._send_lock = threading.Lock()
        self._out_buf = bytearray()
        self._wake_r, self._wake_w = os.pipe()
        os.set_blocking(self._wake_r, False)
        os.set_blocking(self._wake_w, False)
        self._active_lock = threading.Lock()
        self._active: dict[str, RequestContext] = {}
        self._workers: list[threading.Thread] = []
        self.closed = threading.Event()

    def _wake(self) -> None:
        try:
            os.write(self._wake_w, b"\x01")
        except OSError:
            pass

    def send_json(self, obj: dict[str, Any], *, ctx: RequestContext | None = None, wake: bool = True) -> bool:
        raw = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
        with self._send_lock:
            if self.closed.is_set():
                return False
            if ctx is not None and ctx.cancel_event.is_set():
                return False
            if len(self._out_buf) + len(raw) > MAX_OUTBUF_HARD_BYTES:
                self.closed.set()
                return False
            self._out_buf.extend(raw)
        if wake:
            self._wake()
        return True

    def cancel_all(self) -> None:
        self.closed.set()
        with self._active_lock:
            ctxs = list(self._active.values())
        for ctx in ctxs:
            ctx.cancel()
        self._wake()
        # Only shutdown here; let serve()'s finally own conn.close() so FD reuse cannot race.
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def join_workers(self, timeout_s: float = 5.0) -> None:
        deadline = time.monotonic() + timeout_s
        with self._active_lock:
            threads = list(self._workers)
        for th in threads:
            rem = max(0.05, deadline - time.monotonic())
            th.join(timeout=rem)

    def _run_tool_worker(self, req_id: Any, rk: str, params: Any, ctx: RequestContext) -> None:
        resp_to_send: dict[str, Any] | None = None
        try:
            resp_to_send = self.engine.call_tool(req_id, params, ctx)
        except RequestCancelled:
            pass
        except Exception as exc:
            resp_to_send = self.engine.jsonrpc_err(req_id, -32603, f"Internal error: {type(exc).__name__}")
        finally:
            try:
                if resp_to_send is not None:
                    self.send_json(resp_to_send, ctx=ctx, wake=False)
            finally:
                self.daemon.release_inflight()
                with self._active_lock:
                    self._active.pop(rk, None)
                self.daemon.touch_activity()
                self._wake()

    def _handle_message(self, raw_line: bytes) -> None:
        self.daemon.touch_activity()
        if len(raw_line) > MAX_LINE_BYTES:
            self.send_json(self.engine.jsonrpc_err(None, -32600, "Frame too large"))
            return
        try:
            msg = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(self.engine.jsonrpc_err(None, -32700, "Parse error"))
            return

        if isinstance(msg, dict) and msg.get("method") == "notifications/cancelled":
            rk = cancellation_req_key(msg)
            if rk is not None:
                with self._active_lock:
                    ctx = self._active.get(rk)
                if ctx is not None:
                    ctx.cancel()
            elif "id" in msg:
                self.send_json(self.engine.jsonrpc_err(None, -32600, "Invalid cancellation"))
            return

        sync_resp, action = self.engine.handle_sync_control(msg, initialized=self.initialized)
        if action == "initialized":
            self.initialized = True
        if sync_resp is not None:
            self.send_json(sync_resp)
            return

        if action == "tools/call":
            req_id = msg.get("id")
            rk = canonical_req_key(req_id)
            if rk is None:
                self.send_json(self.engine.jsonrpc_err(None, -32600, "Invalid Request id"))
                return

            with self._active_lock:
                if rk in self._active:
                    self.send_json(self.engine.jsonrpc_err(req_id, -32600, "Duplicate active request id"))
                    return
                if not self.daemon.try_acquire_inflight():
                    self.daemon.write_audit(
                        {"ev": "tool", "conn_id": self.conn_id, "req_id": req_id, "decision": "refuse", "reason": "busy-max-inflight"}
                    )
                    self.send_json(self.engine.jsonrpc_err(req_id, -32000, "Server busy: max inflight requests reached"))
                    return

                ctx = RequestContext(req_id, self.default_timeout_s)
                self._active[rk] = ctx
                th = threading.Thread(
                    target=self._run_tool_worker,
                    args=(req_id, rk, msg.get("params"), ctx),
                    daemon=True,
                )
                self._workers = [w for w in self._workers if w.is_alive()]
                self._workers.append(th)
            try:
                th.start()
            except Exception:
                with self._active_lock:
                    self._active.pop(rk, None)
                    self._workers.remove(th)
                self.daemon.release_inflight()
                self._wake()
                raise

    def serve(self) -> None:
        buf = bytearray()
        self.conn.setblocking(False)
        conn_fd = self.conn.fileno()
        poller = select.poll()
        base_hup = select.POLLHUP | select.POLLERR | select.POLLNVAL
        cur_mask = select.POLLIN | base_hup
        poller.register(conn_fd, cur_mask)
        poller.register(self._wake_r, select.POLLIN)
        read_eof = False
        try:
            while not self.closed.is_set():
                # A finished worker has already queued its response. Check liveness
                # first so an empty buffer snapshot cannot precede its final enqueue.
                with self._active_lock:
                    still_running = any(w.is_alive() for w in self._workers)
                with self._send_lock:
                    out_len = len(self._out_buf)
                if read_eof and not still_running and out_len == 0:
                    break
                want_in = not read_eof and out_len < MAX_OUTBUF_BYTES
                want_out = out_len > 0
                desired = (select.POLLIN if want_in else 0) | (select.POLLOUT if want_out else 0) | base_hup
                if desired != cur_mask:
                    poller.modify(conn_fd, desired)
                    cur_mask = desired

                events = poller.poll(50 if read_eof else 500)
                if self.closed.is_set():
                    break
                for fd, ev in events:
                    if fd == self._wake_r:
                        try:
                            os.read(self._wake_r, 4096)
                        except OSError:
                            pass
                        continue
                    if fd != conn_fd:
                        continue
                    if ev & (select.POLLERR | select.POLLNVAL):
                        self.cancel_all()
                        break
                    if (ev & select.POLLHUP) and not (ev & select.POLLIN):
                        self.cancel_all()
                        break
                    if ev & select.POLLOUT:
                        with self._send_lock:
                            if self._out_buf:
                                try:
                                    sent = self.conn.send(self._out_buf)
                                    del self._out_buf[:sent]
                                except BlockingIOError:
                                    pass
                                except OSError:
                                    self.closed.set()
                                    break
                    if ev & select.POLLIN:
                        try:
                            chunk = self.conn.recv(65536)
                        except BlockingIOError:
                            continue
                        except OSError:
                            self.cancel_all()
                            break
                        if not chunk:
                            read_eof = True
                            continue
                        buf.extend(chunk)
                        if len(buf) > MAX_LINE_BYTES:
                            self.send_json(self.engine.jsonrpc_err(None, -32600, "Line buffer overflow"), wake=False)
                            read_eof = True
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
            for fd in (conn_fd, self._wake_r):
                try:
                    poller.unregister(fd)
                except (OSError, KeyError, ValueError):
                    pass
            if not read_eof:
                self.cancel_all()
            self.join_workers(timeout_s=5.0)
            self.closed.set()
            # Best-effort drain any small pending error/response if peer socket is still writable.
            try:
                with self._send_lock:
                    rem = bytes(self._out_buf)
                    self._out_buf.clear()
                if rem:
                    self.conn.setblocking(True)
                    self.conn.settimeout(0.2)
                    self.conn.sendall(rem)
            except OSError:
                pass
            for pfd in (self._wake_r, self._wake_w):
                try:
                    os.close(pfd)
                except OSError:
                    pass
            try:
                self.conn.close()
            except OSError:
                pass


class Hybrid2Daemon:
    """Single-instance universal AF_UNIX MCP server with idle auto-shutdown and backpressure."""

    def __init__(
        self,
        sock_path: Path,
        pidfile: Path,
        ready_path: Path,
        log_path: Path | None,
        engine: MCPToolEngine,
        default_timeout_s: float,
        idle_timeout_s: float = 0.0,
        max_clients: int = 32,
        max_inflight: int = 16,
    ) -> None:
        self.sock_path = sock_path
        self.pidfile = pidfile
        self.ready_path = ready_path
        self.log_path = log_path
        self.engine = engine
        self.default_timeout_s = default_timeout_s
        self.idle_timeout_s = max(0.0, float(idle_timeout_s))
        self.max_clients = max(1, int(max_clients))
        self.max_inflight = max(1, int(max_inflight))

        self._stop_event = threading.Event()
        self._lock_fh: Any = None
        self._pid_ino: int | None = None
        self._sock_ino: int | None = None
        self._ready_ino: int | None = None
        self._srv_sock: socket.socket | None = None
        self._sess_lock = threading.Lock()
        self._sessions: set[ClientSession] = set()
        self._next_conn_id = 1
        self._inflight_lock = threading.Lock()
        self._inflight = 0
        self._last_active = time.monotonic()
        self._log_lock = threading.Lock()
        self._idle_exiting = False

    def touch_activity(self) -> None:
        self._last_active = time.monotonic()

    def try_acquire_inflight(self) -> bool:
        with self._inflight_lock:
            if self._inflight >= self.max_inflight:
                return False
            self._inflight += 1
            return True

    def release_inflight(self) -> None:
        with self._inflight_lock:
            self._inflight = max(0, self._inflight - 1)

    def write_audit(self, entry: dict[str, Any]) -> None:
        if self.log_path is None:
            return
        payload = {"ts": round(time.time(), 3), **entry}
        line = json.dumps(payload, ensure_ascii=False) + "\n"
        with self._log_lock:
            try:
                if self.log_path.exists() and self.log_path.stat().st_size >= AUDIT_ROTATE_BYTES:
                    backup = Path(str(self.log_path) + ".1")
                    os.replace(self.log_path, backup)
                with open(self.log_path, "a", encoding="utf-8") as fh:
                    fh.write(line)
            except OSError:
                pass

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
        self._pid_ino = os.fstat(fh.fileno()).st_ino
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
        srv.settimeout(0.25)
        self._sock_ino = os.stat(self.sock_path).st_ino
        self._srv_sock = srv

    def _write_ready_marker(self) -> None:
        self.ready_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ready_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "tracer_pid": read_tracer_pid(),
                    "sock_ino": self._sock_ino,
                    "pid_ino": self._pid_ino,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.ready_path)
        try:
            self._ready_ino = self.ready_path.stat().st_ino
        except OSError:
            self._ready_ino = None

    def _inodes_still_owned(self) -> bool:
        """Detect external unlink/replacement (split-brain defense)."""
        try:
            if self._sock_ino is None or self.sock_path.stat().st_ino != self._sock_ino:
                return False
            if self._pid_ino is None or self.pidfile.stat().st_ino != self._pid_ino:
                return False
        except OSError:
            return False
        return True

    def _unlink_owned_files(self) -> None:
        try:
            if self._sock_ino is not None and self.sock_path.exists() and self.sock_path.stat().st_ino == self._sock_ino:
                self.sock_path.unlink()
        except OSError:
            pass
        try:
            if self._ready_ino is not None and self.ready_path.exists() and self.ready_path.stat().st_ino == self._ready_ino:
                self.ready_path.unlink()
        except OSError:
            pass

    def _release_pidfile(self) -> None:
        try:
            if self._pid_ino is not None and self.pidfile.exists() and self.pidfile.stat().st_ino == self._pid_ino:
                self.pidfile.unlink()
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
            self._lock_fh = None

    def request_stop(self) -> None:
        self._stop_event.set()

    def _spawn_client_thread(self, conn: socket.socket, client_threads: list[threading.Thread]) -> None:
        self.touch_activity()
        # Only the accept loop mutates this list, including during backlog drain.
        client_threads[:] = [thread for thread in client_threads if thread.is_alive()]
        if len(client_threads) >= self.max_clients:
            self.write_audit({"ev": "conn", "decision": "refuse", "reason": "max-clients"})
            try:
                conn.setblocking(False)
                conn.send((json.dumps(self.engine.jsonrpc_err(None, -32000, "Server busy: max clients reached")) + "\n").encode("utf-8"))
            except OSError:
                pass
            finally:
                conn.close()
            return
        try:
            th = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
            th.start()
        except (RuntimeError, OSError):
            conn.close()
            self.write_audit({"ev": "conn", "decision": "refuse", "reason": "thread-start-failed"})
            return
        client_threads.append(th)

    def _handle_client(self, conn: socket.socket) -> None:
        sess: ClientSession | None = None
        conn_id = 0
        try:
            peer_pid, _, _ = verify_peercred(conn)
            with self._sess_lock:
                conn_id = self._next_conn_id
                self._next_conn_id += 1
                sess = ClientSession(conn, self, conn_id, peer_pid)
                self._sessions.add(sess)
            self.write_audit({"ev": "conn", "decision": "open", "conn_id": conn_id, "peer_pid": peer_pid})
            sess.serve()
        except Refuse as exc:
            self.write_audit({"ev": "conn", "decision": "refuse", "reason": str(exc)})
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass
            if sess is not None:
                with self._sess_lock:
                    self._sessions.discard(sess)
                self.touch_activity()
                self.write_audit({"ev": "conn", "decision": "close", "conn_id": conn_id})

    def _drain_accept_backlog(self, client_threads: list[threading.Thread]) -> None:
        """Accept any peers already queued in listen(64) before closing srv_sock."""
        assert self._srv_sock is not None
        self._srv_sock.setblocking(False)
        while True:
            try:
                conn, _ = self._srv_sock.accept()
            except BlockingIOError:
                break
            except OSError:
                break
            self._spawn_client_thread(conn, client_threads)

    def run(self) -> int:
        self._acquire_pidfile()
        self._bind_socket()
        self._write_ready_marker()
        self.touch_activity()
        last_ino_check = time.monotonic()
        self.write_audit(
            {
                "ev": "daemon",
                "action": "start",
                "pid": os.getpid(),
                "tracer_pid": read_tracer_pid(),
                "idle_timeout_s": self.idle_timeout_s,
                "max_clients": self.max_clients,
                "max_inflight": self.max_inflight,
            }
        )
        client_threads: list[threading.Thread] = []
        stop_reason = "signal"
        try:
            assert self._srv_sock is not None
            while not self._stop_event.is_set():
                client_threads = [t for t in client_threads if t.is_alive()]
                try:
                    conn, _ = self._srv_sock.accept()
                    self._spawn_client_thread(conn, client_threads)
                    continue
                except socket.timeout:
                    pass
                except OSError:
                    break

                now = time.monotonic()
                if now - last_ino_check >= 5.0:
                    last_ino_check = now
                    if not self._inodes_still_owned():
                        stop_reason = "inode-replaced"
                        self.write_audit({"ev": "daemon", "action": "inode-lost"})
                        break

                if self.idle_timeout_s > 0.0:
                    with self._sess_lock:
                        sess_cnt = len(self._sessions)
                    with self._inflight_lock:
                        inflight_cnt = self._inflight
                    if sess_cnt == 0 and inflight_cnt == 0 and (now - self._last_active) >= self.idle_timeout_s:
                        # Race-free idle exit: unlink sock+ready, drain backlog, immediately free pidfile
                        # so concurrent ctl start can bind a new daemon with zero lock delay, then let
                        # drained connections finish cleanly without hard cutoff!
                        self._unlink_owned_files()
                        self._drain_accept_backlog(client_threads)
                        try:
                            self._srv_sock.close()
                        except OSError:
                            pass
                        self._srv_sock = None
                        self._release_pidfile()
                        stop_reason = "idle-timeout"
                        self._idle_exiting = True
                        while not self._stop_event.is_set() and any(t.is_alive() for t in client_threads):
                            for th in list(client_threads):
                                th.join(timeout=0.2)
                            client_threads = [t for t in client_threads if t.is_alive()]
                        break
        finally:
            self._unlink_owned_files()
            if self._srv_sock is not None:
                try:
                    self._srv_sock.close()
                except OSError:
                    pass
            if (not self._idle_exiting and stop_reason != "idle-timeout") or self._stop_event.is_set():
                with self._sess_lock:
                    sessions = list(self._sessions)
                for sess in sessions:
                    sess.cancel_all()
                for sess in sessions:
                    sess.join_workers(timeout_s=5.0)
            for th in client_threads:
                th.join(timeout=2.0)
            self._release_pidfile()
            self.write_audit({"ev": "daemon", "action": "stop", "pid": os.getpid(), "reason": stop_reason})
        return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Stage 7.2 Native Hybrid 2.0 universal MCP UDS daemon")
    ap.add_argument("--socket", default=DEFAULT_SOCK_PATH, help="AF_UNIX socket path (<=107 bytes)")
    ap.add_argument("--map", action="append", default=[], help="Path map GUEST=HOST (repeatable)")
    ap.add_argument("--home", required=True, help="Clean HOME dir for native git subprocesses")
    ap.add_argument("--tmp", required=True, help="Clean TMPDIR for native git subprocesses")
    ap.add_argument("--pidfile", default=DEFAULT_PID_PATH, help="Pidfile path for single-instance flock")
    ap.add_argument("--ready", default="", help="Ready marker path (defaults next to socket)")
    ap.add_argument("--log", default="", help="Optional sanitized audit JSONL log path")
    ap.add_argument("--git-bin", default="/data/data/com.termux/files/usr/bin/git", help="Native git binary path")
    ap.add_argument("--default-timeout", type=float, default=30.0, help="Default per-tool timeout (seconds)")
    ap.add_argument("--idle-timeout", type=float, default=0.0, help="Idle auto-shutdown seconds (0 disables)")
    ap.add_argument("--max-clients", type=int, default=32, help="Max concurrent UDS client sessions")
    ap.add_argument("--max-inflight", type=int, default=16, help="Max concurrent inflight tool executions")
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

    if (sock_path.parent / "disabled.flag").exists():
        print("error: global disabled.flag is active; refusing daemon start", file=sys.stderr)
        return 6

    maps = parse_map_specs(args.map, DEFAULT_DAEMON_MAPS)
    os.makedirs(args.home, exist_ok=True)
    os.makedirs(args.tmp, exist_ok=True)
    log_path = Path(args.log) if args.log else None
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    ready_path = Path(args.ready) if args.ready else (sock_path.parent / Path(DEFAULT_READY_PATH).name)

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
        ready_path=ready_path,
        log_path=log_path,
        engine=engine,
        default_timeout_s=args.default_timeout,
        idle_timeout_s=args.idle_timeout,
        max_clients=args.max_clients,
        max_inflight=args.max_inflight,
    )
    daemon_holder["d"] = daemon

    def _on_sig(_signum: int, _frame: Any) -> None:
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
