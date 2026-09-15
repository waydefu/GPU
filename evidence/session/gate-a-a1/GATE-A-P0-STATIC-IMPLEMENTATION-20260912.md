# Gate A P0 static implementation — 2026-09-12

## SOURCE

```text
branch: qualification/gatea-a1-microprobe-20260912
base:   4196798dd7bb93ab386b955009f49e7a5a0e1019 (preserved, not amended)
head:   2844a18a5f50250ac2ac48fc9fdb30514006651a
worktree: /root/projects/GPU加速/src/f8-ahb-gatea-a1, post-commit clean
D0a:    qualification/d0a-narrow-20260912 / a6cc795, untouched
```

## DIFF

```text
lorie/src/main/cpp/lorie/lorie.h | 395 +++++++++++++++++++++++
1 file changed, 395 insertions(+), 0 deletions(-)
```

Three hunks: system includes (stddef/stdint/stdlib/time/unistd/pthread, additive);
P0 foundation block after `LorieGpuCopyEntry`; one sideband member appended last
in `lorie_shared_server_state` (existing offsets unchanged).

## STATIC CHECKLIST

- ABI exact size/offset: PASS — asserts for sideband (40B + 7 offsets), frame
  (40B + 8 offsets), 6 bodies, entry ABI (168B).
- Atomics fixed-width/aligned: PASS — u32/u64, natural alignment, asserts.
- Lock-free explicit: PASS — compile-time `__atomic_always_lock_free(4/8)` assert
  + runtime per-address `lorieGateAAtomicsLockFree` gate.
- Release/acquire centralized: PASS — all accessors in one block; existing call
  sites untouched (P5 rewires; documented boundary, not a violation).
- First failure sticky: PASS — once-CAS + relaxed code store + pure derivation.
- Fatal sticky, single authority: PASS — one CAS pair; no competing authority.
- Fatal wakeup reachable: PASS — waiter broadcast primitives; P1 wires wakeup.
- Queue entry ABI: UNCHANGED (assert + zero entry changes).
- completedSerial semantics: UNCHANGED (accessors only, no call-site change).
- Default OFF: PASS — exact-"1" flag, zero call sites, OFF trivially == D0a.
- Production behavior: UNCHANGED — header-only additive, no call sites.
- No imported enablement / replay / D0b / Gate H: confirmed absent.
- No new volatile sync; no TODO/FIXME; `git diff --check`: PASS.
- Name collisions: all `LorieGateA*` symbols exist only in `lorie.h`.

## REVIEWED DEVIATION (layout/semantics identical, race-freedom tightened)

R3 text described fatal as plain reason write + CAS 0→1. Two concurrent fatal
racers could then interleave a losing reason with the winning flag (formal data
race on `fatalReason`). Implementation instead CASes 0→reason (nonzero fail code)
so the single atomic edge carries flag+reason; `fatalReason` is kept as a
diagnostic mirror only and MUST NOT be read for decisions. Sticky, 0=clean, and
the 40-byte layout are unchanged.

## SCOPE

No P1+ flow, unlock transition, publication, sampling, Done/Destroy/Close
changes, imported support, replay, entry/completedSerial changes. No CI,
APK, ADB, device, runtime, Stable, or HDMI operation.

## NATIVE COMPILE QUALIFICATION (2026-09-12, post-static)

```text
command: ANDROID_HOME=/root/android-sdk ./gradlew --no-daemon --no-build-cache
         --max-workers=2 ':lorie:buildCMakeDebug[arm64-v8a]'
result: BUILD SUCCESSFUL, exit 0
log:    evidence/session/gate-a-a1/GATE-A-P0-NATIVE-BUILD-20260912.log
```

Warnings: 9 total, all proven pre-existing — 1 GLX typedef (S4 baseline);
3 c99-designator on the keycode table (present at base `4196798:363`, lines
merely shifted +395 by this diff); 4 format + 1 reorder-init in untouched
`.cpp` files. Zero new warnings from P0 header code. Worktree verified clean
after build (all outputs gitignored). APK packaging deliberately not attempted
(known x86-64 AIDL-on-ARM64 blocker).
