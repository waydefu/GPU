# S4 PRE-D0a HYGIENE — 2026-09-11

## STATUS

```text
PASS
```

The four source hygiene fixes are applied and the native `Xlorie` target builds.
Local APK packaging is blocked on this ARM64 host because the installed Android
Build Tools AIDL executable is x86-64. The exact source was subsequently built
on the fork's x64 GitHub Actions runner; artifact provenance is recorded below.
Runtime qualification is still `NOT STARTED` because the fresh ADB lane did not
produce a usable endpoint.

## Scope and safety

- Worktree: `/root/projects/GPU加速/src/f8-ahb`
- HEAD at entry: `98224356e40913dcf2188d18748eba9401639850`
- Existing dirty B3a/E1b/portability changes were preserved; no reset, revert,
  clean, commit, or PR.
- No persistent staging/texture, queue ABI, mutex ownership strategy,
  CloseScreen drain, DoneComposite completion semantics, predicate, shader,
  blend, X-byte repair, or Gate A change.
- No package install, process launch, or runtime qualification was performed.
  Fresh ADB discovery/connect attempts are recorded separately below. Stable
  `com.termux.x11` / `:1` was untouched.

## S4-1 mmap

`lorie/src/main/cpp/lorie/InitOutput.c:436`, `OsVendorInit` now checks the
`mmap()` result against `MAP_FAILED`, clears `lorieScreen.state`, and exits
before `memset()`. It cannot treat `(void *)-1` as a valid mapping.

## S4-2 receive fail-closed

`lorie/src/main/cpp/lorie/buffer.c:499`,
`LorieBuffer_recvHandleFromUnixSocket` now:

- clears `*outBuffer` at entry;
- rejects short struct reads;
- clears sender-process raw pointer/FD fields before receiving process-local
  resources;
- validates FD descriptor dimensions/overflow and mapping result;
- validates the AHardwareBuffer receive return code and handle;
- rejects unknown buffer types;
- closes/unmaps/releases received resources on discard/allocation failure.

`lorie/src/main/cpp/lorie/activity.cpp:211`, `xcallback(EVENT_ADD_BUFFER)` now
checks the caller-visible pointer before `LorieBuffer_description()` or
`g_renderer.addBuffer()`, so a failed receive cannot reuse the previous static
buffer pointer.

## S4-3 fence fail-closed

Producer gates:

- `InitOutput.c:1493`, Composite scheduling rejects the GPU path when the
  existing `lorieEglHasFence()` capability is false.
- `InitOutput.c:1679`, Solid scheduling uses the same gate.

Consumers:

- `renderer.cpp:935`, `Renderer::applyPendingGpuCopies` checks capability and
  all typed PFNs before use.
- `renderer.cpp:943` and `:951` check `EGL_NO_SYNC` and wait result; completion
  is not published on failure.
- `renderer.cpp:987`, `Renderer::redrawLocked` has the same entry gate.
- `renderer.cpp:1115` and `:1139` guard the main redraw fence.
- `renderer.cpp:1167` and `:1172` guard the next-buffer fence.

Only a valid sync handle is waited/destroyed. The successful fence ordering and
`completedSerial` publication path is unchanged; no `glFinish` or new fence
protocol was introduced.

## S4-4 AHB lock paths

`buffer.c:408`, `LorieBuffer_lock` now clears the output pointer first, rejects
NULL/invalid regular or FD mappings, rejects a NULL AHB, records AHB lock
failure without setting `locked`, clears `lockedData`, and returns an error.

`InitOutput.c:2398`, `loriePrepareAccess` stores whether this call acquired the
existing shared mutex and unlocks it on a subsequent AHB lock failure. The
mutex timeout/reinitialization strategy is unchanged.

## Files/functions changed by S4

S4 delta is limited to these existing dirty source files:

- `lorie/src/main/cpp/lorie/InitOutput.c`
  - `OsVendorInit`
  - `lorieTryScheduleGpuBlit`
  - `lorieTryScheduleGpuSolid`
  - `loriePrepareAccess`
  - one local declaration for the existing fence capability query
- `lorie/src/main/cpp/lorie/buffer.c`
  - `LorieBuffer_lock`
  - `LorieBuffer_recvHandleFromUnixSocket`
- `lorie/src/main/cpp/lorie/activity.cpp`
  - `xcallback` / `EVENT_ADD_BUFFER`
- `lorie/src/main/cpp/lorie/renderer.cpp`
  - `Renderer::applyPendingGpuCopies`
  - `Renderer::redrawLocked`

No D0a function or persistent resource was added.

## Verification

### git diff

```text
git diff --check: PASS
```

Final tracked diff stat, including the pre-existing dirty worktree changes:

```text
 lorie/src/main/cpp/lorie/InitOutput.c      | 156 ++++++++++++++++++++++++-
 lorie/src/main/cpp/lorie/activity.cpp      |   4 +
 lorie/src/main/cpp/lorie/buffer.c          | 175 +++++++++++++++++++++++------
 lorie/src/main/cpp/lorie/lorie.h           |   5 +
 lorie/src/main/cpp/lorie/renderer.cpp      | 162 ++++++++++++++++++++++----
 lorie/src/main/cpp/lorie/shm/shmem.c       |   2 +-
 lorie/src/main/cpp/patches/dix-config.h.in |   8 +-
 lorie/src/main/cpp/patches/x11.patch       |  73 ++++++++++++
 lorie/src/main/cpp/patches/xserver.patch   |  47 ++++----
 lorie/src/main/cpp/recipes/xkbcomp.cmake   |   2 +-
 lorie/src/main/cpp/recipes/xserver.cmake   |   8 +-
 11 files changed, 552 insertions(+), 90 deletions(-)
```

### Build

Minimal native target:

```text
./gradlew --no-daemon --no-build-cache --max-workers=2 ':lorie:buildCMakeDebug[arm64-v8a]'
exit=0
BUILD SUCCESSFUL
```

One pre-existing GLX typedef redefinition warning remained; no new S4 compile
warning blocked the target.

APK packaging:

```text
./gradlew --no-daemon --no-build-cache --max-workers=2 ':lorie-app:assembleStandaloneDebug'
exit=1
failed task: :lorie:compileDebugAidl
error: A problem occurred starting process 'command "/root/android-sdk/build-tools/36.0.0/aidl"'
```

Tooling evidence:

```text
host: aarch64
build-tools/36.0.0/aidl: ELF x86-64
interpreter: /lib64/ld-linux-x86-64.so.2
run result: cannot execute: required file not found
build-tools/35.0.0/aidl: ELF x86-64
ARM64 AIDL: not found
qemu-x86_64/box64: not found
```

No SDK package, license, compatibility layer, build override, old APK, or
local repackaging was used.

## CI recovery and artifact provenance

Qualification source:

```text
branch: qualification/s4-pre-d0a-20260911
base: 98224356e40913dcf2188d18748eba9401639850
checkpoint: f0b8afc67b58c72a88cf56108435e53833291bf1
quad typedef fix: a9d8c4d1aec6a76388c9f281ed5ef89f4a91592c
patch closure: fd988c45e51692c6cae4420f84466872bedf9bf6
```

CI recovery attempts:

```text
34604480905 / f0b8afc: failed — quad_t/u_quad_t macro collision
34605194362 / a9d8c4d: failed — missing lorieRecheckGpuCopies definition
34606849337 / fd988c4: PASS — Build + APK + unstripped artifact
```

Workflow: `waydefu/termux-x11` `Build / debug_build.yml`, x64
`ubuntu-latest`, `workflow_dispatch` on the exact branch.

Artifact provenance:

```text
APK artifact ID: 10267113234
APK artifact digest: sha256:0c977ff3e0990ea04b419414258d922b8b5f9320a5dda4cfd4131a2e66d51c49
APK bytes: 14886126
APK SHA256: ece4321447380f21f04a99750dadb3a9dfec34146e17bc34df228f0ba1870f43
package: com.waydefu.x11gpu
versionCode: 15
versionName: 1.03.01-fd988c4-11.09.26

unstripped artifact ID: 10266793366
unstripped ZIP bytes: 28127581
unstripped ZIP SHA256: 44face0c2b550deb0ae6c352d59ddf1149aec42202c6fd378515b285cbc2417a
ARM64 embedded library SHA256: f22bbe6d006321fb8e5dd08441b5f56ff7fd1a203d2078d575ca79f213df520f
ARM64 unstripped library SHA256: d06c7293b52dcee557c84d7fa4219d72bc4cfe7da64338fe02ae8649c3efc019
ARM64 Build ID (both): 5c50d21dd8c4610ac6ed031c5a6c765dfd28b9f0
```

The embedded library is stripped and the CI member is unstripped; matching
Build ID, rather than equal file hashes, is the binding.

## Runtime ADB boundary

No package install, process launch, or runtime test was performed. The first
PRoot wrapper was invalid because `/usr/local/bin/f8-adb-port` executes the
Termux helper with Ubuntu `/usr/bin/python3`; its candidate port `33685` was
attempted only for fresh validation, failed to connect, and was rejected.

A native ARM64 isolated server was then started on the approved listener:

```text
TADB: /data/data/com.termux/files/usr/bin/adb
server: -L tcp:5038 server nodaemon — PASS
server-status: PASS
  version=35.0.2
  mdns_backend=OPENSCREEN
  os=Linux 6.17.0-PRoot-Distro (aarch64)
devices -l before candidate: empty
```

The adb 35.0.2 mDNS commands were unavailable in this client:

```text
mdns check: unsupported (`unknown host service 'mdns:check'`)
mdns track-services --proto-text: unsupported (`unknown mdns command`)
mdns services: unsupported (`unknown host service 'mdns:services'`)
```

The user-supplied candidate `10.56.180.219:46761` was attempted exactly once
through the isolated server. It was rejected as a device-auth candidate
(`SSLV3_ALERT_CERTIFICATE_UNKNOWN`, same fingerprint on retry).

Key finding: the phone authorized the Termux-home key
(`/data/data/com.termux/files/home/.android/adbkey`), not the `/root` key.
Pairing must be done under the same HOME the connect lane uses. The isolated
server was restarted with `HOME=/data/data/com.termux/files/home`, after
which the fresh connect endpoint `10.56.180.219:39929` connected:

```text
connected to 10.56.180.219:39929
device product:myron_global model:25102PCBEG device:myron
get-state: device
ro.product.model: 25102PCBEG
ro.product.device: myron
```

ADB Gate A: PASS. Port 5037 was not touched. APK installed only after SHA
verification; Stable re-verified untouched before and after runtime
(`1.03.01-11b82d9-06.09.26`, firstInstallTime unchanged).

The isolated 5038 server that holds the authorized session was left running for
the qualification window; port 5037 was not touched. No historical endpoint was
guessed or reused; every `:3` runtime gate below ran on the verified serial.

## Runtime results

Raw evidence: `evidence/session/p2-b3a/s4-runtime-20260912/` (3 sessions,
`warmup=10 count=20 mode=1 reuse=1 batch=16 cold=0`, runner
`/tmp/p2b3a_session_s4.sh` = lane-adapted copy of `/tmp/p2b3a_session.sh`).

```text
Oracle 1514/1514: 3/3 PASS (fail=0, exact_px=1396616, maxΔ=0, Xnz=0)
Batch16 exact protocol smoke: 3/3 CELLDONE ops=20, telemetry 1999/1999,
  dropped=0, R3 fallback=0, correctness fields null (NOT_OBSERVABLE)
Lifecycle recreate x3: 3/3 fresh X PIDs (5885, 11607, 15028), 3/3 NO_X3_RESIDUE
X FD across recreates: 79 → 79 → 79 start (no monotonic growth)
New SIGSEGV/SIGILL/SIGABRT on device: 0 (crash buffer holds only historical
  entries plus two host-side adb bind-conflict aborts from our own lane setup)
Stable: UNTOUCHED (version + firstInstallTime re-verified after runtime)
External display: non-target, untouched (Experimental verified on displayId=0)
```

## Verdict

```text
S4 source hygiene: STATIC PASS
Native minimal build: PASS
x64 CI APK/provenance: PASS
Runtime qualification: PASS (oracle 3/3, batch16 smoke 3/3, lifecycle 3/3,
  NO_X3_RESIDUE 3/3, no new device fatal signal, Stable untouched)
Overall S4: PASS
Architecture semantics changed: NO
D0a implemented: NO
Stable: UNTOUCHED
```

## Next action

S4 is CLOSED. Begin Gate D0a narrow prototype per
`GATE-A-D-ARCHITECTURE-REVIEW-20260911.md`, default-off Experimental-only.
