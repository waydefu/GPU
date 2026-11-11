#!/usr/bin/env python3
from pathlib import Path
import shutil

root = Path('/root/projects/GPU加速/src/f8-ahb-gatea-a1')
out = Path('/root/projects/GPU加速/evidence/session/gate-a-a1/source')
out.mkdir(parents=True, exist_ok=True)
for rel in (
    'lorie/src/main/cpp/lorie/gatea_a1_microprobe.cpp',
    'lorie/src/main/cpp/lorie/gatea_a1_microprobe.h',
    'lorie/src/main/cpp/lorie/renderer.cpp',
    'lorie/src/main/cpp/recipes/xserver.cmake',
    'lorie-app/build.gradle',
    '.github/workflows/debug_build.yml',
):
    shutil.copy2(root / rel, out / Path(rel).name)
for src in (
    Path('/tmp/gatea-a1-submodule-audit-01.txt'),
    Path('/root/projects/GPU加速/evidence/session/gate-a-a1/source-preflight-stop.txt'),
):
    shutil.copy2(src, out / src.name)
print('RAW_SOURCE_COPY=PASS')
for path in sorted(out.iterdir()):
    if path.is_file():
        print(f'{path.name} bytes={path.stat().st_size}')
