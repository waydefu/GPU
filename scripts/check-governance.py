"""Validate published evidence and screen active text without logging matched values."""

import ipaddress
import os
import re
import subprocess
import sys
from pathlib import Path

ACTIVE = (
    "HANDOFF.md", "AGENTS.md", "WORKTREE-MAP.md", "README.md", "TEST-MATRIX.md",
    ".claude/rules/gpu-structure.md", ".github/workflows", "docs/governance-checks.md",
    "scripts", "patches/run_tiny_pixmap.py",
)

# Prior captures remain immutable everywhere. Closed tracks also reject new files.
CLOSED = (
    "docs/archive/handoffs/", "evidence/baseline/", "evidence/control/", "evidence/nonlegacy/",
    "evidence/session/gate-a-a1/", "evidence/session/gl/", "evidence/session/p2-",
    "evidence/session/s3/", "evidence/session/tiny-pixmap/", "evidence/session/xfce-v6/",
)
SHA = re.compile(r"[a-f0-9]{40}")
LOCAL_PATH = re.compile(r"/root/\.gemini/")
CREDENTIAL = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{22,}"
    r"|AIza[0-9A-Za-z_-]{35}|ya29\.[0-9A-Za-z._-]{20,}|(?:AKIA|ASIA)[A-Z0-9]{16}"
    r"|glpat-[A-Za-z0-9_-]{20,}|xox[baprs]-[0-9A-Za-z-]{20,}"
    r"|(?:sk|rk)_live_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{32,}|npm_[A-Za-z0-9]{30,})\b"
    r"|-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"
    r"|(?i:aws_secret_access_key|authorization\s*:\s*bearer)\s*[:=]?\s*['\"]?[A-Za-z0-9/+=_.-]{24,}"
)
ENDPOINT = re.compile(
    r"(?<![\w.])(?P<v4>(?:[0-9]{1,3}\.){3}[0-9]{1,3}):(?P<p4>[0-9]{1,5})(?![\w.])"
    r"|\[(?P<v6>[A-Fa-f0-9:.]+)(?:%[\w.-]+)?\]:(?P<p6>[0-9]{1,5})(?![\w.])"
)
LAN = tuple(ipaddress.ip_network(net) for net in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16",
    "100.64.0.0/10", "fc00::/7", "fe80::/10",
))


def git(*args):
    return subprocess.check_output(["git", *args])


def guard_frozen(base, head, event):
    if not SHA.fullmatch(base) or not SHA.fullmatch(head) or git("rev-parse", "HEAD").decode().strip() != head:
        raise ValueError("missing or mismatched comparison SHA")
    if event not in ("pull_request", "push"):
        raise ValueError("missing or unsupported governance event")
    if event == "pull_request" and git("rev-parse", f"{head}^1").decode().strip() != base:
        raise ValueError("checkout does not match the pull request base")
    subprocess.run(["git", "merge-base", "--is-ancestor", base, head], check=True)
    diff = git("diff", "--name-status", "-z", "--no-renames", base, head, "--", "evidence/", "docs/archive/handoffs/")
    if not diff:
        return []
    fields = os.fsdecode(diff).rstrip("\0").split("\0")
    if len(fields) % 2:
        raise ValueError("incomplete frozen evidence diff")
    return [
        (status, path) for status, path in zip(fields[::2], fields[1::2])
        if status != "A" or path.startswith(CLOSED)
    ]


def lan_endpoint(text):
    for match in ENDPOINT.finditer(text):
        try:
            address = ipaddress.ip_address(match["v4"] or match["v6"])
        except ValueError:
            continue
        if 0 < int(match["p4"] or match["p6"]) <= 65535:
            address = getattr(address, "ipv4_mapped", None) or address
            if any(address in network for network in LAN):
                return True
    return False


def content_flags(text):
    return [
        kind for kind, violation in (
            ("local session path", LOCAL_PATH.search(text)),
            ("credential pattern", CREDENTIAL.search(text)),
            ("private LAN endpoint", lan_endpoint(text)),
        ) if violation
    ]


def scan_active():
    files = os.fsdecode(git("ls-files", "-z", "--", *ACTIVE)).rstrip("\0").split("\0")
    if not all(Path(path).exists() for path in ACTIVE) or "" in files:
        raise ValueError("active scan inputs missing")
    blocked = False
    for name in files:
        path = Path(name)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"active scan input is not a regular file: {name!r}")
        if content_flags(name):
            print("Blocked active file with sensitive path name", file=sys.stderr)
            blocked = True
            continue
        flags = content_flags(path.read_text(encoding="utf-8", errors="replace"))
        if flags:
            print(f"Blocked {name!r}: {', '.join(flags)}", file=sys.stderr)
            blocked = True
    return int(blocked)


def main():
    command = sys.argv[1:]
    try:
        if command == ["scan"]:
            return scan_active()
        if command == ["freeze"]:
            blocked = guard_frozen(os.environ["COMPARE_BASE"], os.environ["GITHUB_SHA"], os.environ["GITHUB_EVENT_NAME"])
            for status, path in blocked:
                print(f"Frozen evidence change: {status} {path!r}", file=sys.stderr)
            return int(bool(blocked))
        raise ValueError("expected scan or freeze")
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Governance check failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
