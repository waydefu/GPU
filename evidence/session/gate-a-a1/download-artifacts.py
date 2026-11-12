#!/usr/bin/env python3
from pathlib import Path
import subprocess

run_id = '34688831275'
repo = 'waydefu/termux-x11'
dest = Path('/root/projects/GPU加速/evidence/session/gate-a-a1/artifacts') / run_id
dest.mkdir(parents=True, exist_ok=True)
for name in ('termux-x11-universal-debug', 'termux-x11-unstripped-libraries-for-ndk-stack'):
    command = ['gh', 'run', 'download', run_id, '--repo', repo, '--name', name, '--dir', str(dest)]
    print('RUN=' + ' '.join(command))
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    print('EXIT=' + str(result.returncode))
    if result.stdout:
        print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='')
    if result.returncode:
        raise SystemExit(result.returncode)
print('ARTIFACT_DOWNLOADS=PASS')
