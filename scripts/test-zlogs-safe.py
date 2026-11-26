"""Regression tests for failed compression verification pipelines."""

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


class ZlogsSafetyTest(unittest.TestCase):
    def check_failure(self, tool_variable, tool_body, diagnostic):
        script = Path(__file__).with_name("zlogs-safe.sh")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tool = root / "failing-tool"
            tool.write_text("#!/bin/sh\n" + tool_body)
            tool.chmod(0o700)

            source = root / "sample.log"
            payload = b"synthetic log fixture\n" * 100_000
            source.write_bytes(payload)
            old = time.time() - 3600
            os.utime(source, (old, old))
            manifest = root / "manifest.tsv"

            result = subprocess.run(
                ["bash", str(script), str(root), str(manifest)],
                env={**os.environ, "MIN_AGE_H": "0", tool_variable: str(tool)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(diagnostic, result.stdout)
            self.assertEqual(source.read_bytes(), payload)
            self.assertFalse(list(root.glob("sample.log.zst*")))
            self.assertEqual(len(manifest.read_text().splitlines()), 1)

    def test_failed_checksum_with_valid_output_keeps_source(self):
        self.check_failure(
            "SHA256_BIN",
            'sha256sum "$@"\nexit 42\n',
            "FAIL sha256 orig",
        )

    def test_failed_decoder_with_complete_output_keeps_source(self):
        self.check_failure(
            "ZSTD_BIN",
            '''if [ "$1" = -dc ]; then
    cat -- "$3"
    exit 43
fi
cp -- "$7" "$5"
''',
            "FAIL verify",
        )


if __name__ == "__main__":
    unittest.main()
