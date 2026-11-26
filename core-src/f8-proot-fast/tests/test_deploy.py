"""Offline checks for deployment publication, backup selection, and smoke exit codes."""

import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest


DEPLOY = Path(__file__).resolve().parents[1] / "deploy"
BINARY = "bin/proot-fast8"
LOADER = "libexec/loader"


def write_binary(path, version):
    path.write_text(f"""#!/bin/bash
case "$1" in
  --version) echo 5.1.107.92-{version} ;;
  -0) echo 1514 ;;
  *) exit 64 ;;
esac
""")
    path.chmod(0o755)


def write_manifest(directory, name, paths):
    hashes = subprocess.check_output(["sha256sum", *paths], cwd=directory)
    (directory / name).write_bytes(hashes)


class DeployTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.stage = self.root / "stage/out"
        self.target = self.root / "target"
        self.backups = self.root / "backups"
        for release, version in ((self.stage, "fast9"), (self.target, "fast8")):
            (release / "bin").mkdir(parents=True)
            (release / "libexec").mkdir()
            write_binary(release / BINARY, version)
            (release / LOADER).write_text(f"{version} loader\n")
        (self.stage / "libexec/loader32").write_text("candidate loader32\n")
        write_manifest(self.stage, "candidate.sha256", [BINARY, LOADER, "libexec/loader32"])
        write_manifest(self.target, "deployed.sha256", [BINARY, LOADER])
        self.environment = dict(os.environ, TARGET_OUT=str(self.target),
                                STAGE_DIR=str(self.stage.parent), BACKUP_ROOT=str(self.backups),
                                SCRIPT_DIR=str(DEPLOY), UBU_ROOTFS=str(self.root / "guest"))
        self.source = (DEPLOY / "deploy-proot-candidate.sh").read_text()

    def run_shell(self, script):
        return subprocess.run(["bash", "-eu", "-o", "pipefail", "-c", script],
                              env=self.environment, capture_output=True, text=True, timeout=10)

    def apply(self, stub=""):
        start = self.source.index("# --- LIVE / TARGET APPLY")
        helper = DEPLOY / "release-files.sh"
        includes = f"source {shlex.quote(str(helper))}\n" if helper.exists() else ""
        return self.run_shell(includes + stub + "\n" + self.source[start:])

    def run_rollback(self, *args):
        return subprocess.run(["bash", str(DEPLOY / "rollback-to-fast8.sh"),
                               "--backup-root", str(self.backups), "--target-out",
                               str(self.target), *map(str, args)],
                              capture_output=True, text=True, timeout=10)

    def test_partial_publish_restores_previous_release(self):
        before = {p: (self.target / p).read_bytes()
                  for p in (BINARY, LOADER, "deployed.sha256")}
        failure = """
mv() {
    if [[ ${!#} == "$TARGET_OUT/libexec/loader" && ! -e "$STAGE_DIR/injected" ]]; then
        touch "$STAGE_DIR/injected"
        echo INJECTED_LOADER_RENAME >&2
        return 77
    fi
    command mv "$@"
}
"""
        result = self.apply(failure)
        self.assertTrue((self.stage.parent / "injected").exists(), result.stderr)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RECOVERY_PASS", result.stderr)
        for p, expected in before.items():
            self.assertEqual((self.target / p).read_bytes(), expected, p)
        self.assertFalse((self.target / "libexec/loader32").exists())
        self.assertFalse((self.backups / "LATEST_FAST8_BACKUP").exists())

    def test_redeploy_preserves_latest_fast8_pointer(self):
        first = self.apply()
        self.assertEqual(first.returncode, 0, first.stderr)
        pointer = self.backups / "LATEST_FAST8_BACKUP"
        first_backup = pointer.read_text()
        first_binary = (Path(first_backup.strip()) / BINARY).read_bytes()
        second = self.apply()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(pointer.read_text(), first_backup)
        self.assertEqual((Path(first_backup.strip()) / BINARY).read_bytes(), first_binary)
        self.assertEqual(self.run_rollback("--dry-run").returncode, 0)
        restored = self.run_rollback("--apply", "--confirm-live")
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertIn("ROLLBACK_PASS", restored.stdout)
        self.assertEqual((self.target / BINARY).read_bytes(), first_binary)

    def test_post_deploy_failure_restores_previous_fast9_and_keeps_fast8_pointer(self):
        initial = self.apply()
        self.assertEqual(initial.returncode, 0, initial.stderr)
        pointer = self.backups / "LATEST_FAST8_BACKUP"
        fast8 = pointer.read_bytes()
        paths = (BINARY, LOADER, "libexec/loader32", "deployed.sha256")
        previous = {p: (self.target / p).read_bytes() for p in paths}
        (self.stage / LOADER).write_text("new candidate loader\n")
        write_manifest(self.stage, "candidate.sha256", paths[:-1])
        result = self.apply("""
sha256sum() {
    if [[ "$*" == "-c deployed.sha256" ]]; then
        echo INJECTED_POST_DEPLOY_CHECK >&2
        return 78
    fi
    command sha256sum "$@"
}
""")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("INJECTED_POST_DEPLOY_CHECK", result.stderr)
        self.assertIn("RECOVERY_PASS", result.stderr)
        for p, expected in previous.items():
            self.assertEqual((self.target / p).read_bytes(), expected, p)
        self.assertEqual(pointer.read_bytes(), fast8)

    def test_failed_recovery_retains_verified_backup(self):
        result = self.apply("""
mv() {
    if [[ "$*" == *'/candidate/deployed.sha256 '* ||
          "$*" == *'/recovery/libexec/loader '* ]]; then
        echo INJECTED_RENAME_FAILURE >&2
        return 77
    fi
    command mv "$@"
}
""")
        self.assertEqual(result.returncode, 11, result.stderr)
        self.assertIn("RECOVERY_FAILED", result.stderr)
        self.assertEqual(result.stderr.count("INJECTED_RENAME_FAILURE"), 2)
        backups = list(self.backups.glob("out8-previous-*"))
        self.assertEqual(len(backups), 1)
        restored = self.run_rollback("--apply", "--confirm-live", "--backup-dir", backups[0])
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertEqual((self.target / LOADER).read_text(), "fast8 loader\n")

    def test_rollback_rejects_valid_hashes_for_fast9(self):
        backup = self.backups / "previous"
        for subtree in ("bin", "libexec"):
            (backup / subtree).mkdir(parents=True)
        write_binary(backup / BINARY, "fast9")
        (backup / LOADER).write_text("fast9 loader\n")
        write_manifest(backup, "backup.sha256", [BINARY, LOADER])
        result = self.run_rollback("--dry-run", "--backup-dir", backup)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("ROLLBACK_DRY_RUN_PASS", result.stdout)

    def test_claude_smoke_checks_exit_in_both_modes(self):
        guest_bin = self.root / "guest/usr/bin"
        guest_bin.mkdir(parents=True)
        start = self.source.index("run_claude_smoke() {")
        stop = self.source.index('\necho "4.', start)
        for with_xvfb in (False, True):
            if with_xvfb:
                (guest_bin / "Xvfb").touch(mode=0o755)
            for rc in (0, 124, 127, 133):
                with self.subTest(xvfb=with_xvfb, launcher_rc=rc):
                    result = self.run_shell(f"launcher() {{ return {rc}; }}\n"
                                            + self.source[start:stop]
                                            + "\nrun_claude_smoke launcher dummy")
                    self.assertEqual(result.returncode, 0 if rc in (0, 124) else 1,
                                     result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
