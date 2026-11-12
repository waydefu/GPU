#!/usr/bin/env python3
from pathlib import Path
import base64
import json
import subprocess

out = Path('/root/projects/GPU加速/evidence/session/gate-a-a1')
repo = 'waydefu/termux-x11'
run_id = '34688831275'
head = '3db76baa15c0a6c13460349060485d863102dc86'

def gh(*args):
    result = subprocess.run(['gh', *args], text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f'gh {args}: {result.returncode}: {result.stderr}')
    return result.stdout

run_view = gh('run', 'view', run_id, '--repo', repo, '--json',
              'databaseId,workflowName,status,conclusion,headSha,headBranch,event,workflowDatabaseId,jobs,url,createdAt,updatedAt,number,displayTitle')
(out / 'ci-run-view.json').write_text(run_view)
run_api = gh('api', f'repos/{repo}/actions/runs/{run_id}')
(out / 'ci-run-api.json').write_text(run_api)
artifact_api = gh('api', f'repos/{repo}/actions/runs/{run_id}/artifacts')
(out / 'ci-artifacts.json').write_text(artifact_api)
checks = gh('api', f'repos/{repo}/commits/{head}/check-runs')
(out / 'ci-check-runs.json').write_text(checks)
workflow_api = gh('api', f'repos/{repo}/contents/.github/workflows/debug_build.yml?ref={head}')
(out / 'workflow-at-head-api.json').write_text(workflow_api)
workflow_obj = json.loads(workflow_api)
(out / 'workflow-at-head.yml').write_bytes(base64.b64decode(workflow_obj['content']))
print('CI_METADATA=PASS')
for path in ('ci-run-view.json', 'ci-run-api.json', 'ci-artifacts.json', 'ci-check-runs.json', 'workflow-at-head-api.json', 'workflow-at-head.yml'):
    full = out / path
    print(f'{path} bytes={full.stat().st_size}')
