#!/usr/bin/env python3
"""Host mocks: Android Activity liveness must not use workstation /proc."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "android_activity_liveness", HERE / "android_activity_liveness.py"
)
M = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(M)


class AndroidActivityLivenessTests(unittest.TestCase):
    def test_host_proc_absent_does_not_imply_dead(self):
        rec = M.classify_android_activity_liveness(
            device_proc_exists=True,
            device_ps_identity_ok=True,
            host_proc_exists=False,
            activity_pid=19659,
        )
        self.assertEqual(rec["activity_alive_during_wait"], 1)
        self.assertEqual(rec["host_proc_used_as_death"], 0)
        self.assertEqual(rec["authority"], M.AUTHORITY)

    def test_device_proc_alive_classifies_alive(self):
        rec = M.classify_android_activity_liveness(
            device_proc_exists=True,
            device_ps_identity_ok=True,
            host_proc_exists=True,
            activity_pid=19659,
            renderer_tid=19569,
        )
        self.assertEqual(rec["activity_alive_during_wait"], 1)
        self.assertEqual(rec["device_proc_exists"], 1)
        self.assertEqual(rec["device_ps_identity_ok"], 1)

    def test_device_proc_dead_classifies_dead(self):
        rec = M.classify_android_activity_liveness(
            device_proc_exists=False,
            device_ps_identity_ok=False,
            host_proc_exists=False,
            activity_pid=19659,
        )
        self.assertEqual(rec["activity_alive_during_wait"], 0)

    def test_host_proc_exists_cannot_override_device_dead(self):
        rec = M.classify_android_activity_liveness(
            device_proc_exists=False,
            device_ps_identity_ok=False,
            host_proc_exists=True,
            activity_pid=19659,
        )
        self.assertEqual(rec["activity_alive_during_wait"], 0)
        self.assertEqual(rec["host_proc_used_as_life"], 0)

    def test_device_proc_without_ps_identity_is_dead(self):
        rec = M.classify_android_activity_liveness(
            device_proc_exists=True,
            device_ps_identity_ok=False,
            host_proc_exists=False,
            activity_pid=19659,
        )
        self.assertEqual(rec["activity_alive_during_wait"], 0)

    def test_frozen_abb27a65_shape_is_alive(self):
        rec = M.classify_android_activity_liveness(
            device_proc_exists=True,
            device_ps_identity_ok=True,
            host_proc_exists=False,
            activity_pid=19659,
            renderer_tid=19569,
        )
        self.assertEqual(rec["activity_alive_during_wait"], 1)
        text = M.format_record(rec)
        self.assertIn("host_proc_used_as_death=0", text)
        self.assertIn("activity_alive_during_wait=1", text)


if __name__ == "__main__":
    unittest.main()
