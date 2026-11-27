#!/usr/bin/env python3
"""Shared MCP JSON-RPC 2.0 dispatcher and read-only tool implementations for Stage 7.2.

Used both by the native Termux UDS daemon (`f8_hybrid2_daemon.py`) and by the
local PRoot fallback path inside `f8_hybrid2_relay.py`.
Upgraded per Stage 7.2 universal audit:
- Enforces MCP `initialize` state machine (`-32002` before initialization)
- Supports pidfd_open + wakeup-pipe `select.poll()` in `git_ro` (<1ms cancel/exit)
- Uses O_NOFOLLOW + chunked reads + JSON size caps + regex line cap (anti-OOM/ReDoS)
- UTF-8 byte-safe payload trimming inside valid JSON (`truncated: true`)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import select
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from f8_hybrid2_policy import Policy, Refuse, open_nofollow, pidfd_open

_MAY_BACKTRACK_RE = re.compile(r"[*+?{|]")

SUPPORTED_PROTOCOL_VERSIONS = (
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)
DEFAULT_PROTOCOL_VERSION = "2025-03-26"
MAX_TEXT_BYTES = 1024 * 1024  # 1 MiB UTF-8 cap
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_JSON_DOC_BYTES = 16 * 1024 * 1024
MAX_JSONL_BYTES = 32 * 1024 * 1024
MAX_JSONL_LINE_BYTES = 1024 * 1024
MAX_SEARCH_FILE_BYTES = 2 * 1024 * 1024
MAX_SEARCH_LINE_CHARS = 4096
MAX_REGEX_CHARS = 512

TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "repo_tree_scan",
        "description": "Read-only deterministic directory walk with file counts, byte total, and SHA-256 tree digest.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "description": "Mapped directory path to scan."},
                "max_entries": {"type": "integer", "minimum": 1, "maximum": 50000, "default": 2000},
                "compute_sha256": {"type": "boolean", "default": True},
                "exclude_git": {"type": "boolean", "default": True},
                "timeout_s": {"type": "number", "minimum": 0.001, "maximum": 120.0},
            },
            "required": ["root"],
        },
    },
    {
        "name": "repo_text_search",
        "description": "Read-only regex or fixed-string text search across files inside mapped workspaces.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "description": "Mapped directory or file path to search."},
                "pattern": {"type": "string", "description": "Search pattern."},
                "fixed_string": {"type": "boolean", "default": False},
                "case_sensitive": {"type": "boolean", "default": True},
                "max_matches": {"type": "integer", "minimum": 1, "maximum": 5000, "default": 200},
                "include_ext": {"type": "array", "items": {"type": "string"}},
                "timeout_s": {"type": "number", "minimum": 0.001, "maximum": 120.0},
            },
            "required": ["root", "pattern"],
        },
    },
    {
        "name": "git_ro",
        "description": "Read-only allowlisted git subcommands (status, diff, log, show, rev-parse, ls-files, etc.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cwd": {"type": "string", "description": "Mapped repository directory."},
                "args": {"type": "array", "items": {"type": "string"}, "description": "Git arguments."},
                "timeout_s": {"type": "number", "minimum": 0.001, "maximum": 120.0},
            },
            "required": ["cwd", "args"],
        },
    },
    {
        "name": "python_json_summary",
        "description": "Read-only summary and SHA-256 verification of .json or .jsonl files inside mapped workspaces.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Mapped path to a .json or .jsonl file."},
                "limit_records": {"type": "integer", "minimum": 1, "maximum": 200000, "default": 50000},
                "timeout_s": {"type": "number", "minimum": 0.001, "maximum": 120.0},
            },
            "required": ["path"],
        },
    },
]


class RequestCancelled(Exception):
    """Raised when an in-flight request was cancelled via notifications/cancelled or disconnect."""


class RequestTimeout(Exception):
    """Raised when a tool invocation exceeds its execution deadline."""


class RequestContext:
    """Per-request cancellation, timeout deadline, wakeup pipe, and subprocess pgid tracker."""

    def __init__(self, req_id: Any, timeout_s: float) -> None:
        self.req_id = req_id
        self.cancel_event = threading.Event()
        self.timed_out = False
        self.deadline = time.monotonic() + max(0.001, float(timeout_s))
        self._lock = threading.Lock()
        self._proc_pgid: int | None = None
        self._wake_w: int | None = None

    def attach_wake_fd(self, w_fd: int | None) -> None:
        with self._lock:
            self._wake_w = w_fd
            if w_fd is not None and self.cancel_event.is_set():
                try:
                    os.write(w_fd, b"\x01")
                except OSError:
                    pass

    def set_proc(self, proc: subprocess.Popen[bytes] | None) -> None:
        with self._lock:
            self._proc_pgid = proc.pid if proc is not None else None
            if proc is not None and self.cancel_event.is_set():
                self._kill_pgid(proc.pid)

    @staticmethod
    def _kill_pgid(pgid: int) -> None:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError:
            try:
                os.kill(pgid, signal.SIGKILL)
            except OSError:
                pass

    def cancel(self) -> None:
        # Hold _lock while signaling pgid and wake_w so attach_wake_fd(None)+close() cannot race.
        with self._lock:
            self.cancel_event.set()
            if self._proc_pgid is not None:
                self._kill_pgid(self._proc_pgid)
            if self._wake_w is not None:
                try:
                    os.write(self._wake_w, b"\x01")
                except OSError:
                    pass

    def check(self) -> None:
        if self.cancel_event.is_set():
            raise RequestCancelled("cancelled")
        if time.monotonic() > self.deadline:
            with self._lock:
                self.timed_out = True
                if self._proc_pgid is not None:
                    self._kill_pgid(self._proc_pgid)
            raise RequestTimeout("timeout")


def canonical_req_key(req_id: Any) -> str | None:
    """Strictly validate JSON-RPC request id (str or int, excluding bool) and normalize key."""
    if isinstance(req_id, bool) or not isinstance(req_id, (str, int)):
        return None
    kind = "s" if isinstance(req_id, str) else "i"
    return f"{kind}:{req_id}"


def cancellation_req_key(msg: Any) -> str | None:
    """Return the target only for a valid JSON-RPC cancellation notification."""
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or "id" in msg:
        return None
    if msg.get("method") != "notifications/cancelled":
        return None
    params = msg.get("params")
    if not isinstance(params, dict) or "requestId" not in params:
        return None
    return canonical_req_key(params["requestId"])


def _strict_int_arg(args: dict[str, Any], key: str, default: int, lo: int, hi: int) -> int:
    if key not in args:
        return default
    val = args[key]
    if isinstance(val, bool) or not isinstance(val, int):
        raise Refuse(f"bad-{key}")
    return max(lo, min(val, hi))


def _fit_json_payload(payload: dict[str, Any], limit_bytes: int = MAX_TEXT_BYTES) -> str:
    """Serialize payload cleanly within UTF-8 byte budget without breaking JSON syntax."""
    text = json.dumps(payload, ensure_ascii=False)
    if len(text.encode("utf-8")) <= limit_bytes:
        return text

    trimmed = dict(payload)
    trimmed["truncated"] = True
    for list_key in ("entries", "matches"):
        if list_key in trimmed and isinstance(trimmed[list_key], list):
            items = trimmed[list_key]
            lo, hi = 0, len(items)
            best = 0
            while lo <= hi:
                mid = (lo + hi) // 2
                trimmed[list_key] = items[:mid]
                cand = json.dumps(trimmed, ensure_ascii=False)
                if len(cand.encode("utf-8")) <= limit_bytes:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            trimmed[list_key] = items[:best]
            return json.dumps(trimmed, ensure_ascii=False)

    if any(k in trimmed and isinstance(trimmed[k], str) for k in ("stdout", "stderr")):
        for str_key in ("stdout", "stderr"):
            if str_key in trimmed and isinstance(trimmed[str_key], str):
                other_key = "stderr" if str_key == "stdout" else "stdout"
                saved_other = trimmed.get(other_key, "")
                # Iteratively halve whichever string fields exceed budget until combined JSON fits.
                cand = json.dumps(trimmed, ensure_ascii=False)
                while len(cand.encode("utf-8")) > limit_bytes and trimmed[str_key]:
                    cur = trimmed[str_key]
                    trimmed[str_key] = cur[: len(cur) // 2]
                    cand = json.dumps(trimmed, ensure_ascii=False)
                if len(cand.encode("utf-8")) <= limit_bytes:
                    return cand
                if isinstance(saved_other, str) and not trimmed.get(other_key):
                    continue
        cand = json.dumps(trimmed, ensure_ascii=False)
        if len(cand.encode("utf-8")) <= limit_bytes:
            return cand

    return json.dumps({"tool": payload.get("tool"), "truncated": True, "error": "output-too-large"})


class MCPToolEngine:
    """Stateless-per-call MCP JSON-RPC engine backed by strict Policy checks."""

    def __init__(
        self,
        policy: Policy,
        git_bin: str = "/data/data/com.termux/files/usr/bin/git",
        default_timeout_s: float = 30.0,
        audit_cb: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.policy = policy
        self.git_bin = git_bin
        self.default_timeout_s = default_timeout_s
        self.audit_cb = audit_cb

    def _audit(self, **fields: Any) -> None:
        if self.audit_cb is not None:
            self.audit_cb(fields)

    @staticmethod
    def negotiate_protocol(client_version: str | None) -> str:
        if isinstance(client_version, str) and client_version in SUPPORTED_PROTOCOL_VERSIONS:
            return client_version
        return DEFAULT_PROTOCOL_VERSION

    @staticmethod
    def jsonrpc_ok(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def jsonrpc_err(req_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    def handle_sync_control(
        self, msg: dict[str, Any], *, initialized: bool = True
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Handle control JSON-RPC methods and enforce initialize gating."""
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            raw_id = msg.get("id") if isinstance(msg, dict) else None
            return self.jsonrpc_err(raw_id if canonical_req_key(raw_id) is not None else None, -32600, "Invalid Request"), None

        method = msg.get("method")
        has_id = "id" in msg
        req_id = msg.get("id")
        if has_id and canonical_req_key(req_id) is None:
            return self.jsonrpc_err(None, -32600, "Invalid Request id"), None

        if not isinstance(method, str) or not method:
            return (None if not has_id else self.jsonrpc_err(req_id, -32600, "Missing method")), None

        if method == "initialize":
            if not has_id:
                return None, None
            params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
            proto = self.negotiate_protocol(params.get("protocolVersion"))
            return self.jsonrpc_ok(
                req_id,
                {
                    "protocolVersion": proto,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "f8-hybrid2", "version": "0.2.0"},
                },
            ), "initialized"

        if method == "notifications/initialized":
            return None, "initialized"

        if method == "ping":
            return (None if not has_id else self.jsonrpc_ok(req_id, {})), None

        if not initialized:
            return (None if not has_id else self.jsonrpc_err(req_id, -32002, "Server not initialized")), None

        if method == "tools/list":
            return (None if not has_id else self.jsonrpc_ok(req_id, {"tools": TOOL_DEFS})), None

        if method == "tools/call":
            if not has_id:
                return None, None
            return None, "tools/call"

        if not has_id:
            return None, None
        return self.jsonrpc_err(req_id, -32601, f"Method not found: {method}"), None

    def call_tool(self, req_id: Any, params: Any, ctx: RequestContext) -> dict[str, Any]:
        """Execute a validated read-only tool call under ctx cancellation & timeout."""
        t0 = time.monotonic()
        if not isinstance(params, dict):
            return self.jsonrpc_err(req_id, -32602, "Invalid params")
        name = params.get("name")
        args = params.get("arguments")
        if args is None:
            args = {}
        if not isinstance(name, str) or not isinstance(args, dict):
            return self.jsonrpc_err(req_id, -32602, "Invalid tool call params")

        raw_timeout = args.get("timeout_s")
        if isinstance(raw_timeout, (int, float)) and not isinstance(raw_timeout, bool) and raw_timeout > 0:
            ctx.deadline = min(ctx.deadline, t0 + float(raw_timeout))

        try:
            if name == "repo_tree_scan":
                payload = self._tool_tree_scan(args, ctx)
            elif name == "repo_text_search":
                payload = self._tool_text_search(args, ctx)
            elif name == "git_ro":
                payload = self._tool_git_ro(args, ctx)
            elif name == "python_json_summary":
                payload = self._tool_json_summary(args, ctx)
            else:
                self._audit(ev="tool", req_id=req_id, tool=name, decision="refuse", reason="unknown-tool")
                return self.jsonrpc_err(req_id, -32602, f"Unknown tool: {name}")
        except Refuse as exc:
            elapsed_ms = round((time.monotonic() - t0) * 1000.0, 2)
            self._audit(ev="tool", req_id=req_id, tool=name, decision="refuse", reason=str(exc), elapsed_ms=elapsed_ms)
            return self.jsonrpc_err(req_id, -32602, f"Policy refused: {exc}")
        except RequestTimeout:
            elapsed_ms = round((time.monotonic() - t0) * 1000.0, 2)
            self._audit(ev="tool", req_id=req_id, tool=name, decision="timeout", elapsed_ms=elapsed_ms)
            return self.jsonrpc_err(req_id, -32001, f"Tool '{name}' timed out")
        except RequestCancelled:
            elapsed_ms = round((time.monotonic() - t0) * 1000.0, 2)
            self._audit(ev="tool", req_id=req_id, tool=name, decision="cancelled", elapsed_ms=elapsed_ms)
            raise
        except OSError as exc:
            elapsed_ms = round((time.monotonic() - t0) * 1000.0, 2)
            self._audit(ev="tool", req_id=req_id, tool=name, decision="error", reason=type(exc).__name__, elapsed_ms=elapsed_ms)
            return self.jsonrpc_ok(
                req_id,
                {"content": [{"type": "text", "text": json.dumps({"error": str(exc)})}], "isError": True},
            )

        text = _fit_json_payload(payload, MAX_TEXT_BYTES)
        elapsed_ms = round((time.monotonic() - t0) * 1000.0, 2)
        self._audit(
            ev="tool",
            req_id=req_id,
            tool=name,
            decision="ok",
            elapsed_ms=elapsed_ms,
            bytes_out=len(text.encode("utf-8")),
        )
        return self.jsonrpc_ok(
            req_id,
            {
                "content": [{"type": "text", "text": text}],
                "isError": False,
            },
        )

    def _tool_tree_scan(self, args: dict[str, Any], ctx: RequestContext) -> dict[str, Any]:
        guest_root = args.get("root")
        if not isinstance(guest_root, str):
            raise Refuse("bad-root")
        host_root = self.policy.map_path(guest_root, cwd="/", must_exist=True)
        if not os.path.isdir(host_root):
            raise Refuse("root-not-dir")

        max_entries = _strict_int_arg(args, "max_entries", 2000, 1, 50000)
        compute_sha = bool(args.get("compute_sha256", True))
        exclude_git = bool(args.get("exclude_git", True))

        file_count = 0
        total_bytes = 0
        digest = hashlib.sha256() if compute_sha else None
        entries: list[dict[str, Any]] = []
        truncated = False

        for dirpath, dirnames, filenames in os.walk(host_root, followlinks=False):
            ctx.check()
            dirnames[:] = sorted(
                d for d in dirnames
                if not d.startswith(".l2s.") and not (exclude_git and d == ".git")
            )
            for fname in sorted(filenames):
                ctx.check()
                if fname.startswith(".l2s."):
                    continue
                full = os.path.join(dirpath, fname)
                if os.path.islink(full):
                    continue
                rel = os.path.relpath(full, host_root)
                try:
                    if compute_sha:
                        size = 0
                        assert digest is not None
                        digest.update(rel.encode("utf-8", errors="replace"))
                        digest.update(b"\0")
                        with open_nofollow(full) as fh:
                            while chunk := fh.read(262144):
                                ctx.check()
                                size += len(chunk)
                                digest.update(chunk)
                    else:
                        size = os.lstat(full).st_size
                except OSError:
                    continue
                file_count += 1
                total_bytes += size
                if len(entries) < max_entries:
                    entries.append({"rel": rel, "size": size})
                else:
                    truncated = True

        return {
            "tool": "repo_tree_scan",
            "root": guest_root,
            "file_count": file_count,
            "total_bytes": total_bytes,
            "digest_sha256": digest.hexdigest() if digest is not None else None,
            "truncated": truncated,
            "entries": entries,
        }

    def _run_text_search_sync(
        self,
        host_root: str,
        guest_root: str,
        pattern: str,
        fixed: bool,
        case_sensitive: bool,
        max_matches: int,
        exts: tuple[str, ...] | None,
        ctx: RequestContext,
    ) -> dict[str, Any]:
        if fixed:
            needle = pattern if case_sensitive else pattern.lower()
            rx = None
        else:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                rx = re.compile(pattern, flags)
            except re.error as exc:
                raise Refuse(f"bad-regex: {exc}") from exc
            needle = ""

        matches: list[dict[str, Any]] = []
        files_scanned = 0
        skipped_oversize = 0
        truncated = False

        def scan_file(fpath: str, rel: str) -> None:
            nonlocal files_scanned, skipped_oversize, truncated
            ctx.check()
            if exts is not None and not any(rel.endswith(e) for e in exts):
                return
            try:
                with open_nofollow(fpath) as fh:
                    raw = fh.read(MAX_SEARCH_FILE_BYTES + 1)
            except OSError:
                return
            if len(raw) > MAX_SEARCH_FILE_BYTES:
                skipped_oversize += 1
                truncated = True
                return
            if b"\x00" in raw:
                return
            files_scanned += 1
            text = raw.decode("utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), 1):
                if lineno % 256 == 0:
                    ctx.check()
                slice_line = line[:MAX_SEARCH_LINE_CHARS]
                hit = (
                    (needle in (slice_line if case_sensitive else slice_line.lower()))
                    if fixed
                    else bool(rx.search(slice_line))
                )
                if hit:
                    if len(matches) >= max_matches:
                        truncated = True
                        return
                    matches.append({"file": rel, "line": lineno, "text": slice_line[:300]})

        if os.path.isfile(host_root):
            scan_file(host_root, os.path.basename(host_root))
        else:
            for dirpath, dirnames, filenames in os.walk(host_root, followlinks=False):
                ctx.check()
                dirnames[:] = sorted(d for d in dirnames if not d.startswith(".l2s.") and d != ".git")
                for fname in sorted(filenames):
                    if fname.startswith(".l2s."):
                        continue
                    full = os.path.join(dirpath, fname)
                    if os.path.islink(full):
                        continue
                    scan_file(full, os.path.relpath(full, host_root))
                    if truncated and len(matches) >= max_matches:
                        break
                if truncated and len(matches) >= max_matches:
                    break

        return {
            "tool": "repo_text_search",
            "root": guest_root,
            "files_scanned": files_scanned,
            "skipped_oversize": skipped_oversize,
            "match_count": len(matches),
            "truncated": truncated,
            "matches": matches,
        }

    def _run_supervised_popen(
        self,
        cmd: list[str],
        cwd: str,
        env: dict[str, str],
        ctx: RequestContext,
        stdin_bytes: bytes | None = None,
    ) -> tuple[int, bytes, bytes]:
        """Drain bounded pipes while supervising cancellation, deadline and child exit."""
        wake_r, wake_w = os.pipe()
        os.set_blocking(wake_r, False)
        os.set_blocking(wake_w, False)
        ctx.attach_wake_fd(wake_w)
        pfd = -1
        proc: subprocess.Popen[bytes] | None = None
        try:
            with tempfile.TemporaryFile(mode="w+b") as in_f:
                if stdin_bytes is not None:
                    in_f.write(stdin_bytes)
                    in_f.seek(0)
                proc = subprocess.Popen(
                    cmd, cwd=cwd, env=env,
                    stdin=in_f if stdin_bytes is not None else subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    shell=False, start_new_session=True,
                )
                ctx.set_proc(proc)
                try:
                    pfd = pidfd_open(proc.pid)
                    poller = select.poll()
                    poller.register(wake_r, select.POLLIN)
                    if pfd >= 0:
                        poller.register(pfd, select.POLLIN)
                    assert proc.stdout is not None and proc.stderr is not None
                    streams = {proc.stdout.fileno(): (bytearray(), MAX_OUTPUT_BYTES),
                               proc.stderr.fileno(): (bytearray(), 256 * 1024)}
                    outputs = list(streams.values())
                    for fd in streams:
                        os.set_blocking(fd, False)
                        poller.register(fd, select.POLLIN | select.POLLHUP | select.POLLERR)
                    while True:
                        ctx.check()
                        rc = proc.poll()
                        if rc is not None and not streams:
                            ctx.check()
                            return rc, bytes(outputs[0][0]), bytes(outputs[1][0])
                        rem_ms = max(1, int((ctx.deadline - time.monotonic()) * 1000.0))
                        for fd, _events in poller.poll(min(rem_ms, 10) if pfd < 0 else rem_ms):
                            if fd == pfd:
                                poller.unregister(pfd)
                                continue
                            if fd not in streams:
                                continue
                            buf, limit = streams[fd]
                            try:
                                chunk = os.read(fd, min(65536, limit - len(buf) + 1))
                            except BlockingIOError:
                                continue
                            if not chunk:
                                poller.unregister(fd)
                                del streams[fd]
                            elif len(buf) + len(chunk) > limit:
                                raise Refuse("subprocess-output-limit")
                            else:
                                buf.extend(chunk)
                except BaseException:
                    RequestContext._kill_pgid(proc.pid)
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        pass
                    raise
                finally:
                    ctx.set_proc(None)
                    if proc.stdout is not None:
                        proc.stdout.close()
                    if proc.stderr is not None:
                        proc.stderr.close()
        finally:
            ctx.attach_wake_fd(None)
            if pfd >= 0:
                os.close(pfd)
            os.close(wake_r)
            os.close(wake_w)

    def _tool_text_search(self, args: dict[str, Any], ctx: RequestContext) -> dict[str, Any]:
        guest_root = args.get("root")
        pattern = args.get("pattern")
        if not isinstance(guest_root, str) or not isinstance(pattern, str) or not pattern:
            raise Refuse("bad-search-args")
        if len(pattern) > MAX_REGEX_CHARS:
            raise Refuse("pattern-too-long")
        host_root = self.policy.map_path(guest_root, cwd="/", must_exist=True)
        fixed = bool(args.get("fixed_string", False))
        case_sensitive = bool(args.get("case_sensitive", True))
        max_matches = _strict_int_arg(args, "max_matches", 200, 1, 5000)
        raw_exts = args.get("include_ext")
        exts: tuple[str, ...] | None = None
        if isinstance(raw_exts, list) and raw_exts:
            exts = tuple(str(x) for x in raw_exts if isinstance(x, str))

        if not fixed:
            try:
                re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
            except re.error as exc:
                raise Refuse(f"bad-regex: {exc}") from exc

        # Any regex with backtracking metacharacters runs in an isolated subprocess
        # so ReDoS cannot stall the daemon GIL and is killpg'd cleanly on timeout/cancel.
        if not fixed and _MAY_BACKTRACK_RE.search(pattern):
            req_blob = json.dumps(
                {
                    "host_root": host_root,
                    "guest_root": guest_root,
                    "pattern": pattern,
                    "case_sensitive": case_sensitive,
                    "max_matches": max_matches,
                    "exts": list(exts) if exts is not None else None,
                }
            ).encode("utf-8")
            rc, stdout_b, _stderr_b = self._run_supervised_popen(
                [sys.executable, str(Path(__file__).resolve()), "--regex-worker"],
                cwd=self.policy.tmp,
                env=self.policy.clean_env(),
                ctx=ctx,
                stdin_bytes=req_blob,
            )
            if rc != 0:
                raise OSError(f"regex-worker-rc:{rc}")
            try:
                return json.loads(stdout_b.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise Refuse("regex-worker-invalid-output") from exc

        return self._run_text_search_sync(host_root, guest_root, pattern, fixed, case_sensitive, max_matches, exts, ctx)

    def _tool_git_ro(self, args: dict[str, Any], ctx: RequestContext) -> dict[str, Any]:
        cwd_guest = args.get("cwd")
        git_args = args.get("args")
        if not isinstance(cwd_guest, str) or not isinstance(git_args, list):
            raise Refuse("bad-git-args")
        clean_args, host_cwd, env = self.policy.validate_git_ro(git_args, cwd_guest)
        rc, stdout_b, stderr_b = self._run_supervised_popen([self.git_bin, *clean_args], cwd=host_cwd, env=env, ctx=ctx)

        return {
            "tool": "git_ro",
            "cwd": cwd_guest,
            "returncode": rc,
            "stdout": stdout_b.decode("utf-8", errors="replace"),
            "stderr": stderr_b.decode("utf-8", errors="replace"),
        }

    def _tool_json_summary(self, args: dict[str, Any], ctx: RequestContext) -> dict[str, Any]:
        guest_path = args.get("path")
        if not isinstance(guest_path, str):
            raise Refuse("bad-path")
        host_path = self.policy.map_path(guest_path, cwd="/", must_exist=True)
        if not os.path.isfile(host_path):
            raise Refuse("not-a-file")
        limit = _strict_int_arg(args, "limit_records", 50000, 1, 200000)

        h = hashlib.sha256()
        total_size = 0
        with open_nofollow(host_path) as fh:
            while chunk := fh.read(262144):
                ctx.check()
                total_size += len(chunk)
                h.update(chunk)
        sha256_hex = h.hexdigest()

        keys_seen: list[str] = []
        keys_set: set[str] = set()
        record_count = 0
        fmt = "jsonl"

        with open_nofollow(host_path) as bfh:
            is_json_ext = guest_path.endswith(".json") and not guest_path.endswith(".jsonl")
            if is_json_ext:
                if total_size > MAX_JSON_DOC_BYTES:
                    raise Refuse("json-too-large")
                raw_doc = bfh.read(MAX_JSON_DOC_BYTES + 1)
                if len(raw_doc) > MAX_JSON_DOC_BYTES:
                    raise Refuse("json-too-large")
                try:
                    obj = json.loads(raw_doc.decode("utf-8", errors="replace"))
                    fmt = "json"
                    if isinstance(obj, list):
                        record_count = len(obj)
                        for item in obj[:100]:
                            if isinstance(item, dict):
                                for k in item.keys():
                                    if k not in keys_set and len(keys_seen) < 40:
                                        keys_set.add(k)
                                        keys_seen.append(str(k))
                    elif isinstance(obj, dict):
                        record_count = 1
                        keys_seen = [str(k) for k in list(obj.keys())[:40]]
                    return {
                        "tool": "python_json_summary",
                        "path": guest_path,
                        "format": fmt,
                        "record_count": record_count,
                        "keys_sample": keys_seen,
                        "sha256": sha256_hex,
                    }
                except json.JSONDecodeError:
                    bfh.seek(0)

            if total_size > MAX_JSONL_BYTES:
                raise Refuse("jsonl-too-large")
            bytes_seen = 0
            idx = 0
            while True:
                idx += 1
                if idx % 256 == 0:
                    ctx.check()
                raw_line = bfh.readline(MAX_JSONL_LINE_BYTES + 1)
                if not raw_line:
                    break
                if len(raw_line) > MAX_JSONL_LINE_BYTES:
                    raise Refuse("jsonl-line-too-large")
                bytes_seen += len(raw_line)
                if bytes_seen > MAX_JSONL_BYTES:
                    raise Refuse("jsonl-too-large")
                s = raw_line.decode("utf-8", errors="replace").strip()
                if not s:
                    continue
                record_count += 1
                if record_count <= limit:
                    try:
                        rec = json.loads(s)
                        if isinstance(rec, dict):
                            for k in rec.keys():
                                if k not in keys_set and len(keys_seen) < 40:
                                    keys_set.add(k)
                                    keys_seen.append(str(k))
                    except json.JSONDecodeError:
                        pass

        return {
            "tool": "python_json_summary",
            "path": guest_path,
            "format": fmt,
            "record_count": record_count,
            "keys_sample": keys_seen,
            "sha256": sha256_hex,
        }


def _regex_worker_main() -> int:
    cfg = json.loads(sys.stdin.read())
    dummy_pol = Policy([("/", cfg["host_root"])], home=cfg["host_root"], tmp=tempfile.gettempdir())
    eng = MCPToolEngine(dummy_pol)
    exts = tuple(cfg["exts"]) if cfg.get("exts") is not None else None
    res = eng._run_text_search_sync(
        cfg["host_root"],
        cfg["guest_root"],
        cfg["pattern"],
        False,
        bool(cfg["case_sensitive"]),
        int(cfg["max_matches"]),
        exts,
        RequestContext("worker", 3600.0),
    )
    sys.stdout.write(_fit_json_payload(res, MAX_TEXT_BYTES))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--regex-worker":
        raise SystemExit(_regex_worker_main())
