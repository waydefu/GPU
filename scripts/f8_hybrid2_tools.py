#!/usr/bin/env python3
"""Shared MCP JSON-RPC 2.0 dispatcher and read-only tool implementations for Stage 7.2.

Used both by the native Termux UDS daemon (`f8_hybrid2_daemon.py`) and by the
local PRoot fallback path inside `f8_hybrid2_relay.py` so protocol semantics
and tool results stay identical across native and fallback paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from f8_hybrid2_policy import Policy, Refuse, pidfd_open

SUPPORTED_PROTOCOL_VERSIONS = (
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)
DEFAULT_PROTOCOL_VERSION = "2025-03-26"
MAX_TEXT_BYTES = 1024 * 1024  # 1 MiB cap per serialized tool response
MAX_OUTPUT_BYTES = 2 * 1024 * 1024

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
    """Per-request cancellation, timeout deadline, and subprocess pgid tracker."""

    def __init__(self, req_id: Any, timeout_s: float) -> None:
        self.req_id = req_id
        self.cancel_event = threading.Event()
        self.timed_out = False
        self.deadline = time.monotonic() + max(0.001, float(timeout_s))
        self._lock = threading.Lock()
        self._proc_pgid: int | None = None

    def set_proc(self, proc: subprocess.Popen[bytes] | None) -> None:
        with self._lock:
            self._proc_pgid = proc.pid if proc is not None else None
            already_cancelled = self.cancel_event.is_set()
        if already_cancelled and proc is not None:
            self._kill_pgid(proc.pid)

    def _kill_pgid(self, pgid: int) -> None:
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
        self.cancel_event.set()
        with self._lock:
            pgid = self._proc_pgid
        if pgid is not None:
            self._kill_pgid(pgid)

    def check(self) -> None:
        if self.cancel_event.is_set():
            raise RequestCancelled("cancelled")
        if time.monotonic() > self.deadline:
            self.timed_out = True
            with self._lock:
                pgid = self._proc_pgid
            if pgid is not None:
                self._kill_pgid(pgid)
            raise RequestTimeout("timeout")


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

    def handle_sync_control(self, msg: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        """Handle lightweight non-tool JSON-RPC requests; return (response_or_None, tool_call_name_if_async)."""
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            return self.jsonrpc_err(msg.get("id") if isinstance(msg, dict) else None, -32600, "Invalid Request"), None

        method = msg.get("method")
        req_id = msg.get("id")
        is_notif = "id" not in msg

        if not isinstance(method, str) or not method:
            return (None if is_notif else self.jsonrpc_err(req_id, -32600, "Missing method")), None

        if method == "initialize":
            params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
            proto = self.negotiate_protocol(params.get("protocolVersion"))
            return self.jsonrpc_ok(
                req_id,
                {
                    "protocolVersion": proto,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "f8-hybrid2", "version": "0.1.0"},
                },
            ), None

        if method == "notifications/initialized":
            return None, None

        if method == "ping":
            return (None if is_notif else self.jsonrpc_ok(req_id, {})), None

        if method == "tools/list":
            return (None if is_notif else self.jsonrpc_ok(req_id, {"tools": TOOL_DEFS})), None

        if method == "tools/call":
            if is_notif:
                return None, None
            return None, "tools/call"

        if is_notif:
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
        if isinstance(raw_timeout, (int, float)) and raw_timeout > 0:
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

        text = json.dumps(payload, ensure_ascii=False)
        if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
            text = text[: MAX_TEXT_BYTES - 64] + '..."}'
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

        max_entries = int(args.get("max_entries", 2000))
        max_entries = max(1, min(max_entries, 50000))
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
                        with open(full, "rb") as fh:
                            data = fh.read()
                        size = len(data)
                        assert digest is not None
                        digest.update(rel.encode("utf-8", errors="replace"))
                        digest.update(b"\0")
                        digest.update(data)
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

    def _tool_text_search(self, args: dict[str, Any], ctx: RequestContext) -> dict[str, Any]:
        guest_root = args.get("root")
        pattern = args.get("pattern")
        if not isinstance(guest_root, str) or not isinstance(pattern, str) or not pattern:
            raise Refuse("bad-search-args")
        host_root = self.policy.map_path(guest_root, cwd="/", must_exist=True)
        fixed = bool(args.get("fixed_string", False))
        case_sensitive = bool(args.get("case_sensitive", True))
        max_matches = max(1, min(int(args.get("max_matches", 200)), 5000))
        raw_exts = args.get("include_ext")
        exts: tuple[str, ...] | None = None
        if isinstance(raw_exts, list) and raw_exts:
            exts = tuple(str(x) for x in raw_exts if isinstance(x, str))

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
        truncated = False

        def scan_file(fpath: str, rel: str) -> None:
            nonlocal files_scanned, truncated
            ctx.check()
            if exts is not None and not any(rel.endswith(e) for e in exts):
                return
            try:
                with open(fpath, "rb") as fh:
                    raw = fh.read(2 * 1024 * 1024)
            except OSError:
                return
            if b"\x00" in raw:
                return
            files_scanned += 1
            text = raw.decode("utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), 1):
                if lineno % 256 == 0:
                    ctx.check()
                hit = (
                    (needle in (line if case_sensitive else line.lower()))
                    if fixed
                    else bool(rx.search(line))
                )
                if hit:
                    if len(matches) >= max_matches:
                        truncated = True
                        return
                    matches.append({"file": rel, "line": lineno, "text": line[:300]})

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
                    if truncated:
                        break
                if truncated:
                    break

        return {
            "tool": "repo_text_search",
            "root": guest_root,
            "files_scanned": files_scanned,
            "match_count": len(matches),
            "truncated": truncated,
            "matches": matches,
        }

    def _tool_git_ro(self, args: dict[str, Any], ctx: RequestContext) -> dict[str, Any]:
        cwd_guest = args.get("cwd")
        git_args = args.get("args")
        if not isinstance(cwd_guest, str) or not isinstance(git_args, list):
            raise Refuse("bad-git-args")
        clean_args, host_cwd, env = self.policy.validate_git_ro(git_args, cwd_guest)

        # Write child stdout/stderr to temporary unlinked files instead of PIPEs
        # so polling + killpg on cancel/timeout can never deadlock on full pipe buffers.
        import tempfile

        with (
            tempfile.TemporaryFile(mode="w+b") as out_f,
            tempfile.TemporaryFile(mode="w+b") as err_f,
        ):
            proc = subprocess.Popen(
                [self.git_bin, *clean_args],
                cwd=host_cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=out_f,
                stderr=err_f,
                shell=False,
                start_new_session=True,
            )
            ctx.set_proc(proc)
            pfd = pidfd_open(proc.pid)
            try:
                while True:
                    rc = proc.poll()
                    if rc is not None:
                        break
                    ctx.check()
                    ctx.cancel_event.wait(0.02)
            except (RequestCancelled, RequestTimeout):
                ctx.set_proc(proc)  # guarantees killpg if race
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    pass
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
                raise
            finally:
                if pfd >= 0:
                    try:
                        os.close(pfd)
                    except OSError:
                        pass
                ctx.set_proc(None)

            out_f.seek(0)
            err_f.seek(0)
            stdout_b = out_f.read(MAX_OUTPUT_BYTES)
            stderr_b = err_f.read(256 * 1024)

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
        limit = max(1, min(int(args.get("limit_records", 50000)), 200000))

        h = hashlib.sha256()
        with open(host_path, "rb") as fh:
            while chunk := fh.read(256 * 1024):
                ctx.check()
                h.update(chunk)
        sha256_hex = h.hexdigest()

        keys_seen: list[str] = []
        keys_set: set[str] = set()
        record_count = 0
        fmt = "jsonl"

        with open(host_path, "r", encoding="utf-8", errors="replace") as fh:
            first_chunk = fh.read(4096)
            fh.seek(0)
            stripped = first_chunk.lstrip()
            if guest_path.endswith(".json") and not guest_path.endswith(".jsonl") or stripped.startswith("["):
                if not guest_path.endswith(".jsonl"):
                    try:
                        obj = json.load(fh)
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
                        fh.seek(0)

            for idx, line in enumerate(fh, 1):
                if idx % 256 == 0:
                    ctx.check()
                s = line.strip()
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
