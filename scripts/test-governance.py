"""Offline fixtures for evidence, content, and display safety."""

import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


governance = load("governance", "scripts/check-governance.py")
tiny = load("tiny", "patches/run_tiny_pixmap.py")


class ContentTest(unittest.TestCase):
    def test_cli_blocks_sensitive_values_without_echo(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            for name in governance.ACTIVE:
                path = root / name
                if name in (".github/workflows", "scripts"):
                    path /= "fixture.txt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("clean fixture\n")
            value = "ghs_" + "A" * 32
            readme = root / "README.md"
            readme.write_text(value)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            command = [sys.executable, str(ROOT / "scripts/check-governance.py"), "scan"]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("README.md", result.stderr)
            self.assertNotIn(value, result.stdout + result.stderr)
            readme.unlink()
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2)

    def test_private_endpoints(self):
        for address in (
            "10.1.2.3", "172.16.0.1", "172.31.255.254", "192.168.1.5",
            "169.254.10.5", "100.64.0.1", "[fd12::5]", "[fe80::20%wlan0]",
        ):
            with self.subTest(address=address):
                self.assertEqual(governance.content_flags(address + ":4321"), ["private LAN endpoint"])
        for address in ("192.0.2.1", "172.32.0.1", "172.15.0.1", "10.265.0.1", "[2001:db8::1]"):
            self.assertEqual(governance.content_flags(address + ":4321"), [])

    def test_credential_and_path_patterns(self):
        for marker in (
            "ghs_" + "A" * 32,
            "ghu_" + "A" * 32,
            "github_pat_" + "A" * 32,
            "AKIA" + "A" * 16,
            "AIza" + "A" * 35,
            "ya29." + "A" * 35,
            "sk-proj-" + "A" * 35,
            "xoxb-" + "9" * 25,
            "glpat-" + "A" * 22,
            "npm_" + "A" * 32,
            "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
        ):
            self.assertEqual(governance.content_flags(marker), ["credential pattern"])
        self.assertEqual(governance.content_flags("/root/" + ".gemini/session"), ["local session path"])
        self.assertEqual(governance.content_flags("COMMIT=a0a1e5fa; token=example"), [])


class FrozenTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.closed = self.write("evidence/session/gl/old.txt", "closed")
        self.active = self.write("evidence/session/proot/old.txt", "published")
        self.archived = self.write("docs/archive/handoffs/old.md", "archived")
        self.base = self.commit("initial")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True).strip()

    def write(self, name, contents):
        path = self.root / name
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(contents)
        return path

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def guard(self, base, head, event):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/check-governance.py"), "freeze"],
            cwd=self.root,
            env={**os.environ, "COMPARE_BASE": base, "GITHUB_SHA": head, "GITHUB_EVENT_NAME": event},
            capture_output=True, text=True, check=False,
        )

    def test_push_accepts_new_evidence_on_active_track(self):
        self.write("evidence/session/proot/new.txt", "new evidence")
        head = self.commit("append")
        self.assertEqual(self.guard(self.base, head, "push").returncode, 0)

    def test_push_rejects_frozen_edits_and_wrong_checkout(self):
        self.active.write_text("modified")
        self.archived.unlink()
        head = self.commit("changed")
        failure = self.guard(self.base, head, "push")
        self.assertEqual(failure.returncode, 1)
        self.assertIn("proot/old.txt", failure.stderr)
        self.assertIn("handoffs/old.md", failure.stderr)
        self.assertEqual(self.guard(self.base, self.base, "push").returncode, 2)
        self.assertEqual(self.guard("0" * 40, head, "push").returncode, 2)

    def test_pr_rejects_new_file_in_closed_track_on_merge_checkout(self):
        self.git("switch", "-qc", "candidate")
        self.write("evidence/session/gl/new.txt", "closed track addition")
        self.commit("guarded addition")
        self.git("switch", "-q", "main")
        self.write("other.txt", "base advanced")
        base = self.commit("advance base")
        self.git("merge", "--no-ff", "-qm", "synthetic PR merge", "candidate")
        head = self.git("rev-parse", "HEAD")
        failure = self.guard(base, head, "pull_request")
        self.assertEqual(failure.returncode, 1)
        self.assertIn("gl/new.txt", failure.stderr)


class AdbTest(unittest.TestCase):
    def test_selected_device_has_explicit_lane_and_scrubbed_env(self):
        serial = "192.0.2.1:4321"
        with patch.dict(os.environ, {
            "ADB_SERIAL": serial, "ADB_SERVER_SOCKET": "tcp:wrong:5037",
            "ANDROID_ADB_SERVER_ADDRESS": "wrong", "ANDROID_ADB_SERVER_PORT": "5037",
        }, clear=True), patch.object(
            tiny.subprocess, "check_output", side_effect=["device\n", "myron\n"],
        ) as reader:
            adb, env = tiny.adb_target()
        self.assertEqual(adb, (tiny.ADB, "-H", "127.0.0.1", "-P", "5038", "-s", serial))
        self.assertEqual(set(env), {"ADB_SERIAL"})
        self.assertEqual(reader.call_args_list[0].args[0], [*adb, "get-state"])
        self.assertEqual(reader.call_args_list[1].args[0], [*adb, "shell", "getprop", "ro.product.device"])
        with patch.object(tiny.subprocess, "run") as runner:
            tiny.start_activity(adb, env)
        argv = runner.call_args.args[0]
        self.assertEqual(tuple(argv[:len(adb)]), adb)
        self.assertEqual(argv[-1], "com.waydefu.x11gpu/com.termux.x11.MainActivity")
        self.assertTrue(runner.call_args.kwargs["check"])
        with tempfile.TemporaryDirectory() as out, patch.object(tiny, "EVDIR", out), patch.object(
            tiny.subprocess, "check_output", return_value=b"fixture\n",
        ) as dump:
            tiny.snapshot_logcat("fixture", adb, env)
        self.assertEqual(tuple(dump.call_args.args[0][:len(adb)]), adb)

    def test_ambiguous_isolated_devices_and_wrong_product_fail(self):
        entries = "192.0.2.1:4321\tdevice\n192.0.2.2:4321\tdevice\n"
        with patch.dict(os.environ, {}, clear=True), patch.object(
            tiny.subprocess, "check_output", return_value=entries,
        ) as reader, self.assertRaises(RuntimeError):
            tiny.adb_target()
        self.assertEqual(reader.call_args.args[0], [*tiny.ADB_LANE, "devices"])
        with patch.dict(os.environ, {"ADB_SERIAL": "192.0.2.1:4321"}, clear=True), patch.object(
            tiny.subprocess, "check_output", side_effect=["device", "other-model"],
        ), self.assertRaises(RuntimeError):
            tiny.adb_target()

    def test_stable_uses_runtime_pid_starttime_display_and_socket(self):
        with tempfile.TemporaryDirectory() as temp, socket.socket(socket.AF_UNIX) as unix_socket:
            proc = Path(temp)
            lock = proc / ".X1-lock"
            server_socket = proc / "X1"
            unix_socket.bind(str(server_socket))
            lock.write_text(" 415\n")
            for pid, argv in (
                (415, b"termux-x11 com.termux.x11 :1 -legacy-drawing\0"),
                (732, b"xfce4-session\0"),
                (887, b"xfwm4\0"),
            ):
                directory = proc / str(pid)
                directory.mkdir()
                (directory / "cmdline").write_bytes(argv)
                (directory / "environ").write_bytes(b"DISPLAY=:1\0")
                (directory / "stat").write_text(f"{pid} (name with spaces) S " + "0 " * 18 + "12345\n")
            original = tiny.stable_snapshot(proc, lock, server_socket)
            self.assertIsNotNone(original)
            self.assertEqual(original[0], (415, 12345))
            stat_file = proc / "887/stat"
            stat_file.write_text(stat_file.read_text().replace("12345", "12346"))
            self.assertNotEqual(original, tiny.stable_snapshot(proc, lock, server_socket))
            (proc / "887/environ").write_bytes(b"DISPLAY=:3\0")
            self.assertIsNone(tiny.stable_snapshot(proc, lock, server_socket))


if __name__ == "__main__":
    unittest.main()
