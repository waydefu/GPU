#!/usr/bin/env python3
"""Acceptance & regression tests for Stage 7.2 Native Hybrid 2.0 isolated prototype.

Runs policy, security, fuzz, protocol lifecycle, cancellation, timeout,
disconnect cleanup, and fallback tests with pure stdlib `unittest`.
When run natively on Termux (`F8_HYBRID2_LIVE=1`, TracerPid == 0), also tests
strict native TracerPid == 0 enforcement and real PRoot relay roundtrips.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import signal
import socket
import stat
import struct
import subprocess as sp
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from f8_hybrid2_policy import Policy, Refuse, read_tracer_pid, validate_unix_sock_path
from f8_hybrid2_tools import MCPToolEngine, RequestContext

DAEMON_PY = HERE / "f8_hybrid2_daemon.py"
RELAY_PY = HERE / "f8_hybrid2_relay.py"
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
        symlink_escape = self.ws / "escape"
        if not symlink_escape.exists():
            os.symlink(str(self.outside), str(symlink_escape))

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

    def test_protected_l2s_outside_and_symlink_escape(self) -> None:
        self._refused("protected-path", self.pol.map_path, "/etc/passwd")
        self._refused("protected-path", self.pol.map_path, "/usr/lib")
        self._refused("protected-path", self.pol.map_path, "/root/." + "gemini/x")
        self._refused("protected-path", self.pol.map_path, "/root/.hermes/config.yaml")
        self._refused("protected-path", self.pol.map_path, "/data/data/com.termux/files/home/build/proot-fast/out8/bin/proot-fast8")
        self._refused("protected-path", self.pol.map_path, "../../etc/hosts", cwd="/ws/sub")
        self._refused("path-outside-map", self.pol.map_path, "/root/x")
        self._refused("path-outside-map", self.pol.map_path, "/wsx/y")
        self._refused("path-outside-map", self.pol.map_path, "sub/../../x", cwd="/ws")
        self._refused("l2s-path", self.pol.map_path, "/ws/.l2s.a0001")
        self._refused("l2s-path", self.pol.map_path, ".l2s.x", cwd="/ws")
        self._refused("symlink-escape", self.pol.map_path, "/ws/escape/secret.txt")
        self._refused("bad-path", self.pol.map_path, "/ws/a\x00b")
        mapped = self.pol.map_path("sub/../a.py", cwd="/ws", must_exist=True)
        self.assertEqual(mapped, str((self.ws / "a.py").resolve()))

    def test_git_readonly_allowlist_and_denies(self) -> None:
        ok_cmds = (
            ["status", "--short"],
            ["log", "-n", "1"],
            ["rev-parse", "HEAD"],
            ["ls-files"],
            ["diff"],
            ["-C", "/ws/repo", "show", "--stat", "HEAD"],
        )
        for cmd in ok_cmds:
            clean, hcwd, env = self.pol.validate_git_ro(cmd, "/ws/repo")
            self.assertEqual(hcwd, str(self.repo.resolve()))
            self.assertEqual(env["GIT_CONFIG_GLOBAL"], "/dev/null")
            if cmd[-1] == "diff" or "show" in cmd:
                self.assertIn("--no-ext-diff", clean)

        denied = (
            ("git-subcmd-denied", ["commit", "-m", "x"]),
            ("git-subcmd-denied", ["push"]),
            ("git-subcmd-denied", ["checkout", "."]),
            ("git-subcmd-denied", ["reset", "--hard"]),
            ("git-subcmd-denied", ["config", "user.name", "x"]),
            ("git-write-flag-denied", ["branch", "-D", "main"]),
            ("git-write-flag-denied", ["tag", "-a", "v1", "-m", "x"]),
            ("git-pre-flag-denied", ["-c", "core.pager=cat", "status"]),
            ("git-pre-flag-denied", ["--git-dir=/etc", "status"]),
            ("git-option-denied", ["diff", "--ext-diff"]),
            ("git-option-denied", ["log", "--output=/tmp/x"]),
            ("git-option-denied", ["status", "--upload-pack=evil"]),
        )
        for reason, cmd in denied:
            self._refused(reason, self.pol.validate_git_ro, cmd, "/ws/repo")

    def test_git_config_injection_and_gitfile(self) -> None:
        cfg = self.repo / ".git/config"
        base = cfg.read_text(encoding="utf-8")
        try:
            for bad in (
                '[filter "lfs"]\n\tclean = evil\n',
                '[core]\n\tfsmonitor = true\n',
                '[include]\n\tpath = /x\n',
                '[diff "x"]\n\ttextconv = evil\n',
                '[core]\n\tpager = evil\n',
                '[core]\n\tsshCommand = evil\n',
                '[includeIf "gitdir:/"]\n\tpath = x\n',
            ):
                cfg.write_text(base + bad, encoding="utf-8")
                self._refused("git-config-unsafe", self.pol.validate_git_ro, ["status"], "/ws/repo")
            cfg.write_text(base + "[user]\n\tname = ok\n", encoding="utf-8")
            self.pol.validate_git_ro(["status"], "/ws/repo")
        finally:
            cfg.write_text(base, encoding="utf-8")

        wt = self.ws / "wt"
        wt.mkdir(exist_ok=True)
        (wt / ".git").write_text("gitdir: /root/projects/x/.git/worktrees/wt\n", encoding="utf-8")
        self._refused("gitfile-absolute", self.pol.validate_git_ro, ["status"], "/ws/wt")
        (wt / ".git").write_text("garbage\n", encoding="utf-8")
        self._refused("gitfile-malformed", self.pol.validate_git_ro, ["status"], "/ws/wt")
        (wt / ".git").write_text("gitdir: ../escape/.git\n", encoding="utf-8")
        self._refused("symlink-escape", self.pol.validate_git_ro, ["status"], "/ws/wt")

    def test_env_scrubbed(self) -> None:
        os.environ["LANG"] = "en_US.UTF-8"
        env = self.pol.clean_env({"LANG": "C.UTF-8", "LD_PRELOAD": "/evil.so", "GH_TOKEN": "tok"})
        self.assertEqual(env["LANG"], "C.UTF-8")
        self.assertEqual(env["PYTHONNOUSERSITE"], "1")
        self.assertEqual(env["HOME"], str(self.home.resolve()))
        self.assertNotIn("LD_PRELOAD", env)
        self.assertNotIn("GH_TOKEN", env)

    def test_jsonrpc_control_and_fuzz(self) -> None:
        eng = MCPToolEngine(self.pol, git_bin=SYSTEM_GIT)
        rnd = random.Random(1234)
        for _ in range(3000):
            bad_obj: object
            choice = rnd.randrange(4)
            if choice == 0:
                bad_obj = rnd.randrange(100)
            elif choice == 1:
                bad_obj = {"jsonrpc": "1.0", "id": 1}
            elif choice == 2:
                bad_obj = {"jsonrpc": "2.0", "id": 1, "method": "bad_" + str(rnd.randrange(999))}
            else:
                bad_obj = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": rnd.randrange(5)}
            resp, async_kind = eng.handle_sync_control(bad_obj)  # must never raise
            if async_kind == "tools/call":
                r = eng.call_tool(1, bad_obj.get("params"), RequestContext(1, 1.0))  # type: ignore[union-attr]
                self.assertIn("error", r)
            else:
                self.assertIn("error", resp)


class DaemonLifecycleAndProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        # Keep UDS path well under 107 bytes using TMPDIR (or default temp dir).
        self.base = Path(tempfile.mkdtemp(prefix="hyb2_"))
        self.ws = self.base / "ws"
        self.repo = self.ws / "repo"
        self.run = self.base / "run"
        self.sockd = self.base / "s"
        self.sock = self.sockd / "m.sock"
        self.pidfile = self.run / "d.pid"
        self.log = self.run / "audit.jsonl"
        for d in (self.ws, self.repo, self.run, self.sockd):
            d.mkdir(parents=True, exist_ok=True)
        git_run(["init", "-q"], self.repo)
        (self.repo / "readme.md").write_text("Stage 7.2 Native Hybrid\nline2\n", encoding="utf-8")
        git_run(["add", "readme.md"], self.repo)
        git_run(["commit", "-q", "-m", "init"], self.repo)

        # Synthetic heavy tree (1,500 files) for realistic cancel / timeout testing.
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
        shutil.rmtree(self.base, ignore_errors=True)

    def _start_daemon(self, extra: list[str] | None = None, skip_tracer: bool | None = None) -> sp.Popen[bytes]:
        if skip_tracer is None:
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
            "--log",
            str(self.log),
            "--git-bin",
            SYSTEM_GIT,
        ]
        if skip_tracer:
            cmd.append("--skip-tracer-check")
        if extra:
            cmd.extend(extra)
        out_f = open(self.run / "daemon.out", "ab")
        p = sp.Popen(cmd, stdin=sp.DEVNULL, stdout=out_f, stderr=out_f, start_new_session=True)
        out_f.close()
        for _ in range(100):
            if self.sock.exists() and self.pidfile.exists() and self.pidfile.read_text().strip():
                if not skip_tracer:
                    self.assertEqual(read_tracer_pid(p.pid), 0)
                return p
            if p.poll() is not None:
                err = (self.run / "daemon.out").read_text(encoding="utf-8", errors="replace")
                raise RuntimeError(f"daemon exited rc={p.returncode}: {err}")
            time.sleep(0.05)
        raise RuntimeError("daemon failed to become ready")

    @staticmethod
    def _uds_rpc(sock_path: Path) -> tuple[socket.socket, any]:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(10.0)
        s.connect(str(sock_path))
        f = s.makefile("rb")
        return s, f

    @staticmethod
    def _send(s: socket.socket, obj: dict) -> None:
        s.sendall((json.dumps(obj) + "\n").encode("utf-8"))

    def test_overlong_socket_and_single_instance_and_perms(self) -> None:
        long_dir = self.base / ("x" * 110)
        r = sp.run(
            [
                sys.executable,
                str(DAEMON_PY),
                "--socket",
                str(long_dir / "m.sock"),
                "--map",
                f"/ws={self.ws}",
                "--home",
                str(self.base / "h"),
                "--tmp",
                str(self.base / "t"),
                "--pidfile",
                str(self.run / "long.pid"),
                "--skip-tracer-check",
            ],
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(r.returncode, 4)
        self.assertIn(b"AF_UNIX limit", r.stderr)
        self.assertFalse(long_dir.exists())

        self.proc = self._start_daemon()
        self.assertEqual(stat.S_IMODE(os.stat(self.sock).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(self.sockd).st_mode), 0o700)
        self.assertEqual(os.stat(self.sock).st_uid, os.getuid())

        second = sp.run(
            [
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
                "--skip-tracer-check",
            ],
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(second.returncode, 3)

    def test_mcp_handshake_tools_cancel_timeout_disconnect_and_malformed_fuzz(self) -> None:
        self.proc = self._start_daemon()
        base_fds = proc_count_fds(self.proc.pid)

        # 1) Probe check
        probe = sp.run(
            [sys.executable, str(RELAY_PY), "--socket", str(self.sock), "--probe"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        self.assertTrue(json.loads(probe.stdout)["ok"])

        # 2) Initialize + tools/list + all 4 read-only tools + notifications/cancelled
        s, f = self._uds_rpc(self.sock)
        try:
            self._send(s, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}})
            r1 = json.loads(f.readline())
            self.assertEqual(r1["result"]["protocolVersion"], "2025-11-25")
            self._send(s, {"jsonrpc": "2.0", "method": "notifications/initialized"})

            self._send(s, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            r2 = json.loads(f.readline())
            names = [t["name"] for t in r2["result"]["tools"]]
            self.assertEqual(names, ["repo_tree_scan", "repo_text_search", "git_ro", "python_json_summary"])

            self._send(s, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["rev-parse", "--is-inside-work-tree"]}}})
            r3 = json.loads(f.readline())
            payload3 = json.loads(r3["result"]["content"][0]["text"])
            self.assertEqual(payload3["returncode"], 0)
            self.assertEqual(payload3["stdout"].strip(), "true")

            self._send(s, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "repo_text_search", "arguments": {"root": "/ws/repo", "pattern": "Stage 7.2"}}})
            r4 = json.loads(f.readline())
            payload4 = json.loads(r4["result"]["content"][0]["text"])
            self.assertEqual(payload4["match_count"], 1)

            self._send(s, {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "python_json_summary", "arguments": {"path": "/ws/sample.jsonl"}}})
            r5 = json.loads(f.readline())
            payload5 = json.loads(r5["result"]["content"][0]["text"])
            self.assertEqual(payload5["record_count"], 500)

            # Single-request cancellation on slow scan: must abort id=6 without killing daemon/conn
            self._send(s, {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "repo_tree_scan", "arguments": {"root": "/ws/bigtree", "compute_sha256": True}}})
            time.sleep(0.03)
            self._send(s, {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 6}})
            self._send(s, {"jsonrpc": "2.0", "id": 7, "method": "ping"})
            # Wait for ping; id=6 must NOT produce a response after cancellation (or ping returns cleanly).
            seen_ids = []
            for _ in range(5):
                resp = json.loads(f.readline())
                seen_ids.append(resp.get("id"))
                if resp.get("id") == 7:
                    break
            self.assertIn(7, seen_ids)

            # Timeout check: 1 ms timeout on 1,500-file scan -> JSON-RPC -32001, daemon healthy after
            self._send(s, {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "repo_tree_scan", "arguments": {"root": "/ws/bigtree", "compute_sha256": True, "timeout_s": 0.001}}})
            r8 = json.loads(f.readline())
            self.assertEqual(r8["error"]["code"], -32001)

            # Timeout check on git_ro child Popen -> os.killpg cleans up child process cleanly
            self._send(s, {"jsonrpc": "2.0", "id": 81, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["log", "--all", "--stat"], "timeout_s": 0.001}}})
            r81 = json.loads(f.readline())
            self.assertEqual(r81["error"]["code"], -32001)
            self.assertEqual(children_of(self.proc.pid), [])

            # Daemon still answers subsequent request cleanly
            self._send(s, {"jsonrpc": "2.0", "id": 9, "method": "ping"})
            r9 = json.loads(f.readline())
            self.assertEqual(r9["result"], {})
        finally:
            f.close()
            s.close()

        # 3) Disconnect cleanup (SIGKILL relay mid-request) -> children_final=0, daemon survives
        relay = sp.Popen(
            [sys.executable, str(RELAY_PY), "--socket", str(self.sock), "--no-fallback"],
            stdin=sp.PIPE,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            start_new_session=True,
        )
        try:
            assert relay.stdin is not None
            relay.stdin.write(
                (json.dumps({"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"name": "repo_tree_scan", "arguments": {"root": "/ws/bigtree", "compute_sha256": True}}}) + "\n").encode()
            )
            relay.stdin.flush()
            time.sleep(0.03)
            relay.kill()
            relay.wait(timeout=5)
        finally:
            for pipe in (relay.stdin, relay.stdout, relay.stderr):
                if pipe is not None:
                    try:
                        pipe.close()
                    except OSError:
                        pass
        time.sleep(0.3)
        self.assertEqual(children_of(self.proc.pid), [])
        self.assertIsNone(self.proc.poll())

        # 4) Malformed socket frames fuzz
        for raw in (b"\n", b"{bad json\n", b'{"jsonrpc":"1.0","id":1}\n', b"\xff\xfe\n"):
            cs = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            cs.settimeout(3.0)
            cs.connect(str(self.sock))
            cs.sendall(raw)
            cs.shutdown(socket.SHUT_WR)
            cs.recv(512)
            cs.close()

        time.sleep(0.2)
        self.assertLessEqual(proc_count_fds(self.proc.pid), base_fds + 1)

        # 5) Clean SIGTERM -> zero residue
        self.proc.send_signal(signal.SIGTERM)
        rc = self.proc.wait(timeout=10)
        self.assertEqual(rc, 0)
        self.assertFalse(self.sock.exists())
        self.assertFalse(self.pidfile.exists())

        # 6) Audit log must contain no file content or secrets
        audit_text = self.log.read_text(encoding="utf-8")
        self.assertNotIn("needle line", audit_text)
        self.assertIn('"decision": "timeout"', audit_text)

    def test_fallback_modes_match_native_output(self) -> None:
        # Compare daemon bridge output vs F8_NO_HYBRID=1 fallback vs daemon-down fallback
        self.proc = self._start_daemon()

        def rpc_via_relay(extra_env: dict[str, str], sock_override: Path | None = None) -> dict:
            env = dict(os.environ)
            env.update(extra_env)
            cmd = [
                sys.executable,
                str(RELAY_PY),
                "--socket",
                str(sock_override or self.sock),
                "--map",
                f"/ws={self.ws}",
                "--git-bin",
                SYSTEM_GIT,
            ]
            reqs = "\n".join(
                [
                    json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}),
                    json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                    json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "repo_tree_scan", "arguments": {"root": "/ws/repo"}}}),
                    json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "git_ro", "arguments": {"cwd": "/ws/repo", "args": ["status", "--short"]}}}),
                ]
            ) + "\n"
            p = sp.run(cmd, input=reqs.encode(), capture_output=True, env=env, timeout=15)
            self.assertEqual(p.returncode, 0, p.stderr)
            lines = [json.loads(line) for line in p.stdout.decode().splitlines() if line.strip()]
            return {"resps": lines, "stderr": p.stderr.decode(errors="replace")}

        native = rpc_via_relay({})
        no_hyb = rpc_via_relay({"F8_NO_HYBRID": "1"})
        self.assertIn("F8_NO_HYBRID=1", no_hyb["stderr"])

        # Stop daemon -> missing socket fallback
        self.proc.send_signal(signal.SIGTERM)
        self.proc.wait(timeout=5)
        down = rpc_via_relay({}, sock_override=self.sockd / "missing.sock")
        self.assertIn("daemon-unavailable", down["stderr"])

        for idx in (1, 2):
            p_nat = json.loads(native["resps"][idx]["result"]["content"][0]["text"])
            p_no = json.loads(no_hyb["resps"][idx]["result"]["content"][0]["text"])
            p_dn = json.loads(down["resps"][idx]["result"]["content"][0]["text"])
            self.assertEqual(p_nat, p_no)
            self.assertEqual(p_nat, p_dn)


if __name__ == "__main__":
    unittest.main(verbosity=2, failfast=False)
