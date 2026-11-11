#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('/root/projects/GPU加速/src/f8-ahb-gatea-a1')
EVIDENCE = Path('/root/projects/GPU加速/evidence/session/gate-a-a1')
CHECKPOINT = '3db76baa15c0a6c13460349060485d863102dc86'
BASE = 'a6cc7952861b8a63740d42bf78553573cfa0eec0'
BRANCH = 'qualification/gatea-a1-microprobe-20260912'
REPO = 'waydefu/termux-x11'
RUN_ID = '34688831275'


def run(*args, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f'{args}: {result.returncode}: {result.stderr.decode(errors="replace")}')
    return result.stdout


def gh_json(*args):
    return json.loads(run('gh', *args))


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

remote_refs = run('git', 'ls-remote', 'fork', f'refs/heads/{BRANCH}').decode().strip()
remote_sha = remote_refs.split('\t', 1)[0] if remote_refs else None
branch_api = gh_json('api', f'repos/{REPO}/branches/{BRANCH}')
run_api = gh_json('api', f'repos/{REPO}/actions/runs/{RUN_ID}')
artifacts_api = gh_json('api', f'repos/{REPO}/actions/runs/{RUN_ID}/artifacts')
prs = gh_json('pr', 'list', '--repo', REPO, '--head', f'waydefu:{BRANCH}', '--state', 'all', '--json', 'number,state,url')

assert remote_sha == CHECKPOINT, (remote_sha, CHECKPOINT)
assert branch_api['commit']['sha'] == CHECKPOINT, branch_api['commit']['sha']
assert run_api['head_sha'] == CHECKPOINT, run_api['head_sha']
assert run_api['head_branch'] == BRANCH
assert run_api['path'] == '.github/workflows/debug_build.yml'
assert run_api['event'] == 'workflow_dispatch'
assert run_api['run_attempt'] == 1
assert run_api['status'] == 'completed' and run_api['conclusion'] == 'success'
assert not prs, prs

selected = {item['name']: item for item in artifacts_api['artifacts'] if item['name'] in {
    'termux-x11-universal-debug',
    'termux-x11-unstripped-libraries-for-ndk-stack',
}}
assert set(selected) == {'termux-x11-universal-debug', 'termux-x11-unstripped-libraries-for-ndk-stack'}
assert all(item['workflow_run']['head_sha'] == CHECKPOINT for item in selected.values())

status = run('git', 'status', '--short', '--ignore-submodules=none', '--untracked-files=all').decode().splitlines()
assert len(status) == 8 and all(line[0:2] == ' m' for line in status), status
assert run('git', 'diff', '--check') == b''
source_diff = run('git', 'diff', f'{BASE}..{CHECKPOINT}', '--binary')
source_diff_sha256 = hashlib.sha256(source_diff).hexdigest()
new_files = {}
for rel in ('lorie/src/main/cpp/lorie/gatea_a1_microprobe.cpp', 'lorie/src/main/cpp/lorie/gatea_a1_microprobe.h'):
    path = ROOT / rel
    new_files[rel] = {'bytes': path.stat().st_size, 'sha256': sha256(path)}

apk = EVIDENCE / 'artifacts' / RUN_ID / 'termux-x11-universal-debug.apk'
unstripped = EVIDENCE / 'artifacts' / RUN_ID / '01x55434/obj/arm64-v8a/libXlorie.so'
assert apk.is_file() and unstripped.is_file()
reports = {
    'apk': json.loads((EVIDENCE / 'apk-verification/apk-report.json').read_text()),
    'elf': json.loads((EVIDENCE / 'elf-verification/elf-report.json').read_text()),
}
assert reports['apk']['apk_sha256'] == sha256(apk)
assert reports['elf']['unstripped_sha256'] == sha256(unstripped)

result = {
    'remote_refs': remote_refs,
    'remote_branch_api': {'name': branch_api['name'], 'sha': branch_api['commit']['sha']},
    'run_api': {key: run_api[key] for key in ('id', 'run_attempt', 'run_number', 'event', 'status', 'conclusion', 'head_branch', 'head_sha', 'path', 'workflow_id', 'html_url')},
    'selected_artifacts': selected,
    'pull_requests_for_branch': prs,
    'git_status_after_commit': status,
    'git_diff_check': 'PASS',
    'source_diff_sha256': source_diff_sha256,
    'new_files': new_files,
    'artifact_targets': {
        'apk': {'path': str(apk), 'bytes': apk.stat().st_size, 'sha256': sha256(apk)},
        'unstripped_arm64': {'path': str(unstripped), 'bytes': unstripped.stat().st_size, 'sha256': sha256(unstripped)},
    },
}
(EVIDENCE / 'final-external-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
