# Gate A P2 — R10 COMPLETE · **GAP-4 / CF-PENDING 全關** — 2026-09-21, updated 2026-09-23

```
STATUS: **GAP-4 CLOSED · CF-PENDING-001 CLOSED · CF-PENDING-002 CLOSED**
        R7 13/13 → dc94485 CARRY_FORWARD（13/13 predicate intact，4 個已實機重現）
        R8 10/10 → dc94485 CARRY_FORWARD（claim scope 原樣帶走：無 -noreset）
        R0–R6 → dc94485 CARRY_FORWARD + 1 項 REVERIFY（已由 R9-F1 / R10-E2 滿足）
        **p2_runtime_closed 仍為 false**——17 項 ledger 尚未完成
        **R10 COMPLETE — A / B / C / E 四個 series 全 PASS**（V2-R10-AGG）
        無 leak · 15 次 clean close counter 零失衡 · Stable 全程未動
        唯一帶走的發現：activity.maps_count 跨 session 上飄，轉 D-04
        **D-06 DECIDED** — V1 不做 generation 2，採 fresh-process recovery
        **V2-R10-DESIGN / PROBE-INVENTORY 完成**（commit 16cdb22），R10 尚未跑任何 round
        R10 cell set 重建為 **A / B / C 三模式**，取代 WARM-R1..R5 / COLD-R1..R5
        R9 DEVICE PACKET **COMPLETE — 2/2 PASS**（V2-R9-AGG）
        R9-F1 PASS  r9-f1/attempt-03   expected fatal x-wrong-generation reason=6
        R9-F2 PASS  r9-f2/attempt-02   new nonce · empty registry · event=5 · no fatal
        R9 DEVICE CELL SET = **2 格**（F1 / F2）。COLD-2 於 2026-09-22 被移除。
        6 格 source-proven RUNTIME-NOT-CONSTRUCTIBLE：WARM-1/2/3 · COLD-1/3 · COLD-2
        FIXTURE 改為 tests/r9/p_r9_boundary.c（不用 R8 test extension）
        RUNNER V2 · commit 3a12e73 · host gates: 32 judge 向量 · 36 evidence 測試
        R8 10/10 PASS · V2-R8-AGG PASS (12/12 re-verified, 554 evidence files hashed)
        R7 13/13 PASS (frozen, never rerun)
        D-01 ACCEPTED · D-02 IMPLEMENTED+SMOKED · D-12 ACCEPTED
        INSTALLED ARTIFACT dc94485 / CI 35673085569
        b984ded remains the authority for all R7 / pre-09-22 R8 evidence;
        b984ded and dc94485 evidence are NOT poolable
        Production Gate A BLOCKED
        V1-Core NOT QUALIFIED
        TOOLING 9d26816（P2 tools）· 7cab5ab（p2_scan）· 4de9e33（R10）· 3a12e73（R9）
        ADB SERIAL 換了：手機換網段，現在是 192.168.1.104:36405（lane 5038）
        永遠用 mdns 重新探測，不要沿用舊值
```

## 2026-09-22 — R9 的三件事（先讀這段）

**1. COLD-2 沒了，而且不是 FAIL。**
`x-bump-unterminal` 需要同一個 X process 裡的**第二次** `lorieActivityConnected()`
且 `generation != 0`，而那是到不了的。X 只有在 `lorieGateAActive()` 已經是 false
時才能比它的 Activity 活得久（`InitOutput.c:620-624`）；clean close 連
`sessionNonce` 一起歸零（`:3334-3335`），所以那條路是終點（`:567`）；而每一個能把
gate 關掉的 fatal publisher 都在同一口氣裡讓 X process 結束 —— X 這邊是
`lorieGateAFatalHalt` 的 `_exit(127)`（`lorie.h:1414-1416`），renderer 那邊是因為
14 個 publish 點全都在 X 卡在 `gateAWaitTerminal` 等同一個 serial 時才觸發。
完整逐行證明：`planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md`。

**產品層結論（D-06，只記錄不決策）：Gate A 根本沒有可到達的 generation boundary。**
每個 X process 只會 bump 一次（第一次 Activity 連上，generation 0 -> 1），之後到不了。
旁證（非證明）：`evidence/` 下所有 Gate A 紀錄、201989 行 `GATEA_EVENT`，
`generation` 從來沒有超過 1。

**2. R9 不能用 p_r8_lifecycle。**
R9 要 arm 自己的 fault，而 `parseArm()` 只允許 `R8-P1`/`destroy-while-gpu-owned` 和
`R8-P2`/`close-while-lease` 兩對，其他 case 配任何 fault 都會 `x-r8-env` 開機即停。
把 R8 解除 arm 又會讓 `LorieR8TestExtensionInit` 提早 return，extension 根本沒註冊。
兩種都各燒掉一次 attempt 實測過。現在用 `tests/r9/p_r9_boundary.c`：純 XCB，
一次 `PictOpOver` composite 就是整個 Gate A direct 路徑的觸發器，不碰 extension。

**3. 五次 INVALID 沒有一次是產品缺陷。**
四次是工具讀錯來源（fd table / validate stage / registry counter），一次是我自己加的
clean-close 步驟把證據弄髒。每一條都有 offline 測試釘住，每一個 attempt 都凍結不重判。
細節見各 attempt 目錄下的 `ATTEMPT-FROZEN-INVALID.md` 與 `V2-R9-AGG.md` 的 attempt ledger。

Do **not** rerun R7 or any frozen attempt.
Do **not** rebuild/reinstall the product or dispatch CI without product-defect evidence (§2.2).
Do **not** touch Stable `com.termux.x11` `:1`. Experimental is `com.waydefu.x11gpu` `:3` only.
Do **not** rerun R9-F1 or R9-F2 — both are PASS and frozen (§6.5).
Do **not** run any of the six removed cells: judge-r9.py returns R9_BLOCKED and
that is correct. Reopen them only if the product gains a warm reconnect/rebind
entry point, or a renderer fatal publisher reachable OUTSIDE an X terminal wait.
Do **not** assume a long-lived experimental X keeps Gate A alive — ONE DE_RESET
(the last X client disconnecting) permanently and SILENTLY kills it. See §6 Q10.
Do **not** trust any R8 result predating runner **v10** — see "the one thing" below.

---

## 1. The one thing that will bite you

Gate A accelerates **only `PictOpOver`**:
```c
// InitOutput.c lorieCanAccelCompositePictures()
if (op != PictOpOver) return FALSE;      // returns BEFORE any trace is emitted
```
The R8 fixture used `PictOpSrc` until runner v10, so every composite silently took the
CPU fallback and the Gate A direct EXA pair-lease path was **never entered**.
`DIRECT_ADMIT_REJECT` was also 0 — which reads as "not refused" but actually means
"not attempted". This is invisible in logs.

**Verification rule:** a composite that *should* have been accelerated only took the
GPU path if `gatea-ring.txt` contains `event=5` (`LORIE_GATEA_EVENT_LEASE_GPU_OWNED`).

**Scope — do not apply this unconditionally.** Across the ten passing cells the
`event=5` count matches each cell's `pair_composite()` count in `p_r8_lifecycle.c`
exactly, and three cells legitimately show zero:
```
R8-C4, R8-C5-full     cell issues no composite at all -> vacuously 0
R8-C5-overflow        issues 2 composites, still 0, and that IS the pass condition:
                      registry full -> "New dest while full: composite should
                      fallback, not lease" (p_r8_lifecycle.c:439). Not a wrapped
                      ring: overflow=0, seq 0..160 unbroken.
```
Reading "no `event=5`, no Gate A" as an absolute would invalidate three PASSes that
are correct. Compare against the cell's composite count first.

Also required by that same check: src `a8r8g8b8`, dst `x8r8g8b8`, no mask, no
transform/repeat, filter Nearest, no componentAlpha/alphaMap, src and dst different
drawables.

---

## 2. Bring the environment up

```bash
# 1. phone: Settings -> Developer options -> Wireless debugging ON
# 2. discover the endpoint (port changes every time; never hardcode)
/usr/bin/python3 - <<'PY'
import time,socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
F=[]
class L(ServiceListener):
    def add_service(s,zc,t,n):
        i=zc.get_service_info(t,n,timeout=3000)
        if i and i.port: F.append((socket.inet_ntoa(i.addresses[0]), i.port))
    update_service=add_service
    def remove_service(s,*a): pass
zc=Zeroconf(); ServiceBrowser(zc,"_adb-tls-connect._tcp.local.",L())
t=time.time()+10
while time.time()<t and not F: time.sleep(0.3)
zc.close(); print(f"{F[0][0]}:{F[0][1]}" if F else "NOT_FOUND")
PY

# 3. isolated lane on 5038 ONLY. Never touch 5037.
TADB=/data/data/com.termux/files/usr/bin/adb
E="env -u ADB_SERVER_SOCKET -u ANDROID_ADB_SERVER_ADDRESS -u ANDROID_ADB_SERVER_PORT \
   HOME=/data/data/com.termux/files/home ANDROID_NO_USE_FWMARK_CLIENT=1"
$E "$TADB" -L tcp:5038 start-server            # -L is the SERVER listen spec
$E "$TADB" -H 127.0.0.1 -P 5038 connect <IP>:<PORT>
$E "$TADB" -H 127.0.0.1 -P 5038 devices        # SERIAL must appear VERBATIM

# 4. fixture lives in tmpfs and is destroyed by every reboot
f8-r8-fixture                                   # rebuilds and verifies the pinned hash
```

`HOME=` is mandatory — the phone authorised the Termux-home key; without it you get
`SSLV3_ALERT_CERTIFICATE_UNKNOWN`. Client form is `adb -H 127.0.0.1 -P 5038 -s <SERIAL>`;
**never** `ANDROID_ADB_SERVER_PORT` (the harness scrubs it) and never `adb -L` as a
client flag (it works, but it reads as a server spec and invites review challenges).

**Bare `adb -P <port>` AUTO-STARTS an empty server if that port has none**, returning
exit 0 with an empty device list. A dead lane therefore looks healthy. Measured
2026-09-21 on a scratch port:
```
adb -P 5999 devices          -> "daemon not running; starting now" + empty list + rc 0
adb -H 127.0.0.1 -P 5999 ..  -> "cannot start server on remote host"        + rc 1
```
So the client form prescribed above (`-H 127.0.0.1 -P 5038`) is itself immune — it
fails loudly instead of inventing a lane. The hazard is the bare `-P` form. Either
way, always assert the discovered SERIAL appears verbatim in `devices` (V-23 / R-27).

---

## 3. Run a cell

```bash
cd evidence/session/gate-a-a1/p2-r8-runtime
CELL_ID=R8-C1 \
EVIDENCE=$PWD/runtime-b984ded/r8-c1/attempt-NN \
VALIDATE_ONLY=1 bash run-r8-one-cell-b984ded-v11.sh     # zero-mutation dry run first

CELL_ID=R8-C1 EVIDENCE=<same> SERIAL=<serial> \
  bash run-r8-one-cell-b984ded-v11.sh                    # the attempt-consuming call
```
The runner takes **no flags** — it is environment-driven. `CELL_ID` must be one of
exactly these ten (lowercase `r8-c1` is rejected; so are bare `R8-C3` and `R8-C5`):
```
R8-C1  R8-C2  R8-C3-window  R8-C3-disconnect  R8-C4
R8-C5-full  R8-C5-overflow  R8-D  R8-P1  R8-P2
```
`EVIDENCE` must NOT already exist. Exit 3 = `R8_BLOCKED` (attempt NOT consumed), 2 = `R8_INVALID`, else judge rc.
Afterwards write the manifest: `sha256sum ./* > sha256sums.txt` inside the attempt dir
(the runner does not do this, and aggregate check 9 needs it).

**Before any grant, run the standing gate:**
```bash
python3 evidence/session/gate-a-a1/planning-v2/p009-judge-fixture-contract-matrix/check-judge-fixture-contract.py
# exit 1 -> do not grant
```
Re-run it after ANY change to `judge-r8-v2.py` or `p_r8_lifecycle.c`.

---

## 4. The method that saved attempts

After the second consumed attempt, **every** judge or fixture change was replayed
offline against already-captured evidence before spending another attempt, and
previously passing cells were re-judged to prove no regression:

```bash
cp -a <attempt-dir>/. /tmp/replay/
python3 <r8>/collect-r8.py --raw /tmp/replay/collect-input.txt \
  --out-x /tmp/replay/x-observations.jsonl --out-r /tmp/replay/renderer-observations.jsonl \
  --completeness /tmp/replay/completeness.json
python3 <r8>/judge-r8-v2.py --manifest /tmp/replay/manifest.json --spec <r8>/lifecycle-cell-spec.json \
  --evidence /tmp/replay --cell R8-C1 --output /tmp/replay-judge.json
```
Four of the nine defects were found this way with zero extra device runs. Do this.

---

## 5. Where things are

```
plan            ~/Downloads/V1-CORE-EXECUTOR-MASTER-PLAN-V2.3.md   <-- CURRENT
                (the file named V2.md is V2.1; V2.2 is also superseded)
tooling source  src/f8-ahb-gatea-r7-p1-arm/tests/r8/                (git worktree, fork branch
                feat/gatea-r8-lifecycle-support-20260918 @ 14caa7b, pushed)
runner+manifest evidence/session/gate-a-a1/p2-r8-runtime/            (v3..v11, all retained)
this round      evidence/session/gate-a-a1/planning-v2/
                  p003-tooling-hash/            p007-terminal-contract/
                  p008-execution-interface/     p009-judge-fixture-contract-matrix/  <-- gate
                  r8-c1-attempt-09-rca/         r8-c1-second-blocker/
                  r8-c2-src-trace/              r8-d-design/
                  r8-p1-p2-construction-gap/    r8-aggregate/V2-R8-AGG.md
                  r9-design-freeze/Q7-Q8-process-identity.md
                  r9-design-freeze/Q3-generation-nonce-lifecycle.md
                  r9-design-freeze/Q5-stale-ready-cross-generation.md
                  r9-design-freeze/Q6-stale-inflight-frame-cross-generation.md
                  r9-design-freeze/Q4-renderer-state-retained-across-generations.md
                  r9-design-freeze/Q9-socket-lifecycle-cross-generation-residue.md
                  r9-design-freeze/Q10-same-process-reset-support.md
                  r9-design-freeze/Q1-Q2-activity-restart-boundaries.md
                  r9-design-freeze/Q11-clean-recovery-after-fatal.md
                  product-defect-r8-obs-phase-collision/
PRs             waydefu/GPU #9, #10, #11 all MERGED 2026-09-21 (verified via gh)
```

---

## 6. R9 DESIGN FREEZE — what is done and what is not

> ## ⚠ §6 ～ §6.4 是 DESIGN-FREEZE 當下的紀錄。R9 已於 2026-09-22 執行完畢。
> **現行狀態看 §6.5 和 [`V2-R9-AGG.md`](evidence/session/gate-a-a1/planning-v2/r9-agg/V2-R9-AGG.md)。**
> 以下原文保留，因為它是「當時設計了什麼」的紀錄；但這幾條已經被**證據推翻或決策取代**，
> 照著做會走錯路：
>
> | §6 裡的說法 | 現況 | 權威 |
> |---|---|---|
> | R9 DEVICE CELL SET = **3 格**（COLD-2 / F1 / F2） | **2 格**（F1 / F2）。移除 6 格。 | §6.5 · `V2-R9-AGG.md` |
> | R9-COLD-2「可構造」、fault 8 會讓「X 存活」 | **X 不會存活**，COLD-2 不可構造並已移除 | `COLD2-ROUTE-SEARCH.md` §A |
> | 「存活的 X 裡要有 generation boundary，必須先進入 fatal 狀態」 | 更強：**根本沒有可到達的 generation boundary**。那個 fatal 拿不到手。 | `COLD2-ROUTE-SEARCH.md` §C-§E |
> | 「R9 packets 必須驅動 `lorieActivityConnected()` 製造 boundary」 | 第二次 boundary 到不了。R9 觀測到的**只有一個 generation**。 | 同上 |
> | Q4/F3 OBS_TERMINAL_ONE_SHOT 是 R9 fixture 的 BLOCKER | **已解**：D-02 另加 epoch record，不動原終結器 | §6.1 D-02 · `V2-R9-AGG.md` |
> | DE_RESET 三選項，(c)`-terminate`「真正移除」 | **決策是 `-noreset`（D-01）**。`-terminate` 會在最後一個 client 離線時殺掉 X，那會毀掉 R9 的前提。 | §6.1 D-01 |
> | `R9_CELL_SPEC_FROZEN_V1` / 28 向量 / `device_cells=3` | `R9_CELL_SPEC_FROZEN_V2` / 32 向量 / `device_cells=2`；`spec_sha` 已變 | §6.5 · commit `3a12e73` |
> | R9 fixture = `p_r8_lifecycle` | `tests/r9/p_r9_boundary.c`（不需 R8 test extension） | §6.5 |
>
> Q1-Q11 的 source trace 本身**沒有被推翻**，照常引用。被取代的是根據它們做出的
> cell 規劃與 fixture 計畫。


**RESOLVED (see `planning-v2/r9-design-freeze/Q7-Q8-process-identity.md`):**
```
Q8  starttime IS obtainable and stable: /proc/<pid>/stat field 22, 71/71 readable,
    identical across reads, unit 1/100 s. Parse relative to the LAST ')' — comm can
    contain spaces and parentheses.
Q7  PID alone is NOT sufficient. /proc/sys/kernel/pid_max is unreadable inside this
    PRoot, so the reuse margin cannot even be computed.
-> §8.3 process identity = (PID, starttime). D-13 does NOT trigger.
   Every R9 packet crossing a generation boundary must carry and record BOTH.
```

**RESOLVED (see `planning-v2/r9-design-freeze/Q3-generation-nonce-lifecycle.md`):**
```
Q3  The tuple's two halves have DIFFERENT lifetimes, and PR #7's design does not
    say so:
      sessionNonce  once per X PROCESS (getrandom, InitOutput.c:523-525). Nothing
                    re-rolls it. A clean close zeroes it (InitOutput.c:3335) and
                    Gate A is then dead for the rest of that process.
      generation    once per Activity SHARE, 1-based, monotonic, bumped ONLY by
                    lorieActivityConnected() (InitOutput.c:584-586), saturating at
                    UINT64_MAX into permanent disable.
    TWO independent authorities hold it: the shared mapping, and the renderer's
    LATCHED copy (activity.cpp:137-139, taken only on EVENT_SHARED_SERVER_STATE at
    activity.cpp:504). The renderer admits against its latch, never the shared field.
    TRAP: a re-share bump clears generationFatal back to 0 (lorie.h:505), so
    "no fatal after the bump" proves nothing.
-> R9 packets must drive lorieActivityConnected() to create a boundary, and must
   record BOTH authorities at the boundary, not just the shared pair.
   [SUPERSEDED 2026-09-22] 第一次連線的 boundary 可以，**第二次到不了** —— 每個 X
   process 只 bump 一次 generation。R9 兩格都只觀測到一個 generation。
   「兩個 authority 分開記錄」這條仍然有效而且照做了（boundary record 裡
   shared_* 與 renderer_bound_* 是分開的欄位）。見 COLD2-ROUTE-SEARCH.md §C-§E。
-> Q10 is pre-answered by this trace: same-process reset after a clean close is
   impossible without new code. Confirm against the trace, do not re-derive.
```

**RESOLVED (see `planning-v2/r9-design-freeze/Q5-stale-ready-cross-generation.md`):**
```
Q5  §8.2 calls this "the most dangerous UAF surface". THE SOURCE DOES NOT SUPPORT
    THAT. A stale READY cannot be reached by a new generation — four independent
    filters:
      renderer.cpp:857        draw-time lookup skips entries whose tuple != bound
      renderer.cpp:718-720    retirement needs an exact (id, nonce, generation)
      activity.cpp:204-207    rebind over a live READY is "r-rebind-busy" FATAL,
                              because lorieGateAImportBusy() counts READY occupancy
                              (renderer.cpp:292)
      InitOutput.c:2695-2699  X re-validates tuple + REG_READY + fingerprint per use
-> Do NOT design R9 to defend this. Design R9 to PROVE the halt.
   The real residual is a LIFETIME hole, not a UAF: gateADestroyReadyImport()
   (renderer.cpp:444) has exactly ONE caller (renderer.cpp:783, the UNREGISTER
   handler). Every other exit relies on process death to reclaim the GL objects.
   That is another hard input to Q10 — an R9-RESET needs a READY teardown that
   does not exist yet.
```

**RESOLVED (see `planning-v2/r9-design-freeze/Q6-stale-inflight-frame-cross-generation.md`):**
```
Q6  Every traced path ends in DROP or FATAL. Nothing reaches "executed under the
    new generation". Ten-row race matrix in the doc. Verdicts:
      FRAME_TUPLE_REVALIDATED_SAFE     X: one check, synchronous dispatch, fatal on
                                       mismatch (cmdentrypoint.cpp:640-643)
      STALE_FRAME_DROPPED_ON_REPLAY    deferred: BY-VALUE tuple snapshot
                                       (cmdentrypoint.cpp:759-762), revalidated at
                                       replay (:802 / :723-733), dropped WITH cleanup
      STALE_FRAME_FATAL_CONTAINMENT    renderer frame path + both EOF paths halt
      QUEUE_LIFETIME_GAP               the re-share bump asserts the REGISTRY but NOT
                                       the gpuCopyQueue, and never purges the deferred
                                       queue. NOT PROVEN that empty registry implies
                                       drained queue.
      COMPLETION_CROSS_GENERATION_GAP  EVENT_GPU_COPY_DONE carries NO tuple; it is a
                                       doorbell. NO generation check exists anywhere on
                                       the completion path. Containment rests ENTIRELY
                                       on gpuCopySerialCounter never being reset
                                       (InitOutput.c:3459-3460). Load-bearing and
                                       invisible: reset it per generation and the only
                                       protection disappears silently.
    DESIGN_REQUIRED not raised.
-> The bump runs on the X MAIN thread; the record pump runs on the X INPUT thread
   (cmdentrypoint.cpp:1519-1526), sharing no lock. The window is real; reachability
   of the silent-drop row is NOT PROVEN.
-> BLOCKER for any R9-DEFER packet: DEFER_ENQUEUE emits the tuple BEFORE assigning
   it (cmdentrypoint.cpp:741-758 vs :759-762), so it always logs nonce=0
   generation=0 — confirmed 570/570 across the whole R8 corpus. The deferred
   queue's tuple snapshot is currently UNOBSERVABLE in evidence. Same class as
   GAP-8: product-side, contained, product deliberately NOT rebuilt.
```

**RESOLVED (see `planning-v2/r9-design-freeze/Q4-renderer-state-retained-across-generations.md`):**
```
Q4  Retention is the DEFAULT, not an oversight: g_renderer (activity.cpp:128) and
    every Gate A table (renderer.cpp:218-222) are file-scope statics, so their
    lifetime is the APK PROCESS. 13-item inventory with a reset site per item in the
    doc. Three findings:
      F1 MAPPING_POINTER_LIFETIME_DEFECT (NEW)
         gateAMappedState occurs on 4 lines tree-wide: decl activity.cpp:143,
         ONE write :503, ONE read :418-419, and NO clear site. Both
         setSharedState(NULL) paths (:436 HUP, :549 connect_) make the GL thread
         munmap that mapping (renderer.cpp:2404-2405, :2427-2428), and neither
         clears gateABound — so the :418 guard can be TRUE with an unmapped pointee.
         The re-share path is SAFE (:503 precedes :506). Reachability of the
         exposed step NOT PROVEN (Java-side sequencing is outside this tree).
         Both outcomes are already-terminal, but it converts a CLASSIFIED halt into
         an UNCLASSIFIED crash — destroying the identity gateAHupPreserve exists for.
      F2 GL_OBJECT_PROCESS_LIFETIME
         refreshContext (renderer.cpp:1620-1660) swaps only the SURFACE; ctx is
         never destroyed. gpuCopyFbo and the 3 programs are never deleted. So Q5's
         READY-teardown hole CANNOT self-heal, and removeAllBuffers (:1526-1540)
         is not a second reclamation path — it touches only the legacy lists.
      F3 OBS_TERMINAL_ONE_SHOT  <-- BLOCKER for R9 fixture design
         lorieR8ObsEnd("r") fires at most ONCE per APK process
         (r8RendererEndEmitted, renderer.cpp:147/:158, never cleared; two of its
         three preconditions are also never-cleared latches at :820 and :1644).
         R9 spans generations inside one process, so there is currently NO
         per-generation renderer observation terminal. Decide this BEFORE writing
         any R9 fixture.
         [RESOLVED 2026-09-22 by D-02] 沒有動那個 one-shot 終結器。改成**另外加**
         per-epoch 的 R_EPOCH_BEGIN/END，當普通 semantic phase record，碰不到
         r8Ended[] latch，R8 既有契約原封不動。見 §6.1 D-02。
    DESIGN_REQUIRED not raised.
-> Q10 now has THREE independent pre-answers: no nonce re-roll (Q3), no READY
   teardown outside UNREGISTER (Q5), no context turnover (Q4/F2).
```

**RESOLVED (see `planning-v2/r9-design-freeze/Q11-clean-recovery-after-fatal.md`):**
```
Q11 F2 is SATISFIABLE from source. No DESIGN_REQUIRED. Q11 is NOT in-process
    recovery — every fatal is noreturn _exit(127) (lorie.h:1414-1418); it is
    FRESH-SESSION recovery, per plan §8.8 (new nonce / empty registry / clean
    direct SUCCESS).
      (a) NEW NONCE     structural. The shared region is ANONYMOUS in all three
                        creation paths (buffer.c:94-106) and cannot be reopened by
                        name; a fresh X process memsets it (InitOutput.c:510) and
                        draws a fresh getrandom nonce (:523-525).
      (b) EMPTY REGISTRY structural for a NEW PROCESS PAIR — every Gate A table on
                        both sides is a file-scope static (cmdentrypoint.cpp:66,
                        renderer.cpp:218-220, activity.cpp:137-143).
      (c) DIRECT SUCCESS follows from (a)+(b); no source-level obstacle.
    A BOUND fatal kills BOTH processes: both peer-HUP arms terminate the Activity
    (lorie_gatea_hup_class.h:32-36; activity.cpp:421-426), and gateABound is cleared
    at only two lines, NEITHER on a fatal path (activity.cpp:173 via renderer.cpp:813
    clean-close only, and :211).
    TWO ASSERTIONS F2 MUST MAKE:
      F1 SURVIVE_ARM_RESIDUE_RISK — HUP_UNBOUND (activity.cpp:420, :429-438) and
         X-inactive-at-EOF (cmdentrypoint.cpp:1349-1354) let a process live on
         carrying the WHOLE Q4 inventory. Not reachable from a live-generation
         fatal, but F2 must ASSERT the Activity process died — record (PID,
         starttime) per Q7/Q8 on both sides and require the tuple to change.
         Socket closure alone does NOT prove it.
      F2 OBS_CHANNEL_CROSS_SESSION — the R8 obs sink is LOGCAT
         (lorie_r8_obs.c:146..220), which survives process death, and `logcat -c`
         is a redline. Residue must be judged on the WINDOWED capture only
         (runner:142 `logcat -T "$since"`, :267 logcat-since.txt). Misreading
         pre-window carryover would fail a correct F2.
-> OPEN, owned by F1's construction not F2: whether the expected F1 fatal
   (enum16/side2 -> x-wrong-generation/reason6) leaves the generation live at that
   instant. Settle when F1 is designed; F2 inherits the answer.
```

**RESOLVED (see `planning-v2/r9-design-freeze/Q9-socket-lifecycle-cross-generation-residue.md`):**
```
Q9  The two sides are ASYMMETRIC and only X leaks. Three findings:
      F1 SOCKET_TEARDOWN_ASYMMETRY
         renderer connect_ tears the old socket down FIRST (ALooper_removeFd :545,
         close(oldFd) :548). getXConnection does NEITHER — it registers the new fd
         (cmdentrypoint.cpp:1521) and reassigns conn_fd (:1522) without closing or
         unregistering the old one. closeLorieConnection is reachable ONLY from the
         three input-thread error/EOF arms (:848, :1308, :1351). So two fds can be
         registered to handleLorieEvents at once. That repeated connects are an
         EXPECTED mode is proven by the bump branch itself (InitOutput.c:571-579) —
         a first-and-only connect could never take it.
      F2 SHARED_DECODER_UNSYNCHRONIZED
         gateARecordDecoder is ONE process-wide static (:71) used by TWO callers on
         TWO threads reading TWO different fd expressions: handleLorieEventsProto
         uses the callback's `fd` (:1327, X INPUT thread) and lorieGateAPumpConnection
         uses `conn_fd` (:1281, X MAIN thread, from InitOutput.c:2768). NO mutex
         covers it — cmdentrypoint.cpp has only gateARegistryMutex (:67) and
         gateASendMutex (:68). Partial state is retained BY DESIGN
         (InitOutput.c:2775-2776). Concurrency NOT PROVEN (nothing suspends the
         input thread; InputThreadUnregisterDev occurs only at :833).
      F3 STALE_EOF_DESTROYS_LIVE_STATE
         Both proto teardown arms unconditionally lorieRecordDecoderDestroy
         (:1309, :1352) and drain registeredBuffers (:838-839) — process-wide state
         that may belong to the NEW connection. conn_fd itself IS correctly
         identity-guarded (:834-835); the decoder and the buffer list are not.
    DESIGN_REQUIRED not raised (all three hinge on Java-side close ordering, which
    is outside the tree).
-> R9 RECONNECT packets must record, from /proc on the X PID, whether the previous
   fd was still registered at the bump; and must NOT read "decoder reset" as evidence
   of a clean boundary — a stale EOF produces the same observable.
```

**RESOLVED — and this one bites (see `planning-v2/r9-design-freeze/Q10-same-process-reset-support.md`):**
```
Q10 A same-process reset path ALREADY EXISTS, is the DEFAULT, needs no new code, and
    PERMANENTLY KILLS Gate A while the X server keeps running.
      - The Gate A protocol has NO reset primitive (8 msg types, none of them reset).
      - dispatchExceptionAtReset defaults to DE_RESET (xserver/dix/dispatch.c:3480),
        and `-terminate` is NOT passed here (start-x3.py:15 -> f8-x11gpu -> Loader
        ":3"; CmdEntryPoint.java:41/:166 pass argv through unchanged).
      - dix/main.c:325 calls CloseScreen UNCONDITIONALLY; only ddxGiveUp and the loop
        break are DE_TERMINATE-gated (:347, :353-356).
      - lorieCloseScreen IS the installed hook (InitOutput.c:1461) and calls
        gateACloseGeneration() (:1240), which zeroes sessionNonce (:3335).
      - the loop re-enters OsInit -> OsVendorInit (dix/main.c:151; os/osinit.c:317),
        which returns immediately on `stateFd != -1` (InitOutput.c:494-495):
        NO new region, NO memset, NO getrandom.
      - lorieActivityConnected is guarded by sessionNonce != 0 (:567) -> can never
        re-enter -> no generation can ever be allocated again in that X process.
    => THE LAST X CLIENT DISCONNECTING SILENTLY AND PERMANENTLY DISABLES GATE A.
       No fatal, no log line saying so. It reads exactly like "Gate A inactive".
    DESIGN_REQUIRED RAISED on D-01, scoped to 7 enumerated items (5 product, 1
    test-support, 1 existing call simply not wired to the bump). R9-RESET is
    constructible today but can only ever prove the kill, never a recovery.
-> N1/N2 CLOSED 2026-09-22, zero attempt cost. EXISTING R8 EVIDENCE IS CLEAN:
   R8 never reaches DE_RESET, because the fixture does not just exit — it issues a
   custom X request whose handler calls upstream GiveUp(0) directly
   (lorie_r8_test.c:341-342 -> os/utils.c:426-430 -> DE_TERMINATE), which pre-empts
   the default reset. Class P cells never get there at all (fatal_no_clean_term).
   Verified across all ten passing attempts of runtime-b984ded:
     x_pre_cleanup=DEAD and NO_X3_RESIDUE in 10/10. A DE_RESET would have left X
     ALIVE. No R8 result is a post-reset observation; nothing needs re-judging.
-> BUT R8's immunity is an ACCIDENT OF ITS FIXTURE and does NOT transfer:
     ANY R9 fixture that EXITS NORMALLY instead of issuing the terminate request
     drops the last client, fires DE_RESET, and silently kills Gate A for the rest
     of that X process — no fatal, no log line.
   [DECIDED 2026-09-22 = D-01: `-noreset`。**不是** 下面任何一個。]
   `-noreset` 把 dispatchExceptionAtReset 設成 0，最後一個 client 離線時不 reset，
   Gate A 留著、X 也留著。選項 (c) 的 `-terminate` 會在最後一個 client 離線時直接
   結束 X —— 那會把「X 活過 client」這個 R9 前提整個毀掉，所以下面把它寫成
   「REMOVES it」是錯的。R9 兩格都是靠 `-noreset` 跑出來的，runner 在 cell 開始前
   會檢查 /proc/<x_pid>/cmdline 真的帶這個 flag，沒有就 refuse。
   Three options, only one actually removes the hazard:
     (a) keep issuing the explicit terminate        — avoids it
     (b) hold a second X client across the boundary — avoids it
     (c) launch X with `-terminate`                 — REMOVES it, but changes the
         frozen X launch command (start-x3.py:15) => Astra/Sol decision.
-> UPSTREAM-CONFIRMED (not inferred from the vendored tree alone):
     X.Org Xserver(1): "-terminate causes the server to terminate at server reset,
       instead of continuing to run"; "-noreset prevents a server reset when the
       last client connection is closed". Reset-and-continue is the DOCUMENTED
       DEFAULT; -terminate is opt-in and this deployment does not opt in.
     Debian xorg-server 2:21.1.24-1 has `dispatchExceptionAtReset = DE_RESET;` at
       dix/dispatch.c:3480 — SAME FILE, SAME LINE as the vendored tree.
     patches/xserver.patch modifies dix/main.c, dix/dispatch.c, os/osinit.c and
       os/utils.c but contains ZERO occurrences of DE_RESET / DE_TERMINATE /
       terminate / noreset. The reset machinery is untouched.
     Trigger named: dix/dispatch.c:3569 CloseDownClient() ->
       ShouldDisconnectRemainingClients() -> SetDispatchExceptionTimer() (:421-433).
```

## 6.1 DECISIONS TAKEN 2026-09-22 (ASTRA) — D-01 / D-02

### D-01 = **ACCEPTED**  — R9 reset policy
```
V1-Core / R9 launch X with `-noreset`.
Same-process DE_RESET support is OUT OF SCOPE for V1-Core -> DEFERRED.
```
Source basis (all verified, not inferred):
```
os/utils.c:900-902      -noreset -> dispatchExceptionAtReset = 0
dix/dispatch.c:423-427  SetDispatchExceptionTimer(): !(0 & DE_TERMINATE) is TRUE,
                        so `dispatchException |= 0` -> NOTHING is set, and it returns
=> last-client disconnect raises no exception -> the dispatch loop never exits
   -> CloseScreen never runs -> gateACloseGeneration() never runs
   -> the tuple is never zeroed by last-client=0
os/utils.c:426-432      GiveUp() sets dispatchException |= DE_TERMINATE DIRECTLY,
                        bypassing dispatchExceptionAtReset entirely
=> R8's explicit fixture terminate is UNAFFECTED by -noreset. No R8 regression.
```
**`-noreset` is a LAUNCH FLAG, not a source change — and that is the only compatible
mechanism.** `verify-r8-support.py:68-69` asserts
`char dispatchExceptionAtReset = DE_RESET;` is present in the product source
(`product_reset_default`). Changing the source default to achieve D-01 would FAIL
that existing host check. Do not attempt it.

**Claim-scope note, mandatory in any R9 write-up:**
```
R8 10/10 was completed on the HISTORICAL launch configuration, WITHOUT -noreset
(start-x3.py:15). Those PASSes stand unchanged and are NOT re-judged (§5.1), but
their claim scope does NOT include same-process DE_RESET continuity. R8 and R9
evidence are CONFIGURATION-DISTINCT and must never be pooled on this axis.
```
(R8 never reached DE_RESET regardless — the fixture forces DE_TERMINATE; verified
10/10 `x_pre_cleanup=DEAD` + `NO_X3_RESIDUE`. See §6 Q10.)

### D-02 = **IMPLEMENTED, INSTALLED, SMOKE-PASSED** — R9 multi-epoch observation
```
R8 process-level BEGIN/END           UNCHANGED. Keeps its one-shot terminal contract.
R9 epoch boundaries                  ORDINARY semantic phase records —
                                     R_EPOCH_BEGIN / R_EPOCH_END.
                                     NOT a second BEGIN/END producer, so they cannot
                                     collide with the existing r8Ended[] latch.
每個 epoch phase 自帶                epoch_id, epoch_nonce, epoch_generation, reason.
                                     MUST NOT rely on the process-global r8Nonce /
                                     r8Generation (lorie_r8_obs.c:22-23) to represent
                                     a historical epoch.
Renderer process END authority       MOVES to: explicit whole-run finalization.
                                       != generation unbind   (renderer.cpp:820)
                                       != surface quiesced    (renderer.cpp:1644)
                                       != first epoch end
Exact control transport              DELIBERATELY NOT FROZEN. To be source-bound by
                                     the implementation packet. Do not pre-commit to
                                     an opcode; that would add another harness
                                     assumption.
```
**Why the current design cannot carry epochs (the blocker this decision answers):**
```
lorie_r8_obs.c:184-192   once r8Ended[ix] is set, EVERY later record is DROPPED and
                         emits R8_OBS_POST_END, which tooling maps to
                         R8_INVALID POST_END_OBSERVATION
renderer.cpp:149-159     the renderer END fires on
                         GenerationUnbound && SurfaceQuiesced && LoopDrained
renderer.cpp:820, :1644  the first two are set during GENERATION 1 and NEVER cleared
=> a nested design that keeps the current END trigger would finalize at the end of
   epoch 1 and invalidate every later epoch.
```

**SOURCE-BOUND CONSTRAINT ON THE TRANSPORT — read before choosing one:**
```
verify-r8-support.py:66  need('lorieR8ObsEnd' not in term_fn, "terminate_no_obs_end")
                         where term_fn = the body of ProcLorieR8Terminate
=> wiring whole-run finalization INTO the existing terminate control is FORBIDDEN by
   an existing host check. Either pick a different seam, or amend that check
   deliberately and record why.
```

### SMOKE RESULT ON THE NEW ARTIFACT — 2026-09-22
```
INSTALLED   dc94485a7ef4f74cada36ea3c1d35d0aa0f48693   CI 35673085569
            VERSION 1.03.01-dc94485-22.09.26
            APK_SHA256 1bd8bef0909249737ea43acf0a35f3c995d941e1badbfcf370e5cd854f4bb8a3
            BUILD_ID   bc993eee0c4420b9721801b06d7183ed53de487b
            SIGNER     b6da0148… unchanged, apksigner-verified
            measured on device with sha256sum after install, before any cell ran

RESULT      R8-D   R8_PASS   runtime-dc94485/r8-d/attempt-01    55-file manifest
            R8-P2  R8_PASS   runtime-dc94485/r8-p2/attempt-01   53-file manifest
            runner run-r8-one-cell-dc94485.sh + manifest
            runtime-dc94485/r8-runtime-tooling-manifest-dc94485.json

EVIDENCE    p2-r9-artifact/artifact-dc94485/SMOKE-RESULT.md
```

**THE SMOKE FOUND A REAL REGRESSION — which is why 2 cells beat 0 cells.**
```
The FIRST artifact (7e3a05e) failed R8-D:
  runtime-7e3a05e/r8-d/attempt-01   R8_INVALID PRODUCERS_NOT_FINALIZED   r_end=0
Cause: the renderer END was gated on lorieGateAObserveRunFinalize(st) read AT the
terminal. R_SURFACE_QUIESCED is the LAST renderer record (seq 25/26, after
R_UNBOUND_FINAL at 22 and R_EPOCH_END at 23); by then X has died, the Activity has
called setSharedState(NULL), and the GL thread has munmap'd the region and set
state = nullptr. The read saw NULL and the END never fired.
The seam review had proven the publish/observe ORDERING rigorously but never asked
whether the MAPPING was still mapped when the terminal conditions complete. It is not.
dc94485 latches the flag when first visible with a live mapping. Semantics unchanged.
That attempt stays INVALID and frozen (§5.1) — it is the evidence for the fix.
```

**Measured on dc94485 — all three D-02 goals confirmed on device:**
```
                       R8-D              R8-P2
renderer BEGIN/END     1 / 1             1 / 0   <- P2 proves the gate does NOT fire on
                                                    the fatal path (no TERMINATE sent ->
                                                    runFinalize never published). A gate
                                                    that fired unconditionally would have
                                                    passed R8-D and failed ONLY here.
R_EPOCH_BEGIN/END      1 / 1             1 / 0
epoch original_nonce   0                 0       <- MUST stay 0; tuple_bind() discards
                                                    such rows, and admitting renderer
                                                    rows would change the judge's input
                                                    set for FROZEN cells
DEFER_ENQUEUE          16, real nonce    6, real nonce   <- Q6-F1 FIXED (was 0/0 in
                                                            570/570 b984ded records)
```

**NOT established:** the other 8 cells on dc94485 (deliberately unrun — the audit found
no cell whose semantics are touched, and these two cover both production changes plus
both terminal shapes); and R9 itself — only ONE epoch occurs per R8 cell, so multi-epoch
behaviour is made POSSIBLE by D-02 but has not been demonstrated.

### ARTIFACT — BUILT, BOUND, **NOT INSTALLED** (2026-09-22)
```
PRODUCT_SHA    7e3a05e0a809dedd4d4a59dfb57b8e07528991b7   (pushed to fork branch)
CI_RUN         35633676606   completed/success, 3m13s
VERSION        1.03.01-7e3a05e-21.09.26      (was 1.03.01-b984ded-18.09.26)
APK_SHA256     fd4bbed07f2d723d26e5a22ce5b1c9dd39957db4fc318da5a9ae8a9b0a3cc8c9
BUILD_ID       ed3e15a9c01e90eb5637a73fcdb69b7a5160daf7   (CHANGED this time — the
               fb4f017->b984ded transition left it identical, so the old
               "NON-DISCRIMINATING" note does not apply here)
SIGNER         b6da0148… UNCHANGED, and this time INDEPENDENTLY VERIFIED with
               apksigner on both artifacts (b984ded's provenance only DERIVED it)
VARIANT        termux-x11-universal-debug — RE-DERIVED, not assumed: both variants of
               run 35347497216 were hashed and only universal reproduced 0d06de68…
EVIDENCE       evidence/session/gate-a-a1/p2-r9-artifact/artifact-7e3a05e/
```
**The frozen R8 corpus stays bound to b984ded. b984ded and 7e3a05e evidence must
never be pooled.** Plan §2.2 now carries both blocks explicitly.

### TOUCHED-SEMANTICS AUDIT — DONE (evidence: `p2-r9-artifact/touched-semantics-audit/AUDIT.md`)
```
The product delta is EXACTLY ONE COMMIT: 14caa7b / 2b6f9f0 / 2a14ab2 touched only
tests/, which is why PRODUCT_SHA never moved off b984ded.

Every added line was classified by #ifdef LORIE_ENABLE_R8_TEST_SUPPORT membership.
After removing comments, #endif directives, the layout-identical field rename, a
compile-time-only static assert and two uncalled static inlines, the PRODUCTION
delta is exactly TWO changes:

A  gateAMappedState = NULL  (activity.cpp, 2 sites)
   Read at exactly one site (:418-419, peer-HUP). In that handler the READ precedes
   the CLEAR in the same invocation. Only a LATER read could differ — and all ten
   cells log GATEA_BIND=1 (one bind, no second connect_), with HUP occurring only in
   P1 and P2 and only as the single terminal HUP.
   -> NO REACHABLE BEHAVIOUR CHANGE IN ANY R8 CELL.

B  statement reorder in gateAQueueDeferredRecord (cmdentrypoint.cpp)
   In a production build the #ifdef block does not exist, so the reorder is a NO-OP.
   In a test build the code stepped over (DeferAllocId / snprintf / lorieR8Obs /
   WakeReceived) touches neither `queued` nor `shared`. Only the LOGGED values change.
   Both judges do require_obs(xrows,"DEFER_ENQUEUE") — PRESENCE ONLY
   (judge-r8.py:353, judge-r8-v2.py:421). Nothing reads its nonce/generation.
   -> NO REACHABLE VERDICT CHANGE IN ANY R8 CELL.

RECOMMENDED SCOPE — 2 cells, chosen for coverage not count:
  R8-D   heaviest DEFER_ENQUEUE producer (15 records); exercises change B directly
  R8-P2  the ONLY coverage of change A's reachable path (HUP=1), and the fatal
         terminal where the new END gating must NOT fire
  Together: both production changes, the epoch records, the finalize re-gate in both
  its firing and non-firing forms, and both terminal shapes.
NOT recommended: full 10/10 (8 extra attempts buy no coverage) or zero runs (leaves
  the new binary entirely unmeasured — BUILD_ID did change).
DECISION OWNER: ASTRA/SOL under D-12. The audit is input, not the decision.
```

### D-02 IMPLEMENTATION — DONE IN SOURCE 2026-09-22 (not built)
```
SEAM SELECTED  existing reserved word in struct LorieGateATestFault (+20, formerly
               `pad`, never read). ABI-LAYOUT-NEUTRAL: no size/offset/alignment
               change, all five pre-existing static asserts unchanged.
               Full option table + rejections: planning-v2/d02-seam-review/SEAM-REVIEW.md
               Full change + verification record:  .../IMPLEMENTATION-RECORD.md
CHANGED        9 files, +234/-12, in the worktree. NOT COMMITTED, NOT BUILT.
  finalize     lorie.h runFinalize + accessors; ProcLorieR8Terminate publishes it
               before GiveUp(0); lorieR8MaybeFinalizeRendererObs(st) requires it.
  epochs       lorieR8ObsEpoch/ObsTuple/EpochAllocId; R_EPOCH_BEGIN at bind
               (activity.cpp), R_EPOCH_END at unbind (renderer.cpp). epoch_id is
               independent of epoch_generation (Q2-F2).
  bundled fix  Q6-F1 DEFER_ENQUEUE now emitted AFTER the tuple is assigned.
  bundled fix  Q4-F1 gateAMappedState cleared on BOTH unmap paths.
VERIFIED       test_r8_epoch_obs.c (NEW) 17/17; test_r8_obs_terminal.py 10/10;
               +15 new static checks in verify-r8-support.py, all passing.
               OFFLINE JUDGE REGRESSION: epoch records injected into all ten frozen
               runtime-b984ded attempts, re-collected and re-judged ->
               **10/10 verdicts IDENTICAL to baseline**. Frozen evidence untouched
               (scratch copies only).
CAUGHT MID-WAY The first draft stamped the epoch tuple into original_nonce/
               original_generation. That WOULD have been a frozen-contract
               regression: judge-r8-v2.py:243-248 tuple_bind() discards rows whose
               original_nonce is 0, and the renderer never calls lorieR8BindTuple(),
               so every renderer row is discarded TODAY (evidence: r-stream origins
               are {(0,0)} in every cell). Fixed: the epoch tuple lives in epoch_*
               only; original_* keeps its meaning. Pinned by a host check.
```

**PRE-EXISTING HOST FAILURES — not caused by D-02, but they block the build step:**
```
verify-r8-support.py is RED at HEAD on three checks, before any D-02 change:
  collector_unchanged  sha256(collect-r8.py) != FROZEN_COLLECTOR_SHA
                       (collect-r8.py is UNMODIFIED by this work)
  judge_vectors_v2     test-judge-r8-v2.py reports failures=5 (also unmodified)
  obs_ingestion        1 failure, reproduced on a pristine `git archive HEAD` tree
After D-02 the verifier reports EXACTLY these three and no others.
Someone must resolve them before build/CI. They are a separate matter.
```

### IMPLEMENTATION IMPACT — D-02 (corrected 2026-09-22)
```
D-02 requires TEST-SUPPORT NATIVE SOURCE CHANGES:
  - lorieR8MaybeFinalizeRendererObs() END trigger      (renderer.cpp:149-159)
  - per-epoch tuple recording                          (lorie_r8_obs.c:22-23, :176-200)

Being inside #ifdef LORIE_ENABLE_R8_TEST_SUPPORT does NOT make it free:
      no Production Gate A semantic redesign
   != no experimental APK rebuild
A NEW EXPERIMENTAL ARTIFACT WILL BE REQUIRED once D-02 is implemented, and a rebuild
is a §2.2-gated action.

REQUIRED CHAIN — P009 alone is NOT sufficient, because B changes a NATIVE
OBSERVATION PRODUCER:
  [done 09-22] DESIGN FREEZE -> source implementation -> static/host tests -> P009
  [NEXT]       build/CI -> artifact bind -> affected observation regression
  -> only then design R9 runtime
  (the offline judge replay already done is the HOST-SIDE pre-check for that last
   step, not a substitute for it)

R8 REQUALIFICATION IS *NOT* AUTOMATICALLY REQUIRED:
  Historical R8 evidence is untouched. The new artifact need only prove that R8
  terminal semantics were not broken by the observation change. Whether a full
  10/10 requalification is needed is decided AFTER a diff / touched-semantics audit
  (same method as GAP-4), and MUST NOT be assumed now.

Affected host tests already locking this contract (the regression floor):
  tests/r8/test_r8_obs_terminal.py   10 cases incl. x_end_then_any,
                                     r_unbound_end_then_surface, reset_path_no_end
  tests/r8/test_r8_obs_terminal.c    compiled+run by verify-r8-support.py:416-425
  tests/r8/verify-r8-support.py      :66 terminate_no_obs_end, :150 x_obs_end_at_giveup,
                                     :181 post_end_diag, :68-69 product_reset_default
  tests/r8/test_r8_obs_ingestion.py
```

---

**CONTRADICTION FOUND AND CORRECTED — Q3 §B.2.** Q3 called the clean close "terminal
for the process" and glossed its caller as "i.e. X server shutdown". The caller
enumeration was right; the gloss was wrong and under-stated reachability. Q3 is
corrected in place and now points at Q10. Q3 §A.1's consequence is unchanged and is
now MORE load-bearing: Q10 supplies the live-process path that reaches it.

**RESOLVED (see `planning-v2/r9-design-freeze/Q1-Q2-activity-restart-boundaries.md`):**
```
Q1  WARM NEW X, SAME ACTIVITY — this is a HALT MODE, not a recovery mode.
    Warm reconnect is a designed flow (MainActivity.java:604-612, a 250 ms retry
    loop; renderer.cpp:1240-1241 "created once, only the fd is re-sent").
    BUT connect_ (activity.cpp:544-550) resets ONLY the socket, the shared-state
    mapping and the LEGACY buffer lists. It does NOT clear gateABound and does NOT
    drain the Gate A tables (removeAllBuffers, renderer.cpp:1526-1540, touches only
    the legacy lists). So the new X meets an Activity still claiming the OLD tuple:
      activity.cpp:204-207  gateABound==1 && tuple differs && lorieGateAImportBusy()
                            -> lorieGateAFatalHalt("r-rebind-busy")
    => An R9 WARM packet must EXPECT r-rebind-busy while imports are live, or first
       prove the tables are empty. Do NOT write it as a success path by default.
    RETAINED across a warm new X: the bound-tuple latch, all three Gate A tables,
    the EGL context and every GL object, stateCond/stateCondFd, the R8 obs latches.

Q2  COLD ACTIVITY RESTART — the Activity world is genuinely rebuilt (new process;
    Renderer::init runs because `if (ctx) return` does not trip, renderer.cpp:1232).
    NOTHING on the X side is rebuilt: gateAXRegistry, gpuCopySerialCounter, the
    shared region + its nonce, registeredBuffers, the deferred queue all survive.
    Reconciliation is the next generation bump, which FAIL-STOPS on non-terminal old
    work ("x-bump-unterminal", cmdentrypoint.cpp:389-393).
    CONSEQUENCE FOR THE R9 SCHEMA: (nonce, generation) CANNOT distinguish
    "same X, new Activity" from "same X, same Activity, new generation" — the nonce
    is per X PROCESS (Q3) and only the generation advances. Every R9 boundary record
    must ALSO carry the Activity's (PID, starttime) per Q7/Q8, and D-02's epoch_id
    must be independent of epoch_generation for the same reason.
```

**Q4/N1 CLOSED by Q1.** The dangling `gateAMappedState` read is now REACHABLE, not
hypothetical: the warm-reconnect flow produces exactly the required ordering —
`connect_:549` munmaps the old mapping while `gateABound` stays 1, then `:556-560`
registers the new fd BEFORE any `EVENT_SHARED_SERVER_STATE` (`:503`, the only writer
of `gateAMappedState`). With a 250 ms UI retry loop, a flapping X yields a
registered-but-not-yet-stateful connection routinely. Whether it has OCCURRED is
still a runtime question.

**R9 DESIGN FREEZE IS COMPLETE.** All eleven questions are resolved, one
`DESIGN_REQUIRED` was raised and accepted (D-01), and one design decision is recorded
pending implementation (D-02). §8.1's bar — "R9 must not be run off PR #7's design;
these answers replace it" — is now met **on the design axis**.

**What actually gates R9 runtime now is D-02's implementation**, not more tracing.

**Still outranking them — one settled, one not:**
```
1  Q10/N1+N2  CLOSED 2026-09-22. Existing R8 evidence is clean (10/10 X DEAD).
              What REMAINS is the decision: R9 fixtures must not exit normally, or
              X must be launched with `-terminate`. Astra/Sol call — see §6 Q10.
              [CLOSED 2026-09-22 = D-01 `-noreset`, NOT `-terminate`. R9 fixture
               正常 exit 就好。]
2  Q4/F3      OPEN. There is no per-generation renderer observation terminal.
              Settle this BEFORE any R9 fixture work.
              [CLOSED 2026-09-22 = D-02, 另加 epoch record。]
```
~~**Before any R9 fixture work, settle Q4/F3**~~ — **兩項都已結案，R9 已執行完畢（§6.5）。**
§8.1 forbids running R9 off PR #7's design; these answers replace it.

---

## 6.2 V2-R9-DESIGN — DONE 2026-09-22 (`planning-v2/r9-design/`)

**§8.6's four deliverables now all exist, so R9 runtime packets are no longer blocked
on that gate:**
```
r9-design-freeze.md        planning-v2/r9-design-freeze/   9 files (Q1-Q11)
r9-identity-contract.json  planning-v2/r9-design/          NEW
r9-cell-spec.json          planning-v2/r9-design/          NEW
r9-decision-log.md         planning-v2/r9-design/          NEW
V2-R9-DESIGN.md            planning-v2/r9-design/          the packet itself
```

**THE FREEZE INVALIDATED PART OF §8.7, WHICH WAS WRITTEN BEFORE THE ANSWERS EXISTED.
Five corrections, recorded in r9-cell-spec.json:**
```
1  §8.7 #14 V2-R9-RESET          REMOVED. Q10: the reset already exists, is the
                                 DEFAULT, and permanently disables Gate A. The packet
                                 can only prove the kill, never a recovery.
2  "no stale READY consumed"     TAUTOLOGY. Q5 proved it structurally impossible (four
                                 filters). The obligation is that the HALT fired.
3  WARM-1/2/3 as a success chain WRONG SHAPE. Q1-F1 makes warm-rebind-over-live-
                                 imports a HALT. They must differ by TABLE STATE.
4  §8.4 WARM/COLD definitions    INCOMPLETE. Q2-F2: (nonce, generation) cannot
                                 distinguish them. Activity (PID, starttime) is now
                                 the required discriminator.
5  #5/#6/#7 conditional          NO LONGER CONDITIONAL — done via dc94485.
```

**THE CELL SET — 8 cells, with an honest constructibility column:**
> **[SUPERSEDED 2026-09-22]** 8 格裡 6 格已移除（WARM-1/2/3 · COLD-1/3 · COLD-2），
> device packet 是 **F1 / F2 兩格，都 PASS**。這個 constructibility 欄位是這份設計
> 最划算的部分：4 個 `NOT_PROVEN` 全部真的不可構造，4 個 `PLAUSIBLE` 裡也有 2 個是。
> **六格都沒有燒掉 attempt**（COLD-2 在證明成立前已花掉的兩次除外，維持凍結 INVALID）。
```
R9-WARM-1           Q1, Q4          PLAUSIBLE     PASS
R9-WARM-2           Q1-F1, Q5       NOT_PROVEN *  PASS via expected r-rebind-busy
R9-WARM-3           Q4-F1, Q1-F2    NOT_PROVEN    PASS
R9-COLD-1           Q2, Q2-F1       PLAUSIBLE     PASS
R9-COLD-2           Q2-F1, Q3       NOT_PROVEN    PASS via expected x-bump-unterminal
R9-COLD-3           Q3, Q2-F2       PLAUSIBLE     PASS
R9-F1-STALE-REPLAY  V-11, Q5, Q6    NOT_PROVEN *  PASS via expected fatal
R9-F2-RECOVERY      Q11             PLAUSIBLE     PASS
```
**FOUR OF EIGHT HAVE UNPROVEN CONSTRUCTION, and that is this packet's most important
output.** §8.8 separates INVALID_CONSTRUCTION (payload never reached the path) from
VALID_FAIL (it did and was mishandled). A cell whose construction is assumed burns
attempts and produces the former. The two hardest:
```
R9-WARM-2  needs the Activity to call connect_ with a NEW fd while the previous X is
           still alive AND bound, with a READY import outstanding. connect_ resets the
           socket, mapping and legacy lists but NOT gateABound and NOT the Gate A
           tables (activity.cpp:544-550) — which is precisely what makes the next bind
           fatal. The trigger is Java-side and the runner has no mechanism for it.
R9-F1      Q5/Q6 made this HARDER than V-11 assumed. Every route for delivering stale
           state is already filtered or fatal. F1 must find one that actually reaches
           the current path, or it is INVALID_CONSTRUCTION — which is NOT VALID_FAIL.
```

**UNBLOCKED:** #2 FIXTURE, #3 JUDGE, #4 HOST-VERIFY (all host-only). #5/#6/#7 done.
**STILL BLOCKED:** every device packet on #4; WARM-2 and F1 additionally on a proven
construction; F2 on F1's expected fatal (§8.8 forbids manufacturing another one).

**SEVEN STANDING OBLIGATIONS FOR EVERY R9 PACKET** are listed in `V2-R9-DESIGN.md`.
The two most easily forgotten:
```
- launch with -noreset (D-01), or every "Gate A inactive" observation is unattributable
- record x_fd_table_had_previous_conn_fd from /proc — Q9-F1 means the product reports
  NOTHING about the previous fd still being registered
```

**NOT CLAIMED:** that any R9 cell will pass; that multi-epoch observation WORKS (D-02
makes it POSSIBLE — the smoke proved the records exist in a SINGLE-epoch run, and no
test has yet crossed a boundary with the renderer surviving).

---

## 6.3 V2-R9-FIXTURE 構造證明 — DONE 2026-09-22（`planning-v2/r9-fixture/`）

全部離線完成，**零 attempt**。結論是 §8.7 的 9 個 device packet（#8-16）收斂成 **3 格**。

> **[SUPERSEDED 2026-09-22]** 再收斂成 **2 格**。下面 `#1 R9-COLD-2 可構造` 這一項
> **是錯的**：fault 8 publish fatal 的那一刻，X 正卡在同一個 serial 的
> `gateAWaitTerminal` 裡（`InitOutput.c:3539`），`lorieGateADeriveResult` 在
> `fatal != 0` 直接短路（`lorie.h:296-297`），走到
> `gateAXFatal("x-direct-not-success")`（`:3546`）後因為 fatal 已被 publish 而
> `_exit(127)`（`:3212-3217`）。**X 不會存活**，`pendingCount` 留在 1 也沒有用，
> 因為沒有下一個 `lorieActivityConnected()` 可以撞上它。
> 逐行證明：`planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md` §A-§B。

### 最終 R9 DEVICE CELL SET — 3 格（→ 現為 2 格，見上方 SUPERSEDED）
```
#1  R9-COLD-2   可構造  fault 8  (RENDERER_FATAL_PRE_FENCE) -> expected x-bump-unterminal
                        它 publish fatal 所以 X 存活，且觸發點嚴格落在 lease
                        (cmdentrypoint.cpp:226-227) 與 ack (:270-271) 之間，
                        pendingCount 留在 1 —— 正是 x-bump-unterminal 要偵測的
#2  R9-F1       可構造  fault 16 (STALE_READY_REPLAY, renderer.cpp:674-679) —— 機制
                        產品裡本來就有。V-11 的四個成分全部驗到：
                        enum16 / side2 / x-wrong-generation / FAIL_GENERATION = 6
#3  R9-F2       等 F1 的 expected fatal 出現後可構造（Q11 未發現 source 障礙）
```

### 移除 6 格 — `SOURCE_PROVEN_RUNTIME_NOT_CONSTRUCTIBLE`
**不是 PASS、不是 FAIL、不是 INVALID、不是 runtime-qualified。** 每一格都註明了會讓它
重新開啟的條件。
```
R9-WARM-1/2/3   ASTRA 2026-09-22 選項 (c)。產品沒有 same-Activity warm reconnect 的
                入口：三個 tryConnect() 呼叫點全部不通 ——
                  :276 onCreate      launchMode="singleInstance"，am start 不重跑
                  :588 onReceive…    需要 intent 帶 Binder，shell 的 am broadcast 傳不了
                  :1132              被 !connected 擋住，而 connected() 就是 conn_fd != -1
                為了測產品走不到的路而開第二個 X（破壞 :3 邊界）或加人工 test seam，
                性價比不成立。r-rebind-busy 的 containment 已由 Q1-F1 + Q5 四道 filter
                從 source 證明。
R9-COLD-1/3     COLD1-ROUTE-SEARCH.md：**沒有**任何可驅動的 published renderer fatal
                同時滿足「registry TERMINAL」。26 個 gateARendererFatal 呼叫點全部列舉；
                唯一 pre-lease 的 test-fault 站點(:674)不會 fatal renderer，而每一個
                published fatal 都嚴格落在 lease 與 ack 之間。
                三個候選逐條被否決：
                  r-tuple-mismatch   terminal 但不可驅動（需 latch/import tuple 不符）
                  r-duplicate-ready  terminal 但 X 端結構性拒絕 strict double-insert
                                     (cmdentrypoint.cpp:121-124「P3 never does this」)
                  r-ready-send       terminal 但需要 socket write 失敗
V2-R9-RESET     不存在（Q10 / D-01）
```

### 比 COLD-1 本身更重要的發現
```
GATE A 沒有可達的、乾淨的 same-process generation boundary。
```
把這次搜尋與 Q10、COLD 三難放在一起才看得出來：
```
clean close   會把 sessionNonce 歸零（InitOutput.c:3334-3335），之後 Gate A 在該 X
              process 內永久死亡（Q10）。乾淨的 END 是終點，不是轉換。
bump path     lorieActivityConnected() 退休舊世代而**不**歸零 nonce
              （InitOutput.c:575-586）—— 這才是乾淨轉換，而且它寫得很好。但要走到它需要
              connect_ 帶新 fd，那需要
                WARM reconnect 入口 -> 產品裡不存在，或
                新的 Activity (COLD) -> 但 Activity 死亡會讓 X 走 x-eof fatal，
                                        除非 generationFatal 已經被設起來（三難）
=> 存活的 X 裡要有 generation boundary，必須先進入 fatal 狀態。
```
bump 機制本身建得很完整（nonce/generation 非對稱、registry 輪替、先 poison 再 close、
fatal 清除），而就這份 trace 所能判斷，它**在不先進入 fatal 的前提下完全走不到**。

**對 R9 的後果：** 三格存活的 cell **全部**是 fatal-path cell。R9 裡完全沒有乾淨路徑的
generation-boundary cell —— 而那是**產品的性質，不是測試設計的缺口**。

> **[SUPERSEDED 2026-09-22 — 結論比這裡寫的更強]** 不是「必須先進入 fatal 狀態」，
> 而是**根本到不了**：那個前置 fatal 拿不到手。X 側每一個 publisher 都在同一口氣裡
> `_exit(127)`（`lorie.h:1414-1416`），renderer 側 14 個 publish 點全在 X 卡於
> `gateAWaitTerminal` 時才觸發。所以每個 X process 只 bump 一次 generation，
> `lorieGateARegistryCloseGeneration`（`cmdentrypoint.cpp:380`）沒有 runtime caller，
> `x-bump-unterminal`（`:391`）與 `x-share-in-lease`（`InitOutput.c:570`）是純防禦碼。
> 旁證（非證明）：`evidence/` 下 201989 行 `GATEA_EVENT`，`generation` 從沒超過 1。
> 「這是產品性質不是測試缺口」這句話仍然成立，而且更強烈地成立。D-06 只記錄不決策。

**超出 R9 的後果：** 這屬於 **D-06**（production lifecycle redesign 範圍）。Production
Gate A 被期望要能存活一般的 Activity lifecycle 事件；如果唯一可達的 generation
boundary 要穿過 fatal，那是 production-lifecycle 的問題，不是 R9 的。**此處記錄，不在此處決定。**

---

## 6.4 V2-R9-FIXTURE 凍結 · JUDGE · HOST-VERIFY — DONE 2026-09-22（commit `6ee3b5c`）

> **[SUPERSEDED 2026-09-22 — 數字全部變了，見 §6.5]**
> `R9_CELL_SPEC_FROZEN_V1` → **V2**；`3 格 + 7 項移除` → **2 格 + 7 項移除**（COLD-2 移入）；
> `28 向量 / device_cells=3` → **32 向量 / device_cells=2**；另加 `test_r9_evidence.py` 36 個測試
> 與 `p_r9_boundary.c`。`spec_sha` 已隨之改變，不要拿下面那個值去比對。
> 現行 commit 是 `3a12e73`，不是 `6ee3b5c`。

`tests/r9/` 新增四個檔，全部 host-only、零 attempt、未動產品：
```
r9-lifecycle-cell-spec.json   規格凍結（R9_CELL_SPEC_FROZEN_V1），3 格 + 7 項移除記錄
judge-r9.py                   R9 judge，verdict 碼與 R8 相同（0/1/2/3）
test-judge-r9.py              28 個向量：3 正 + 25 負，每個負向量只釘一條斷言
verify-r9-support.py          HOST-VERIFY，含 source binding
```

**跑起來的結果：**
```
verify-r9-support.py   R9_SUPPORT_HOST_STATIC_OK   rc=0
test-judge-r9.py       r9_judge_vectors=28 device_cells=3 failures=0
spec_sha  3e7d0da558217f60e70114cfff67b992078cb476e707e945d11d509c56911a1f
judge_sha 10a430ff297e1476a276ef6b00e193d07bdfe69b815c88a53bede7a71bd94567
```

**judge 刻意強制 INVALID / FAIL 的分界（§8.8）：**
```
INVALID  payload 根本沒到達被測路徑 -> 沒有資訊
FAIL     到達了但處理錯 -> 有資訊
```
最重要的一條是 F1 的靜默丟棄陷阱：Gate A 不 active 時 `handleGateARecord` 會在 tuple
檢查**之前**就 return（`cmdentrypoint.cpp:629-631`）。**被丟掉的 frame 不是 pass**，
judge 把它判成 `STALE_FRAME_SILENTLY_DROPPED` / INVALID。

**verify-r9-support.py 的 source binding —— 規格不被信任，要釘回產品 source：**
```
fault 8 / 16 的編號與消費點      fault 8 確實會 PUBLISH（否則 X 走 x-eof，cell 不可構造）
fault 16 確實送出 (nonce-1, generation-1)
兩個 expected fatal token + reason 6
F1 靜默丟棄的程式形狀仍然存在
dispatchExceptionAtReset = DE_RESET 仍是預設（這正是 -noreset 必要的原因；上游若改，
                                          D-01 的推導要重做）
D-02 的 epoch API 與 finalization latch 仍在（否則 R9 根本無法被觀測）
```

**已驗證非空轉：** 三次故意的規格突變（fault 16→15、reason 6→5、刪掉一筆 removal
記錄）各自被**應該抓到它的那條檢查**抓到，還原後回到綠。一個永遠通過的驗證器等於沒有。

**規格本身也帶紅線：** `runtime_authorization` 明文寫 `NOT GRANTED` ——
**規格存在不等於授權執行任何 attempt。**

---

## 6.5 R9 RUNTIME — COMPLETE 2026-09-22（commit `3a12e73`）

```
V2-R9-AGG            evidence/session/gate-a-a1/planning-v2/r9-agg/V2-R9-AGG.md
COLD-2 removal proof planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md
runner V2            evidence/session/gate-a-a1/p2-r9-runtime/run-r9-one-cell-dc94485.sh
fixture              src/f8-ahb-gatea-r7-p1-arm/tests/r9/p_r9_boundary.c
                     binary /tmp/p_r9_boundary (tmpfs; rebuilt after every reboot)
                     cc -O2 -o /tmp/p_r9_boundary tests/r9/p_r9_boundary.c -lxcb -lxcb-render
evidence             p2-r9-runtime/runtime-dc94485/{r9-cold-2,r9-f1,r9-f2}/attempt-*
```

Run a cell (the runner refuses anything else):

```bash
CELL_ID=R9-F1 SERIAL=$(cat /tmp/r9_serial) \
EVIDENCE=$PWD/runtime-dc94485/r9-f1/attempt-NN ./run-r9-one-cell-dc94485.sh
```

`VALIDATE_ONLY=1` exits before `SERIAL` is even read and mutates nothing.

### Verdicts

```
R9-F1  PASS  r9-f1/attempt-03  GATEA_FATAL_HALT what=x-wrong-generation reason=6
R9-F2  PASS  r9-f2/attempt-02  nonce 14133..691 -> 15990..726, registry 0/0,
                               event=5 present, zero halts
```

Every attempt, including the five INVALID ones, is listed with its cause in
`V2-R9-AGG.md`'s attempt ledger, and each frozen attempt directory carries its own
`ATTEMPT-FROZEN-INVALID.md`. None was a product defect and none was reclassified.

### Things in here that will bite the next person

* **The dump sink is LOCAL, not on the device.** X:3 runs in this PRoot rootfs, so
  `gatea-ring.txt` / `gatea-summary.txt` are local paths. Reading them with
  `adb shell cat` silently returns nothing. The R8 runner always used `cp -a`; the
  first R9 runner did not, and every attempt before the fix captured an empty ring.
* **A healthy cell produces no dump at all.** `lorieGateADumpSummary` runs on a fatal,
  a clean close or a terminate. So for R9-F2 there are no `c25`/`c26` counters and no
  `GATEA_SUMMARY` line — that is correct, not a capture failure. The shared tuple
  comes from `GATEA_BIND` (a real acquire load of `state->gateA.sessionNonce`,
  `activity.cpp:202-203`, logged before latching at `:219-220`) and the registry from
  the live `REGISTER_READY`(1) / `UNREGISTER_ACK`(25) events.
* **Do not try to force a dump with SIGTERM.** Measured on `r9-f2/attempt-01`: it does
  not reach `CloseScreen` in this build (no `X_CLOSE_ENTER`, no `Server stopped`,
  no dump) and it fatals the renderer with `r-hup`, which the judge then reads —
  correctly — as `UNEXPECTED_FATAL_IN_FRESH_SESSION`.
* **`snap()` must survive an absent Activity.** `pidof` exits 1 when the process is
  gone and `set -o pipefail` turns that into an aborted run. R9-F1 halts X and the
  Activity goes with it, so "gone" is the expected state at snap-after time.
* **F1 has ONE identity boundary, not two.** Its X halting is the pass, so there is no
  live "after" identity; a second all-None record would make `load_boundaries` refuse
  a correct run.

## 6.6 D-06 DECIDED + R10 REDESIGNED — 2026-09-22

```
D-06 決策        evidence/session/gate-a-a1/planning-v2/d06/D-06-DECISION.md
R10 設計         evidence/session/gate-a-a1/planning-v2/r10-design/V2-R10-DESIGN.md
R10 probe 證據   evidence/session/gate-a-a1/p2-r10-probe/probe-01/   （35 檔，已 hash）
R10 metric 凍結  src/f8-ahb-gatea-r7-p1-arm/tests/r10/r10-probe-inventory.json
R10 取樣器       src/f8-ahb-gatea-r7-p1-arm/tests/r10/r10_sample.py
```

### D-06：V1 不做 generation 2

V1 不實作也不驗證 same-X warm reconnect、Activity replacement while retaining X、
generation 2、cross-generation registry handoff、cross-generation GPU reclamation。
V1 的 recovery model 是 **fresh-process recovery**。

**重點是：這不是政策選擇，是產品目前唯一有的行為。** 新發現（D-06 §2.3）——
`lorieGateAClassifyPeerHup` 的兩個 bound 分支**都** `_exit(127)`
（`lorie_gatea_hup_class.h:28-34`、`activity.cpp:442-447`），所以只要 Gate A 是
bound，X 的 socket 一 HUP，Activity process 就一起死。兩個分支都有實測：
`r9-f1/attempt-03` 的 `GATEA_HUP_PRESERVE` + Zygote `exited cleanly (127)`，
`r9-f2/attempt-01` 的 `what=r-hup reason=6`。

**唯一例外，而且很重要（D-06 §2.4）：** clean close 時 renderer 會
`lorieGateAUnbindTuple`（`renderer.cpp:846`），`gateABound` 歸 0，之後的 HUP 被分類為
`UNBOUND`，**Activity 活下來**。新的 X 可以透過 `CmdEntryPoint` 每秒一次的
`ACTION_START` 廣播重新接上（`CmdEntryPoint.java:125-129` → `MainActivity.java:130-133`
→ `tryConnect` → `:612`）。實測兩次：R8-D attempt-01（renderer 29941 在
`R_UNBOUND_FINAL` 後 2.5 秒仍在跑），以及 2026-09-22 的 probe-01。

那是**新 session，不是 generation 2**：新 X process → 新 nonce → generation 1 →
空 registry，完全不需要改產品。它之所以重要，是因為 **Activity process 活得比 session 久**，
所以任何沒在 clean close 釋放掉的東西，會在使用者永遠不會重開的 process 裡累積。
R10-B 就是為這件事設計的。

### R10 重建成三個模式

```
R10-A  單一 session 內，workload 跑 N 次 —— 一次 workload 有沒有留下東西
R10-B  一個存活的 Activity + >=5 個連續 clean session —— 一個 session 有沒有留下東西
       （= 計畫書 §8.4 的 WARM，正確地重新界定）
R10-C  >=5 次完整冷啟 + F/H 結尾各一輪 —— 系統殘留與「有沒有繼承舊 session 狀態」
```

`V2-R10-NOISE` 必須在任何受判 round 之前跑完並凍結 tolerance。

### probe-01 三個會改變設計的實測

1. **64×64 的 pair 量不到。** 一對約 32 KB，而 Activity 的 `egl_mtrack` 在 workload
   完全相同的情況下擺動 ~35 MB、PSS 擺動 ~1.4 MB。R8/R9 的 workload 比雜訊低兩三個
   數量級。R10 改用 4 對 1024×1024。
2. **看起來像 leak 的東西不是 leak。** `activity.fd_count` 連續五個取樣每次 +1、
   `gfx_dev` 每次 +8 KB，第六次全部被回收（fd 210→175）。系列跑不完就下 leak 結論會錯。
3. **Activity 的 `/proc` 要用 `run-as`。** 一般 `adb shell` 讀 fd / maps /
   smaps_rollup 是 Permission denied 或空白。而且 **絕對不能配 shell redirect**：
   `run-as p wc -l < /proc/X/maps` 是外層 shell 在解析，會回空字串卻看起來像讀到了。

### clean close 的正確形狀（probe-01 實測）

```
GATEA_SUMMARY where=x-close-screen nonce=0 generation=0 generationFatal=0
  c12/c13 AHB      16/16      c14/c15 EGLImage 16/16    c16/c17 texture 16/16
  c18 X registry 0   c19 renderer registry 0   c20 lease 0   c27 close 1
```

**注意 counter 索引**：`c18`/`c19` 才是 registry-current，`c25`/`c26` 是
UNREGISTER / RESOURCE_DESTROY。工具原本讀錯（已於 `b68770f` 修正並加靜態檢查）；
用舊的讀法，上面這個完全乾淨的 close 會被讀成「16 個 entry 沒釋放」。

## 6.7 R10 COMPLETE — 2026-09-22（commit `4de9e33`）

```
彙總      evidence/session/gate-a-a1/planning-v2/r10-agg/V2-R10-AGG.md
runner    evidence/session/gate-a-a1/p2-r10-runtime/run-r10.sh
證據      evidence/session/gate-a-a1/p2-r10-runtime/runtime-dc94485/
          noise-01 · r10-a-01 · r10-b-01 · r10-c-01 · r10-e-01(INVALID) · r10-e-02
tolerance src/f8-ahb-gatea-r7-p1-arm/tests/r10/r10-tolerance.json  （先凍結後判）
```

```bash
MODE=B ROUNDS=5 SERIAL=$(cat /tmp/r9_serial) \
EVIDENCE=$PWD/runtime-dc94485/r10-b-02 ./run-r10.sh
```

### 結果

```
R10-A  單 session 5 次 workload           PASS   每次 registry 0/0、lease 0、event=5 x8
R10-B  一個存活 Activity + 5 個 session    PASS   同一個 pid 25809 撐完 5 個 session
R10-C  5 次完整冷啟                        PASS   5 個不同 pid、5 個不同 nonce
R10-E  F / H 兩種非乾淨結尾 + fresh        PASS   兩種結尾都讓兩個 process 一起死
所有 session generation 都是 1 —— D-06 在 runtime 被強制檢查，不是假設
```

### 三個要記住的事

1. **counter 索引錯了會製造假 leak。** 15 次 clean close 每次都是
   `AHB 8/8 · EGLImage 8/8 · texture 8/8 · registry 0/0 · lease 0`。若用舊的
   c25/c26 讀法，這 15 次全部會被讀成「每邊漏 8 個」。`b68770f` 已修並加靜態檢查。
2. **memory 類指標很弱，不要拿它當結論。** 凍結出來的 idle 雜訊帶是
   `x.pss_kb` ~17 MB、`activity.pss_kb` ~21 MB、`vm_size_kb` ~728 MB，
   而 workload 一次才配 ~32 MB。R10 的正確性結論靠的是 **counter（精確）**
   與 **fd / maps 計數**（帶寬 1 / 8 / 2）。
3. **F / H 結尾不能拿來算 leak。** 它們照設計就不釋放任何東西——process 帶著資源死掉、
   由 OS 回收。E1 死的時候 registry 還掛著 2/2，那是結尾的定義，不是漏。
   judge 對 mode E 直接早退，vector E02 釘住這件事。

### 帶走的發現（D-04）

`activity.maps_count` 跨 session 持續上飄：B@B3 +10、C@B3 +22、C@B0 +13，
而 idle 帶寬只有 2。不算 LEAK（序列中間有回落，不是嚴格遞增），但方向一致、
幅度是雜訊的 5–10 倍。**不是 Gate A 記帳問題**：同幾輪的 counter 都精確平衡，
而且 R10-C 每輪 process 全新也照樣飄，所以不可能是長壽 Activity 的累積。
判斷：**不是 V1 blocker**（每 session 約 2–4 個 mapping、無 counter 失衡、無 fd 成長、
無 PSS 趨勢），但留給 D-04。要收斂的話：跑 20+ session 的長序列 + `/proc/<pid>/maps` 差分。

## 6.8 P2 CLOSURE 進行中 — GAP-4 與三項 carry-forward 已關 — 2026-09-23

```
報告   evidence/session/gate-a-a1/planning-v2/p2-closure/GAP-4-TOUCHED-SYMBOLS.md
工具   src/f8-ahb-gatea-r7-p1-arm/tests/p2/{p2_scan,touched_symbols,verify_r7_predicates}.py
```

### 掃描先推翻了問題本身

`CF-PENDING-001` 寫「R7 13/13 取得於 `a4c8177`」——**證據不是這樣**。13 格分散在
**四個** artifact：`a07d66c`(9)、`8545b26`(1)、`a4c8177`(2)、`fdfb1ce`(1)，
而其中三個本身就是 Gate A fatal 語意的修復 commit。R7 是**沿著修復鏈**被 qualify 的，
不是在鏈上某一點。只問 `a4c8177 → b984ded` 會讓十一格建立在從未涵蓋它們的前提上。

### 兩段 diff 的逐行判讀

```
a4c8177 → b984ded   production 語意變更 = 0
                    全部是保留回傳值的重構、前向宣告、唯讀 getter，
                    以及 notifyGpuCopyDoneCause（guard 外的 body 與舊版逐字相同）
b984ded → dc94485   production 語意變更 = 1
                    Q4-F1 的 gateAMappedState = NULL（修 use-after-unmap，兩條 unmap 路徑）
                    Q6-F1 只是把同 5 行往前移，算出來的值不變
                    runFinalize 要 arm 了 test fault 才可達
```

### 工具第一版是錯的，而且錯得剛好會放過

`verify_r7_predicates` 第一版對 R7 全部回 INTACT，**同時**對 cell 14
`x-destroy-in-lease` 也回 INTACT——那正是 token 被移進 `#else` 的唯一案例。
**不會失敗的對照組不是對照組**，所以那批結果不能用。

原因：`guard_map` 回答「這行是不是寫在 guard 裡」，而它把 `#else` 正確地判為不在
guard 內。但 experimental APK 是 `-DLORIE_ENABLE_R8_TEST_SUPPORT=ON` 編的
（`lorie/build.gradle:41`），在那個編譯下 `#else` **根本不會被編進去**——
predicate 檢查要問的是相反的問題。加了 `compiled_map(guard_on=True)` 之後，
cell 14 變成 `sites=2 (live 1)`：`InitOutput.c:3434` 在 source 裡但不在 binary 裡，
`:3911` 才是活的。**§3 的所有結論都是修正後重新推導的**，錯誤版本刻意保留在 audit trail。

### 裁決（我依授權直接簽）

```
CF-PENDING-001  R7 → dc94485    CARRY_FORWARD，13/13 predicate intact
                                其中 4 個已在 dc94485 實機重現：
                                  cell 8  r-test-fatal-pre-fence r6  ← R10-E1 同一個 fault
                                  cell 9  x-wrong-generation r6      ← R9-F1
                                  cell 10/13 x-hup r6                ← R9/R10 corpus
CF-PENDING-002  R0–R6 → dc94485 CARRY_FORWARD + peer-HUP 路徑 REVERIFY
                                該 REVERIFY 已由 R10-E2（r-hup）與 R9-F1
                                （GATEA_HUP_PRESERVE）在 dc94485 上滿足，不需新跑
R8 b984ded→dc94485              CARRY_FORWARD。claim scope 原樣帶走：
                                10/10 是在**沒有 -noreset** 下跑的，不含
                                same-process DE_RESET continuity，不可與 R9/R10 混判
```

**注意：`p2_runtime_closed` 仍是 false。** 上面只關掉三個 carry-forward 項，
17 項 ledger 的其餘部分還沒做。

## 7. Redlines still in force

```
Stable com.termux.x11 :1 is never touched. Experimental APKs only in com.waydefu.x11gpu.
Isolated adb on 5038 only. 5037 is never killed or reused.
Kill experimental X only by exact cmdline prefix 'termux-x11gpu com.waydefu.x11gpu :3'.
Never `pkill -f f8-x11gpu`. Never `logcat -c`.
X3_PRECHECK must use the runner's x3pid() form (walk /proc and compare the cmdline
  prefix). A bare `pgrep -f '...:3'` matches the operator's OWN shell and false-BLOCKs.
EPHEMERAL values (SERIAL, Stable PID, endpoints) are discovered at runtime. The plan's
  snapshot values are report-only and WILL be stale.
Frozen attempts and their classifiers are never reclassified or diluted (§5.1).
```

## 8. Known-open, carried forward

```
GAP-4  CLOSED 2026-09-23 — 見 §6.8。連帶 CF-PENDING-001 / CF-PENDING-002 一併關閉。
       注意原始描述有誤：R7 不是只在 a4c8177，而是分散在四個 artifact。
GAP-8  PRODUCT defect: ProcLorieR8Checkpoint emits a duplicate "phase" key, and
       total_actual_buffer_pending is hardcoded null. Both contained tooling-side;
       product deliberately NOT rebuilt (§13.4 chain cost). Evidence recorded.
R-28   CLOSED — TOOLING_COMMIT 2a14ab2 is now on a remote.
D-06   FED, not decided. Two inputs now on the record:
       (a) Gate A has NO reachable generation boundary at all. The bump runs once per
           X process and a second is unreachable, so lorieGateARegistryCloseGeneration
           (cmdentrypoint.cpp:380) has no runtime caller and x-bump-unterminal (:391)
           and x-share-in-lease (InitOutput.c:570) are defensive-only.
           Proof: planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md §C-§E.
       (b) the READY GL objects have no teardown outside UNREGISTER and the EGL
           context never turns over, so only process death reclaims them (Q4-F2, Q5).
       R9-F2 shows the NEXT process starts clean; it does NOT show the previous one
       released anything.
D-04   OPEN — resource leak disposition. R10 delivered no leak, with ONE item
       attached: activity.maps_count drifts upward across sessions (+10 to +22 over
       5 rounds, idle band 2). Not a Gate A accounting failure. See V2-R10-AGG §5.
R-30   OPEN — the three ahb_*_fence_fd metrics (plan §9.4, from V-5) have NO trace
       site in dc94485. Frozen null in r10-probe-inventory.json so the gap stays
       visible. R10 cannot answer the fence-fd ownership question without a product
       change, which is a D-12-class decision R10 does not make.
R-29   OPEN — the six removed R9 cells are not "done", they are unreachable in THIS
       product. Reopen WARM-1/2/3 and COLD-2 if a warm reconnect/rebind entry point
       is added; reopen COLD-1/3 and COLD-2 if a renderer fatal publisher appears
       that is reachable OUTSIDE an X terminal wait. verify-r9-support.py pins the
       source facts, so the host gate goes red when either becomes true.
```
