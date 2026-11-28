#!/usr/bin/env python3
"""Security policy, path mapping, git read-only validation, and OS helpers for Stage 7.2.

Reuses and preserves the core path/git/environment/socket/peercred hardening from
Stage 5 `f8-hybrid-daemon.py`, upgraded per Stage 7.2 universal MCP audit:
- Default runtime directory moved to TERMUX_HOME (`~/.f8hyb2`, immune to `$PREFIX/tmp` wipes)
- `map_path()` verifies BOTH pre-symlink guest paths and `real_host` against protected targets
- `open_nofollow()` prevents symlink TOCTOU on file reads
- `validate_git_ro()` validates path-like sub-args, blocks `--no-index` / `-f`, enforces
  `--no-textconv` + `GIT_OPTIONAL_LOCKS=0`, and scans `config.worktree` + absolute `commondir`
"""

from __future__ import annotations

import ctypes
import fcntl
import json
import os
import posixpath
import re
import socket
import stat
import struct
from pathlib import Path
from typing import BinaryIO

AF_UNIX_PATH_MAX = 107
TRUSTED_GIT_ROOTS_ENV = "F8_HYBRID2_TRUSTED_GIT_ROOTS"

TERMUX_HOME = "/data/data/com.termux/files/home"
DEFAULT_RUNTIME_DIR = f"{TERMUX_HOME}/.f8hyb2"
DEFAULT_SOCK_PATH = f"{DEFAULT_RUNTIME_DIR}/m.sock"
DEFAULT_PID_PATH = f"{DEFAULT_RUNTIME_DIR}/d.pid"
DEFAULT_READY_PATH = f"{DEFAULT_RUNTIME_DIR}/ready"
DEFAULT_DISABLED_PATH = f"{DEFAULT_RUNTIME_DIR}/disabled.flag"
DEFAULT_CTL_LOCK_PATH = f"{DEFAULT_RUNTIME_DIR}/ctl.lock"
DEFAULT_LOG_PATH = f"{DEFAULT_RUNTIME_DIR}/audit.jsonl"

ROOTFS_PROJECTS_HOST = "/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs/root/projects"
DEFAULT_DAEMON_MAPS: tuple[tuple[str, str], ...] = (
    ("/root/projects", ROOTFS_PROJECTS_HOST),
)
DEFAULT_FALLBACK_MAPS: tuple[tuple[str, str], ...] = (
    ("/root/projects", "/root/projects"),
)

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
    "/root/.codex",
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
    "/data/data/com.termux/files/home/.f8hyb2",
    "/data/data/com.termux/files/home/build/proot-fast/out8",
    "/data/data/com.termux/files/home/build/proot-fast/shard2",
    "/system",
    "/vendor",
    "/apex",
)

_ROOTFS_PREFIX = "/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs"
# PRoot link2symlink store: Git objects written inside PRoot are symlinks into it (F13).
DEFAULT_L2S_DIR = _ROOTFS_PREFIX + "/.l2s"
_LOOSE_OBJECT_NAME = re.compile(r"[0-9a-f]{38}|[0-9a-f]{62}")
_PACK_FILE_NAME = re.compile(r"pack-(?:[0-9a-f]{40}|[0-9a-f]{64})\.(pack|idx|rev)")

GIT_PRE_FLAGS: dict[str, bool] = {
    "-C": True,
    "--no-pager": False,
    "--literal-pathspecs": False,
    "--noglob-pathspecs": False,
    "--glob-pathspecs": False,
    "--icase-pathspecs": False,
    "--no-optional-locks": False,
}

GIT_NOEXT_DIFF_SUBS: frozenset[str] = frozenset({"diff", "log", "show", "blame"})
GIT_NOTEXTCONV_SUBS: frozenset[str] = frozenset({"diff", "log", "show", "grep", "blame"})

_COMMON_COLOR_FLAGS = frozenset({"--color", "--no-color"})
_COMMON_DIFF_FLAGS = frozenset(
    {
        "--stat", "--numstat", "--shortstat", "--summary", "--name-only", "--name-status",
        "--patch", "-p", "--no-patch", "-s", "--raw", "--no-renames", "--find-renames",
        "-M", "-C", "--check", "-w", "--ignore-all-space", "-b", "--ignore-space-change",
        "--no-prefix", "--abbrev",
    }
)
_COMMON_DIFF_VAL_FLAGS = frozenset({"-U", "--unified", "--src-prefix", "--dst-prefix", "--abbrev", "--find-renames"})

# Strict per-subcommand allowlist:
# - flags_no_val: flags accepting NO separate argument
# - flags_eq_only: OPTARG or `=`-only flags; NEVER consume next argv element!
# - flags_val_req: flags verified to unconditionally consume the next non-`-` argv element
# - flags_int_attached: short flags like `-n10` or `-U3` accepting only attached digits
# - flags_path_val: flags whose value MUST pass Policy.map_path()
GIT_SUBCMD_SPECS: dict[str, dict[str, object]] = {
    "status": {
        "flags_no_val": frozenset(
            {"--short", "-s", "--branch", "-b", "--porcelain", "--ignored", "--no-renames", "-z", "--show-stash", "--ahead-behind", "--no-ahead-behind", "-v", "--verbose", "-u", "--untracked-files", "--find-renames"}
        ),
        "flags_eq_only": frozenset({"--porcelain", "--untracked-files", "-u", "--ignored", "--find-renames"}),
        "flags_val_req": frozenset(),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "paths_only",
    },
    "diff": {
        "flags_no_val": _COMMON_DIFF_FLAGS | _COMMON_COLOR_FLAGS | frozenset({"--cached", "--staged", "--word-diff"}),
        "flags_eq_only": _COMMON_DIFF_VAL_FLAGS | frozenset({"--color", "--word-diff", "-M", "-C"}),
        "flags_val_req": frozenset(),
        "flags_int_attached": frozenset({"-U"}),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "log": {
        "flags_no_val": _COMMON_DIFF_FLAGS
        | _COMMON_COLOR_FLAGS
        | frozenset(
            {
                "--oneline", "--abbrev-commit", "--decorate", "--no-decorate", "--graph", "--all",
                "--branches", "--tags", "--remotes", "--first-parent", "--merges", "--no-merges",
                "--fixed-strings", "-F", "-i", "--regexp-ignore-case", "-E", "--extended-regexp",
                "--pickaxe-regex", "--follow", "--reverse", "--topo-order", "--date-order",
            }
        ),
        "flags_eq_only": _COMMON_DIFF_VAL_FLAGS
        | frozenset(
            {
                "-n", "--max-count", "--format", "--pretty", "--since", "--after", "--until",
                "--before", "--author", "--committer", "--grep", "-S", "-G", "--date", "--color", "-M", "-C",
            }
        ),
        "flags_val_req": frozenset({"-n", "--max-count", "--since", "--after", "--until", "--before", "--author", "--committer", "--grep", "-S", "-G", "--date"}),
        "flags_int_attached": frozenset({"-n", "-U"}),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "show": {
        "flags_no_val": _COMMON_DIFF_FLAGS | _COMMON_COLOR_FLAGS | frozenset({"--oneline", "--abbrev-commit"}),
        "flags_eq_only": _COMMON_DIFF_VAL_FLAGS | frozenset({"--format", "--pretty", "--color", "-M", "-C"}),
        "flags_val_req": frozenset(),
        "flags_int_attached": frozenset({"-U"}),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "rev-parse": {
        "flags_no_val": frozenset(
            {
                "--is-inside-work-tree", "--is-bare-repository", "--abbrev-ref", "--short", "--verify",
                "-q", "--quiet", "--symbolic", "--symbolic-full-name", "--show-toplevel",
                "--git-dir", "--git-common-dir", "--all", "--branches", "--tags", "--remotes",
            }
        ),
        "flags_eq_only": frozenset({"--abbrev-ref", "--short", "--prefix"}),
        "flags_val_req": frozenset({"--prefix"}),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "ls-files": {
        "flags_no_val": frozenset(
            {
                "--cached", "-c", "--modified", "-m", "--others", "-o", "--deleted", "-d",
                "--ignored", "-i", "--unmerged", "-u", "--stage", "-s", "--exclude-standard",
                "--full-name", "-z", "--error-unmatch", "--eol",
            }
        ),
        "flags_eq_only": frozenset(),
        "flags_val_req": frozenset(),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "paths_only",
    },
    "branch": {
        "flags_no_val": _COMMON_COLOR_FLAGS
        | frozenset({"--list", "-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose", "--abbrev", "--no-abbrev", "--show-current", "--merged", "--no-merged"}),
        "flags_eq_only": frozenset({"--abbrev", "--merged", "--no-merged", "--contains", "--no-contains", "--points-at", "--sort", "--format", "--color"}),
        "flags_val_req": frozenset({"--contains", "--no-contains", "--points-at", "--sort", "--format"}),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "require_flag:--list",
    },
    "tag": {
        "flags_no_val": _COMMON_COLOR_FLAGS | frozenset({"--list", "-v", "--verify", "--merged", "--no-merged"}),
        "flags_eq_only": frozenset({"--sort", "--contains", "--no-contains", "--points-at", "--merged", "--no-merged", "--format", "-n", "--color"}),
        "flags_val_req": frozenset({"--sort", "--contains", "--no-contains", "--points-at", "--format"}),
        "flags_int_attached": frozenset({"-n"}),
        "flags_path_val": frozenset(),
        "pos_mode": "require_flag:--list,-v,--verify",
    },
    "describe": {
        "flags_no_val": frozenset({"--tags", "--all", "--exact-match", "--long", "--always", "--dirty", "--broken", "--first-parent", "--contains", "--abbrev"}),
        "flags_eq_only": frozenset({"--abbrev", "--dirty", "--match", "--exclude"}),
        "flags_val_req": frozenset({"--match", "--exclude"}),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "grep": {
        "flags_no_val": _COMMON_COLOR_FLAGS
        | frozenset(
            {
                "-n", "--line-number", "-i", "--ignore-case", "-F", "--fixed-strings", "-E", "--extended-regexp",
                "-P", "--perl-regexp", "-w", "--word-regexp", "-l", "--files-with-matches", "--files-without-match",
                "-c", "--count", "-h", "--no-filename", "-H", "--heading", "--break", "-I", "--cached",
                "--untracked", "--and", "--or", "--not", "-q", "--quiet",
            }
        ),
        "flags_eq_only": frozenset({"-A", "--after-context", "-B", "--before-context", "-C", "--context", "--max-depth", "--color"}),
        "flags_val_req": frozenset({"-e", "-A", "--after-context", "-B", "--before-context", "-C", "--context", "--max-depth"}),
        "flags_int_attached": frozenset({"-A", "-B", "-C"}),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "blame": {
        "flags_no_val": frozenset({"-n", "--line-porcelain", "--porcelain", "-p", "-e", "--show-email", "-s", "-w", "-M", "-C", "--abbrev", "--score-debug", "--first-parent", "--color-lines", "--color-by-age"}),
        "flags_eq_only": frozenset({"--abbrev", "--date", "-M", "-C"}),
        "flags_val_req": frozenset({"-L", "--date"}),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset({"--contents"}),
        "pos_mode": "refs_and_paths",
    },
    "shortlog": {
        "flags_no_val": frozenset({"-s", "--summary", "-n", "--numbered", "-e", "--email", "-c", "--committer", "--all", "--no-merges"}),
        "flags_eq_only": frozenset({"--since", "--after", "--until", "--before", "--format", "--group"}),
        "flags_val_req": frozenset({"--since", "--after", "--until", "--before", "--group"}),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "cat-file": {
        "flags_no_val": frozenset({"-t", "-s", "-p", "-e"}),
        "flags_eq_only": frozenset(),
        "flags_val_req": frozenset(),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "ls-tree": {
        "flags_no_val": frozenset({"-r", "-t", "-d", "-l", "--long", "--name-only", "--name-status", "--full-name", "--full-tree", "-z", "--abbrev"}),
        "flags_eq_only": frozenset({"--abbrev", "--format"}),
        "flags_val_req": frozenset({"--format"}),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "rev-list": {
        "flags_no_val": frozenset({"--count", "--all", "--branches", "--tags", "--remotes", "--first-parent", "--merges", "--no-merges", "--reverse", "--topo-order", "--date-order", "--oneline", "--objects", "--parents", "--boundary"}),
        "flags_eq_only": frozenset({"-n", "--max-count", "--since", "--after", "--until", "--before", "--author"}),
        "flags_val_req": frozenset({"-n", "--max-count", "--since", "--after", "--until", "--before", "--author"}),
        "flags_int_attached": frozenset({"-n"}),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "symbolic-ref": {
        "flags_no_val": frozenset({"--short", "-q", "--quiet"}),
        "flags_eq_only": frozenset(),
        "flags_val_req": frozenset(),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "exact_1_ref",
    },
    "for-each-ref": {
        "flags_no_val": _COMMON_COLOR_FLAGS | frozenset({"--merged", "--no-merged"}),
        "flags_eq_only": frozenset({"--format", "--sort", "--count", "--merged", "--no-merged", "--contains", "--no-contains", "--points-at", "--color"}),
        "flags_val_req": frozenset({"--format", "--sort", "--count", "--contains", "--no-contains", "--points-at"}),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "count-objects": {
        "flags_no_val": frozenset({"-v", "--verbose", "-H", "--human-readable"}),
        "flags_eq_only": frozenset(),
        "flags_val_req": frozenset(),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "none",
    },
    "name-rev": {
        "flags_no_val": frozenset({"--tags", "--name-only", "--always", "--no-undefined", "--all"}),
        "flags_eq_only": frozenset({"--refs", "--exclude"}),
        "flags_val_req": frozenset({"--refs", "--exclude"}),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
    "merge-base": {
        "flags_no_val": frozenset({"--is-ancestor", "--octopus", "--independent", "--fork-point", "--all"}),
        "flags_eq_only": frozenset(),
        "flags_val_req": frozenset(),
        "flags_int_attached": frozenset(),
        "flags_path_val": frozenset(),
        "pos_mode": "refs_and_paths",
    },
}

GIT_RO: frozenset[str] = frozenset(GIT_SUBCMD_SPECS.keys())

GIT_BAD_CFG = re.compile(
    r"(?im)(?:^\s*|\]\s*)(?:"
    r"fsmonitor|sshcommand|askpass|credential|uploadpack|receivepack|pager|editor"
    r"|external|textconv|smudge|clean|hookspath|autocrlf"
    r"|command|process|driver|helper|program|proxycommand|exec"
    r")\b|^\s*\[(?:include|includeif|filter)\b"
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


def proc_matches_cmdline(pid: int, needle: str) -> bool:
    """Verify live /proc/<pid>/cmdline contains needle before signaling."""
    if pid <= 0:
        return False
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    cmd = raw.replace(b"\x00", b" ").decode("utf-8", errors="replace")
    return needle in cmd


def open_nofollow(path: str | Path) -> BinaryIO:
    """Open regular file read-only with O_NOFOLLOW | O_NONBLOCK (defeats symlink TOCTOU and FIFOs)."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(str(path), flags)
    try:
        st = os.fstat(fd)
        import stat as stat_mod

        if not stat_mod.S_ISREG(st.st_mode):
            raise OSError("not a regular file")
        return os.fdopen(fd, "rb")
    except Exception:
        os.close(fd)
        raise


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


def parse_map_specs(items: list[str] | None, default_maps: tuple[tuple[str, str], ...]) -> list[tuple[str, str]]:
    """Parse GUEST=HOST CLI map items or return defaults."""
    if not items:
        return list(default_maps)
    out: list[tuple[str, str]] = []
    for item in items:
        if "=" in item:
            g, h = item.split("=", 1)
            out.append((g, h))
        else:
            out.append((item, item))
    return out


def resolve_path(path: str) -> str:
    """os.path.realpath that detects links with readlink() instead of lstat() (F14).

    PRoot's link2symlink reports a symlink whose target name starts with ``.l2s.`` as a
    regular file to lstat(), so realpath() stops at it and an escaping link looks
    contained. readlink() still returns such a link's target, while PRoot's own hard-link
    emulation returns EINVAL (a genuine hard link, which is not a path redirect).
    Non-strict like realpath(): missing components are kept literally.
    """
    path = os.fspath(path)
    if not path.startswith("/"):
        path = os.getcwd() + "/" + path
    # No abspath()/normpath(): `link/../x` must take the parent of link's target, as the kernel does.
    pending = path.split("/")[::-1]
    resolved = "/"
    hops = 0
    while pending:
        name = pending.pop()
        if name in ("", "."):
            continue
        if name == "..":
            resolved = posixpath.dirname(resolved)
            continue
        candidate = posixpath.join(resolved, name)
        try:
            target = os.readlink(candidate)
        except OSError:
            resolved = candidate
            continue
        if not target:
            resolved = candidate
            continue
        hops += 1
        if hops > 40:  # loop: like realpath(), return the unresolved remainder (open() will fail ELOOP)
            return posixpath.normpath(posixpath.join(candidate, *pending[::-1]))
        if target.startswith("/"):
            resolved = "/"
        pending.extend(target.split("/")[::-1])
    return resolved


def is_link(path: str) -> bool:
    """os.path.islink() that PRoot's ``.l2s.`` lstat rewriting cannot hide (F14)."""
    try:
        return bool(os.readlink(path))
    except OSError:
        return False


def append_rotating(path: Path, line: str, max_bytes: int) -> None:
    """Append one line; past max_bytes move the file to ``<path>.1`` (one generation).

    Safe across processes: the writer holds flock on the file it appends to and re-checks
    that the path still names that file, so concurrent writers never rotate twice and
    overwrite the previous generation.
    """
    for _ in range(4):
        fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            st = os.fstat(fd)
            try:
                current = os.stat(path)
            except FileNotFoundError:
                continue
            if (current.st_dev, current.st_ino) != (st.st_dev, st.st_ino):
                continue  # rotated by another writer while we waited for the lock
            if st.st_size >= max_bytes:
                os.replace(path, str(path) + ".1")
                continue
            data = memoryview(line.encode("utf-8"))
            while data:
                data = data[os.write(fd, data):]
            return
        finally:
            os.close(fd)
    raise OSError(f"append_rotating: {path} kept changing under the lock")


def _has_l2s_component(path_str: str) -> bool:
    return any(part.startswith(".l2s.") for part in path_str.split("/") if part)


def _is_protected_norm(norm_path: str) -> bool:
    for p in PROTECTED:
        if norm_path == p or norm_path.startswith(p + "/"):
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
        single_thread_git: bool = False,
        l2s_dir: str | None = DEFAULT_L2S_DIR,
    ) -> None:
        self.single_thread_git = single_thread_git
        # Literal and resolved spellings of the l2s store; None disables the F13 allowance.
        self._l2s_dirs: frozenset[str] | None = None
        if l2s_dir and os.path.isdir(l2s_dir):
            self._l2s_dirs = frozenset({posixpath.normpath(l2s_dir), resolve_path(l2s_dir)})
        cleaned: list[tuple[str, str]] = []
        for g_prefix, h_prefix in maps:
            gn = posixpath.normpath(g_prefix)
            if not gn.startswith("/"):
                raise ValueError(f"guest map must be absolute: {g_prefix!r}")
            hr = resolve_path(h_prefix)
            cleaned.append((gn, hr))
        cleaned.sort(key=lambda kv: len(kv[0]), reverse=True)
        self.maps = cleaned
        self.home = resolve_path(home)
        self.tmp = resolve_path(tmp)
        self.path_env = path_env

        # Real host equivalents of PROTECTED so symlinks inside mapped roots cannot bypass PROTECTED.
        prot_hosts: list[str] = []
        for p in PROTECTED:
            prot_hosts.append(posixpath.normpath(p))
            prot_hosts.append(resolve_path(p))
            if not p.startswith("/data/"):
                prot_hosts.append(posixpath.normpath(_ROOTFS_PREFIX + p))
                prot_hosts.append(resolve_path(_ROOTFS_PREFIX + p))
        self._protected_real: tuple[str, ...] = tuple(dict.fromkeys(prot_hosts))

        # Configuration comes from the launcher, outside the checkout.
        try:
            roots = json.loads(os.environ.get(TRUSTED_GIT_ROOTS_ENV, "[]"))
        except (ValueError, RecursionError):
            roots = []
        guest_roots = tuple(roots) if isinstance(roots, list) and all(
            isinstance(root, str) and root.startswith("/") and "\x00" not in root
            for root in roots
        ) else ()

        self.trusted_git_roots: set[str] = set()
        for root in guest_roots:
            try:
                self.trusted_git_roots.add(self.map_path(root, must_exist=True))
            except Refuse:
                continue

    def _is_l2s_object_link(self, path: str, kind: str) -> bool:
        """True only for PRoot's exact two-hop link2symlink layout of one Git object file."""
        if self._l2s_dirs is None:
            return False
        try:
            hop1 = os.readlink(path)
            if not (hop1.startswith("/") and posixpath.normpath(hop1) == hop1):
                return False
            l2s_dir, name1 = posixpath.split(hop1)
            if l2s_dir not in self._l2s_dirs or not re.fullmatch(rf"\.l2s\.tmp_{kind}_[A-Za-z0-9]{{6}}[0-9]{{4}}", name1):
                return False
            hop2 = os.readlink(hop1)
            if not (hop2.startswith("/") and posixpath.normpath(hop2) == hop2):
                return False
            dir2, name2 = posixpath.split(hop2)
            if dir2 not in self._l2s_dirs or not re.fullmatch(re.escape(name1) + r"\.[0-9]{4}", name2):
                return False
            st = os.lstat(hop2)
        except OSError:
            return False
        if not stat.S_ISREG(st.st_mode):
            return False
        return resolve_path(path) == os.path.join(resolve_path(dir2), name2)

    def _is_protected_host(self, real_host: str, h_root: str) -> bool:
        for p in self._protected_real:
            # Never let a protected ancestor of an explicitly mapped root poison the whole mapped root.
            if h_root == p or h_root.startswith(p + "/"):
                continue
            if real_host == p or real_host.startswith(p + "/"):
                return True
        return False

    def map_path(self, guest: str, cwd: str | None = None, *, must_exist: bool = False) -> str:
        """Resolve a guest path into a safe host realpath inside allowed maps."""
        if not isinstance(guest, str) or not guest or "\x00" in guest:
            raise Refuse("bad-path")
        base = cwd if (cwd and isinstance(cwd, str) and cwd.startswith("/")) else "/"
        joined = guest if guest.startswith("/") else posixpath.join(base, guest)
        # Collapse POSIX `//` prefix so `//etc/passwd` normalizes to `/etc/passwd`.
        joined = re.sub(r"^/+", "/", joined)
        norm = posixpath.normpath(joined)
        if _has_l2s_component(norm):
            raise Refuse("l2s-path")
        if _is_protected_norm(norm):
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
        rel = "" if norm == g_prefix else norm[len(g_prefix) :].lstrip("/")
        candidate = os.path.join(h_root, rel) if rel else h_root
        real_host = resolve_path(candidate)
        if _has_l2s_component(real_host):
            raise Refuse("l2s-path")
        try:
            common = os.path.commonpath([h_root, real_host])
        except ValueError as exc:
            raise Refuse("symlink-escape") from exc
        if common != h_root:
            raise Refuse("symlink-escape")
        # Also verify resolved host path did not land in a protected target inside mapped subtree.
        if self._is_protected_host(real_host, h_root):
            raise Refuse("protected-path")
        if must_exist and not os.path.exists(real_host):
            raise Refuse("path-missing")
        return real_host

    def _find_git_root(self, host_dir: str) -> tuple[str | None, str | None]:
        """Walk upward inside mapped root to find nearest .git directory/file."""
        cur = resolve_path(host_dir)
        allowed_roots = [h_root for _, h_root in self.maps]
        while True:
            if not any(os.path.commonpath([r, cur]) == r for r in allowed_roots):
                return None, None
            # Refuse implicit bare repositories, including nested ones before a
            # parent worktree is discovered.
            if (os.path.isfile(os.path.join(cur, "HEAD")) and
                os.path.isdir(os.path.join(cur, "objects")) and
                os.path.isdir(os.path.join(cur, "refs"))):
                raise Refuse("git-bare-unsupported")
            dot_git = os.path.join(cur, ".git")
            if os.path.isdir(dot_git) or os.path.isfile(dot_git):
                return cur, dot_git
            parent = os.path.dirname(cur)
            if parent == cur:
                return None, None
            cur = parent

    def git_cfg_scan(self, host_dir: str) -> None:
        """Scan .git directory, config.worktree, and .git file; refuse unsafe directives."""
        repo_root, dot_git = self._find_git_root(host_dir)
        if dot_git is None or repo_root is None:
            raise Refuse("git-repository-unidentified")
        cfg_paths: list[Path] = []
        allowed_roots = [h_root for _, h_root in self.maps]
        if repo_root not in self.trusted_git_roots:
            raise Refuse("git-checkout-not-trusted")
        dg = Path(dot_git)
        real_dg = resolve_path(dot_git)
        if not any(os.path.commonpath([r, real_dg]) == r for r in allowed_roots):
            raise Refuse("symlink-escape")
        if any(self._is_protected_host(real_dg, r) for r in allowed_roots if os.path.commonpath([r, real_dg]) == r):
            raise Refuse("protected-path")
        if dg.is_file():
            try:
                with open_nofollow(dg) as fh:
                    raw = fh.read(4096).decode("utf-8", errors="replace").strip()
            except OSError as exc:
                raise Refuse("gitfile-unreadable") from exc
            if not raw.startswith("gitdir:"):
                raise Refuse("gitfile-malformed")
            target = raw[len("gitdir:") :].strip()
            if not target or os.path.isabs(target):
                raise Refuse("gitfile-absolute")
            resolved_gitdir = resolve_path(os.path.join(repo_root, target))
            if not any(os.path.commonpath([r, resolved_gitdir]) == r for r in allowed_roots):
                raise Refuse("symlink-escape")
            if not os.path.isdir(resolved_gitdir):
                raise Refuse("git-repository-unidentified")
            cfg_paths.append(Path(resolved_gitdir) / "config")
            cfg_paths.append(Path(resolved_gitdir) / "config.worktree")
            commondir = Path(resolved_gitdir) / "commondir"
            if commondir.is_file():
                try:
                    with open_nofollow(commondir) as cfh:
                        rel_c = cfh.read(4096).decode("utf-8", errors="replace").strip()
                except OSError as exc:
                    raise Refuse("gitfile-unreadable") from exc
                if not rel_c or os.path.isabs(rel_c):
                    raise Refuse("gitfile-absolute")
                cdir = resolve_path(os.path.join(resolved_gitdir, rel_c))
                if not any(os.path.commonpath([r, cdir]) == r for r in allowed_roots):
                    raise Refuse("symlink-escape")
                if not os.path.isdir(cdir):
                    raise Refuse("git-repository-unidentified")
                cfg_paths.append(Path(cdir) / "config")
                cfg_paths.append(Path(cdir) / "config.worktree")
        else:
            # A commondir on a non-gitfile layout is unsupported; do not ignore it.
            if os.path.lexists(dg / "commondir"):
                raise Refuse("git-commondir-unsupported")
            cfg_paths.append(dg / "config")
            cfg_paths.append(dg / "config.worktree")
            wt_dir = dg / "worktrees"
            if wt_dir.is_dir():
                for sub in wt_dir.iterdir():
                    if sub.is_dir():
                        cfg_paths.append(sub / "config")
                        cfg_paths.append(sub / "config.worktree")

        def check_metadata_path(path: str | Path) -> None:
            resolved = resolve_path(path)
            roots = [root for root in allowed_roots if os.path.commonpath([root, resolved]) == root]
            if not roots:
                raise Refuse("symlink-escape")
            if any(self._is_protected_host(resolved, root) for root in roots):
                raise Refuse("protected-path")

        for metadata_dir in {cfg.parent for cfg in cfg_paths}:
            objects = metadata_dir / "objects"
            pack_dir = objects / "pack"
            for candidate in (metadata_dir, objects, objects / "info", pack_dir):
                check_metadata_path(candidate)
            object_dirs = [pack_dir]
            if objects.is_dir():
                with os.scandir(objects) as entries:
                    for entry in entries:
                        if not re.fullmatch(r"[0-9a-fA-F]{2}", entry.name):
                            continue
                        # Validate a loose-object fan-out link before following it.
                        if entry.is_symlink():
                            check_metadata_path(entry.path)
                        if entry.is_dir():
                            object_dirs.append(Path(entry.path))
            for object_dir in object_dirs:
                if not object_dir.is_dir():
                    continue
                with os.scandir(object_dir) as entries:
                    for entry in entries:
                        if not entry.is_symlink():
                            continue
                        if object_dir == pack_dir:
                            m = _PACK_FILE_NAME.fullmatch(entry.name)
                            kind = m.group(1) if m else None
                        else:
                            kind = "obj" if _LOOSE_OBJECT_NAME.fullmatch(entry.name) else None
                        if kind is not None and self._is_l2s_object_link(entry.path, kind):
                            continue
                        check_metadata_path(entry.path)
            # Alternates can recursively redirect reads outside the map.
            if os.path.lexists(objects / "info/alternates"):
                raise Refuse("git-alternates-unsupported")
        for cfg in cfg_paths:
            check_metadata_path(cfg)
            if not cfg.is_file():
                continue
            try:
                with open_nofollow(cfg) as fh:
                    raw_cfg = fh.read(512 * 1024 + 1)
            except OSError as exc:
                raise Refuse("git-config-unreadable") from exc
            if len(raw_cfg) > 512 * 1024:
                raise Refuse("git-config-too-large")
            content = raw_cfg.decode("utf-8", errors="replace")
            # core.worktree changes Git's worktree root; conservatively refuse the key
            # in any section, including inline section forms.
            if re.search(r"(?im)(?:^\s*|\]\s*)worktree\s*(?:=|$)", content):
                raise Refuse("git-config-unsafe")
            if GIT_BAD_CFG.search(content):
                raise Refuse("git-config-unsafe")

        if dg.is_file() or dg.is_symlink():
            raise Refuse("git-worktree-not-supported")

    def clean_env(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        """Build a scrubbed deterministic environment for native/fallback child execution."""
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
        env["GIT_OPTIONAL_LOCKS"] = "0"
        # Protected command-scope config: reject implicit bare repository discovery.
        git_cfg = [("safe.bareRepository", "explicit")]
        if self.single_thread_git:
            # Budget mode counts one task per git child; these settings change speed, not output.
            git_cfg += [("core.preloadIndex", "false"), ("index.threads", "1"), ("grep.threads", "1"),
                        ("pack.threads", "1")]
        env["GIT_CONFIG_COUNT"] = str(len(git_cfg))
        for i, (key, val) in enumerate(git_cfg):
            env[f"GIT_CONFIG_KEY_{i}"] = key
            env[f"GIT_CONFIG_VALUE_{i}"] = val
        ceilings = sorted({os.path.dirname(h) for _, h in self.maps if os.path.dirname(h) and os.path.dirname(h) != h})
        if ceilings:
            env["GIT_CEILING_DIRECTORIES"] = ":".join(ceilings)
        if extra:
            for k, v in extra.items():
                if k in _ENV_KEEP and isinstance(v, str) and "\x00" not in v:
                    env[k] = v
        return env

    def _map_git_arg(self, sub: str, arg: str, cwd_guest: str, host_cwd: str) -> str:
        """Validate path-like git arguments against Policy boundaries."""
        if _has_l2s_component(arg):
            raise Refuse("l2s-path")
        if arg.startswith("/") or arg.startswith("./") or arg.startswith("../") or arg in (".", ".."):
            return self.map_path(arg, cwd=cwd_guest, must_exist=False)
        if ".." in arg.split("/"):
            return self.map_path(arg, cwd=cwd_guest, must_exist=False)
        # Check bare symlink name (no `/`) and any symlinked prefix (catches `escape/missing`).
        joined = os.path.join(host_cwd, arg)
        if is_link(joined) or os.path.lexists(joined):
            return self.map_path(arg, cwd=cwd_guest, must_exist=False)
        if "/" in arg:
            cur = host_cwd
            for comp in arg.split("/")[:-1]:
                if not comp:
                    continue
                cur = os.path.join(cur, comp)
                if is_link(cur):
                    return self.map_path(arg, cwd=cwd_guest, must_exist=False)
        return arg

    def validate_git_ro(self, args: list[str], cwd_guest: str) -> tuple[list[str], str, dict[str, str]]:
        """Validate read-only git arguments against strict per-subcommand allowlists."""
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
        spec = GIT_SUBCMD_SPECS.get(sub)
        if spec is None:
            raise Refuse("git-subcmd-denied")

        flags_no_val: frozenset[str] = spec["flags_no_val"]  # type: ignore[assignment]
        flags_eq_only: frozenset[str] = spec["flags_eq_only"]  # type: ignore[assignment]
        flags_val_req: frozenset[str] = spec["flags_val_req"]  # type: ignore[assignment]
        flags_int_attached: frozenset[str] = spec["flags_int_attached"]  # type: ignore[assignment]
        flags_path_val: frozenset[str] = spec["flags_path_val"]  # type: ignore[assignment]
        pos_mode: str = spec["pos_mode"]  # type: ignore[assignment]

        sub_args = args[i + 1 :]
        mapped_sub_args: list[str] = []
        seen_flags: set[str] = set()
        pos_count = 0
        j = 0
        while j < len(sub_args):
            a = sub_args[j]
            if not isinstance(a, str) or "\x00" in a:
                raise Refuse("bad-arg")

            if a == "--":
                if pos_mode in ("none", "exact_1_ref") or pos_mode.startswith("require_flag:"):
                    raise Refuse("git-write-arg-denied")
                mapped_sub_args.append(a)
                for rest in sub_args[j + 1 :]:
                    if not isinstance(rest, str) or "\x00" in rest:
                        raise Refuse("bad-arg")
                    mapped_sub_args.append(self._map_git_arg(sub, rest, cwd_guest, host_cwd))
                    pos_count += 1
                break

            if a.startswith("-") and a != "-":
                if "=" in a:
                    flag_name, flag_val = a.split("=", 1)
                    if flag_name in flags_path_val:
                        mapped_val = self.map_path(flag_val, cwd=cwd_guest, must_exist=False)
                        mapped_sub_args.append(f"{flag_name}={mapped_val}")
                        seen_flags.add(flag_name)
                        j += 1
                        continue
                    if flag_name in flags_eq_only or flag_name in flags_val_req:
                        if (
                            flag_val.startswith("/")
                            or flag_val.startswith("./")
                            or flag_val.startswith("../")
                            or ".." in flag_val.split("/")
                        ):
                            raise Refuse("git-option-denied")
                        mapped_sub_args.append(a)
                        seen_flags.add(flag_name)
                        j += 1
                        continue
                    raise Refuse("git-option-denied")

                # Attached short int flags like `-n10`, `-U3`, `-A2`, `-B2`, `-C2`
                attached_matched = False
                for pfx in flags_int_attached:
                    if len(a) > len(pfx) and a.startswith(pfx) and a[len(pfx) :].isdigit():
                        mapped_sub_args.append(a)
                        seen_flags.add(pfx)
                        attached_matched = True
                        break
                if attached_matched:
                    j += 1
                    continue

                if a in flags_no_val:
                    mapped_sub_args.append(a)
                    seen_flags.add(a)
                    j += 1
                    continue

                if a in flags_path_val:
                    if j + 1 >= len(sub_args) or not isinstance(sub_args[j + 1], str):
                        raise Refuse("git-flag-missing-arg")
                    mapped_val = self.map_path(sub_args[j + 1], cwd=cwd_guest, must_exist=False)
                    mapped_sub_args.extend([a, mapped_val])
                    seen_flags.add(a)
                    j += 2
                    continue

                if a in flags_val_req:
                    if j + 1 >= len(sub_args) or not isinstance(sub_args[j + 1], str) or "\x00" in sub_args[j + 1]:
                        raise Refuse("git-flag-missing-arg")
                    val = sub_args[j + 1]
                    if val.startswith("-") or val.startswith("/") or val.startswith("./") or val.startswith("../") or ".." in val.split("/"):
                        raise Refuse("git-option-denied")
                    mapped_sub_args.extend([a, val])
                    seen_flags.add(a)
                    j += 2
                    continue

                raise Refuse("git-option-denied")

            # Positional argument
            if pos_mode == "none":
                raise Refuse("git-write-arg-denied")
            if pos_mode.startswith("require_flag:"):
                req_set = set(pos_mode.split(":", 1)[1].split(","))
                if not (seen_flags & req_set):
                    raise Refuse("git-write-arg-denied")
                # Also reject ref-creation style `git branch -f` or multi-arg create even with flags
                if sub == "tag" and pos_count >= 1 and "--list" not in seen_flags:
                    raise Refuse("git-write-arg-denied")
            if pos_mode == "paths_only":
                mapped_sub_args.append(self.map_path(a, cwd=cwd_guest, must_exist=False))
            else:
                mapped_sub_args.append(self._map_git_arg(sub, a, cwd_guest, host_cwd))
            pos_count += 1
            j += 1

        if pos_mode == "exact_1_ref" and pos_count != 1:
            raise Refuse("git-write-arg-denied")

        self.git_cfg_scan(host_cwd)

        clean_args = list(out_pre)
        clean_args.append(sub)
        if sub in GIT_NOEXT_DIFF_SUBS:
            clean_args.append("--no-ext-diff")
        if sub in GIT_NOTEXTCONV_SUBS:
            clean_args.append("--no-textconv")
        clean_args.extend(mapped_sub_args)
        return clean_args, host_cwd, self.clean_env()
