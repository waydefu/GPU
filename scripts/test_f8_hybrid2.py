#!/usr/bin/env python3
"""Acceptance & regression tests for Stage 7.2 universal Native Hybrid 2.0 backend.

Covers all Neon + Hydrogen review gates:
- Policy & Stage 5 security parity (`protected-path` incl. `//etc/passwd` and protected subtree
  inside mapped parent, symlink-escape, `.l2s.*`, `git diff --no-index`, `git grep -f/etc/passwd`,
  `git blame --contents=escape/...`, single-line `[core] fsmonitor = true`, `config.worktree`,
  `filter.process`, `commondir`, `GIT_CEILING_DIRECTORIES`, FIFO non-blocking O_NOFOLLOW)
- MCP state machine (`initialize` gating), canonical `req_id` (`int` vs `str`, `bool` rejected),
  duplicate active `req_id`, strict int arg rejection (`null`/non-int -> `-32602` even in fallback),
  UTF-8 byte-safe payload trimming for both `entries` and `stdout`+`stderr` with `\x1b`,
  OOM/ReDoS/jsonl-line limits
- Multi-client (`4+`) concurrency & isolation, `--max-inflight` deterministic `-32000`,
  `--max-clients` `-32000`, `SIGKILL` disconnect + strict `fds == base_fds`
- Race-free `idle_timeout` + backlog drain + immediate `d.pid` release + `ready` inode guard
- Unified `ctl` CLI (`start/stop/restart/status/probe/disable/enable/ensure-running/client-config`)
  under thundering-herd and stripped 7-env (`env -i`), plus fallback parity across all 4 tools.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import signal
import socket
import stat
import subprocess as sp
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import f8_hybrid2_ctl as ctl
from f8_hybrid2_policy import Policy, Refuse, read_tracer_pid
from f8_hybrid2_tools import MAX_JSONL_LINE_BYTES, MCPToolEngine, RequestContext, _fit_json_payload

DAEMON_PY = HERE / "f8_hybrid2_daemon.py"
RELAY_PY = HERE / "f8_hybrid2_relay.py"
CTL_PY = HERE / "f8_hybrid2_ctl.py"
DEFAULT_TERMUX_GIT = "/data/data/com.termux/files/usr/bin/git"
SYSTEM_GIT = DEFAULT_TERMUX_GIT if os.path.exists(DEFAULT_TERMUX_GIT) else shutil.which("git") or "git"


def proc_count_fds(pid: int) -> int:
    return len(os.listdir(f"/proc/{pid}/fd"))


def children_of(pid: int) -> list[int]:
    kids: list[int] = []
    for d in Path("/proc").iterdir():
        if d.name.isdigit():
            try:
                st = (d / "stat").read_text(encoding="utf-8", errors="replace")
                ppid = int(st.rsplit(")", 1)[1].split()[1])
                if ppid == pid:
                    kids.append(int(d.name))
            except (OSError, ValueError, IndexError):
                pass
    return kids


def git_run(args: list[str], cwd: Path) -> None:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(cwd),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    sp.run([SYSTEM_GIT, *args], cwd=cwd, env=env, check=True, stdout=sp.PIPE, stderr=sp.PIPE)


class PolicyAndSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = Path(tempfile.mkdtemp(prefix="hyb2_pol_"))
        self.ws = self.tmp_root / "ws"
        self.sub = self.ws / "sub"
        self.repo = self.ws / "repo"
        self.outside = self.tmp_root / "outside"
        self.home = self.tmp_root / "hhome"
        self.htmp = self.tmp_root / "htmp"
        for d in (self.sub, self.repo, self.outside, self.home, self.htmp):
            d.mkdir(parents=True, exist_ok=True)
        (self.ws / "a.py").write_text("print('ok')\n", encoding="utf-8")
        (self.outside / "secret.txt").write_text("no-access\n", encoding="utf-8")
        os.symlink(str(self.outside), str(self.ws / "escape"))
        os.symlink(str(self.outside), str(self.repo / "escape"))

        git_run(["init", "-q"], self.repo)
        (self.repo / "hello.txt").write_text("hello world\nneedle line\n", encoding="utf-8")
        git_run(["add", "hello.txt"], self.repo)
        git_run(["commit", "-q", "-m", "init"], self.repo)

        self.pol = Policy([("/ws", str(self.ws))], home=str(self.home), tmp=str(self.htmp))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _refused(self, expected: str, fn, *args, **kwargs) -> None:
        with self.assertRaises(Refuse) as cm:
            fn(*args, **kwargs)
        self.assertIn(expected, str(cm.exception))

    def test_protected_double_slash_l2s_and_symlink_to_protected(self) -> None:
        self._refused("protected-path", self.pol.map_path, "/etc/passwd")
        self._refused("protected-path", self.pol.map_path, "//etc/passwd")
        self._refused("protected-path", self.pol.map_path, "/usr/lib")
        self._refused("protected-path", self.pol.map_path, "/root/." + "gemini/x")
        self._refused("protected-path", self.pol.map_path, "/root/.hermes/config.yaml")
        self._refused("protected-path", self.pol.map_path, "/root/.codex/auth.json")
        self._refused("protected-path", self.pol.map_path, "/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8")
        self._refused("protected-path", self.pol.map_path, "/data/data/com.termux/files/home/.f8hyb2/m.sock")
        self._refused("protected-path", self.pol.map_path, "../../etc/hosts", cwd="/ws/sub")
        self._refused("path-outside-map", self.pol.map_path, "/root/x")
        self._refused("path-outside-map", self.pol.map_path, "/wsx/y")
        self._refused("path-outside-map", self.pol.map_path, "sub/../../x", cwd="/ws")
        self._refused("l2s-path", self.pol.map_path, "/ws/.l2s.a0001")
        self._refused("l2s-path", self.pol.map_path, ".l2s.x", cwd="/ws")
        self._refused("symlink-escape", self.pol.map_path, "/ws/escape/secret.txt")
        self._refused("bad-path", self.pol.map_path, "/ws/a\x00b")

        # Symlink inside mapped parent targeting a PROTECTED subtree (simulated /root mapping)
        if Path("/root/.hermes").exists():
            root_pol = Policy([("/root", "/root")], home=str(self.home), tmp=str(self.htmp))
            self._refused("protected-path", root_pol.map_path, "/root/.hermes/config.yaml")
            root_pol_parent = Policy([("/p", str(self.ws))], home=str(self.home), tmp=str(self.htmp))
            os.symlink("/root/.hermes", str(self.ws / "hermes_link"))
            self._refused("symlink-escape", root_pol_parent.map_path, "/p/hermes_link/config.yaml")

        mapped = self.pol.map_path("sub/../a.py", cwd="/ws", must_exist=True)
        self.assertEqual(mapped, str((self.ws / "a.py").resolve()))

    def test_git_readonly_allowlist_and_bypass_denies(self) -> None:
        ok_cmds = (
            ["status", "--short"],
            ["log", "-n", "1"],
            ["rev-parse", "HEAD"],
            ["rev-parse", "--abbrev-ref", "HEAD"],
            ["ls-files"],
            ["grep", "-n", "init"],
            ["diff"],
            ["diff", "--", "/ws/repo/hello.txt"],
            ["-C", "/ws/repo", "show", "--stat", "HEAD"],
            ["branch"],
            ["branch", "--show-current"],
            ["branch", "--list", "m*"],
            ["tag"],
            ["tag", "--list", "v*"],
            ["symbolic-ref", "HEAD"],
            ["symbolic-ref", "--short", "HEAD"],
            ["for-each-ref", "--format=%(refname)", "refs/heads"],
            ["count-objects", "-v"],
        )
        for cmd in ok_cmds:
            clean, hcwd, env = self.pol.validate_git_ro(cmd, "/ws/repo")
            self.assertEqual(hcwd, str(self.repo.resolve()))
            self.assertEqual(env["GIT_CONFIG_GLOBAL"], "/dev/null")
            self.assertEqual(env["GIT_OPTIONAL_LOCKS"], "0")
            self.assertIn("GIT_CEILING_DIRECTORIES", env)
            if "diff" in cmd or "show" in cmd:
                self.assertIn("--no-ext-diff", clean)
                self.assertIn("--no-textconv", clean)
            if "grep" in cmd:
                self.assertNotIn("--no-ext-diff", clean)
                self.assertIn("--no-textconv", clean)

        denied = (
            ("git-subcmd-denied", ["commit", "-m", "x"]),
            ("git-subcmd-denied", ["push"]),
            ("git-subcmd-denied", ["checkout", "."]),
            ("git-subcmd-denied", ["reset", "--hard"]),
            ("git-subcmd-denied", ["config", "user.name", "x"]),
            # Strict write/create prevention on branch, tag, symbolic-ref, for-each-ref, etc.
            ("git-write-arg-denied", ["branch", "evil"]),
            ("git-option-denied", ["branch", "-l", "evil"]),
            ("git-option-denied", ["branch", "-D", "main"]),
            ("git-option-denied", ["branch", "-f", "main"]),
            ("git-option-denied", ["branch", "-m", "old", "new"]),
            ("git-write-arg-denied", ["tag", "v1"]),
            ("git-option-denied", ["tag", "-a", "v1", "-m", "x"]),
            ("git-option-denied", ["tag", "-d", "v1"]),
            ("git-option-denied", ["tag", "-l", "v1"]),
            ("git-write-arg-denied", ["symbolic-ref", "HEAD", "refs/heads/evil"]),
            ("git-write-arg-denied", ["symbolic-ref"]),
            ("git-option-denied", ["symbolic-ref", "-d", "HEAD"]),
            ("git-option-denied", ["symbolic-ref", "--delete", "HEAD"]),
            ("git-option-denied", ["for-each-ref", "--shell"]),
            ("git-option-denied", ["rev-parse", "--sq-quote", "x"]),
            ("git-write-arg-denied", ["count-objects", "extra"]),
            ("git-pre-flag-denied", ["-c", "core.pager=cat", "status"]),
            ("git-pre-flag-denied", ["--git-dir=/etc", "status"]),
            ("git-option-denied", ["diff", "--ext-diff"]),
            ("git-option-denied", ["diff", "--no-index", "/etc/passwd", "/dev/null"]),
            ("git-option-denied", ["grep", "--no-index", "root", "/etc/passwd"]),
            ("git-option-denied", ["grep", "-f", "/etc/passwd", "x"]),
            ("git-option-denied", ["grep", "-f/etc/passwd", "x"]),
            ("git-option-denied", ["grep", "-Ocat", "x"]),
            ("git-option-denied", ["log", "--output=/tmp/x"]),
            ("git-option-denied", ["log", "--unknown-flag"]),
            ("git-option-denied", ["status", "--upload-pack=evil"]),
            # Neon Round-3 OPTARG / `=`-only bypass PoCs MUST all be refused!
            ("git-write-arg-denied", ["branch", "--abbrev", "evil"]),
            ("git-option-denied", ["branch", "--abbrev", "-f", "--abbrev", "main"]),
            ("git-option-denied", ["diff", "-U", "--output=/tmp/pwned"]),
            ("git-option-denied", ["diff", "-U", "--ext-diff"]),
            ("git-option-denied", ["diff", "-U", "--no-index", "escape/secret.txt", "hello.txt"]),
            ("git-option-denied", ["log", "--pretty", "--output=/tmp/pwned", "-n1"]),
            ("git-option-denied", ["show", "-U", "--output=/tmp/pwned", "HEAD"]),
            ("protected-path", ["blame", "-M", "--contents=/etc/passwd", "hello.txt"]),
            ("git-option-denied", ["status", "-u", "--output=/tmp/x"]),
            ("protected-path", ["log", "--", "/etc/passwd"]),
            ("path-outside-map", ["diff", "--", "../../outside/secret.txt"]),
            ("symlink-escape", ["blame", "--contents=escape/secret.txt", "HEAD", "--", "hello.txt"]),
            ("symlink-escape", ["status", "--", "escape"]),
            ("symlink-escape", ["log", "--", "escape/missing"]),
            ("l2s-path", ["log", "--", ".l2s.foo"]),
        )
        for reason, cmd in denied:
            self._refused(reason, self.pol.validate_git_ro, cmd, "/ws/repo")

    def test_git_config_inline_worktree_filter_and_gitfile(self) -> None:
        cfg = self.repo / ".git/config"
        wt_cfg = self.repo / ".git/config.worktree"
        base = cfg.read_text(encoding="utf-8")
        try:
            for bad in (
                '[filter "lfs"]\n\tclean = evil\n',
                '[filter "x"]\n\tprocess = evil\n',
                '[diff "x"]\n\tcommand = evil\n',
                '[core] fsmonitor = true\n',
                '[diff "x"] command = evil\n',
                '[include]\n\tpath = /x\n',
                '[diff "x"]\n\ttextconv = evil\n',
                '[core]\n\tpager = evil\n',
                '[core]\n\tsshCommand = evil\n',
                '[includeIf "gitdir:/"]\n\tpath = x\n',
            ):
                cfg.write_text(base + bad, encoding="utf-8")
                self._refused("git-config-unsafe", self.pol.validate_git_ro, ["status"], "/ws/repo")

            cfg.write_text(base + "#" + ("x" * (520 * 1024)), encoding="utf-8")
            self._refused("git-config-too-large", self.pol.validate_git_ro, ["status"], "/ws/repo")

            cfg.write_text(base + "[user]\n\tname = ok\n", encoding="utf-8")
            self.pol.validate_git_ro(["status"], "/ws/repo")

            wt_cfg.write_text('[core] fsmonitor = evil\n', encoding="utf-8")
            self._refused("git-config-unsafe", self.pol.validate_git_ro, ["status"], "/ws/repo")
        finally:
            cfg.write_text(base, encoding="utf-8")
            wt_cfg.unlink(missing_ok=True)

        wt = self.ws / "wt"
        wt.mkdir(exist_ok=True)
        (wt / ".git").write_text("gitdir: /root/projects/x/.git/worktrees/wt\n", encoding="utf-8")
        self._refused("gitfile-absolute", self.pol.validate_git_ro, ["status"], "/ws/wt")
        (wt / ".git").write_text("garbage\n", encoding="utf-8")
        self._refused("gitfile-malformed", self.pol.validate_git_ro, ["status"], "/ws/wt")
        (wt / ".git").write_text("gitdir: ../escape/.git\n", encoding="utf-8")
        self._refused("symlink-escape", self.pol.validate_git_ro, ["status"], "/ws/wt")

        real_gd = self.ws / "real_gd"
        real_gd.mkdir()
        (real_gd / "commondir").write_text("/etc/git\n", encoding="utf-8")
        (wt / ".git").write_text("gitdir: ../real_gd\n", encoding="utf-8")
        self._refused("gitfile-absolute", self.pol.validate_git_ro, ["status"], "/ws/wt")

    def test_env_utf8_fit_fifo_jsonl_limits_and_client_config(self) -> None:
        os.environ["LANG"] = "en_US.UTF-8"
        env = self.pol.clean_env({"LANG": "C.UTF-8", "LD_PRELOAD": "/evil.so", "GH_TOKEN": "tok"})
        self.assertEqual(env["LANG"], "C.UTF-8")
        self.assertEqual(env["PYTHONNOUSERSITE"], "1")
        self.assertEqual(env["GIT_OPTIONAL_LOCKS"], "0")
        self.assertNotIn("LD_PRELOAD", env)
        self.assertNotIn("GH_TOKEN", env)

        # UTF-8 multibyte truncation for both entries and stdout+stderr with \x1b escapes
        big = {
            "tool": "repo_tree_scan",
            "truncated": False,
            "entries": [{"rel": f"中文_{i}.txt", "size": i} for i in range(500)],
        }
        fitted = _fit_json_payload(big, limit_bytes=512)
        self.assertLessEqual(len(fitted.encode("utf-8")), 512)
        self.assertTrue(json.loads(fitted)["truncated"])

        big_git = {
            "tool": "git_ro",
            "stdout": "\x1b" * 1024,
            "stderr": "\x1b" * 50000,
        }
        fitted_git = _fit_json_payload(big_git, limit_bytes=512)
        self.assertLessEqual(len(fitted_git.encode("utf-8")), 512)
        self.assertTrue(json.loads(fitted_git)["truncated"])

        eng = MCPToolEngine(self.pol, git_bin=SYSTEM_GIT)
        # Strict int parameter rejection (no hang/TypeError)
        r_bad_int = eng.call_tool(1, {"name": "repo_tree_scan", "arguments": {"root": "/ws", "max_entries": None}}, RequestContext(1, 2.0))
        self.assertEqual(r_bad_int["error"]["code"], -32602)

        # FIFO inside workspace must NOT block
        os.mkfifo(str(self.ws / "pipe.fifo"))
        r_fifo = eng.call_tool(2, {"name": "repo_tree_scan", "arguments": {"root": "/ws"}}, RequestContext(2, 2.0))
        self.assertFalse(r_fifo["result"]["isError"])

        # Oversize search file (>2 MiB) reported via skipped_oversize/truncated
        (self.ws / "huge.txt").write_bytes(b"abc\n" * 600000)
        r_srch = eng.call_tool(3, {"name": "repo_text_search", "arguments": {"root": "/ws", "pattern": "abc"}}, RequestContext(3, 4.0))
        d_srch = json.loads(r_srch["result"]["content"][0]["text"])
        self.assertGreaterEqual(d_srch["skipped_oversize"], 1)
        self.assertTrue(d_srch["truncated"])

        # Neon Round-3 `--regex-worker` >2 MiB stdout truncation must NOT throw JSONDecodeError (-32603)
        big_dir = self.ws / "many_matches"
        big_dir.mkdir(exist_ok=True)
        line_300 = ("Z" * 300) + "\n"
        for fi in range(6):
            (big_dir / f"m{fi}.txt").write_text(line_300 * 1000, encoding="utf-8")
        r_big_rx = eng.call_tool(
            31,
            {"name": "repo_text_search", "arguments": {"root": "/ws/many_matches", "pattern": "Z{300}", "max_matches": 5000}},
            RequestContext(31, 8.0),
        )
        self.assertFalse(r_big_rx["result"]["isError"])
        d_big_rx = json.loads(r_big_rx["result"]["content"][0]["text"])
        self.assertTrue(d_big_rx["truncated"])
        self.assertLessEqual(len(r_big_rx["result"]["content"][0]["text"].encode("utf-8")), 1024 * 1024)

        # Oversize single line in .jsonl refused cleanly
        (self.ws / "longline.jsonl").write_bytes(b'{"a":"' + (b"x" * (MAX_JSONL_LINE_BYTES + 128)) + b'"}\n')
        r_jsonl = eng.call_tool(4, {"name": "python_json_summary", "arguments": {"path": "/ws/longline.jsonl"}}, RequestContext(4, 3.0))
        self.assertEqual(r_jsonl["error"]["code"], -32602)
        self.assertIn("jsonl-line-too-large", r_jsonl["error"]["message"])

        # Verify ctl client-config outputs --auto-start for every client & valid JSON for JSON clients
        snips = ctl.client_config_snippets("/tmp/test.sock")
        for cname, snip in snips.items():
            self.assertIn("--auto-start", snip, cname)
        for k in ("claude-desktop", "antigravity", "opencode"):
            obj = json.loads(snips[k])
            self.assertIsInstance(obj, dict)

    def test_jsonrpc_control_and_fuzz(self) -> None:
        eng = MCPToolEngine(self.pol, git_bin=SYSTEM_GIT)
        resp_uninit, _ = eng.handle_sync_control({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, initialized=False)
        self.assertEqual(resp_uninit["error"]["code"], -32002)
        resp_bool, _ = eng.handle_sync_control({"jsonrpc": "2.0", "id": True, "method": "initialize"}, initialized=False)
        self.assertEqual(resp_bool["error"]["code"], -32600)

        rnd = random.Random(1234)
        for _ in range(3000):
            choice = rnd.randrange(4)
            if choice == 0:
                bad_obj: object = rnd.randrange(100)
            elif choice == 1:
                bad_obj = {"jsonrpc": "1.0", "id": 1}
            elif choice == 2:
                bad_obj = {"jsonrpc": "2.0", "id": 1, "method": "bad_" + str(rnd.randrange(999))}
            else:
                bad_obj = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": rnd.randrange(5)}
            resp, action = eng.handle_sync_control(bad_obj, initialized=True)
            if action == "tools/call":
                r = eng.call_tool(1, bad_obj.get("params"), RequestContext(1, 1.0))  # type: ignore[union-attr]
                self.assertIn("error", r)
            else:
                self.assertIn("error", resp)


class UniversalDaemonAndCtlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="hyb2_"))
        self.ws = self.base / "ws"
        self.repo = self.ws / "repo"
        self.rdir = self.base / "r"
        self.sock = self.rdir / "m.sock"
        self.pidfile = self.rdir / "d.pid"
        self.ready = self.rdir / "ready"
        self.log = self.rdir / "audit.jsonl"
        for d in (self.ws, self.repo, self.rdir):
            d.mkdir(parents=True, exist_ok=True)

        git_run(["init", "-q"], self.repo)
        (self.repo / "readme.md").write_text("Stage 7.2 Universal MCP\nneedle line\n", encoding="utf-8")
        git_run(["add", "readme.md"], self.repo)
        git_run(["commit", "-q", "-m", "init"], self.repo)

        self.big = self.ws / "bigtree"
        for d_idx in range(15):
            sub = self.big / f"d{d_idx:02d}"
            sub.mkdir(parents=True, exist_ok=True)
            for f_idx in range(100):
                (sub / f"f{f_idx:03d}.txt").write_text(f"payload {d_idx}-{f_idx}\n" * 80, encoding="utf-8")

        (self.ws / "sample.jsonl").write_text(
            "".join(json.dumps({"i": i, "ok": True}) + "\n" for i in range(500)),
            encoding="utf-8",
        )
        self.proc: sp.Popen[bytes] | None = None

    def tearDown(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
            try:
                self.proc.wait(timeout=5)
            except sp.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        ctl.stop_daemon(self.rdir, timeout_s=3.0)
        shutil.rmtree(self.base, ignore_errors=True)

    def _start_daemon(self, extra: list[str] | None = None) -> sp.Popen[bytes]:
        skip_tracer = os.environ.get("F8_HYBRID2_NATIVE") != "1"
        cmd = [
            sys.executable,
            str(DAEMON_PY),
            "--socket",
            str(self.sock),
            "--map",
            f"/ws={self.ws}",
            "--home",
            str(self.base / "h"),
            "--tmp",
            str(self.base / "t"),
            "--pidfile",
            str(self.pidfile),
            "--ready",
            str(self.ready),
            "--log",
            str(self.log),
            "--git-bin",
            SYSTEM_GIT,
        ]
        if skip_tracer:
            cmd.append("--skip-tracer-check")
        if extra:
            cmd.extend(extra)
        out_f = open(self.rdir / "daemon.out", "ab")
        p = sp.Popen(cmd, stdin=sp.DEVNULL, stdout=out_f, stderr=out_f, start_new_session=True)
        out_f.close()
        for _ in range(100):
            if self.sock.exists() and self.ready.exists() and self.pidfile.exists():
                if not skip_tracer:
                    self.assertEqual(read_tracer_pid(p.pid), 0)
                return p
            if p.poll() is not None:
                raise RuntimeError((self.rdir / "daemon.out").read_text(encoding="utf-8", errors="replace"))
            time.sleep(0.05)
        raise RuntimeError("daemon failed to become ready")

    @staticmethod
    def _uds_rpc(sock_path: Path) -> tuple[socket.socket, any]:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(10.0)
        s.connect(str(sock_path))
        return s, s.makefile("rb")

    @staticmethod
    def _send(s: socket.socket, obj: dict) -> None:
        s.sendall((json.dumps(obj) + "\n").encode("utf-8"))

    def test_overlong_socket_single_instance_and_perms(self) -> None:
        long_dir = self.base / ("x" * 110)
        r = sp.run(
            [
                sys.executable, str(DAEMON_PY), "--socket", str(long_dir / "m.sock"),
                "--map", f"/ws={self.ws}", "--home", str(self.base / "h"), "--tmp", str(self.base / "t"),
                "--pidfile", str(self.base / "long.pid"), "--skip-tracer-check",
            ],
            capture_output=True, timeout=10,
        )
        self.assertEqual(r.returncode, 4)
        self.assertIn(b"AF_UNIX limit", r.stderr)
        self.assertFalse(long_dir.exists())

        self.proc = self._start_daemon()
        self.assertEqual(stat.S_IMODE(os.stat(self.sock).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(self.rdir).st_mode), 0o700)

        second = sp.run(
            [
                sys.executable, str(DAEMON_PY), "--socket", str(self.sock),
                "--map", f"/ws={self.ws}", "--home", str(self.base / "h"), "--tmp", str(self.base / "t"),
                "--pidfile", str(self.pidfile), "--skip-tracer-check",
            ],
            capture_output=True, timeout=10,
        )
        self.assertEqual(second.returncode, 3)

    def test_4clients_max_clients_max_inflight_cancel_and_strict_fd(self) -> None:
        self.proc = self._start_daemon(["--max-clients", "4", "--max-inflight", "1"])
        base_fds = proc_count_fds(self.proc.pid)

        clients = [self._uds_rpc(self.sock) for _ in range(4)]
        try:
            # 5th client exceeds --max-clients=4 -> gets -32000
            s5, f5 = self._uds_rpc(self.sock)
            busy5 = json.loads(f5.readline())
            self.assertEqual(busy5["error"]["code"], -32000)
            f5.close()
            s5.close()

            for s, f in clients:
                self._send(s, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}})
                self.assertEqual(json.loads(f.readline())["result"]["protocolVersion"], "2025-11-25")

            # Uninitialized check on fresh reconnect tested separately; test duplicate req_id + deterministic max-inflight=1
            sa, fa = clients[0]
            sb, fb = clients[1]
            self._send(sa, {"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"name": "repo_tree_scan", "arguments": {"root": "/ws/bigtree"}}})
            time.sleep(0.02)
            # While sa holds the sole inflight slot, sb MUST deterministically receive -32000
            self._send(sb, {"jsonrpc": "2.0", "id": 11, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["rev-parse", "HEAD"]}}})
            r_b_busy = json.loads(fb.readline())
            self.assertEqual(r_b_busy["error"]["code"], -32000)

            r_a10 = json.loads(fa.readline())
            self.assertEqual(r_a10["id"], 10)

            # Concurrent 4-client isolation: cancel on client A does not affect client B..D
            self._send(sa, {"jsonrpc": "2.0", "id": 20, "method": "tools/call", "params": {"name": "repo_tree_scan", "arguments": {"root": "/ws/bigtree"}}})
            time.sleep(0.02)
            self._send(sa, {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 20}})
            for _ in range(50):
                if self.log.exists() and '"req_id": 20' in self.log.read_text(encoding="utf-8"):
                    break
                time.sleep(0.02)
            time.sleep(0.02)

            for idx, (sc, fc) in enumerate(clients):
                self._send(sc, {"jsonrpc": "2.0", "id": 30 + idx, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["status", "--short"]}}})
                rc = json.loads(fc.readline())
                self.assertEqual(rc["id"], 30 + idx)
                self.assertEqual(json.loads(rc["result"]["content"][0]["text"])["returncode"], 0)

            # git_ro 1ms timeout -> -32001 & children==0
            self._send(sa, {"jsonrpc": "2.0", "id": 40, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["log", "--all", "--stat"], "timeout_s": 0.001}}})
            self.assertEqual(json.loads(fa.readline())["error"]["code"], -32001)
            self.assertEqual(children_of(self.proc.pid), [])
        finally:
            for s, f in clients:
                f.close()
                s.close()

        time.sleep(0.25)
        self.assertEqual(proc_count_fds(self.proc.pid), base_fds)

        # Also test 4 concurrent clients executing tools simultaneously with --max-inflight 4
        ctl.stop_daemon(self.rdir, timeout_s=3.0)
        self.proc.wait(timeout=5)
        self.proc = self._start_daemon(["--max-clients", "4", "--max-inflight", "4"])
        clients4 = [self._uds_rpc(self.sock) for _ in range(4)]
        try:
            for idx, (sc, fc) in enumerate(clients4):
                self._send(sc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})
                json.loads(fc.readline())
            for idx, (sc, _fc) in enumerate(clients4):
                self._send(sc, {"jsonrpc": "2.0", "id": 50 + idx, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["rev-parse", "HEAD"]}}})
            for idx, (_sc, fc) in enumerate(clients4):
                r4 = json.loads(fc.readline())
                self.assertEqual(r4["id"], 50 + idx)
                self.assertEqual(json.loads(r4["result"]["content"][0]["text"])["returncode"], 0)
        finally:
            for s, f in clients4:
                f.close()
                s.close()

    def test_idle_exit_pid_release_backlog_and_ready_inode_guard(self) -> None:
        self.proc = self._start_daemon(["--idle-timeout", "0.3"])
        old_pid = self.proc.pid
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and self.sock.exists():
            time.sleep(0.02)
        self.assertFalse(self.sock.exists())

        # Immediately launch replacement daemon -> must NOT hit pidfile-locked even right as D1 exits!
        skip_native = os.environ.get("F8_HYBRID2_NATIVE") != "1"
        new_res = ctl.ensure_running(self.rdir, daemon_py=str(DAEMON_PY), maps=[f"/ws={self.ws}"], idle_timeout=0.0, skip_tracer_check=skip_native)
        self.assertTrue(new_res["ok"], new_res)
        self.assertNotEqual(new_res["pid"], old_pid)
        self.assertEqual(self.proc.wait(timeout=8), 0)
        # Old daemon exit MUST NOT delete new daemon's ready or socket!
        self.assertTrue(ctl.get_status(self.rdir)["running"])
        self.assertTrue(self.ready.exists())
        self.assertTrue(self.sock.exists())
        ctl.stop_daemon(self.rdir)

        # Fresh daemon + external socket unlink self-heal
        self.proc = self._start_daemon(["--idle-timeout", "0"])
        old_pid2 = self.proc.pid
        self.sock.unlink()
        self.assertEqual(self.proc.wait(timeout=10), 0)
        self.assertFalse(Path(f"/proc/{old_pid2}").exists())

    def test_ctl_cli_thundering_herd_disable_and_all4_fallback_parity(self) -> None:
        skip_native = os.environ.get("F8_HYBRID2_NATIVE") != "1"
        maps_arg = f"/ws={self.ws}"
        extra = ["--skip-tracer-check"] if skip_native else []

        # Exercise ctl CLI start / status / probe / restart
        r_start = sp.run([sys.executable, str(CTL_PY), "--dir", str(self.rdir), "--daemon-py", str(DAEMON_PY), "--map", maps_arg, "--idle-timeout", "0", *extra, "start"], capture_output=True, text=True, timeout=15)
        self.assertEqual(r_start.returncode, 0, r_start.stderr)
        r_probe = sp.run([sys.executable, str(CTL_PY), "--dir", str(self.rdir), "probe"], capture_output=True, text=True, timeout=10)
        self.assertEqual(r_probe.returncode, 0)
        self.assertTrue(json.loads(r_probe.stdout)["ok"])
        r_restart = sp.run([sys.executable, str(CTL_PY), "--dir", str(self.rdir), "--daemon-py", str(DAEMON_PY), "--map", maps_arg, "--idle-timeout", "0", *extra, "restart"], capture_output=True, text=True, timeout=15)
        self.assertEqual(r_restart.returncode, 0, r_restart.stderr)

        def call_ensure(_i: int) -> dict:
            return ctl.ensure_running(self.rdir, daemon_py=str(DAEMON_PY), maps=[maps_arg], idle_timeout=0.0, timeout_s=6.0, skip_tracer_check=skip_native)

        with ThreadPoolExecutor(4) as ex:
            results = list(ex.map(call_ensure, range(4)))
        self.assertEqual(len({r["pid"] for r in results}), 1)

        # Parity across ALL 4 tools + null max_entries (-32602 without hang)
        reqs = "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["rev-parse", "HEAD"]}}}),
                json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "repo_tree_scan", "arguments": {"root": "/ws/repo"}}}),
                json.dumps({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "repo_text_search", "arguments": {"root": "/ws/repo", "pattern": "needle"}}}),
                json.dumps({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "python_json_summary", "arguments": {"path": "/ws/sample.jsonl"}}}),
                json.dumps({"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "repo_tree_scan", "arguments": {"root": "/ws/repo", "max_entries": None}}}),
            ]
        ) + "\n"
        stripped_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(self.base / "h"), "TMPDIR": str(self.base / "t")}

        p1 = sp.run([sys.executable, str(RELAY_PY), "--socket", str(self.sock), "--map", maps_arg, "--git-bin", SYSTEM_GIT], input=reqs.encode(), capture_output=True, env=stripped_env, timeout=15)
        self.assertEqual(p1.returncode, 0, p1.stderr)
        res1 = {r["id"]: r for r in (json.loads(line) for line in p1.stdout.decode().splitlines() if line.strip())}
        self.assertEqual(len(res1), 6)
        self.assertEqual(res1[6]["error"]["code"], -32602)

        sp.run([sys.executable, str(CTL_PY), "--dir", str(self.rdir), "disable"], check=True, stdout=sp.PIPE)
        p2 = sp.run([sys.executable, str(RELAY_PY), "--socket", str(self.sock), "--map", maps_arg, "--git-bin", SYSTEM_GIT, "--auto-start"], input=reqs.encode(), capture_output=True, env=stripped_env, timeout=15)
        self.assertEqual(p2.returncode, 0, p2.stderr)
        self.assertIn(b"reason=global-disabled", p2.stderr)
        res2 = {r["id"]: r for r in (json.loads(line) for line in p2.stdout.decode().splitlines() if line.strip())}
        for idx in (2, 3, 4, 5, 6):
            self.assertEqual(res1[idx], res2[idx])

        sp.run([sys.executable, str(CTL_PY), "--dir", str(self.rdir), "enable"], check=True, stdout=sp.PIPE)
        r_soft = sp.run([sys.executable, str(CTL_PY), "--dir", str(self.rdir), "--daemon-py", str(DAEMON_PY), "--map", maps_arg, "--soft", "ensure-running"], capture_output=True, env=stripped_env, timeout=10)
        self.assertEqual(r_soft.returncode, 0)

    def test_redos_timeout_disable_exitcode_and_connected_client_lifecycle(self) -> None:
        # 1) ReDoS timeout isolation in repo_text_search (does not stall concurrent client B)
        (self.ws / "redos.txt").write_text(("a" * 3500) + "c\n", encoding="utf-8")
        self.proc = self._start_daemon()
        sa, fa = self._uds_rpc(self.sock)
        sb, fb = self._uds_rpc(self.sock)
        try:
            for s, f in ((sa, fa), (sb, fb)):
                self._send(s, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})
                json.loads(f.readline())
            t0 = time.monotonic()
            self._send(sa, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "repo_text_search", "arguments": {"root": "/ws", "pattern": "(a+)+b", "timeout_s": 0.15}}})
            self._send(sb, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["rev-parse", "HEAD"]}}})
            rb = json.loads(fb.readline())
            self.assertEqual(json.loads(rb["result"]["content"][0]["text"])["returncode"], 0)
            ra = json.loads(fa.readline())
            self.assertEqual(ra["error"]["code"], -32001)
            self.assertLess(time.monotonic() - t0, 1.5)
            time.sleep(0.1)
            self.assertEqual(children_of(self.proc.pid), [])
        finally:
            fa.close(); sa.close(); fb.close(); sb.close()

        # 2) Honest connected-client behavior on `ctl disable` and `ctl enable`:
        # Connected UDS relay gets EOF disconnect (NOT hot-switched); new reconnect uses fallback.
        c1 = sp.Popen([sys.executable, str(RELAY_PY), "--socket", str(self.sock), "--map", f"/ws={self.ws}", "--git-bin", SYSTEM_GIT, "--no-fallback"],
                      stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, start_new_session=True)
        try:
            assert c1.stdin is not None and c1.stdout is not None
            c1.stdin.write((json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}) + "\n").encode())
            c1.stdin.flush()
            self.assertIn(b"f8-hybrid2", c1.stdout.readline())

            # Run ctl disable while c1 is connected -> stops daemon; c1 observes EOF and exits!
            r_dis = sp.run([sys.executable, str(CTL_PY), "--dir", str(self.rdir), "--wait", "4.0", "disable"], capture_output=True, text=True, timeout=10)
            self.assertEqual(r_dis.returncode, 0, r_dis.stdout)
            self.assertTrue(json.loads(r_dis.stdout)["ok"])
            self.assertEqual(c1.stdout.readline(), b"")
            c1.stdin.close()
            c1.wait(timeout=3)
        finally:
            for p in (c1.stdin, c1.stdout, c1.stderr):
                if p is not None:
                    try:
                        p.close()
                    except OSError:
                        pass

        # Connected fallback client C2 stays in fallback even after `ctl enable` + `ctl start`;
        # only a new connection C3 uses the native daemon!
        c2 = sp.Popen([sys.executable, str(RELAY_PY), "--socket", str(self.sock), "--map", f"/ws={self.ws}", "--git-bin", SYSTEM_GIT],
                      stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, start_new_session=True)
        try:
            assert c2.stdin is not None and c2.stdout is not None
            c2.stdin.write((json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}) + "\n").encode())
            c2.stdin.flush()
            self.assertIn(b"f8-hybrid2", c2.stdout.readline())

            skip_native = os.environ.get("F8_HYBRID2_NATIVE") != "1"
            ctl.set_disabled(self.rdir, False)
            res_up = ctl.ensure_running(self.rdir, daemon_py=str(DAEMON_PY), maps=[f"/ws={self.ws}"], idle_timeout=0.0, skip_tracer_check=skip_native)
            self.assertTrue(res_up["ok"])

            audit_before = self.log.read_text(encoding="utf-8")
            c2.stdin.write((json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["status", "--short"]}}}) + "\n").encode())
            c2.stdin.flush()
            self.assertEqual(json.loads(c2.stdout.readline())["id"], 2)
            # C2 stayed in PRoot fallback -> daemon audit has NO new tool entry from C2!
            tail_audit = self.log.read_text(encoding="utf-8")[len(audit_before) :]
            self.assertNotIn('"ev": "tool"', tail_audit)

            # New client C3 hits the newly started daemon!
            c3_in = "\n".join([
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}),
                json.dumps({"jsonrpc": "2.0", "id": 99, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["status", "--short"]}}}),
            ]) + "\n"
            p_c3 = sp.run([sys.executable, str(RELAY_PY), "--socket", str(self.sock), "--no-fallback"], input=c3_in.encode(), capture_output=True, timeout=10)
            self.assertEqual(p_c3.returncode, 0, p_c3.stderr)
            self.assertIn('"req_id": 99', self.log.read_text(encoding="utf-8"))

            c2.stdin.close()
            c2.wait(timeout=3)
        finally:
            for p in (c2.stdin, c2.stdout, c2.stderr):
                if p is not None:
                    try:
                        p.close()
                    except OSError:
                        pass

        # 3) `ctl disable` MUST return exit code 1 & ok=false if daemon ignores SIGTERM and fails to stop in time!
        ctl.stop_daemon(self.rdir, timeout_s=3.0)
        ctl.set_disabled(self.rdir, False)
        stub = sp.Popen(
            [sys.executable, "-c", "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)", "f8_hybrid2_daemon.py"],
            stdin=sp.DEVNULL, stdout=sp.DEVNULL, stderr=sp.DEVNULL,
        )
        try:
            self.pidfile.write_text(f"{stub.pid}\n", encoding="utf-8")
            self.sock.write_text("", encoding="utf-8")
            r_fail = sp.run([sys.executable, str(CTL_PY), "--dir", str(self.rdir), "--wait", "0.2", "disable"], capture_output=True, text=True, timeout=10)
            self.assertEqual(r_fail.returncode, 1)
            payload = json.loads(r_fail.stdout)
            self.assertFalse(payload["ok"])
            self.assertTrue(payload["disabled"])
            self.assertEqual(payload["stop"]["action"], "stop-timeout")
        finally:
            stub.kill()
            stub.wait(timeout=3)
            self.pidfile.unlink(missing_ok=True)
            self.sock.unlink(missing_ok=True)

    def test_fallback_fast_sigterm_wakeup(self) -> None:
        p = sp.Popen(
            [sys.executable, str(RELAY_PY), "--socket", str(self.rdir / "missing.sock"), "--map", f"/ws={self.ws}", "--git-bin", SYSTEM_GIT],
            stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE,
            env={**os.environ, "F8_NO_HYBRID": "1"},
            start_new_session=True,
        )
        try:
            assert p.stdin is not None and p.stdout is not None
            p.stdin.write((json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}) + "\n").encode())
            p.stdin.flush()
            self.assertIn(b"f8-hybrid2", p.stdout.readline())
            t0 = time.monotonic()
            p.send_signal(signal.SIGTERM)
            rc = p.wait(timeout=3)
            self.assertEqual(rc, 0)
            self.assertLess(time.monotonic() - t0, 0.8)
        finally:
            for pipe in (p.stdin, p.stdout, p.stderr):
                if pipe is not None:
                    try:
                        pipe.close()
                    except OSError:
                        pass


if __name__ == "__main__":
    unittest.main(verbosity=2, failfast=False)
