#!/usr/bin/env python3
"""Security policy, path mapping, git read-only validation, and OS helpers for Stage 7.2 Native Hybrid 2.0.

Reuses and preserves the core path/git/environment/socket/peercred hardening from
Stage 5 `f8-hybrid-daemon.py`, adapted as a reusable stdlib module for the
isolated MCP UDS daemon and PRoot fallback relay.
"""

from __future__ import annotations

import ctypes
import os
import posixpath
import re
import socket
import struct
from pathlib import Path

AF_UNIX_PATH_MAX = 107

PROTECTED: tuple[str, ...] = (
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/lib",
    "/lib64",
    "/opt",
    "/proc",
    "/root/.cache",
    "/root/.claude",
    "/root/.config",
    "/root/." + "gemini",
    "/root/.hermes",
    "/root/.local",
    "/root/.npm",
    "/root/.pki",
    "/root/.ssh",
    "/run",
    "/sbin",
    "/snap",
    "/sys",
    "/usr",
    "/var",
    "/data/data/com.termux/files/usr",
    "/data/data/com.termux/files/home/build/proot-fast/out8",
    "/data/data/com.termux/files/home/build/proot-fast/shard2",
    "/system",
    "/vendor",
    "/apex",
)

GIT_RO: frozenset[str] = frozenset(
    {
        "status",
        "diff",
        "log",
        "show",
        "rev-parse",
        "ls-files",
        "branch",
        "tag",
        "describe",
        "grep",
        "blame",
        "shortlog",
        "cat-file",
        "ls-tree",
        "rev-list",
        "symbolic-ref",
        "for-each-ref",
        "count-objects",
        "name-rev",
        "merge-base",
    }
)

GIT_PRE_FLAGS: dict[str, bool] = {
    "-C": True,
    "--no-pager": False,
    "--literal-pathspecs": False,
    "--noglob-pathspecs": False,
    "--glob-pathspecs": False,
    "--icase-pathspecs": False,
    "--no-optional-locks": False,
}

GIT_DENY_PREFIX: tuple[str, ...] = (
    "--exec",
    "--upload-pack",
    "--receive-pack",
    "--ext-diff",
    "--textconv",
    "--paginate",
    "--git-dir",
    "--work-tree",
    "--config-env",
    "--output=",
    "-c",
    "-P",
)

GIT_NOEXT_SUBS: frozenset[str] = frozenset({"diff", "log", "show", "grep", "blame"})

GIT_BAD_CFG = re.compile(
    r"(?im)^\s*(?:"
    r"fsmonitor|sshcommand|askpass|credential|uploadpack|receivepack|pager|editor"
    r"|external|textconv|smudge|clean|hookspath|autocrlf"
    r"|\[(?:include|includeif)\b"
    r")"
)

_ENV_KEEP: tuple[str, ...] = ("LANG", "LC_ALL", "LC_CTYPE", "TERM", "TZ", "COLORTERM")

try:
    _LIBC = ctypes.CDLL(None, use_errno=True)
    _SYSNO_PIDFD_OPEN = 434  # Linux aarch64
except OSError:
    _LIBC = None
    _SYSNO_PIDFD_OPEN = None


class Refuse(Exception):
    """Raised when a request fails security policy validation."""


def pidfd_open(pid: int) -> int:
    """Return a pidfd on Linux aarch64 or -1 if unsupported."""
    if _LIBC is None or _SYSNO_PIDFD_OPEN is None or pid <= 0:
        return -1
    try:
        fd = int(_LIBC.syscall(_SYSNO_PIDFD_OPEN, ctypes.c_int(pid), ctypes.c_uint(0)))
        return fd if fd >= 0 else -1
    except Exception:
        return -1


def read_tracer_pid(pid: str | int = "self") -> int:
    """Read TracerPid from /proc/<pid>/status (-1 if unreadable)."""
    try:
        text = Path(f"/proc/{pid}/status").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return -1
    m = re.search(r"(?m)^TracerPid:\s*(\d+)\s*$", text)
    return int(m.group(1)) if m else -1


def validate_unix_sock_path(sock_path: Path | str) -> Path:
    """Validate AF_UNIX socket path byte length before creating parent directories."""
    p = Path(sock_path)
    raw = str(p).encode("utf-8")
    if len(raw) > AF_UNIX_PATH_MAX:
        raise ValueError(f"socket path exceeds AF_UNIX limit ({len(raw)} > {AF_UNIX_PATH_MAX}): {p}")
    return p


def verify_peercred(conn: socket.socket) -> tuple[int, int, int]:
    """Verify peer UID matches current UID using SO_PEERCRED."""
    if not hasattr(socket, "SO_PEERCRED"):
        raise Refuse("peercred-unsupported")
    raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("iII"))
    pid, uid, gid = struct.unpack("iII", raw)
    if uid != os.getuid():
        raise Refuse("peercred-uid-mismatch")
    return pid, uid, gid


def _has_l2s_component(path_str: str) -> bool:
    return any(part.startswith(".l2s.") for part in path_str.split("/") if part)


def _is_protected(norm_guest: str) -> bool:
    for p in PROTECTED:
        if norm_guest == p or norm_guest.startswith(p + "/"):
            return True
    return False


class Policy:
    """Strict read-only path mapping, git config, and environment scrubber."""

    def __init__(
        self,
        maps: list[tuple[str, str]],
        home: str,
        tmp: str,
        path_env: str = "/data/data/com.termux/files/usr/bin:/usr/bin:/bin",
    ) -> None:
        cleaned: list[tuple[str, str]] = []
        for g_prefix, h_prefix in maps:
            gn = posixpath.normpath(g_prefix)
            if not gn.startswith("/"):
                raise ValueError(f"guest map must be absolute: {g_prefix!r}")
            hr = os.path.realpath(h_prefix)
            cleaned.append((gn, hr))
        # Match longest guest prefix first.
        cleaned.sort(key=lambda kv: len(kv[0]), reverse=True)
        self.maps = cleaned
        self.home = os.path.realpath(home)
        self.tmp = os.path.realpath(tmp)
        self.path_env = path_env

    def map_path(self, guest: str, cwd: str | None = None, *, must_exist: bool = False) -> str:
        """Resolve a guest path into a safe host realpath inside allowed maps."""
        if not isinstance(guest, str) or not guest or "\x00" in guest:
            raise Refuse("bad-path")
        base = cwd if (cwd and isinstance(cwd, str) and cwd.startswith("/")) else "/"
        joined = guest if guest.startswith("/") else posixpath.join(base, guest)
        norm = posixpath.normpath(joined)
        if _has_l2s_component(norm):
            raise Refuse("l2s-path")
        if _is_protected(norm):
            raise Refuse("protected-path")

        matched: tuple[str, str] | None = None
        for g_prefix, h_root in self.maps:
            if g_prefix == "/":
                matched = (g_prefix, h_root)
                break
            if norm == g_prefix or norm.startswith(g_prefix + "/"):
                matched = (g_prefix, h_root)
                break
        if matched is None:
            raise Refuse("path-outside-map")

        g_prefix, h_root = matched
        rel = "" if norm == g_prefix else norm[len(g_prefix):].lstrip("/")
        candidate = os.path.join(h_root, rel) if rel else h_root
        real_host = os.path.realpath(candidate)
        if _has_l2s_component(real_host):
            raise Refuse("l2s-path")
        try:
            common = os.path.commonpath([h_root, real_host])
        except ValueError as exc:
            raise Refuse("symlink-escape") from exc
        if common != h_root:
            raise Refuse("symlink-escape")
        if must_exist and not os.path.exists(real_host):
            raise Refuse("path-missing")
        return real_host

    def _find_git_root(self, host_dir: str) -> tuple[str | None, str | None]:
        """Walk upward inside mapped root to find nearest .git directory/file."""
        cur = os.path.realpath(host_dir)
        allowed_roots = [h_root for _, h_root in self.maps]
        while True:
            if not any(os.path.commonpath([r, cur]) == r for r in allowed_roots):
                return None, None
            dot_git = os.path.join(cur, ".git")
            if os.path.isdir(dot_git):
                return cur, dot_git
            if os.path.isfile(dot_git):
                return cur, dot_git
            parent = os.path.dirname(cur)
            if parent == cur:
                return None, None
            cur = parent

    def git_cfg_scan(self, host_dir: str) -> None:
        """Scan .git directory or .git file and refuse unsafe repo config directives."""
        repo_root, dot_git = self._find_git_root(host_dir)
        if dot_git is None or repo_root is None:
            return
        cfg_paths: list[Path] = []
        dg = Path(dot_git)
        if dg.is_file():
            try:
                raw = dg.read_text(encoding="utf-8", errors="replace").strip()
            except OSError as exc:
                raise Refuse("gitfile-unreadable") from exc
            if not raw.startswith("gitdir:"):
                raise Refuse("gitfile-malformed")
            target = raw[len("gitdir:"):].strip()
            if not target or os.path.isabs(target):
                raise Refuse("gitfile-absolute")
            resolved_gitdir = os.path.realpath(os.path.join(repo_root, target))
            allowed_roots = [h_root for _, h_root in self.maps]
            if not any(os.path.commonpath([r, resolved_gitdir]) == r for r in allowed_roots):
                raise Refuse("symlink-escape")
            cfg_paths.append(Path(resolved_gitdir) / "config")
            commondir = Path(resolved_gitdir) / "commondir"
            if commondir.is_file():
                rel_c = commondir.read_text(encoding="utf-8", errors="replace").strip()
                cdir = os.path.realpath(os.path.join(resolved_gitdir, rel_c))
                if not any(os.path.commonpath([r, cdir]) == r for r in allowed_roots):
                    raise Refuse("symlink-escape")
                cfg_paths.append(Path(cdir) / "config")
        else:
            cfg_paths.append(dg / "config")
            wt_dir = dg / "worktrees"
            if wt_dir.is_dir():
                for sub in wt_dir.iterdir():
                    if sub.is_dir():
                        cfg_paths.append(sub / "config")

        for cfg in cfg_paths:
            if not cfg.is_file():
                continue
            try:
                content = cfg.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                raise Refuse("git-config-unreadable") from exc
            if GIT_BAD_CFG.search(content):
                raise Refuse("git-config-unsafe")

    def clean_env(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        """Build a scrubbed deterministic environment for native child execution."""
        env: dict[str, str] = {}
        for key in _ENV_KEEP:
            val = os.environ.get(key)
            if val:
                env[key] = val
        env.setdefault("LANG", "C.UTF-8")
        env["PATH"] = self.path_env
        env["HOME"] = self.home
        env["TMPDIR"] = self.tmp
        env["PYTHONNOUSERSITE"] = "1"
        env["GIT_CONFIG_NOSYSTEM"] = "1"
        env["GIT_CONFIG_GLOBAL"] = "/dev/null"
        env["GIT_TERMINAL_PROMPT"] = "0"
        if extra:
            for k, v in extra.items():
                if k in _ENV_KEEP and isinstance(v, str) and "\x00" not in v:
                    env[k] = v
        return env

    def validate_git_ro(self, args: list[str], cwd_guest: str) -> tuple[list[str], str, dict[str, str]]:
        """Validate read-only git arguments, map cwd/paths, and return safe argv/cwd/env."""
        if not isinstance(args, list) or not args:
            raise Refuse("git-args-empty")
        host_cwd = self.map_path(cwd_guest, cwd="/", must_exist=True)
        if not os.path.isdir(host_cwd):
            raise Refuse("cwd-not-dir")

        out_pre: list[str] = []
        i = 0
        while i < len(args):
            a = args[i]
            if not isinstance(a, str) or "\x00" in a:
                raise Refuse("bad-arg")
            if a in GIT_PRE_FLAGS:
                takes_val = GIT_PRE_FLAGS[a]
                if takes_val:
                    if i + 1 >= len(args):
                        raise Refuse("git-flag-missing-arg")
                    target_guest = args[i + 1]
                    host_cwd = self.map_path(target_guest, cwd=cwd_guest, must_exist=True)
                    cwd_guest = posixpath.normpath(
                        target_guest if target_guest.startswith("/") else posixpath.join(cwd_guest, target_guest)
                    )
                    out_pre.extend(["-C", host_cwd])
                    i += 2
                    continue
                out_pre.append(a)
                i += 1
                continue
            if a.startswith("-"):
                raise Refuse("git-pre-flag-denied")
            break

        if i >= len(args):
            raise Refuse("git-subcmd-missing")
        sub = args[i]
        if sub not in GIT_RO:
            raise Refuse("git-subcmd-denied")

        sub_args = args[i + 1 :]
        if sub in ("branch", "tag"):
            write_flags = {
                "-d", "-D", "-m", "-M", "-c", "-C", "-f", "--delete", "--move",
                "--copy", "--force", "-a", "-s", "-u", "--edit-description",
                "--set-upstream-to", "--unset-upstream", "--create-reflog",
            }
            for a in sub_args:
                if a in write_flags or a.startswith("--create") or a.startswith("--delete"):
                    raise Refuse("git-write-flag-denied")

        for a in sub_args:
            if not isinstance(a, str) or "\x00" in a:
                raise Refuse("bad-arg")
            for pfx in GIT_DENY_PREFIX:
                if a == pfx or a.startswith(pfx + "=") or (len(pfx) == 2 and a.startswith(pfx)):
                    raise Refuse("git-option-denied")
            if a.startswith("-O") or a.startswith("--output"):
                raise Refuse("git-option-denied")

        self.git_cfg_scan(host_cwd)

        clean_args = list(out_pre)
        clean_args.append(sub)
        if sub in GIT_NOEXT_SUBS:
            clean_args.append("--no-ext-diff")
        clean_args.extend(sub_args)
        return clean_args, host_cwd, self.clean_env()
