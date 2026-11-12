#!/usr/bin/env python3
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path('/root/projects/GPU加速/src/f8-ahb-gatea-a1')
AUDIT = Path('/tmp/gatea-a1-submodule-audit-01.txt')
BASE = 'a6cc7952861b8a63740d42bf78553573cfa0eec0'
BRANCH = 'qualification/gatea-a1-microprobe-20260912'
PARENT_FILES = {
    'lorie/src/main/cpp/lorie/renderer.cpp': ' M',
    'lorie/src/main/cpp/recipes/xserver.cmake': ' M',
    'lorie/src/main/cpp/lorie/gatea_a1_microprobe.cpp': '??',
    'lorie/src/main/cpp/lorie/gatea_a1_microprobe.h': '??',
}
ALL_PINS = {
    'lorie/src/main/cpp/bzip2': '6a8690fc8d26c815e798c588f796eabe9d684cf0',
    'lorie/src/main/cpp/libepoxy': 'c84bc9459357a40e46e2fec0408d04fbdde2c973',
    'lorie/src/main/cpp/libfontenc': '780d1f6f192a331de7b298a96e23ebc44d2a884b',
    'lorie/src/main/cpp/libtirpc': '5ca4ca92f629d9d83e83544b9239abaaacf0a527',
    'lorie/src/main/cpp/libx11': '6c75545a1deb51f5903992c52af6bc35cc9bc103',
    'lorie/src/main/cpp/libxau': 'a9c65683e68b3a4349afee5d7673b393fb924d2e',
    'lorie/src/main/cpp/libxcvt': 'dd8631c61465cc0de5e476c7a98e56528d62b163',
    'lorie/src/main/cpp/libxdmcp': '1192d3bc407348ff316bd3bffc791b3ac73f591b',
    'lorie/src/main/cpp/libxfont': '88b9df882c0ea91d7bb468aa4792ef1b6f13aa9d',
    'lorie/src/main/cpp/libxkbfile': '42e5dedd7fd3c7c73f3870a8751893c03c1afc69',
    'lorie/src/main/cpp/libxshmfence': '89f064748554e11832a3ec783945e1f4c7fe846e',
    'lorie/src/main/cpp/libxtrans': 'cf05ba4a10c90da2c63805a5375e983b174e28b0',
    'lorie/src/main/cpp/pixman': '9cc163c9da0fb4da430641715313d95a6ec466d9',
    'lorie/src/main/cpp/xkbcomp': '2c7789785981ad1fce3858c726615b49293f7de0',
    'lorie/src/main/cpp/xorgproto': 'fcb7e9a1a0b593a44740d83b0babddd331fea830',
    'lorie/src/main/cpp/xserver': '65d790bd208ec380b196eb98f144abb0b32e334d',
}
DIRTY_FILES = {
    'lorie/src/main/cpp/libepoxy': ['src/gen_dispatch.py'],
    'lorie/src/main/cpp/libx11': ['src/KeyBind.c', 'src/Quarks.c', 'src/Xrm.c', 'src/xkb/XKBGeom.c'],
    'lorie/src/main/cpp/libxkbfile': ['src/xkbatom.c'],
    'lorie/src/main/cpp/libxtrans': ['Xtranssock.c', 'Xtransutil.c'],
    'lorie/src/main/cpp/pixman': ['pixman/pixman-arm.c'],
    'lorie/src/main/cpp/xkbcomp': ['alias.c', 'compat.c', 'compat.h', 'indicators.c', 'xkbcomp.c'],
    'lorie/src/main/cpp/xorgproto': ['include/X11/extensions/dri3proto.h'],
    'lorie/src/main/cpp/xserver': [
        'Xext/shm.c', 'Xext/shmint.h', 'Xext/xf86bigfont.c', 'dix/dixutils.c',
        'dix/enterleave.c', 'dix/main.c', 'dri3/dri3_request.c', 'exa/exa.c',
        'exa/exa_render.c', 'exa/exa_unaccel.c', 'fb/fbpict.c', 'include/os.h',
        'include/xkbfile.h', 'miext/damage/damage.c', 'os/backtrace.c',
        'os/osinit.c', 'os/utils.c', 'present/present.h', 'present/present_execute.c',
        'present/present_priv.h', 'present/present_scmd.c', 'present/present_vblank.c',
        'xkb/ddxLoad.c',
    ],
}
AUDIT_HASHES = {
    'lorie/src/main/cpp/libepoxy': '7ba07fbb866977622b1f072b805b29dcaacdf208d6eb6d8cc761ea4f61b4c59d',
    'lorie/src/main/cpp/libx11': 'c0a31f4e34eaf867412dee1413328e250424b82301fe52bdc416e9361b23b71a',
    'lorie/src/main/cpp/libxkbfile': 'b336a927917dfca924fc48e46c8f18653ea630163de47e0edfddcdb3adabb4cf',
    'lorie/src/main/cpp/libxtrans': 'aa3442ab3dc0c871cd410662dfd27ba79192195bbeda4059a02e6042d31062a1',
    'lorie/src/main/cpp/pixman': 'b6e4fe1d15c1e1155d123dc95435cccd7aa3594bceea69789e8e250634c56904',
    'lorie/src/main/cpp/xkbcomp': '9646b19922e8d4583aee24e264d815e14bbb2b6f1667311a844db09aefe987b6',
    'lorie/src/main/cpp/xorgproto': '178005aabd012a8d80aef25d2a9d68fb52afe230aef724470caca3d08596de0b',
    'lorie/src/main/cpp/xserver': 'd3f6e7a9c33f724a155d9116ca90ae897878491736a464909f4aa787924953bf',
}

def run(*args, cwd=ROOT, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f'{args}: exit {result.returncode}: {result.stderr}')
    return result

def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()

def gitlink(path):
    line = run('git', 'ls-tree', 'HEAD', '--', path).stdout.strip()
    return line.split()[2] if line else None

def status_map(output):
    result = {}
    for line in output.splitlines():
        if not line:
            continue
        result[line[3:]] = line[:2]
    return result

def submodule_list():
    result = {}
    for line in run('git', 'submodule', 'status', '--recursive').stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            result[parts[1]] = parts[0].lstrip('-+')
    return result

def audit_records():
    records = {}
    for line in AUDIT.read_text().splitlines():
        match = re.match(
            r'(?P<path>\S+) pin=(?P<pin>[0-9a-f]+) head=(?P<head>[0-9a-f]+) '
            r'recipe=(?P<recipe>\S+) patch=(?P<patch>\S+) modified-set exact=(?P<exact>\S+) '
            r'diff=(?P<diff>[0-9a-f]+)$', line)
        if match:
            records[match['path']] = match.groupdict()
    return records

def residue_paths(root):
    found = []
    for path in root.rglob('*'):
        if '.git' in path.parts:
            continue
        if path.name.endswith(('.orig', '.rej')):
            found.append(str(path.relative_to(root)))
    return found

head = run('git', 'rev-parse', 'HEAD').stdout.strip()
branch = run('git', 'branch', '--show-current').stdout.strip()
all_status = status_map(run('git', 'status', '--porcelain=v1', '--ignore-submodules=none', '--untracked-files=all').stdout)
parent_status = {path: status for path, status in all_status.items() if path not in ALL_PINS}
assert set(all_status) == set(PARENT_FILES) | set(DIRTY_FILES), all_status
assert all_status == {
    **PARENT_FILES,
    **{path: ' M' for path in DIRTY_FILES},
}, all_status
submodules = submodule_list()
records = audit_records()

assert branch == BRANCH, (branch, BRANCH)
assert head == BASE, (head, BASE)
assert set(parent_status) == set(PARENT_FILES), parent_status
assert parent_status == PARENT_FILES, parent_status
assert submodules == ALL_PINS, (submodules, ALL_PINS)
assert set(records) == set(AUDIT_HASHES), (set(records), set(AUDIT_HASHES))
assert 'CONCLUSION: ALL_TRACKED_PATCH_STATE' in AUDIT.read_text()
assert 'CI REPRODUCIBLE: YES' in AUDIT.read_text()
assert run('git', 'diff', '--check').returncode == 0

for path, pin in ALL_PINS.items():
    assert gitlink(path) == pin, (path, gitlink(path), pin)
    actual_head = run('git', '-C', path, 'rev-parse', 'HEAD').stdout.strip()
    assert actual_head == pin, (path, actual_head, pin)

for path, expected_files in DIRTY_FILES.items():
    actual = run('git', '-C', path, 'status', '--porcelain=v1', '--untracked-files=all').stdout.splitlines()
    expected = [' M ' + item for item in expected_files]
    assert actual == expected, (path, actual, expected)
    diff_hash = sha256_bytes(run('git', '-C', path, 'diff', '--binary').stdout.encode())
    assert diff_hash == AUDIT_HASHES[path], (path, diff_hash, AUDIT_HASHES[path])
    assert records[path]['pin'] == ALL_PINS[path]
    assert records[path]['head'] == ALL_PINS[path]
    assert records[path]['exact'] == 'YES'
    print(f'SUBMODULE {path} pin={ALL_PINS[path]} status_files={len(expected_files)} diff_sha256={diff_hash} EXACT=YES')

for path in set(ALL_PINS) - set(DIRTY_FILES):
    actual = run('git', '-C', path, 'status', '--porcelain=v1', '--untracked-files=all').stdout
    assert actual == '', (path, actual)

assert not residue_paths(ROOT), residue_paths(ROOT)
for path in ALL_PINS:
    assert not residue_paths(ROOT / path), (path, residue_paths(ROOT / path))

app_file = ROOT / 'lorie-app/build.gradle'
app_ids = re.findall(r'^\s*applicationId\s+["\']([^"\']+)["\']', app_file.read_text(), re.MULTILINE)
assert app_ids == ['com.waydefu.x11gpu'], app_ids

source_files = [ROOT / path for path in PARENT_FILES if path.endswith(('.cpp', '.h'))]
print(f'BRANCH={branch}')
print(f'HEAD={head}')
print(f'BASE={BASE}')
print('PARENT_SCOPE=EXACTLY_FOUR')
for path in sorted(PARENT_FILES):
    full = ROOT / path
    if full.is_file():
        print(f'PARENT {PARENT_FILES[path]} {path}')
for full in source_files:
    print(f'SOURCE_FILE {full.relative_to(ROOT)} bytes={full.stat().st_size} sha256={sha256_bytes(full.read_bytes())}')
print('APPLICATION_ID=com.waydefu.x11gpu EXACT=YES')
print('PARENT_DIFF_CHECK=PASS')
print('SUBMODULE_DIRTY_COUNT=8')
print('SUBMODULE_PATCH_STATE=ALL_TRACKED_PATCH_STATE')
print('CI_REPRODUCIBLE=YES')
print('RESIDUE=NONE')
print('SOURCE_PREFLIGHT=PASS')
