# Gate A P2 R6 Present GPU-copy 安全退役：實作與驗收計畫

日期：2026-09-15  
狀態：**PLAN ONLY / HOLD**  
基準分支：`qualification/gatea-r6-20260915`  
基準 commit：`95e6f9602b0146ee190870f84a34aad822ef666f`  
計畫用途：交給下一位實作者逐階段執行。  

> 本文件不是來源修改、commit、push、CI、安裝或裝置測試授權。任何階段都必須先確認使用者已明確批准該階段。新發現的 ownership／lifecycle 問題會撤銷舊有「直接跑 D2-OOM」建議。

---

## 0. 一頁摘要

### 0.1 已證明

- `95e6f96` 已補上 renderer legacy-completion telemetry。
- post-schedule `queue_vblank` 失敗分支已使用 bounded wait（有界等待）後才 ACK。
- 五個 `runtime-95e6f96/r6-d2-inflight*` cell 都觀測到 Present completion cover 先於 Composite admission；缺少 reason-1 reject 是 fixture 沒有維持 busy overlap，不是產品錯誤的證據。
- Host judge 目前 25 tests PASS、binding negative tests PASS、static verifier PASS。

### 0.2 尚未證明／已找到的新 HIGH

- `present_execute.c` 的 already-pending requeue failure／renderer-loss 路徑仍可 completion 前 ACK。
- `present_vblank_scrap()` 與 `present_vblank_destroy()` 仍會無條件 ACK pending GPU copy，然後 idle 或 drop pixmap。
- 現行 D2-OOM hook 只覆蓋 post-schedule 分支；在 `95e6f96` 上跑 PASS 也不能封閉上述其他路徑。
- D1 只在 `9369553` historical artifact PASS；現行設計仍要求 D1、D2-INFLIGHT、D2-OOM 在同一 APK。
- timeout／renderer-loss fail-stop 尚未有 runtime qualification；R7 仍禁止啟動。

### 0.3 推薦路徑

1. **先取得 source/lifecycle 與 oracle 變更批准。**
2. 在 `95e6f96` 的新 linked worktree 建立單一安全 retirement helper。
3. 所有 ACK／pending--／release 只能從該 helper 發生。
4. 先寫 RED host tests，再改 C，直到 GREEN。
5. 將 D2-INFLIGHT 改為 busy-reject 與 quiescent-admit 雙分支 oracle。
6. local static + ARM64 incremental + full-clean 全過後建立新 commit。
7. 停下來取得 fork push／CI 授權。
8. 新 artifact qualified 後，再取得 install／device 授權。
9. 新 APK 上依序跑一格 D1、一格 D2-INFLIGHT、一格 D2-OOM；每格失敗即停。
10. 不開 R7、不碰 Stable、不開 PR、不 merge、不 push origin。

---

## 1. Authority 與固定邊界

### 1.1 每次開始都要依序重讀

1. `/root/projects/GPU加速/AGENTS.md`
2. `/root/projects/GPU加速/HANDOFF.md`
3. `/root/projects/GPU加速/TEST-MATRIX.md`
4. `evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md`
5. `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-DESIGN-20260915.md`
6. `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-D2-HOLD-20260915.md`
7. `evidence/session/gate-a-a1/p2-r6-design/GATE-A-P2-R6-D2-INFLIGHT-PHYSICAL-RACE-ANALYSIS-20260915.md`
8. `.cursor/skills/gate-a-r6-design-review/SKILL.md`
9. `.cursor/skills/gate-a-r6-present-retirement-implementation/SKILL.md`
10. `.cursor/skills/gate-a-r6-design-review/references/R6-D2-REVIEW-20260915.md`
11. `/root/.serena/memories/global/f8-workstation.md`

如 authority 與本計畫衝突，以 authority 與使用者最新明確授權為準；停止，不自行調和。

### 1.2 永久禁止／本計畫不包含

- 不碰 `com.termux.x11` Stable 或 display `:1`。
- 不修改 frozen worktrees：
  - `src/f8-ahb-gatea-a1`
  - `src/f8-ahb-gatea-xpump`
  - `src/f8-ahb-gatea-r5-fix`
- 不覆寫任何既有 `runtime-*` cell。
- 不在 `runtime-9369553` 或 `runtime-95e6f96` 新增結果。
- 不 silent retry。
- 不開 R7–R10、Stable、HDMI、Production enable。
- 不開 PR、不 merge、不 push origin、不 force push。
- 不改 queue ABI、P0 sideband、fence semantics、direct predicate、BGRA/RGBX contract。
- 不新增 runtime dependency。
- 不用 renderer delay、sleep 或放大工作量來「製造」reason-1 reject。
- 不把 exact pixels、CLIENT_OK 或 X alive 當作 ownership completion 證據。

### 1.3 Agent 使用限制

- 寫入階段：**ONE WRITER = ONE CURSOR LUNA SESSION = ONE LINKED WORKTREE**。
- Cursor workspace 保持 `/root/projects/GPU加速`，讓 `.cursor/skills/`、writer worktree 與 host evidence 同時可見。
- 實作者先載入 `.cursor/skills/gate-a-r6-present-retirement-implementation/SKILL.md`；不得啟動 Hermes CLI 或其他子代理。
- linked worktree 由 parent／owner 先建立；Cursor Luna 不得再建立第二個 worktree。
- Cursor Luna 完成 RED→GREEN、host gates 與 local builds 後停在 **uncommitted diff**。
- parent 在 Luna 退出後親自複核；只有 parent 可決定 commit。
- 子代理永遠不能做最終 architecture authorization。

---

## 2. 基準狀態與驗收綁定

開始前記錄，不可憑記憶：

```bash
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6 status -sb
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6 rev-parse HEAD
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6 diff --check
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6 log -5 --oneline --decorate
```

必要結果：

```text
branch = qualification/gatea-r6-20260915
HEAD = 95e6f9602b0146ee190870f84a34aad822ef666f
parent worktree tracked files clean
git diff --check exit 0
```

另記錄 xserver submodule：

```bash
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6 submodule status lorie/src/main/cpp/xserver
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6/lorie/src/main/cpp/xserver status --short
```

目前 live submodule 的修改是 parent `xserver.patch` 套用後的預期狀態；不能把它誤判為 scout 污染，也不能用 `reset --hard` 清理。

### 2.1 Environment Matrix

實作者必須在 evidence 記錄：

| 維度 | 必填內容 |
|---|---|
| Host | OS、architecture、PRoot／native、kernel |
| Toolchain | JDK、Gradle、Android NDK/CMake、clang 版本 |
| Local build | incremental 與 full-clean command、exit code、warning fingerprint |
| CI | run ID、head SHA、artifact name、runner OS |
| Device | package、versionName、APK hash、Build ID、ABI、display target |
| Runtime | exact `runtime-<sha>/cell`、fixture source/ELF hash、X PID |
| Stable | package/version/PID before and after；必須 untouched |

不要讀取或輸出任何 token、認證檔或秘密。

---

## 3. Root cause 與安全不變式

### 3.1 現有 unsafe callsites

#### A. already-pending requeue／renderer loss

`src/f8-ahb-gatea-r6/lorie/src/main/cpp/xserver/present/present_execute.c:93-109`

目前如果 `gpu_copy_pending` 且尚未完成：

- `queue_vblank()` 成功才保留 pending；
- requeue 失敗或 renderer stalled 時會進入 raw `lorieGpuCopyAck()`；
- 隨後可能 `present_vblank_scrap()`、`present_pixmap_idle()`。

#### B. scrap

`.../present/present_vblank.c:183-206`

`present_vblank_scrap()` 目前無條件 ACK pending copy，然後 idle、destroy pixmap reference。

#### C. destroy

`.../present/present_vblank.c:208-248`

`present_vblank_destroy()` 目前無條件 ACK pending copy，然後 drop pixmap、regions、fences 和 vblank。

#### D. callers

至少包含：

- `present_execute_post()`
- window destruction：`present_screen.c:71-82`
- queued present scrap：`present_scmd.c` callers
- completion／renderer-loss recheck：`present_scmd.c:255-267`
- Present abort／close／teardown paths

實作者必須再次用 symbol/reference navigation 列舉全部 callers；不得只處理 A–C 三個已知位置。

### 3.2 強制不變式

一旦 `lorieTryScheduleGpuCopy()` 成功並取得 pending count／extra references：

```text
completedSerial < S
→ 不得 ACK
→ 不得 pending--
→ 不得 release src/dst extra references
→ 不得 present_pixmap_idle
→ 不得 scrap/destroy/drop pixmap
→ 不得通知 client 可安全重用
```

唯一成功退役順序：

```text
schedule serial=S
→ pending/ref protection active
→ completedSerial >= S
→ ACK
→ pending-- / ref release
→ pending flag clear
→ idle / scrap / destroy / CPU reuse
```

不確定失敗順序：

```text
timeout 或 renderer loss/HUP
→ fatal fail-stop
→ 不 ACK
→ 不 pending--
→ 不 release
→ 不 idle
→ 不 ordinary teardown return
```

### 3.3 Teardown 前置證明

在將 helper 放入 destructor 前，必須證明：

1. `pvfb` 與 `pvfb->state` 在所有 pending-vblank destroy callers 執行時仍有效。
2. `lorieCloseScreen()` 的 `gateACloseGeneration()` drain 在 underlying Present close 前執行。
3. `pScreenPtr = NULL` 不會破壞 `lorieGpuCopyIsDone()`、wait wrapper 或 ACK 所需狀態。
4. `vblank->pixmap` 與 `gpu_copy_dst_buffer` 在 helper 執行前仍持有有效 refs。
5. 若上述任一條不成立，不得直接加 null fallback 後釋放；回報 architecture decision。

驗收證據：列出 `lorieCloseScreen`、`present_close_screen`、`present_destroy_window`、`present_free_window_vblank`、`present_vblank_destroy` 的呼叫順序與 `path:line`。

---

## 4. 目標架構

### 4.1 單一 retirement helper

推薦在 `present_vblank.c` 實作並於 `present_priv.h` 宣告：

```text
present_gpu_copy_retire_or_fatal(present_vblank_ptr vblank)
```

語義，不是可自行改寫的建議：

1. `vblank == NULL` 是 programming error；不得靜默成功。
2. `gpu_copy_pending == FALSE`：no-op。
3. `gpu_copy_serial == 0` 或持有欄位不一致：protocol fatal，不釋放。
4. 尚未完成：只呼叫 `lorieGpuCopyWaitForPresentOrFatal(serial)`。
5. wrapper 只有 completion 已成立才可返回。
6. 返回後再呼叫唯一的 `lorieGpuCopyAck()`。
7. 接著設定：
   - `gpu_copy_pending = FALSE`
   - `gpu_copy_dst_buffer = NULL`
   - 視 caller 是否仍需 trace serial，決定何時清除 `gpu_copy_serial`；不得在 trace 前丟失 S。
8. helper 不呼叫 `present_pixmap_idle()`、scrap 或 destroy；caller 只能在 helper 成功返回後做這些事。

### 4.2 Raw release 單點化

`xserver/present/` 下：

- `lorieGpuCopyAck()` 的 function call 只能剩 helper 內一個。
- `gpu_copy_pending = FALSE` 的 terminal transition 只能由 helper 完成；初始化除外。
- `present_vblank_scrap()` 與 `present_vblank_destroy()` 必須先呼叫 helper，再 idle/drop。
- raw wait API 不 export；只保留 fail-stop wrapper。

### 4.3 Schedule 後立即建立 ownership state

`lorieTryScheduleGpuCopy()` 成功後，立即將 vblank 設為 pending，再嘗試 requeue：

```text
schedule success
→ vblank serial/dst_buffer 已填
→ gpu_copy_pending = TRUE
→ callback/damage bookkeeping
→ queue_vblank
```

不得等 requeue 成功才設 pending，因 pending/ref 已經在 `lorieTryScheduleGpuCopy()` 內取得。

### 4.4 already-pending 路徑

建議狀態機：

```text
pending && done
→ retire helper（不等待）
→ normal Present completion

pending && !done && renderer healthy && requeue success
→ keep pending
→ return queued

pending && !done && (requeue failure || renderer unavailable)
→ trace requeue/retirement failure context
→ retire helper
   → completion arrives：ACK and continue
   → timeout/loss：fatal, never returns
```

刪除「renderer stalled 時先 ACK 再 scrap」行為。

### 4.5 post-schedule requeue-fail 路徑

保持現有 telemetry ordering，但改用集中 helper：

```text
Present CALLBACK(S,G)
< PRESENT_REQUEUE_FAILED(S,G,dst)
completion cover 可在 marker 前或後發生
max(REQUEUE_FAILED, COMPLETED cover)
< helper ACK
< PRESENT_ACK_AFTER_COMPLETED(S,G,dst)
< idle / later request
```

event 32 `PRESENT_EARLY_ACK` 保持 frozen forbidden，不移除 enum、不改號碼、不重新利用。

### 4.6 不採用的方案

- 不靠 admission predicate 保護已提前釋放的 refs：它救不回 ownership。
- 不在 timeout 時 scrap/fallback：這仍會交還不確定資源。
- 不加入 deferred retirement queue：目前變更面較大，除非集中 bounded wait 被實證不可行才重新提案。
- 不加 renderer artificial delay：它只改 timing，不證明產品 invariant。
- 不用 `sleep()` 假造 busy reject。

---

## 5. 分階段實作

## Gate 0 — 取得明確批准

開始 source mutation 前，確認使用者明確批准兩件事：

1. Present ownership/lifecycle C 修正。
2. D2-INFLIGHT 從 reject-only 改為雙分支 oracle。

建議批准文字：

```text
批准由 parent 在 95e6f96 上建立隔離 worktree，交給一個 Cursor Luna
session 實作集中 Present GPU-copy retirement-or-fatal，並更新 host
oracle/tests/docs。Luna 完成 RED→GREEN、host gates 與 local builds 後停在
未提交 diff，由 parent 複核；不批准 commit、push、CI、install、ADB、
device cell、R7、PR、merge、origin push。
```

沒有此文字或等價明確批准：停止於本計畫。

---

## Gate 1 — 建立隔離 writer worktree

只在 Gate 0 批准後執行。

推薦：

```bash
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6 worktree add \
  -b fix/gatea-r6-present-retirement-20260915 \
  /root/projects/GPU加速/src/f8-ahb-gatea-r6-retire \
  95e6f9602b0146ee190870f84a34aad822ef666f
```

開始寫入前驗證：

```bash
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6-retire rev-parse HEAD
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6-retire status --short
git -C /root/projects/GPU加速/src/f8-ahb-gatea-r6-retire branch --show-current
```

Acceptance criteria：

- exact base `95e6f9602b0146ee190870f84a34aad822ef666f`
- branch exact `fix/gatea-r6-present-retirement-20260915`
- tracked status clean
- 原 `src/f8-ahb-gatea-r6` 保持不變

---

## Gate 2 — 基線測試

先跑現有 host gates；記錄完整 command、exit code 和輸出，不只寫「PASS」。

```bash
cd /root/projects/GPU加速
PYTHONDONTWRITEBYTECODE=1 python3 \
  evidence/session/gate-a-a1/p2-r3-xpump-runtime/test-judge-r6-design.py
bash evidence/session/gate-a-a1/p2-r3-xpump-runtime/test-r6-design-bind.sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  evidence/session/gate-a-a1/p2-r6-design/verify_r6_design_impl.py \
  src/f8-ahb-gatea-r6-retire
bash -n \
  evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r6-design.sh \
  evidence/session/gate-a-a1/p2-r3-xpump-runtime/r6-design-bind.sh \
  evidence/session/gate-a-a1/p2-r3-xpump-runtime/test-r6-design-bind.sh
```

基準預期：

- judge 25 tests PASS
- `BIND_NEG=PASS`
- `R6_DESIGN_IMPL=PASS`
- shell syntax exit 0

如基線不符，先停止分類；不得把既有 failure 算成新修正成果。

---

## Gate 3 — RED：先寫會抓到漏洞的測試

### 3.1 新增 source-structure regression test

推薦檔案：

```text
evidence/session/gate-a-a1/p2-r6-design/test-present-gpu-copy-retirement.py
```

它必須直接讀 exact worktree 的真實 source，不複製 production 條件。至少包含：

1. `present/present_execute.c`、`present_vblank.c` 內 raw `lorieGpuCopyAck(` callsite 合計只能一個，且位於集中 helper。
2. `present_vblank_scrap()` 在 `present_pixmap_idle()` 前呼叫 helper。
3. `present_vblank_destroy()` 在 `dixDestroyPixmap()`／free 前呼叫 helper。
4. already-pending requeue failure 不可直接 ACK／scrap。
5. renderer-stalled 且 serial 未完成不可走普通 return。
6. post-schedule path 先設 `gpu_copy_pending=TRUE`，再可能 requeue／retire。
7. helper 的 source order 必須是 done-check／wait → ACK → clear pending。
8. wrapper 仍是 2000 ms bounded wait、不可 pump X clients、timeout/loss 進 noreturn fatal。
9. event 32 沒有任何 runtime callsite；prototype/enum/文字可存在。
10. `present_scmd.c::lorieRecheckGpuCopies` 的 loss 路徑最終會進 helper/fatal，而非 release。
11. teardown ordering 的必要 symbol 仍存在；如果無法靜態證明，測試輸出明確標記為需人工 source review，不可假 PASS。

### 3.2 驗證 RED

在未改 C 的 `95e6f96` 基線執行。測試必須因下列真實缺陷而 FAIL：

```text
raw ACK in present_execute pending path
raw ACK in present_vblank_scrap
raw ACK in present_vblank_destroy
```

要求：

- exit code 非 0
- failure label 精確對應上述 callsites
- 不是 syntax error、path typo 或 test crash
- 保存 RED command、exit code、labels 到 implementation evidence

測試若一開始就 PASS，表示測錯東西；先修 test，不得進 GREEN。

### 3.3 Judge 的 RED cases

先擴充 `test-judge-r6-design.py`，至少新增：

- `test_inflight_quiescent_cover_before_lease_passes`：目前應因 missing reject 而 RED。
- `test_inflight_lease_before_cover_fails`。
- `test_inflight_callback_without_reject_or_direct_lifecycle_fails`。
- `test_inflight_quiescent_wrong_destination_success_fails`。
- `test_inflight_quiescent_wrong_generation_cover_fails`。
- `test_inflight_busy_reject_path_still_passes`。
- `test_inflight_quiescent_pixels_only_fails`。
- `test_inflight_unrelated_completion_does_not_authorize_lease`。
- `test_inflight_cover_after_callback_but_before_lease_passes`：合法 inter-thread boundary。

至少第一個新正向 case 必須在 judge 改動前正確 RED。

---

## Gate 4 — GREEN：最小 C 修正

### 4.1 允許修改的 source files

預期只碰：

```text
lorie/src/main/cpp/xserver/present/present_execute.c
lorie/src/main/cpp/xserver/present/present_vblank.c
lorie/src/main/cpp/xserver/present/present_priv.h
lorie/src/main/cpp/patches/xserver.patch
```

只有在證明必要時才碰：

```text
lorie/src/main/cpp/lorie/InitOutput.c
lorie/src/main/cpp/lorie/lorie.h
```

如果需要改 renderer、fence semantics、queue ABI、buffer ownership representation 或新增 event，立即停止並回報 architecture decision；不擴 scope。

### 4.2 實作順序

1. 在 `present_priv.h` 宣告集中 helper。
2. 在 `present_vblank.c` 實作 helper。
3. 先讓 scrap/destroy 使用 helper。
4. 執行單一 source regression test，確認這一垂直 slice 從 RED 變 GREEN；其他未完成 case可保持 RED。
5. 重構 `present_execute.c` already-pending state machine。
6. schedule success 後立即設定 pending。
7. post-schedule branch 改用 helper，保存 trace 所需 serial/dst identity 後才清欄位。
8. 移除所有 helper 外 raw ACK。
9. 更新 live xserver patch；不得手工讓 live files 與 `xserver.patch` 分叉。
10. 每一個垂直 slice 都跑對應 test，禁止累積全部修改後才第一次驗證。

### 4.3 Helper 細節檢查

- `lorieGpuCopyIsDone()` 目前 dereference `pvfb->state`；先完成 teardown ordering proof。
- 不用 catch-all 或 null-return 把不一致狀態吞掉。
- 不能在 wait 前清 pending 或 stored buffer pointer。
- 不能在 ACK 後 dereference 可能失去最後 ref 的 opaque buffer。
- 若 telemetry 需要 destination ID，必須在 ACK 前取得，或使用有 ref 保護的既有 pixmap identity；不得新增未受保護指標。
- helper 成功後清除 stale pointer，避免 double ACK。
- helper 重入／二次呼叫必須因 pending=false no-op，不可二次 decrement。
- fatal wrapper 若返回，必須能由 source contract 證明 `completedSerial >= S`。

### 4.4 xserver.patch 一致性

建置權威是 parent patch，不是只改 live submodule。完成 live source 後：

1. 由 submodule exact HEAD `65d790bd208ec380b196eb98f144abb0b32e334d` 的完整 diff 重新產生 `lorie/src/main/cpp/patches/xserver.patch`。
2. `git diff --check` live submodule與 parent都通過。
3. 建立獨立暫存 checkout／worktree，從 clean submodule HEAD 套 patch。
4. 套用 exit 0，套用後 diff 必須與 writer live submodule byte-equivalent。
5. 不使用 `reset --hard` 驗證。

---

## Gate 5 — 修正雙分支 D2-INFLIGHT oracle

這是明確批准過的 validation change，不是「讓 fail 變 pass」。

### 5.1 共同前提

兩個分支都必須：

- telemetry `seq` 唯一、連續；缺 prefix／gap 必須由 authority ring 補齊，否則 FAIL。
- Present REQUEST/CALLBACK 同 client sequence。
- completion cover：renderer role、同 generation、`serial >= S`。
- target buffer pair／destination 正確。
- fixture exit 0、exact pixels。
- 無 fatal、firstFailed、X death、watchdog。
- event 32 出現即 FAIL。

### 5.2 Busy-reject 分支

```text
Present CALLBACK(S,G)
< immediate Composite REQUEST/CALLBACK
< DIRECT_ADMIT_REJECT reason=1
< completion cover(T>=S,G,RENDERER)
< later target direct LEASE/PUBLISH/COMPLETED/SUCCESS
```

要求 cover 前沒有 target direct lease/publish/success。

### 5.3 Quiescent-admit 分支

```text
Present CALLBACK(S,G)
< immediate Composite REQUEST/CALLBACK
completion cover(T>=S,G,RENDERER)
< first target direct LEASE_RESERVED
< PUBLISH
< direct COMPLETED
< SEMANTIC_SUCCESS
```

Completion 可以發生在 Composite callback 前，或 callback 後、lease 前；兩者都合法。唯一安全界線是：

```text
cover.seq < first_target_lease.seq
```

不能只用 callback 判定 admission；callback 同時涵蓋 direct 或 legacy path。

### 5.4 必須 FAIL 的反例

- `lease < completion cover`
- `publish < completion cover`
- 沒 reject，也沒有完整 direct lifecycle
- completion wrong role／generation
- completion 只覆蓋 unrelated serial
- SUCCESS wrong destination／pair
- software fallback pixels-only
- unrelated later SUCCESS
- missing event sequence

### 5.5 歷史證據處理

- 不修改五個既有 cell 內容與原始 FAIL 文件。
- 新增 dated adjudication，說明原 reject-only oracle 造成 construction false-red。
- 不把「五格無 crash」改寫成所有 ownership paths PASS。
- 將 physical-race 文件的 `<0.5 ms`、固定 CPU latency、throughput 與「100% sound」降為不受證據支持的推測；保留 protocol sequence 所證明的 ordering。

---

## Gate 6 — Host GREEN 與 source audit

### 6.1 必跑命令

```bash
cd /root/projects/GPU加速
PYTHONDONTWRITEBYTECODE=1 python3 \
  evidence/session/gate-a-a1/p2-r6-design/test-present-gpu-copy-retirement.py \
  src/f8-ahb-gatea-r6-retire
PYTHONDONTWRITEBYTECODE=1 python3 \
  evidence/session/gate-a-a1/p2-r3-xpump-runtime/test-judge-r6-design.py
bash evidence/session/gate-a-a1/p2-r3-xpump-runtime/test-r6-design-bind.sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  evidence/session/gate-a-a1/p2-r6-design/verify_r6_design_impl.py \
  src/f8-ahb-gatea-r6-retire
```

### 6.2 機械式 callsite audit

必須列出而不是只看 count：

```text
lorieGpuCopyAck(
gpu_copy_pending = FALSE
present_pixmap_idle(
present_vblank_scrap(
present_vblank_destroy(
dixDestroyPixmap(
LorieBuffer_release(
LorieBuffer_gpuCopyPendingDec(
```

Acceptance criteria：

- xserver Present raw ACK call只剩集中 helper一個。
- 沒有 pending copy 可繞過 helper到 idle/scrap/destroy。
- timeout/loss path沒有正常 return或 cleanup。
- helper內 order是 wait/done proof → ACK → clear state。
- live xserver diff與parent patch一致。

### 6.3 Judge suite

- 原25 tests仍全部PASS。
- 新雙分支與負向tests全部PASS。
- historical `9369553` D1 PASS fixture仍PASS。
- historical D2 FAIL fixture不得因寬鬆條件意外PASS；若它代表舊 artifact缺completion，仍應FAIL。

### 6.4 Fixture

更新 `patches/p_r6_d2_present.c` 的錯誤註解：pipelining 只形成 race，**不保證 reject**。

以 warnings-as-errors 編譯實際 fixture：

```bash
cc -O2 -Wall -Wextra -Werror \
  -o /tmp/p_r6_d2_present \
  /root/projects/GPU加速/patches/p_r6_d2_present.c \
  -lxcb -lxcb-render -lxcb-present
```

記錄 source SHA256、ELF SHA256、compiler version與完整 command。新 runtime cell 必須保存 source snapshot或精確 committed source identity，不能只留一個無法重建的 ELF hash。

---

## Gate 7 — ARM64 local build

source frozen後才開始 build；build期間不得再編輯。

### 7.1 Incremental

在 writer worktree：

```bash
./gradlew --no-daemon ':lorie:buildCMakeDebug[arm64-v8a]'
```

要求：

- exit 0
- `BUILD SUCCESSFUL`
- 0 errors
- 與基準warning fingerprint比較，0 new warnings

### 7.2 Full-clean

逐一執行，避免 ARM64／PRoot 資源壓力：

```bash
./gradlew --no-daemon :lorie:clean
./gradlew --no-daemon ':lorie:buildCMakeDebug[arm64-v8a]'
```

要求同上。禁止為了綠燈關閉warning、test或validation。

### 7.3 Standard checks

```bash
git diff --check
git status --short
```

並檢查無：

- debug print
- temporary bypass
- 意外 TODO
- `.pyc`／`__pycache__`
- build artifact進入source diff
- secrets／credential files

---

## Gate 8 — Cursor Luna handoff 與 parent 獨立複核

### 8.1 Luna blast-radius self-review

逐檔確認：

- 只改允許檔案。
- queue ABI、event既有編號、P0/P1/P2 predicate不變。
- event 32保留且runtime不可達。
- no fallback／no early release。
- `lorieRecheckGpuCopies()` renderer-loss路徑會fail-stop。
- window close／client disconnect不會drop in-flight pixmap。
- default-OFF行為未新增telemetry副作用。

### 8.2 Luna 停在未提交 diff

Cursor Luna 不得 commit。完成所有 host gates、local builds、warning comparison
與 self-review 後，回傳 writer skill 規定的 evidence packet，保留 verified
uncommitted diff，然後退出該 writer session。

不得用同一 Luna session審核自己的最終結果，也不得啟動其他agent。

### 8.3 Parent 複核與後續 commit gate

Luna退出後，parent親自重做：

- teardown lifetime與caller trace；
- raw ACK／pending clear／idle／destroy callsite audit；
- helper order、root destination `dst_buffer == NULL`語義；
- judge false-green／false-red cases；
- xserver patch round-trip；
- host tests與ARM64 builds；
- final diff、scope與`git diff --check`。

只有parent複核通過且使用者另行批准commit後，才可建立：

```text
fix(gatea): retire Present GPU copies after completion
```

Commit body 必須寫：

- Root cause：ACK散落在 requeue/scrap/destroy，能早於 completion。
- Why：pending與refs是CPU/client reuse的ownership barrier。
- Changes：集中 retire-or-fatal helper與雙分支host oracle。
- Verification：完整commands、exit codes、warning comparison。
- Breaking change：none。

Commit 後再次跑所有以 HEAD diff 為準的 gates，並記錄新 full SHA。
完成本機 commit 後停止；未獲新授權不得：

- push fork
- dispatch CI
- download artifact
- install
- ADB runtime

---

## Gate 9 — Fork push 與 CI（需另行批准）

建議批准範圍：只允許 push 新 fix branch 到 fork並執行既有 Build workflow；不開PR、不push origin。

CI 必須綁 exact commit：

- remote branch SHA == local commit SHA
- workflow run `headSha` == commit SHA
- conclusion SUCCESS
- 不 rerun red job求綠；修root cause後產生新commit
- universal debug artifact可下載並驗證

Artifact qualification至少包含：

- APK SHA256
- Build ID，兩端一致
- package=`com.waydefu.x11gpu`
- ABI includes arm64-v8a
- signer continuity
- versionName嵌入新short SHA
- xserver patch markers與retirement helper symbols存在
- no Stable package replacement

CI FAIL即停止並建立新阻擋報告；不降門檻。

---

## Gate 10 — Install／device qualification（需另行批准）

### 10.1 授權與操作方式

實機操作一次一條 mutating command，回讀結果後才下一條。開始前重新載入 Android qualification與device-status規則。

僅准 experimental：

```text
com.waydefu.x11gpu
```

Stable `com.termux.x11` 與 display `:1` 絕對不碰。

### 10.2 新 runtime root

只建立：

```text
runtime-<new-short-sha>/
```

並帶精確：

```text
EXPECT_VERSION=1.03.01-<new-short-sha>-15.09.26
```

每格保存：

- source／artifact／fixture binding
- env snapshot
- X PID與liveness
- contiguous telemetry或ring fallback
- logcat begin/follow/end
- fixture stdout/stderr/exit
- exact verdict
- Stable before/after

### 10.3 Runtime順序

因現行設計要求同一APK三格：

1. **R6-D1 一格**
2. **R6-D2-INFLIGHT 一格**
3. **R6-D2-OOM 一格**

每格都使用fresh X PID；任何FAIL／crash／missing evidence即停。JIT-class crash依專案規則分類，不silent retry。

若使用者選擇沿用`9369553` historical D1而不重跑，必須先明確批准變更「same APK」驗收標準並寫carry-forward證明；不得由agent自行決定。

### 10.4 D2-INFLIGHT PASS

只接受：

- busy→reason-1 reject→cover→later direct SUCCESS；或
- cover-before-target-lease→direct lifecycle SUCCESS。

五個舊cell不覆寫、不搬入新runtime。

### 10.5 D2-OOM PASS

必要序列：

```text
Present REQUEST/CALLBACK(S,G)
< PRESENT_REQUEUE_FAILED(S,G,dst)
Present CALLBACK
< renderer COMPLETED(T>=S,G)
max(REQUEUE_FAILED, COMPLETED)
< PRESENT_ACK_AFTER_COMPLETED(S,G,dst)
< later target Composite REQUEST/CALLBACK
< later direct SUCCESS
```

另外：

- event 32出現即FAIL
- env設置但event 33缺失即FAIL
- pixels-only即FAIL
- timeout/loss不應返回CLIENT_OK

D2-OOM成功只證明success-wait branch；不宣稱timeout/loss runtime已證明。

### 10.6 Runtime後停止

- 更新authority docs與HANDOFF。
- Stable再次驗證untouched。
- Production Gate A仍BLOCKED。
- R7仍不開始。

---

## 6. 文件同步清單

實作完成後視實際結果更新：

- `HANDOFF.md`
- `TEST-MATRIX.md`
- `AGENTS.md`（只放持久邊界，不塞暫時PID）
- `p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md`
- `GATE-A-P2-R6-DESIGN-20260915.md`
- `GATE-A-P2-R6-D2-HOLD-20260915.md`（保留歷史，新增superseding文件，不改寫舊結論）
- `GATE-A-P2-R6-D2-INFLIGHT-PHYSICAL-RACE-ANALYSIS-20260915.md`
- 新 implementation evidence：
  `GATE-A-P2-R6-PRESENT-RETIREMENT-IMPLEMENTATION-20260915.md`
- 新 oracle adjudication：
  `GATE-A-P2-R6-D2-INFLIGHT-ORACLE-ADJUDICATION-20260915.md`
- `.cursor/skills/gate-a-r6-design-review/SKILL.md`

Documentation impact 最終必寫 `Updated`；不是 N/A。

---

## 7. Required evidence packet

每階段證據至少包含：

```text
BASE_COMMIT
BRANCH / WORKTREE
STATUS_BEFORE
BASELINE_TESTS
RED_TEST_COMMAND + EXPECTED FAILURE
ROOT_CAUSE
CHANGED_FILES
GREEN_TEST_COMMANDS + EXIT CODES
CALLSITE_AUDIT
PATCH_ROUND_TRIP
INCREMENTAL_BUILD
FULL_CLEAN_BUILD
WARNING_COMPARISON
FINAL_DIFF_REVIEW
COMMIT_SHA
CI_HEAD_SHA / RUN / ARTIFACT（若獲准）
DEVICE_BINDING / CELLS（若獲准）
STABLE_BEFORE_AFTER（若獲准）
DOCUMENTATION_IMPACT
RISKS / UNKNOWN / FOLLOW-UP
```

不得用「tests passed」取代command與exit code。

---

## 8. Stop conditions

以下任一發生立即停止：

- authority與本計畫衝突
- base SHA或branch不符
- worktree不是clean baseline
- 必須改renderer/fence/queue ABI/direct predicate
- helper無法在teardown期間安全讀completed state
- 需要在timeout/loss後普通cleanup才能避免deadlock
- source regression test無法先RED
- raw ACK仍散落多處
- patch無法從clean submodule套用
- 新warning、build failure、host negative test failure
- CI不是exact-head green
- artifact/package/version/Build ID不符
- device target不是experimental display `:3`／built-in display 0
- Stable狀態改變
- telemetry gap且無完整ring
- JIT SIGSEGV或其他crash
- 任何runtime cell FAIL
- 使用者STOP或修改scope

停止時保留logs/diff/evidence，不reset、不覆寫cell、不silent retry。

---

## 9. Definition of Done

只有全部成立才能說本項修正完成：

- [ ] lifecycle source變更有明確批准。
- [ ] oracle validation變更有明確批准。
- [ ] base/worktree/branch精確綁定。
- [ ] teardown ordering已人工複核。
- [ ] regression test先RED且原因正確。
- [ ] 所有raw ACK集中於唯一retirement helper。
- [ ] requeue、loss、scrap、destroy、window close、client teardown皆completion-before-release。
- [ ] timeout/loss fail-stop且不release。
- [ ] source tests與judge雙分支tests全部GREEN。
- [ ] 原25 judge tests、binding tests、static verifier維持PASS。
- [ ] fixture `-Werror` compile PASS且可重建。
- [ ] xserver patch round-trip PASS。
- [ ] ARM64 incremental與full-clean PASS。
- [ ] 0 new warnings。
- [ ] final diff review完成。
- [ ] Conventional Commit建立，body含root cause與verification。
- [ ] 文件同步完成。
- [ ] 無debug垃圾、暫時繞過、意外TODO、秘密、cache。
- [ ] 如進入CI：exact-head CI green與artifact qualification PASS。
- [ ] 如進入device：同一新APK的D1、D2-INFLIGHT、D2-OOM全部PASS。
- [ ] Stable verified untouched。
- [ ] Production Gate A仍BLOCKED；R7未開始。

若只完成source/host階段，正確狀態是：

```text
PRESENT RETIREMENT SOURCE+HOST VERIFIED / AWAITING PUSH-CI AUTHORIZATION
```

若CI完成但未做device：

```text
ARTIFACT QUALIFIED / AWAITING INSTALL-RUNTIME AUTHORIZATION
```

不能提前寫R6 PASS。

---

## 10. 實作者最後回報格式

```text
STATUS
- exact base / branch / head
- completed stage
- next authorization boundary

ROOT CAUSE
- unsafe callsites
- why pending/ref/idle ordering was wrong

CHANGES
- file:symbol
- centralized helper contract
- oracle branch contract

RED EVIDENCE
- command
- exit code
- expected failure labels

GREEN VERIFICATION
- each command + exit code
- warning comparison
- patch round-trip
- final diff review

RUNTIME STATUS
- not run, or exact artifact/cell results

DOCUMENTATION IMPACT
- Updated files

RISKS / UNKNOWN
- timeout/loss runtime remains unproven until authorized design covers it
- any teardown assumption

DECISION REQUIRED
- exact next grant only
```

不得寫「native code 100% sound」；只陳述已被exact source、host tests、CI或runtime直接證明的範圍。
