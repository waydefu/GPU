#!/usr/bin/env python3
"""Unit tests for Stage 6 isolated ADB selection, env isolation, and device identity verification."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage6_adb as A  # noqa: E402


class FakeProc:
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


class Stage6AdbTests(unittest.TestCase):
    def test_adb_env_strips_overriding_vars_and_pins_home(self):
        dirty = {
            "PATH": "/bin",
            "HOME": "/root",
            "ADB_SERVER_SOCKET": "tcp:127.0.0.1:5037",
            "ANDROID_ADB_SERVER_ADDRESS": "127.0.0.1",
            "ANDROID_ADB_SERVER_PORT": "5037",
        }
        clean = A.adb_env(base_env=dirty)
        self.assertEqual(clean["HOME"], str(A.TERMUX_HOME))
        for k in A.ADB_STRIP_ENV:
            self.assertNotIn(k, clean)

    def test_run_adb_passes_isolated_port_and_serial(self):
        calls = []

        def fake_run(cmd, env=None, capture_output=None, text=None, timeout=None):
            calls.append((cmd, env))
            return FakeProc(0, "ok\n")

        with mock.patch.object(A.sp, "run", side_effect=fake_run):
            rc, out = A.run_adb(5038, ["shell", "id"], serial="198.51.100.1:40397")
        self.assertEqual((rc, out), (0, "ok"))
        cmd, env = calls[0]
        self.assertEqual(cmd[:6], [str(A.ADB_BIN), "-H", "127.0.0.1", "-P", "5038", "-s"])
        self.assertEqual(cmd[6:9], ["198.51.100.1:40397", "shell", "id"])
        self.assertEqual(env["HOME"], str(A.TERMUX_HOME))

    def test_detect_myron_serial_selects_and_fails_closed(self):
        good = (
            "List of devices attached\n"
            "emulator-5554          offline\n"
            "198.51.100.2:40397     device product:myron_global model:25102PCBEG device:myron transport_id:1\n"
        )
        with mock.patch.object(A, "run_adb", return_value=(0, good)):
            self.assertEqual(A.detect_myron_serial(5038), "198.51.100.2:40397")

        wrong_dev = "List of devices attached\nusb123 device product:other model:Pixel device:oriole\n"
        with mock.patch.object(A, "run_adb", side_effect=[(0, wrong_dev), (0, "oriole")]):
            with self.assertRaises(SystemExit):
                A.detect_myron_serial(5038)

        empty = "List of devices attached\n"
        with mock.patch.object(A, "run_adb", return_value=(0, empty)):
            with self.assertRaises(SystemExit):
                A.detect_myron_serial(5038)

    def test_verify_device_identity_checks_device_model_and_packages(self):
        ok_out = (
            "__MODEL__=25102PCBEG\n"
            "__DEVICE__=myron\n"
            "__X11__\n"
            "    versionName=1.03.01-11b82d9-06.09.26\n"
            "      firstInstallTime=2026-09-03 22:35:10\n"
            "__X11GPU__\n"
            "    versionName=1.03.01-f592241-24.09.26\n"
            "      firstInstallTime=2026-09-07 03:45:30\n"
        )
        with mock.patch.object(A, "run_adb", return_value=(0, ok_out)) as m:
            ident = A.verify_device_identity(5038, "dev-serial")
        m.assert_called_once()
        self.assertEqual(ident["device"], "myron")
        self.assertEqual(ident["model"], "25102PCBEG")
        self.assertEqual(ident["serial_redacted"], "<redacted-adb-endpoint>")
        self.assertEqual(ident["packages"]["com.termux.x11"]["versionName"], "1.03.01-11b82d9-06.09.26")
        self.assertEqual(ident["packages"]["com.waydefu.x11gpu"]["versionName"], "1.03.01-f592241-24.09.26")

        bad_dev = ok_out.replace("__DEVICE__=myron", "__DEVICE__=other")
        with mock.patch.object(A, "run_adb", return_value=(0, bad_dev)):
            with self.assertRaises(SystemExit):
                A.verify_device_identity(5038, "dev-serial")


if __name__ == "__main__":
    unittest.main()
