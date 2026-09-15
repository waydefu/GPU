# AUTHORITY CHECKSUM — Gate A A1 marker iteration (2026-09-12, CLOSED)

SOURCE:
branch=qualification/gatea-a1-microprobe-20260912
HEAD=4196798dd7bb93ab386b955009f49e7a5a0e1019 (parent 3db76ba preserved, not amended)
worktree=/root/projects/GPU加速/src/f8-ahb-gatea-a1, post-commit clean
diff=+4/-1, 2 files: renderer.cpp (PRECALL+bracing), gatea_a1_microprobe.cpp (ENTRY)
D0a worktree untouched (qualification/d0a-narrow-20260912 / a6cc795)

ARTIFACT:
run=34694695463 completed/success, headSha=4196798=remote branch (QUALIFIED PASS, non-runtime)
APK=5ad7d2c62cc8f31ff1d37a4cdac45a8535cc8856a7cb3a3c97d5487014563c90
package=com.waydefu.x11gpu versionCode=15 versionName=1.03.01-4196798-12.09.26 ABI=arm64-v8a
ZIP: testzip PASS, 493 members, 0 duplicates, STORED 259/259 mod4 PASS
formal zipalign: BLOCKED (x86-64 tool on aarch64), not claimed
ELF Build ID=034eebf4e45af91a988c858e04b7c75f9c460295 embedded==unstripped
strings: PRECALL+ENTRY in both; gateaA1MicroprobeRun in unstripped only (hidden, as designed)
signer: expected experimental cert b6da0148…ee5e1 present (EXACT MATCH component)

RUNTIME:
ONE controlled launch, display 0, no crash, teardown complete, no retry

PRECALL:
present (20:57:20.491, PID 23546)

ENTRY:
present (same second, same PID)

PROBE_BODY_CONFIRMED:
YES

CONTROL:
3/3 SHADER_SAMPLE_EXACT (exact_fail_pixels=0, maxΔ=0)

BGRA:
3/3 SHADER_SAMPLE_EXACT (exact, no black/swap/mismatch; all error counters 0)

RGBA:
3/3 SHADER_SAMPLE_EXACT

ROOT CAUSE (PID 21238 startup SIGSEGV):
STILL UNKNOWN (not merged with this clean run; observed / non-reproduced this iteration)

STABLE:
pid=14862 :1 -legacy-drawing alive post-teardown; experimental empty; :3 unreachable

HDMI:
UNTOUCHED

NEXT:
propose ownership/fence/lifecycle architecture review before any production Gate A
prototype; AWAIT explicit authorization; no further runtime
