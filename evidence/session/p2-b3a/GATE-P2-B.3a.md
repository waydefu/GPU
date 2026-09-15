# Gate P2-B.3a — Cost Census / instrumentation baseline

```
P2-B.3a: INCONCLUSIVE (exact batch16 protocol qualified; architecture verdict unchanged)
```

This gate implemented measurement only. It did not widen the R3 predicate,
change routing, or change rendering semantics. No device was connected during
this run, so no APK was installed and no `:3` runtime trace was collected.

## Provenance and safety

| Item | Value |
|---|---|
| source tree | `/root/projects/GPU加速/src/f8-ahb` |
| branch | `f8-p2-b2-over` |
| HEAD | `98224356e40913dcf2188d18748eba9401639850` |
| experimental target | `com.waydefu.x11gpu`, `DISPLAY=:3` |
| Stable | `com.termux.x11`, `DISPLAY=:1`, PID 26474 — untouched |
| ADB | no connected devices (`adb devices` header only) |
| telemetry | runtime opt-in via `TERMUX_X11_B3A_TELEMETRY != 0` |
| dump | `TERMUX_X11_B3A_OUTPUT=/path/base` → JSON and CSV at close |
| working tree | 8 modified + 2 new files, all identified (B3a telemetry + 6 approved portability repairs); `git diff --check` PASS; nothing committed yet |
| fresh build | `/tmp/b3a-fresh-arm64` (pristine configure, same NDK r29 / android-24 / arm64 / Debug) → 526/536 objects, then link stops on the same 19 undefined → **verdict C** (stale `.cxx` excluded) |
| link status | 19 unresolved (13 X11 + 6 EGL); E1/X1/C1 evidence accepted; link-architecture decision pending |

No Stable query, attach, install, kill, restart, preference change, or display
`:1` access was performed.

## What was instrumented

The X server creates one bounded shared-memory telemetry ring. A Composite
probe starts one record and carries its index through Prepare/Composite/Done;
the GPU queue entry carries that same index to the renderer. The renderer adds
dequeue, upload, draw-submit, and fence timing without per-pixel logging or
per-operation fsync. The record has a validity mask; unavailable values are
serialized as `null` (JSON) or `NA` (CSV).

The ring contains 16,384 records of 352 bytes (5,767,256 bytes including
metadata); this is a one-time shared-state footprint, not a per-pixel or
per-frame allocation.

The current byte flow is:

```
X client PutImage
  -> REGULAR pixmap (calloc)
  -> first GPU use: AHardwareBuffer_allocate
       AHardwareBuffer_lock
       full-pixmap pixman_blt
       AHardwareBuffer_unlock
  -> PrepareComposite: FD region allocate + mmap
       full logical source row memcpy (BGRA AHB -> FD snapshot)
  -> queue publish (src/dst ids, rect list, serial)
  -> renderer dequeue
       FD glTexSubImage2D upload of the stride-wide texture
       GPU draw for requested rectangles
       EGL fence wait
  -> completedSerial publish
  -> DoneComposite wait
       depth<32 X-byte CPU repair
  -> later GetImage/CPU access
```

The measurement boundaries are:

* per shared state: telemetry ring initialization; X and renderer RSS/FD
  lifecycle snapshots;
* per first promotion: AHB allocation, AHB lock, full `pixman_blt`, AHB
  unlock, and aggregate promotion time;
* per Composite Prepare: capability decision, FD region allocation, FD mmap,
  full source clone bytes/time, and aggregate Prepare time;
* per queue entry: serial, batch rectangle count, publish and dequeue time;
* per renderer entry: texture bind/upload bytes/time and draw submission
  time;
* per renderer batch: EGL fence wait;
* per DoneComposite: completion wait plus X-byte repair bytes/time;
* per transaction: monotonic wall time and fallback bit.

`gpu_exec_ns` remains `null`: GLES2/EGL in this path exposes a completion
fence, not a portable GPU execution timestamp. The fence wait is recorded
separately and is not used to infer GPU time.

## Copy accounting

For a record with `rect_area = rect_w * rect_h`:

```
requested_bytes       = rect_area * 4
clone_logical_bytes   = src_w * src_h * 4
clone_physical_bytes  = src_stride_of_fd * src_h * 4
upload_logical_bytes  = src_w * src_h * 4
upload_physical_bytes = src_stride * src_h * 4
clone_amplification   = clone_logical_bytes / requested_bytes
upload_amplification  = upload_physical_bytes / requested_bytes
```

These values are emitted per transaction. A future aggregator must group by
transaction/serial before reporting per-Prepare or per-rect amortization; a
source snapshot is not counted once for every rectangle. In the current R3
clone helper the FD is allocated with `stride == width`, so clone physical
bytes normally equal clone logical bytes; the renderer still uploads the
whole stride-wide source texture before drawing only the requested rectangles.
No device record exists in this run, therefore no cell is reported as a
measured amplification result.

## Existing evidence kept authoritative

The prior corrected R3 oracle remains the correctness authority for the narrow
slice: 1514/1514 tests, 1,396,616 exact pixels, ±1=0, maxΔ=0, Xnz=0; x100,
mixed100, x1000, and bounded XFCE passed. That evidence is not a B3a timing
baseline and is not re-run here. The prior B.1 census remains workload context:
1776 Composite operations, 1166 Over/no-mask candidates, and 981 in the
17–64px bucket. It supplies no source-area or phase-time measurements for this
gate.

## Build and schema checks

* `b3a_telemetry.c` Android arm64 target object: **PASS**.
* `InitOutput.c` target object: **PASS** (root cause fixed in-tree: `patches/dix-config.h.in`
  setgid/setuid defines moved after system includes; generated header carries the fix).
* `renderer.cpp` and `buffer.c` direct target checks: **PASS** via the real build invocation
  (prior "missing EGL/egl.h" was an ad-hoc-command artifact; NDK r29 sysroot has EGL/GLES2/KHR).
* `shmem.c` `basename`: **real pre-existing defect found by the clean build**
  (`#ifdef ANDROID` never true under NDK clang, only `__ANDROID__` is predefined);
  fixed with an approved 1-line guard change. The old `.cxx` object was a fossil of a
  reverted temporary workaround.
* Full `Xlorie` link: **blocked on 19 undefined symbols** (13 X11 + 6 EGL), reproduced
  identically in a pristine fresh build dir → stale-`.cxx` pollution excluded (**verdict C**).
* Host serialization self-check: JSON parses, CSV header and row both contain
  46 fields, unknown `gpu_exec_ns` serializes as `null`, and amplification is
  computed only when its denominator is valid. This synthetic check is not a
  device performance measurement.
* `git diff --check`: **PASS**.

## Fresh-build-dir verdict (C)

`/tmp/b3a-fresh-arm64` (new CMake configure from current source, NDK r29,
`aarch64-linux-android24`, arm64-v8a, Debug, `-j2`) compiled 526/536 edges and
stopped at the link with the **same 19 undefined symbols** as the old tree
(13 X11 live-Display-unreachable + 6 EGL entrypoint/stub). Therefore the local
incremental state is **not** the (sole) cause.

## Canonical Gradle-native verdict (B)

After preserving old-`.cxx` provenance (`/tmp/b3a-oldcxx-prov`) and cleaning only
the arm64 staging dir, `./gradlew --no-daemon --no-build-cache
':lorie:buildCMakeDebug[arm64-v8a]'` (log: `/tmp/b3a-gradle-native.log`)
compiled **536/536** and failed the link on the **same 19 undefined symbols**.
The canonical link line carries `--no-undefined` + `--whole-archive` (both from
`recipes/xserver.cmake`, committed) and **no** `-ffunction-sections` /
`-fdata-sections` / `--gc-sections` anywhere — the section-GC hypothesis for
the CI/local divergence is therefore weakened, not confirmed.
Per the decision tree, the next layer is pristine-9822435 vs current-dirty-tree
attribution (pending approval); architecture changes stay on HOLD.

## Pristine-9822435 verdict (R3 + buildability repairs reach the same link-19)

A detached pristine worktree (`/tmp/b3a-pristine-r3`, HEAD 9822435, all submodule
pins verified, zero network, plus untracked `local.properties` mirroring the main
tree) was brought forward with ONLY approved buildability repairs (setgid order,
quad_t recipe propagation, memfd/SHMLBA patch hunks, scmd hunk retirement,
basename guard — zero rendering/B3a changes). Canonical Gradle-native then
reaches the link and fails on the **exact same 19 undefined symbols**
(13 X11 + 6 EGL) as the dirty tree.

Attribution: **CLOSED — the 19 are independent of the 8改+2新.**
The dirty tree is fully washed clean on this point. What remains is a
link-architecture decision (S3): EGL entrypoint acquisition (loader route) and
xkbcomp dead-Xlib isolation. Per contract §5/S3 + §12, that review belongs to a
later architecture round (Grok 4.6 XHigh suggested), not to this recovery loop.
No EGL alias, no X11 stub, no `--no-undefined` weakening was applied anywhere.

## Required performance result

No CPU baseline, R3 baseline, phase samples, median, p95, p99, correctness
re-run, crash check, or FD delta was available because ADB had no device. The
following are intentionally unclassified rather than inferred:

```
Top R3 cost:                    not_observable
Worst/median/B.1 amplification: not_observable
CPU clearly wins:               none measured
R3 clearly wins:                none measured
All size/reuse/batch/readback cells: indeterminate
```

## Exact next measurement

On a newly established ADB connection, use only the experimental package and
`:3` display. Build/install the current tree after resolving the unrelated
NDK/build-tree header issue, then run paired processes with identical oracle
inputs:

```
TERMUX_X11_B3A_TELEMETRY=1 TERMUX_X11_B3A_CANDIDATE=cpu \
  TERMUX_X11_B3A_OUTPUT=/data/local/tmp/p2b3a-cpu \
  DISPLAY=:3 <same narrow Over oracle with EXA GPU disabled>

TERMUX_X11_B3A_TELEMETRY=1 TERMUX_X11_B3A_CANDIDATE=r3 \
  TERMUX_X11_B3A_OUTPUT=/data/local/tmp/p2b3a-r3 \
  DISPLAY=:3 <the same oracle with the current R3 path enabled>
```

Collect the Tier-1 smoke cells first, then the representative Tier-2 cells:
1×1, 5×24, 16×16, 32×32, 64×64, 128×128, 256×256, 512×512, 1024×1024,
fullscreen; cold/warm; source/rect 1×/4×/16×; reuse 1/4/16/64; batch 1/4/8/16;
GPU-only, immediate GetImage, delayed CPU access; and padded stride/clip/offset
cases. Use warmup ≥100, measured ≥500, and a 1000-iteration stress run. Only
after those files exist should a cost ranking or a Gate A/D decision be made.

## Gate decision

`INCONCLUSIVE` is required: the instrumentation and schema are present and
compile-checked through 526/536 edges of a pristine build, but (a) the completion
criteria requiring paired CPU/R3 runtime data and percentile statistics are not
met, and (b) the qualification link is still blocked on 19 undefined symbols
(link-architecture decision pending). No performance or
zero-copy conclusion is authorized by this artifact.

## 2026-09-10 S3 closure unblocks B3a measurement

S3 closed this round (`evidence/session/s3/GATE-S3-RUNTIME.md`):
S3 LINK / S3-Q1 / S3-E1b / S3-X1 CLOSED, S3 runtime behavioral
PASS WITH OBSERVABILITY LIMITATION, build recovery CLOSED. The E1b
`9b6420d` candidate launched cleanly on displayId=0 with zero SIGSEGV/SIGILL,
so the link-architecture blocker recorded above no longer gates this work.

B3a measurement is therefore **UNBLOCKED**: the next step is the paired
CPU/R3 cost census in "Exact next measurement" above. This gate's measurement
verdict stays **INCONCLUSIVE** until those paired runtime files exist — the
unblock changes readiness, not results.

S3 observability follow-up (per-entry EGL/fence/GL-OES proc telemetry) is
**OPTIONAL / DEFERRED**. Revisit only for an upstream PR, new devices, a
cross-device capability matrix, or a fallback investigation; it is not a
precondition for B3a measurement.

## 2026-09-10 B3a measurement ATTEMPTED — BLOCKED on telemetry dump-lifecycle defect

The UNBLOCKED status above covered readiness (S3 link closed). The authorized
full-matrix run started and hit an instrumentation-credibility stop condition;
no cost data was collected and no cost conclusion is authorized. Full log:
`evidence/session/p2-b3a/B3A-RUN-20260910.md`.

Observed contract break (2/2 probe sessions, deterministic):

- `lorieB3aDump` (one-shot `dumped` flag, fires at `CloseScreen`/`ddxGiveUp`)
  wrote its files at STARTUP with `next_record=0, dropped=0`, before any
  workload ran. Probe2 proved this mid-session, before teardown.
- Screen init runs multiple times per session (2x–14x `InstallProbe` lines);
  each cycle can fire an early empty dump that consumes the flag.
- SIGTERM teardown produced no second dump. Result: every session yields
  zero records; no procedural workaround exists.

What was verified along the way (kept, reusable after the fix):

- Termux-native ADB lane + fresh F8 identity; installed E1b APK carries all
  four B3A control strings (env-only operation, no rebuild needed).
- OUTPUT must target Termux tmp (host `/tmp`); `/data/local/tmp` is
  `shell:shell 771` and unwritable by the app UID.
- Parametric driver `/tmp/p_b3a_cost.c` builds clean and is
  correctness-coupled; its PictFormat first-match bug was found and fixed
  (depth-24 has DIRECT ids 41 AND 42; oracle takes 41).

Gate status is therefore **BLOCKED — telemetry dump-lifecycle fix required**
(a source change; needs an explicit review/buildability round, then S3-Q1
packaging + launch/correctness re-qualification before B3a restarts).
Measurement verdict remains **INCONCLUSIVE** (zero runtime cells by design,
not by choice). The proposed minimal fix (skip empty dumps without latching
`dumped`) is recorded in the run file and NOT implemented here.

## 2026-09-10 telemetry repair round — CLOSED, B3a UNBLOCKED

Approved narrow fix (commit `1954f82`, on top of E1b `9b6420d`; diff vs E1b is
the guard hunk only, 9+/1-; `git diff --check` PASS; no renderer/Composite/
routing/signal/lifecycle refactor):

```c
if (telemetry->next_record == 0)
    return;   /* before latching `dumped` */
```

Narrow re-qualification (all PASS):

1. ARM64 canonical native build: BUILD SUCCESSFUL rc=0
   (`/tmp/b3a-fix-arm64-native.log`).
2. S3-Q1 CI run `34407348596` (head `1954f82`): success; artifact
   `10125997237`; APK `5cc87f41…c1dce` rechecked locally; package
   `com.waydefu.x11gpu` v15 `1.03.01-1954f82`; embedded lib
   `da79b03d…06903fd`; ZIP PASS; forbidden symbols NONE; full libX11
   DT_NEEDED absent; v2 signature verifies; signer `b6da0148…` matches;
   zipalign PASS.
3. Installed experimental `1.03.01-1954f82`; Stable `:1` untouched.
4. Two `:3` sessions on displayId=0, X alive throughout, zero SIGSEGV/SIGILL,
   clean teardowns, zero residue.
5. R3 oracle on the new build: 1514/1514 fail=0 ±1=0 Xnz=0 maxΔ=0.
6. Core acceptance MET: no premature consumed empty dump in either session
   (startup checks clean); final JSONs `next_record=1519` and `=120`,
   parseable, schema v1, candidate labels correct.
7. Relaunch produced exact-count data (120/120, dropped=0).

New observation (methodology, NOT a stop): a mid-session screen
CloseScreen/re-init can dump EARLY with partial data and consume the flag,
truncating that session's tail (session 1: 1519 oracle records dumped
mid-session, 600 later cost records lost). Mitigation: batch each session's
full workload + teardown into ONE command (no round-trip gaps) and validate
`next_record == expected` per session; discard + rerun on truncation.

```text
Telemetry repair: CLOSED
B3a: UNBLOCKED → Tier-1 smoke, then full paired matrix
```

## 2026-09-10 Tier-1 五格輪 — 測量 PASS（用戶指定範圍）

第一輪只跑 1x1、5x24、32x32、64x64、256x256（warmup 100＋measured 500，
warm reuse＋immediate GetImage）。CPU 與 R3 各一 session，holder＋oracle
閘門＋批量＋釋放 dump，`next_record == 4519 == expected` 兩邊 exact-count
驗證通過，teardown 乾淨，Stable 未碰。

Wall medians（毫秒）：1x1 2.908/3.123（1.07x）；5x24 2.888/2.712（0.94x）；
32 2.985/2.739（0.92x）；64 2.930/2.741（0.94x）；256 2.897/4.368（1.51x）。
R3 phase medians：prepare ~0.45～0.68、clone ~0.24～0.45、done ~0.57～0.89；
promotion/upload/queue/draw/fence＝null（warm 攤銷＋renderer 未歸因，符合設計）。
R3 fallback=0、exact_fail=0；CPU fallback 全 1。
X RSS：CPU ＋14MB、R3 ＋6MB；FD 兩邊 79→89。

詳見 `evidence/session/p2-b3a/B3A-T1-5CELL-20260910.md` 與 `t1-5cell/` 原始檔。
成本結論只到 medians；Tier-2 另輪再跑。

## 2026-09-10 Tier-2 U1 reuse 系列 — 攤銷假說被否定

64 reuse{1,4,16,64}＋256 reuse{1,64}，CPU/R3 各一 session，exact-count
5119/5119，teardown 乾淨。64 在 reuse 1→64 完全平坦（2.818→2.876），
256 亦然（4.517→4.704）；measured 窗口 promotion 全 null，per-op 成本是
prepare+clone+done 固定復發。精確表述：被否定的只是「目前 R3 路徑的 warm
reuse 有可觀察攤銷」（H2-current-R3 REJECTED）；persistent residency 本身
是否有效不在本輪證據範圍內，Gate D NOT REJECTED。
256 回歸持續（1.98～2.03x）。另記錄方法學警訊：CPU-64 跨 session 漂移
約 25%（Tier-1 2.930 vs 本輪 2.175），後續以同輪配對為準。
詳見 `B3A-T2-U1-REUSE-20260910.md` 與 `t2-u1-reuse/`。

## 2026-09-10 Tier-2 U2 reuse 系列 — Tier-1 小贏未能複現

1x1、5x24、32x32 × reuse{1,4,16,64}，CPU/R3 各一 session，exact-count
8719/8719，teardown 乾淨（新通道 192.168.1.101:39515，身份複驗同一台 F8）。
12 格 R3 全輸 1.15～1.24x；同參數 32r1 由 Tier-1 的 0.92x 翻成 1.18x。
CPU-32 跨 session 漂移（2.985→2.342），R3-32 穩定（2.739→2.763）。
結論：5～30% 量級的勝負不可靠；可靠的是 reuse 全平坦、256 大幅回歸、
每 composite 固定成本主導。H2-current-R3（目前 R3 路徑 warm reuse 有可觀察攤銷）
REJECTED；Gate D NOT REJECTED——現行 reference path 沒把 reuse 轉成成本下降，
反而更支持「若要吃到 reuse，必須換真正 persistent residency / dirty-region
architecture」。H1/H3 待 GPU-only＋cold。
詳見 `B3A-T2-U2-REUSE-20260910.md` 與 `t2-u2-reuse/`。

## 2026-09-10 U2 正式裁決＋U3 授權（短窗配對）

```text
B3a U2 reuse: PASS
Correctness: PASS
Measurement integrity: PASS
Tier-1 "32–64 px sweet spot": RETRACTED
Reliable findings:
  1. current R3 reuse amortization: NOT OBSERVED
  2. 256x256 regression: REPRODUCED (Tier-1 1.51x, U1 1.98～2.03x)
  3. per-composite fixed/lifecycle cost: DOMINANT SIGNAL
H2-current-R3: REJECTED
Gate D: NOT REJECTED
H1 / H3: OPEN — U3 required
Gate A/D/H decision: NOT AUTHORIZED YET
```

假設定義（凍結）：

```text
H1: R3 在 256x256 的退化主要來自 staging / clone / sync，而非 shader 本體。
H2-current-R3: 目前 R3 路徑的 warm reuse 產生可觀察攤銷。（REJECTED）
Gate D（persistent residency 架構價值）: NOT REJECTED，不在本輪證據範圍。
H3: GPU-only 快但 end-to-end R3 慢 → 瓶頸在 CPU↔GPU lifecycle / repair /
    synchronization。
```

U3 正式量測規則（APPROVED）：

```text
A. warm reuse: 已由 U1/U2 覆蓋，不重跑。
B. batch = 1 / 4（64x64 優先；8/16 視 U3 結果定 U4）。
C. GPU-only 64：wall latency＋queue latency；GPU exec 僅在裝置/driver 暴露
   可靠 timer/query 或 Perfetto render-stage/counter 時填數值，否則
   null / not_observable。Khronos timer-query 屬非同步 GPU completion 量測，
   不得當同步 wall time 用。
D. cold 64：allocate/create、promote、import、first-use 分開歸因；
   AHB lock/unlock 同步成本（lock 可能因 GPU 完成/cache sync 阻塞）不得與
   fence wait 混成一個「GPU 慢」。
E. lifecycle：recreate / release / teardown RSS endpoint / FD endpoint（U4）。
尺寸維持 {1x1, 5x24, 32x32, 64x64, 256x256} 可比對 Tier-1；U3 關鍵三格為
batch 1→4、GPU-only 64、cold 64。
```

短窗配對（paired A/B，B3a 正式規則）：每個 cell 跑 CPU-A → R3-A → R3-B →
CPU-B（或 R3-A → CPU-A → CPU-B → R3-B，兩種順序交替），同窗 paired ratio
為主比較；跨 session 絕對 median 不判 5～30% 量級勝負。thermal/frequency
能廉價讀到就記，讀不到記 not_observed，不為此改 benchmark semantics。

STOP 追加：若 Tier-2 為了量某 phase 必須改變 fence ordering / AHB
ownership / rendering semantics，STOP，不為 instrumentation 改行為。

## 2026-09-10 U3 64x64 短窗配對 batch — batch=1 有效；batch=4 STOP

batch=1 依 CPU-A → R3-A → R3-B → CPU-B 執行；四輪 oracle PASS，
telemetry 各 2119/2119，CPU fallback=1、R3 fallback=0（600/600）。
paired ratio 方向互斥：CPU-A→R3-A 為 1.384x，R3-B→CPU-B 為 0.870x；
aggregate 1.229x 僅描述，不裁勝負，正式標記 `noise-sensitive / INCONCLUSIVE`。
R3 phase median：prepare 0.508ms、clone 0.286ms（16384 bytes）、done 0.706ms、
repair 0.003ms；queue/draw/GPU-exec/fence 均 null/not_observable。內部
surfaceAvailable flag 無直接 telemetry，記 `not_directly_observed`，不以 X liveness
或正確性替代此內部觀測。

batch=4 R3-A oracle PASS，但首個 measured op 出現
`MISMATCH got=00f00f00 expected=00807f00`；telemetry 1923/1923 且 fallback=0。
根因確認在 driver correctness coupling，而非 R3：`p_b3a_cost.c:166-168` 只計一次
Over expected，`:212-221` 實際發出 batch 次 Composite，而 `:231-242` 仍比較單次
expected。四次 CPU reference 恰為 `00f00f00`。batch>1 的 coupling 因此無效，
本輪 STOP；未改 source，GPU-only/cold NOT STARTED。需要另行核准窄 driver-only
修復及 CPU/R3 batch=4 首格重新資格驗證後才可繼續。

最終 teardown `NO_X3_RESIDUE`；Stable 未碰。詳見
`B3A-T2-U3-PAIRED-BATCH-20260910.md`、`t2-u3-paired-batch1/` 與
`t2-u3-paired-batch4-fail/`。

## 2026-09-10 U3 completion — narrow batch repair qualified; GPU-only/cold complete

窄修復只在 `patches/p_b3a_cost.c` 將既有 Over reference 重複 `batch` 次；
`-Wall -Werror` rebuild PASS。CPU/R3 各一個 oracle+batch1+batch4 session：
4519/4519、batch1 expected=00807f00 維持、batch4 expected=00f00f00、所有 cell
exact PASS；R3 fallback=0。故 batch4 是 `MEASUREMENT DRIVER BUG — CLOSED`，
非 R3 regression。

GPU-only 64（mode=0/no immediate GetImage）四個短窗均 PASS、2119/2119，兩個
配對皆 R3 慢（1.142x、1.205x）。但每 op 仍有 X liveness round-trip，且 GPU-exec /
queue 均 null/not_observable；這排除 immediate GetImage 是全差距，仍不足以裁 H3。

cold 64 四個短窗均 PASS、2119/2119，兩個配對 R3/CPU=3.739x、4.203x；R3
fallback=0。cold phase median：prepare 5.138ms、promotion 3.354ms（AHB allocate
2.141ms）、clone 0.407ms、DoneComposite 6.552ms。這是最強 lifecycle cost signal，
支持 H1 候選但不裁 Gate A/D/H。所有 U3 sessions final `NO_X3_RESIDUE`；Stable
未碰。U4 remaining：batch8/16（ring-safe split）＋recreate/release/teardown RSS/FD
endpoint。詳見 `B3A-T2-U3-PAIRED-BATCH-20260910.md` 與原始 evidence dirs。

## 2026-09-10 U4 batch8/16 — batch8 PASS；batch16 遇新鮮 R3 啟動崩潰

U4 batch8：CPU-A/R3-A/CPU-B/R3-B 四輪皆 oracle PASS、cell exact PASS、
telemetry `6319/6319`（1519 + 600×8），R3 fallback=0（4800/4800）。
paired wall ratio R3/CPU=`1.276x`、`1.151x`，aggregate=`1.216x`；只作描述，
不裁架構。resource endpoint 已指向實際 X PID；T0/T1/T2/T3 完整，所有輪
teardown 後 `NO_X3_RESIDUE`。首次 exploratory batch8 的 launcher-PID endpoint
已降級，不納入 aggregate。

U4 batch16：R3-A、CPU-A、CPU-B 各 `11119/11119`，expected=`00ff0000`、cell
exact PASS、oracle PASS，且 endpoint/teardown 完整。第四輪 R3-B 在 workload
開始前，launcher log 出現新鮮原生訊息：

```text
Uctx signo=11 si_code=1 si_addr=0x0000000000000000
PC=0x000000004800226c LR=0x0000007cad92b8e0
Ssig signo=11 code=1 addr=0x0000000000000000
```

沒有 R3-B oracle/cell/JSON；記為 `NOT TESTED`，不是 batch16 PASS。ADB crash
buffer 沒有可把此訊息綁定到同時段的條目，root cause=`UNKNOWN`。依 STOP
規則不重試、不繼續 U4。Fresh evidence：
`B3A-T2-U4-BATCH-20260910.md`、`t2-u4-batch8/`、`t2-u4-batch16/`。

```text
U4 batch8: PASS
U4 batch16: INCONCLUSIVE / BLOCKED (R3-B fresh startup SIGSEGV; 3/4 only)
Gate A/D/H: NOT AUTHORIZED
```

## 2026-09-10 U4-C1 crash forensic — ADB fresh preflight blocked

依批准範圍開始 C1 前，先執行 fresh native-Termux `f8-adb-port`；該 helper
在目前 PRoot context 於 Python `ctypes.CDLL` 階段失敗，exit=1，未產生
endpoint，也未執行任何 device query、launch、`debuggerd` 或 workload。
阻擋行為是 `OSError: dlopen failed: library "libc.so.6" not found`。

因此 C1 launch-only attempt `0/3`：不是 crash PASS/FAIL，也不是
NON-REPRODUCED；狀態為 `ADB_FRESH_PREFLIGHT_BLOCKED`。不得拿記憶中的
`192.168.1.101:45279` 代替 fresh endpoint。無 source mutation、Stable
未碰。完整紀錄：`B3A-U4-C1-PREFLIGHT-20260910.md`。

## 2026-09-10 U4-C1 and U4-L1 — preflight resolved; lifecycle PASS

上節的 `ADB_FRESH_PREFLIGHT_BLOCKED` 已被較晚 fresh Wireless ADB channel
`10.56.180.219:39035` 解除（`device`、`25102PCBEG / myron`）。C1 在同一 frozen
APK 的 controlled launch-only three attempts 是 `0/3` crash reproduction；APK/lib
provenance 與 limitations 見 `B3A-U4-C1-CRASH-FORENSIC-20260910.md`。這不把原始
batch16 R3-B SIGSEGV 說成 fixed 或 false positive；其分類仍是 observed but
non-reproduced。

U4-L1 隨後執行 3 個獨立 R3 create/use/release/teardown/recreate sessions：X PID
`30844`、`2882`、`11183`；每輪 oracle 1514/1514 exact PASS、cold one-op driver
first-pixel exact PASS、telemetry `1520/1520`、dropped=0、R3 fallback=0，並在 exact
teardown 後 `NO_X3_RESIDUE`。server telemetry lifecycle metadata 每輪為
`x_fd_start=79`、`x_fd_end=89`，下一個 X server 都重新由 79 開始；未觀察到
cross-recreate FD retention。adb shell 的 live `/proc/<PID>/fd` count 被拒絕，故記
`NOT OBSERVABLE` 而非 false 0；explicit buffer release counter、renderer queue 與
GPU exec 亦 `NOT OBSERVABLE`。`Gcomp FDCLONE=Gcomp Done=1516` 是 clone/complete
操作性平衡證據，不取代 release counter。

```text
U4-L1 lifecycle: PASS WITH OBSERVABILITY LIMITATIONS
U4 batch8: PASS
U4 batch16: still INCONCLUSIVE / BLOCKED pending C2 exact-sequence gate
Next authorized unit: cold-N5
Gate A/D/H: NOT AUTHORIZED
```

完整 raw 及 aggregation：`B3A-T2-U4-L1-LIFECYCLE-20260910.md`、
`t2-u4-l1-lifecycle/`。Stable 未碰。

## 2026-09-10 U4 cold-N5 — repeated lifecycle cost reproduced

五個 short-window pairs（10 sessions）採 64×64 cold、batch=1、reuse=1、immediate
GetImage、warmup=100、measured=500。每個 session 都 oracle exact PASS、cell first-pixel
exact PASS、telemetry `2119/2119`/dropped=0、CPU fallback=1 或 R3 fallback=0、
`NO_X3_RESIDUE`。measured-only aggregate（2500 samples/side）為 CPU median/p95
`3.670/6.360ms`、R3 `11.703/19.701ms`，R3/CPU median=`3.188x`、p95=`3.098x`。
五個 paired ratios 全同方向：`2.756x`、`2.783x`、`2.387x`、`4.522x`、`4.248x`。

R3 cold phase median/p95：prepare `5.071/8.897ms`、promotion `3.281/5.774ms`
（AHB allocate `2.062/3.539ms`）、clone `0.384/0.682ms`、DoneComposite
`1.285/8.160ms`。upload/queue/GPU-exec/fence 均 null/`NOT OBSERVABLE`。這是
N=5 的 end-to-end cold performance-negative 重現，明確分類為 `CPU clearly wins`
for current R3 cold path；不推論 shader 本體較慢，也不裁 Gate A/D/H。

```text
U4 cold-N5: PASS WITH OBSERVABILITY LIMITATIONS
H1 lifecycle/promotion/staging cost candidate: strengthened
U4 batch16: still INCONCLUSIVE / BLOCKED pending C2 exact-sequence gate
Next authorized unit: C2 provenance prerequisite, then C2 if matching DWARF exists
Gate A/D/H: NOT AUTHORIZED
```

完整 raw：`B3A-T2-U4-COLD-N5-20260910.md`、`t2-u4-cold-n5/`。Stable 未碰。

## 2026-09-10 U4-C2 provenance — BLOCKED before any batch16 replay

C2 的 hard prerequisite 是 installed APK embedded `libXlorie.so` 與 unstripped
symbol file 的 Build ID 相符。installed APK is `5cc87f41…c1dce`; embedded ARM64 lib
is `da79b03d…06903fd`, Build ID `b15d75a5a3d4217eb736208f18d5a1aa84280bf9`。
S3-Q1 artifact carries the exact same but stripped ELF, so it cannot provide DWARF;
historical control unstripped Build ID differs and is excluded.

An unchanged existing `debug_build.yml` was dispatched on exact remote branch
`qualification/s3-runtime-20260909` (readback SHA `1954f82…`), and run `34498279213`
succeeded. It produced exact-source unstripped artifact `10160961032`, expiry
2026-12-09. Its download was explicitly rejected by the execution layer for lack of
consent. No alternative download was attempted. Local provenance build is also
excluded: nominal CMake 3.22.1 resolves to host CMake 3.28.3.

```text
C2 provenance: BLOCKED_AT_ARTIFACT_RETRIEVAL_AUTHORIZATION
matching unstripped Build ID: NOT VERIFIED
C2 exact sequence / logcat / batch16: NOT STARTED
B3a batch16: remains INCONCLUSIVE / BLOCKED
Gate A/D/H: NOT AUTHORIZED
```

Details: `B3A-U4-C2-PROVENANCE-20260910.md`。Stable 未碰。

## 2026-09-11 U4-C2 provenance and exact batch16 sequence — PASS with observability limitations

Artifact `10160961032` was downloaded from `waydefu/termux-x11`, run
`34498279213`, exact head `1954f82cda9b548ab88f420e428f7296a2d3c72c`.
The downloaded ZIP was `28124818` bytes with SHA256
`7edf7776eba65bbf9cbdf1ffabbd2e9c5e79ebf65e6a41c35f9ef9df8e721da5`, exactly
matching the GitHub artifact digest; ZIP test passed, 40 members, no duplicates.

The ARM64 unstripped member `01x55434/obj/arm64-v8a/libXlorie.so` was extracted
and retained. It is AArch64, not stripped, contains DWARF `.debug_*`, has SHA256
`2d555d13b97b1554cc37574f2e0541d0afd1a98b361c7b572c7d9c9739fb9ba6`, and Build
ID `b15d75a5a3d4217eb736208f18d5a1aa84280bf9`. Freshly pulled installed APK
`com.waydefu.x11gpu` is versionCode 15 / `1.03.01-1954f82-09.09.26`, APK SHA256
`5cc87f4121bfe52e7504348e36c36421b28355549b3b26fe031f175a234c1dce`; its
embedded ARM64 library SHA256 is
`da79b03df087435813ff494b62eebc792d4df074a8b520c3006f7288b06903fd` and its
Build ID is the same `b15d75a5a3d4217eb736208f18d5a1aa84280bf9`. Provenance
prerequisite is therefore PASS.

After fresh ADB `device` identity `25102PCBEG / myron`, the exact sequence
`CPU-A → R3-A → CPU-B → R3-B` was completed three times. Protocol was 64×64,
`warmup=100`, `count=500`, `mode=1`, `reuse=1`, `batch=16`, `cold=0`,
expected=`00ff0000`; expected telemetry was `11119` per session.

```text
sessions:        12/12 PASS
telemetry:       133428/133428 records, dropped=0
oracle:          12/12 PASS, 1514/1514, fail=0, maxΔ=0
cell:            12/12 exact PASS, CELLDONE ops=500
CPU fallback:    57,600/57,600 = 1
R3 fallback:     0/57,600 = 0
new signals:     0
teardown:        12/12 NO_X3_RESIDUE
R3-B replays:    3/3 no new SIGSEGV
```

Statistics used only the final 8,000 measured records per session, excluding
1,600 warmup records. Six paired ratios were all greater than one:
`1.359416x`, `1.366946x`, `1.302276x`, `1.235852x`, `1.398776x`, `1.257737x`.
Across 48,000 measured records per candidate, CPU median/p95 was
`2.625000/4.937399ms`; R3 was `3.410521/6.605912ms`; aggregate R3/CPU median
was `1.299246x`. This qualifies the current batch16 end-to-end path as
performance-negative for this protocol; it does not measure shader execution.
GPU execution and queue fields remain null/not observable, and the transaction
includes an X liveness round-trip.

R3 measured phase medians were prepare `0.478698ms`, clone `0.227760ms`, and
DoneComposite `0.887968ms`. One-time promotion and AHardwareBuffer allocation
medians were `2.754349ms` and `1.598360ms`; they are not steady-state measured
rows. Server telemetry endpoints were observed; external renderer RSS/FD,
queue, and GPU execution remained not observable. Stable was untouched.

Evidence:
`B3A-T2-U4-C2-20260911.md`, `B3A-U4-C2-ARTIFACT-PROVENANCE-20260911.md`,
`B3A-U4-C2-EXECUTION-20260911.md`,
`t2-u4-c2-provenance/`, `t2-u4-c2-exact-sequence/`。

```text
C2 artifact provenance: PASS
C2 exact sequence: PASS (3/3 complete sequences)
U4 batch16: QUALIFIED FOR THIS EXACT PROTOCOL / OBSERVABILITY LIMITED
historical startup SIGSEGV: observed / non-reproduced; root cause unknown
Gate A/D/H: NOT AUTHORIZED
Stable: UNTOUCHED
```

## 2026-09-11 Gate A / Gate D architecture decision

The user opened Gate A/D architecture design and narrow-prototype planning;
Gate H remains HOLD. Working-tree symbol tracing and the current AHB/EGL/GL
contract produced this decision:

```text
Gate A direct AHardwareBuffer/EGLImage: BLOCKED for the current BGRA source contract
Gate D persistent dirty-region staging: PASS-CANDIDATE
preferred first prototype: D0, default-off Experimental-only, three functions
Gate H: HOLD
```

Gate A is not rejected as impossible in general. It is blocked because this F8
stack already sampled BGRA EGLImages as black, while direct sampling would also
require a new CPU→GPU ownership/fence handoff before X releases its CPU mapping.
Gate D can retain the qualified queue barrier, per-entry references, blocking EGL
completion fence, completed serial, Done wait, narrow predicate, and fallback.

D0 is limited to `lorieCloneBgraAhbToFd`, `lorieExaComposite`, and
`Renderer::applyPendingGpuCopiesLocked`: one cached FD/GL texture, exact dirty
row copy/upload, and wait-before-staging reuse. No queue ABI, predicate, blend,
X-byte repair, ownership counter, or fence change is authorized by this review.

Full design, risk table, existing-matrix runtime gate, and rollback:
`GATE-A-D-ARCHITECTURE-REVIEW-20260911.md`.

## 2026-09-11 S4 PRE-D0a HYGIENE

```text
S4-1 mmap: PASS — OsVendorInit uses MAP_FAILED and fail-closes
S4-2 recv: PASS — short read/FD/AHB/map failures clear caller output and fail-closed
S4-3 fence: PASS — Composite/Solid capability gates and valid sync-handle guards
S4-4 AHB lock: PASS — failed lock leaves no locked state/pointer; mutex unlock is symmetric
native Xlorie target: PASS
local APK packaging: BLOCKED — ARM64 host has only x86-64 AIDL
x64 CI APK/provenance: PASS — run 34606849337, head fd988c4
S4 runtime: PASS 2026-09-12 — oracle 3/3, batch16 smoke 3/3, lifecycle 3/3,
  NO_X3_RESIDUE 3/3, no new device fatal signal, Stable untouched
D0a: AUTHORIZED (default-off Experimental-only)
Stable: UNTOUCHED
```

The S4 source delta, CI recovery chain, artifact hashes, and ADB boundary are
recorded in `S4-PRE-D0A-HYGIENE-20260911.md`. The exact qualification source is
branch `qualification/s4-pre-d0a-20260911`, head
`fd988c45e51692c6cae4420f84466872bedf9bf6`. The CI APK is
`com.waydefu.x11gpu`, versionCode 15, with ARM64 Build ID
`5c50d21dd8c4610ac6ed031c5a6c765dfd28b9f0`; no older APK was substituted.

Runtime remains blocked because `/usr/local/bin/f8-adb-port` is a PRoot
wrapper and the direct native helper fails with
`dlopen failed: library "libc.so.6" not found`. No endpoint was guessed or
reused, and no package was installed or launched.
