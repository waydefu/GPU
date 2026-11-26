"""Exercise archive and manifest failures on synthetic logs."""

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("zlogs-safe.sh")
HEADER = "path\torig_bytes\torig_sha256\tzst_bytes\n"
PAYLOAD = b"synthetic log fixture\n" * 100_000


class ZlogsSafetyTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "sample.log"
        self.archive = self.root / "sample.log.zst"
        self.manifest = self.root / "manifest.tsv"
        self.source.write_bytes(PAYLOAD)
        old = time.time() - 3600
        os.utime(self.source, (old, old))
        self.env = {**os.environ, "MIN_AGE_H": "0", "SHA256_BIN": shutil.which("sha256sum")}
        self.codec()

    def shim(self, name, body):
        path = self.root / name
        path.write_text("#!/bin/sh\nset -eu\n" + body)
        path.chmod(0o700)
        return str(path)

    def codec(self, action="", decode_status=0):
        self.env["ZSTD_BIN"] = self.shim(
            "codec",
            f'''if [ "$1" = -dc ]; then
    cat -- "$3"
    exit {decode_status}
fi
cat -- "$6"
{action}
''',
        )

    def compress(self, *options):
        return subprocess.run(
            ["bash", str(SCRIPT), str(self.root), str(self.manifest), *options],
            env=self.env, capture_output=True, text=True, check=False,
        )

    def verify_failure(self, result, diagnostic, payload=PAYLOAD, published=False):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stderr)
        self.assertEqual(self.source.read_bytes(), payload)
        self.assertEqual(self.archive.exists(), published)
        self.assertEqual(self.manifest.read_text(), HEADER)
        self.assertFalse(list(self.root.glob("*.tmp.*")))

    def test_failed_checksum_after_valid_output(self):
        self.env["SHA256_BIN"] = self.shim("hash", 'sha256sum "$@"\nexit 42\n')
        self.verify_failure(self.compress("--remove-source"), "FAIL sha256 orig")

    def test_failed_decoder_after_complete_output(self):
        self.codec(decode_status=43)
        self.verify_failure(self.compress("--remove-source"), "FAIL verify")

    def test_source_append_after_compression(self):
        self.codec('printf "new tail" >> "$6"')
        self.verify_failure(
            self.compress("--remove-source"), "FAIL source changed", PAYLOAD + b"new tail",
        )

    def test_manifest_commit_failure_preserves_source(self):
        self.env["PATH"] = str(self.root) + os.pathsep + self.env["PATH"]
        self.shim("mv", "exit 77\n")
        self.verify_failure(self.compress("--remove-source"), "FAIL commit manifest", published=True)
        self.verify_failure(
            self.compress("--remove-source"), "without a usable manifest record", published=True,
        )

    def test_defaults_to_keeping_original_and_records_archive(self):
        result = self.compress()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.source.read_bytes(), PAYLOAD)
        self.assertEqual(self.archive.read_bytes(), PAYLOAD)
        self.assertIn(hashlib.sha256(PAYLOAD).hexdigest(), self.manifest.read_text())

    def test_offline_removal_happens_after_manifest_record(self):
        self.env["PATH"] = str(self.root) + os.pathsep + self.env["PATH"]
        self.env["EXPECTED_MANIFEST"] = str(self.manifest)
        self.shim("rm", f'''if [ "${{2:-}}" = "{self.source}" ]; then
    [ "$(wc -l < "$EXPECTED_MANIFEST")" -eq 2 ] || exit 79
fi
exec "{shutil.which("rm")}" "$@"
''')
        result = self.compress("--remove-source")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.source.exists())
        self.assertEqual(self.archive.read_bytes(), PAYLOAD)


if __name__ == "__main__":
    unittest.main()
