# Gate A R6 檢查報告 ＋ R7／R8／R9／R10 ＋ Gate H 計畫書

日期：2026-09-15  
依據：**只用** `GPU加速-規劃包-20260915/` 內的檔案（9/14 以前的規劃文件視為過期，不引用）。  
性質：**檢查＋規劃，不是授權。** 本文件不授權 source 修改、commit、push、CI、install、ADB、device cell、R7、PR、merge、origin push、Stable、HDMI。

```text
決策：D-1～D-9 已於 2026-09-15 由使用者「照建議」定案（見 §10）；定案不等於寫碼授權
R6：NOT PASS（writer 未提交；2 個 HIGH 需在 commit 前處理）
R7：source-blocked（TERMUX_X11_GATEA_TEST_FAULT 不存在）
R8／R9／R10：NOT STARTED（需要 R7 的 hook 與計數器輸出）
Gate H：HOLD（現有量測沒有穩定交叉點）
Production Gate A：BLOCKED
Stable :1／HDMI：不碰
```

標記說明：

- 【包內已證】：規劃包內的 source／patch／judge／evidence 直接看得到。
- 【需原始碼確認】：規劃包沒有收錄該檔（`InitOutput.c`、`renderer.cpp`、`cmdentrypoint.cpp`、`lorie.h`、harness、host tests），執行前必須由複核者在 workstation 原始碼上確認。

---

## 0. 一頁結論

### 0.1 R6 檢查結果

writer 的方向是對的：`xserver/present/` 裡的 ACK 已集中到唯一 helper，scrap／destroy 先退役再 idle，schedule 成功後立刻設 pending，33→helper→34 順序正確。

但 commit 前有兩個 HIGH：

| # | 嚴重度 | 問題 | 一句話 |
|---|---|---|---|
| F-1 | HIGH | 「renderer stall」被當成「renderer loss」 | 依 patch 自己的定義，stall 包含「Activity 背景化、沒有 surface」。新 helper 在這時會 fail-stop。這個改動不受 PROTO 開關控制，所以 PROTO 關閉時 X 也可能被殺掉 |
| F-2 | HIGH | `xserver.patch` 尾端追加了零 context 的第二段 | 和 KEEP FAIL CI 34943831800（hunk 行數壞掉，到 link 才爆）屬於同一類風險 |

另有 MEDIUM 5 項、LOW 2 項、裁決 2 項，見 §2.3。

### 0.2 建議路線

```text
R6 關帳（A0–A8，§2.5）
  └─ 新 APK：R1 flag-off 重驗 → R3 → R6-D1 → R6-D2-INFLIGHT → R6-D2-OOM → R6-D3 背景化
Artifact B：R7–R10 支援 commit（§3）：fault hook ＋ 正向事件 ＋ 計數器摘要 ＋ ring dump
  └─ R1–R4 重驗 → R7（§4）→ R8（§5）→ R9（§6）→ R10（§7）
GATE A P2 RUNTIME CLOSED（§8）
Gate H：H0 量測設計 → H2 普查 → H3 交叉點裁決 →（有交叉點才）H4–H6 router（§9）
```

### 0.3 使用者決定（2026-09-15 已定案）

使用者回覆「照你建議」，§10 的 D-1～D-9 全部依建議定案。最關鍵的三個：

- **D-1 = (b)**：Present GPU copy 碰到「沒有 surface」時，不 ACK、不 fatal，保持 pending 並繼續 requeue；只有連線死亡或 2000 ms 無進展才 fatal。
- **D-3 = Artifact B**：新增的正向事件（35 `TEST_FAULT_FIRED`、36 `PRESENT_RETIRE`）放 Artifact B，不塞進 R6。
- **D-6 = P2 關帳後**：Gate H 普查等 P2 runtime CLOSED 之後才做。

**定案不等於授權**：D-1=(b) 要改 `InitOutput.c`，仍需 G2 的 source 授權；commit、push、CI、install、device 各自另需授權（§11）。下一步是 A1 獨立複核（唯讀）。

---

## 1. 依據與邊界

### 1.1 本次讀過的檔案

- `README.md`、`AGENTS.md`、`PLANNER-BRIEF-20260915.md`、`PROJECT-PROGRESS-20260915.md`、`HANDOFF.md`、`TEST-MATRIX.md`
- `core-src/present_execute.c`、`present_vblank.c`、`present_priv.h`、`xserver.patch`、`judge-r6-design.py`
- `patches/p_r6_d2_present.c`
- `skills/gate-a-r6-design-review/`（含 `R6-D2-REVIEW-20260915.md`）、`skills/gate-a-r6-present-retirement-implementation/`
- `evidence/session/gate-a-a1/GATE-A-P2-RUNTIME-QUALIFICATION-DESIGN-20260913.md`（R0–R10 官方定義）
- `evidence/session/gate-a-a1/p2-r6-design/` 下的 DESIGN、HOLD、RETIREMENT PLAN／IMPLEMENTATION、ORACLE ADJUDICATION
- `evidence/session/gate-a-a1/GATE-A-P2-B1-B4-IMPLEMENTATION-20260914.md`（B4 lifecycle）
- `evidence/session/gate-a-a1/p2-r3-xpump-implementation/HANDOFF-NEXT-AGENT-20260914.md`（pump 對 legacy record 的 DEFER／CANCEL 政策）
- `evidence/session/gate-a-a1/p2-r3-xpump-runtime/HANDOFF-NEXT-AGENT-20260915.md`、`runtime-95e6f96/GATE-A-P2-R6-RUNTIME-20260915.md`
- `evidence/session/gate-a-a1/p2-r6-ci-34943831800/KEEP-FAIL-20260915.md`
- `evidence/session/p2-b3a/`：`GATE-A-D-ARCHITECTURE-REVIEW-20260911.md`、`GATE-P2-B.3a.md`、`B3A-T1-5CELL-20260910.md`、`B3A-RUN-20260910.md`、`GATE-D0A-DESIGN-20260912.md`、`d0b-r1-scouts/D0B-R1-LUNA-E-SCOPE-AUDIT.md`

### 1.2 包內沒有、執行前必須補看的檔案

`lorie/InitOutput.c`、`renderer.cpp`、`cmdentrypoint.cpp`、`lorie.h`、`present_scmd.c` 的完整檔、`run-r6-design.sh`、`r6-design-bind.sh`、`test-judge-r6-design.py`、`verify_r6_design_impl.py`、`test-present-gpu-copy-retirement.py`。

### 1.3 不可越過的紅線（摘要，完整版以 AGENTS.md 為準）

- Stable `com.termux.x11`／`:1` 永不碰；experimental 只用 `com.waydefu.x11gpu`／`:3`／display 0。
- 不 silent retry；歷史 cell 不覆寫；新 APK 用新的 `runtime-<sha>/`。
- 不改 queue 168／frame 40／sideband 40／direct meta 48；不改 fence 語意；predicate 保持窄；不准 `±1 UNORM` 算 PASS。
- 不加 renderer delay 或 sleep 來「製造」競態；不在 terminal wait 裡 pump X client。
- R6 與 R7 不可同時寫 C；同一個 APK／同一個 X 不可混用 R6 OOM env 與 R7 fault env。
- 子代理同時最多 2 個；一個 writer＝一個 session＝一個 linked worktree；子代理不做最終架構裁決。

---

## 2. R6 檢查

### 2.1 狀態盤點

| 項目 | 狀態 | 出處 |
|---|---|---|
| R6 bounded client（`37d8393`） | CLIENT_OK，不是 design-complete | HANDOFF |
| R6-D1 | 歷史 PASS 在 `9369553` retry5；新 APK 尚未跑 | HANDOFF |
| R6-D2-INFLIGHT（`95e6f96`） | 5 格舊 reject-only oracle 全 FAIL（保留）；新雙分支 judge 在 host 重播時走 quiescent 分支 | ORACLE ADJUDICATION |
| R6-D2-OOM | NOT RUN | HANDOFF |
| Present retirement C | 在 `src/f8-ahb-gatea-r6-retire` 上，未提交；host 測試 37/37、BIND_NEG、R6_DESIGN_IMPL、PRESENT_RETIREMENT 全綠 | RETIREMENT IMPLEMENTATION |
| timeout／renderer-loss／scrap／destroy／CloseScreen 的 runtime | 沒有任何裝置格 | RETIREMENT IMPLEMENTATION §Not proven |

### 2.2 writer diff 靜態檢查：通過的項目【包內已證】

| # | 檢查 | 結果 | 位置 |
|---|---|---|---|
| P-1 | `xserver/present/` 可執行的 raw `lorieGpuCopyAck(` 只剩 helper 內一處 | PASS | `core-src/present_vblank.c:197`（`present_execute.c` 為 0 處） |
| P-2 | helper 順序：未完成才等待（wait-or-fatal）→ ACK → 清除 pending／dst／serial | PASS | `present_vblank.c:190-200` |
| P-3 | `present_vblank_scrap()` 先 helper，再 idle 與 `dixDestroyPixmap` | PASS | `present_vblank.c:211-215` |
| P-4 | `present_vblank_destroy()` 第一行就是 helper，之後才 drop pixmap／region／fence | PASS | `present_vblank.c:225-239` |
| P-5 | schedule 成功後立刻 `gpu_copy_pending = TRUE`，早於 callback trace 與 requeue | PASS | `present_execute.c:118-124` |
| P-6 | post-schedule requeue 失敗：先存 serial／dst scalar → 33 → helper → 34 → 才 flush／idle | PASS | `present_execute.c:151-156, 166-168` |
| P-7 | event 32 只剩宣告，沒有 runtime 呼叫 | PASS | `present_priv.h:114`；兩個 .c 檔都沒有呼叫 |
| P-8 | helper 二次呼叫時因 `!gpu_copy_pending` 直接 return，不會重複 decrement | PASS | `present_vblank.c:190-191` |

### 2.3 發現（依嚴重度排序）

#### F-1　HIGH — stall（沒有 surface）被當成 loss，背景化時 X 可能被 fail-stop

**位置【包內已證】**

- `present_execute.c:78-80`：`gpuCopyStalled = !lorieConnectionAlive() || !lorieRendererAvailable()`，註解寫明包含「activity backgrounded, no surface」。
- `present_priv.h:117-122`（= `xserver.patch:605-610`）：`lorieRendererAvailable()` 在「沒有 surface」時為假，並把它和連線中斷列為同一種「放棄這個 GPU copy」的情況。
- `xserver.patch:620-634`：`lorieRecheckGpuCopies()` 的註解寫明「renderer 通知 batch 完成，**或剛失去 surface** 時呼叫」。它會對 `gpuCopyStalled` 的 pending vblank 呼叫 `present_re_execute()`。
- writer 的 `present_execute.c:105-114`：pending、未完成、stalled 時直接進 helper。helper 在 `present_vblank.c:194-195` 呼叫 `lorieGpuCopyWaitForPresentOrFatal()`。DESIGN §6.3 說明：timeout 或 renderer loss 時該 wrapper 會 `GATEA_FATAL_HALT what=x-present-copy-wait`。
- 95e6f96 已安裝的行為（`xserver.patch:508-517`）：stalled 且未完成時會先 ACK，再 `present_vblank_scrap()`，X 繼續活著。
- `present_execute_copy()` 沒有檢查 PROTO。這條 Present GPU copy 是 Gate A 之前就有的「GPU PRESENT QUALIFIED」路徑。

**失敗情境**

1. 使用者在 experimental `:3` 上跑 Present client（任何 DRI3／Present 畫面）時，把 Activity 切到背景。
2. renderer 失去 surface，送出 GPU_COPY_DONE。
3. X 的 `lorieRecheckGpuCopies()` 對未完成的 vblank 重新執行，進入 stalled 分支，呼叫 helper，再進 wait-or-fatal。
4. 如果 wait 在沒有 surface 時直接判定失敗，或 renderer 在沒有 surface 時 2000 ms 內沒推進 `completedSerial`，X 就會 fatal。
5. PROTO 未設或 PROTO=0 也一樣。這違反 R1「flag-off 等價」，也改變了 experimental 的日常存活性。

**【需原始碼確認】**

- (a) `InitOutput.c` 的 `lorieGpuCopyWait()` 在 `!lorieRendererAvailable()` 時是立即回傳 FALSE，還是繼續等？
- (b) renderer 在沒有 window surface 時還會不會 drain GPU copy queue？
- 規劃者在收到「只看資料夾」指示前曾粗看過 fork 的 `95e6f96`，看起來 (a) 是立即回傳 FALSE（等於立刻 fatal），(b) 是會 drain。這一點**不是從規劃包得到的**，必須由複核者在 workstation 原始碼上重新確認。

**為什麼不能直接接受**

ownership 的角度：「沒有 surface」不代表 GPU 工作的結果不確定。renderer 還連著，排好的 copy 之後仍會執行。這時保留 pending 與 refs 是安全的。真正不確定的是「連線死亡／程序消失」或「在預算內沒有進展」。

**修正選項（D-1）**

| 選項 | 內容 | 評估 |
|---|---|---|
| (a) 維持 fail-stop | 接受「背景化可能殺 X」 | 不建議：R1 flag-off 等價判準必須改寫，日常存活性倒退 |
| **(b) 區分 stall 與 loss（建議）** | Present 路徑：沒有 surface 但連線還在 → 保持 pending、繼續 requeue，不 ACK、不 fatal；連線死亡或 2000 ms 內沒進展 → fatal。scrap／destroy 在沒有 surface 時照樣等（前提是 (b) 確認 renderer 沒有 surface 也會 drain），等不到才 fatal | 要改 wrapper 的語意（`InitOutput.c`），超出 writer skill 允許的檔案 → **需要新授權** |
| (c) 延遲退役清單 | destroy 時把 pixmap／dst ref／serial 移到 orphan list，完成後再退役 | 最完整，但改動大；retirement plan §4.6 已經否決過，留給 Production Gate A |

**定案（2026-09-15）：D-1 = (b)。** 範圍限定為 Present 專用的 wait 語意，不動 EXA／direct 的 wait。實作需 G2 授權。

**連帶決策 D-2（已定案：接受）**：Activity 關閉（真的斷線）時若還有 pending Present copy，(a)(b) 都會 fail-stop。qualification 階段接受，但要寫進 Production Gate A 的 lifecycle 缺口，並用 R7-P2 證明「fail-stop 且沒有釋放 ownership」。

**驗收**

- RED 靜態測試：沒有 surface 但連線還在時，不得進 wait-or-fatal、不得 ACK。
- R1（PROTO 未設與 PROTO=0）在新 APK 上重驗。
- D-1=(b) 已定案：新增裝置格 R6-D3（§2.5 A7），必跑。

#### F-2　HIGH — `xserver.patch` 尾端追加零 context 的第二段 Present patch

**位置【包內已證】**：`core-src/xserver.patch:1231-1342`

- 同一個 `./present/present_execute.c` 出現兩段：`:462` 與 `:1231`。`present_priv.h`（`:570`、`:1299`）和 `present_vblank.c`（`:645`、`:1303`）也各兩段。
- 第二段的 hunk 沒有 context，例如 `@@ -94,6 +94,3 @@`（`:1233`）、`@@ -120 +134 @@`（`:1284`）、`@@ -134 +147,0 @@`（`:1287`）、`@@ -109,0 +110 @@`（`:1301`）。

**風險**

- 零 context 的 hunk 只靠行號定位，無法偵測「已經套過」或位置偏移。
- 同一檔案分兩段套用，第二段要以第一段的輸出為基準。
- KEEP-FAIL 34943831800 已經證明：這個 repo 的 patch 壞掉時，錯誤不會在 configure 階段擋下，而是到 link 才出現（「link missing `lorieRecheckGpuCopies`／`xkbcomp_*`」）。
- 風險包括：CI 再紅一次；更糟的是本機 incremental build 可能在「部分套用」的樹上編過，host 綠燈但 CI 產物和本機不同。

**修正（計畫 A4）**

1. 把三個 Present 檔的語意 diff 併回原本 `:462／:570／:645` 的段落，用標準 context（3 行）重新產生。每個檔案只能有一段。其他檔案的段落必須逐 byte 不變。
2. 驗證（全部要保存 command、exit code、完整輸出）：
   - 以 submodule exact HEAD `65d790bd208ec380b196eb98f144abb0b32e334d`（retirement plan §4.4）建立乾淨暫存 checkout，執行 `patch -p1 --dry-run`：exit 0，輸出不得出現 `offset`、`fuzz`、`FAILED`、`reject`。
   - 實際套用後，與 writer live submodule `diff -r`：必須完全相同。
   - 在套好的樹上執行 `patch -p1 -R --dry-run`：exit 0。
   - `grep -c '^+++ ./present/present_execute.c'` 等於 1（vblank／priv 同樣檢查）。
   - 新 patch 與 `95e6f96` patch 的差異只能出現在三個 Present 段落。
3. ARM64 full-clean build、CI multi-ABI 全綠，並在 CI log／ELF 確認 `present_gpu_copy_retire_or_fatal` 與 `lorieRecheckGpuCopies` 都成功連結。

#### F-3　MEDIUM — helper 對 `serial == 0` 的契約和計畫不一致

- 計畫（RETIREMENT PLAN §4.1-3）：`gpu_copy_serial == 0` 要直接 protocol fatal，不得釋放。
- 實作（`present_vblank.c:194-195`）：`serial == 0` 也丟給 `lorieGpuCopyWaitForPresentOrFatal(0)`。如果 wrapper 只檢查 `completedSerial >= serial`，serial 0 會立刻成立，接著就 ACK 一個狀態不一致的 vblank。
- 【需原始碼確認】wrapper 會不會拒絕 0。
- **建議**：不要依賴外部檔案，helper 內直接 `if (serial == 0) FatalError(...)`（`present_vblank.c` 在允許修改的檔案內）。靜態測試同時斷言「serial 0 不會走到 ACK」。

#### F-4　MEDIUM — already-pending 路徑的 event 33／34 目的端 ID 可能綁錯

- `present_execute.c:75, 96`：`gpuCopyDstId = lorieGateAPixmapBufferId(screen->GetWindowPixmap(window))` 是在**重新執行時**才取當下的 window pixmap。真正排程的目的端存在 `vblank->gpu_copy_dst_buffer`。
- 如果兩次之間 window pixmap 換了（Composite redirect／unredirect、resize 重配 backing），33／34 的 dst 會和實際不同，judge 的目的端綁定可能誤判。
- 只影響 telemetry，不影響 ownership（extra ref 仍保護真正的 buffer）。
- **建議**：schedule 時把 dst ID 存進 vblank（`present_priv.h` 結構加欄位，屬允許修改的檔案），33／34 用存下的值。

#### F-5　MEDIUM — OOM judge 抓不到「等待期間 dispatch 了 client」與「ACK 前就發 lease」

- `judge-r6-design.py:291-328` 的 OOM 分支只檢查 33、34、cover、之後的 Composite 與 direct lifecycle。
- 沒有檢查：`PRESENT_CALLBACK < e < ACK_AFTER_COMPLETED` 這段期間，不得出現 `REQUEST_ARRIVED`（29）、目標端 `LEASE`／`PUBLISH`。DESIGN §9 把「X client dispatch from inside a Gate A terminal wait」列為 FAIL，OOM 分支卻沒有執行這條。
- `:316` 的 `dest_id = ack['dst'] or requeue['dst']` 沒有要求兩者相等。
- **修正**：加上述兩條禁止與 `ack.dst == requeue.dst`。新增負向測試：「等待期間出現 REQUEST」「ACK 前出現 LEASE」「33／34 的 dst 不同」三者都必須 FAIL。

#### F-6　MEDIUM — D1 judge 的 SUCCESS 沒綁定到同一筆交易

- `judge-r6-design.py:233-236`：`first_success` 是 composite callback 之後「任何一個」`EV_SUCCESS`，沒有綁 generation、src／dst。
- 新 APK 要重跑 D1（§2.5 A7），所以要補強。
- **修正**：用既有的 `direct_lifecycle()` 綁定第一筆 Composite 的 LEASE→PUBLISH→COMPLETED→SUCCESS，第二組操作的 REQUEST 必須晚於**這一個** SUCCESS。
- 回歸：歷史 `9369553/r6-d1-retry5` 仍須 PASS；錯 pair 的 SUCCESS 必須 FAIL。

#### F-7　MEDIUM — 新增的 fail-stop／teardown 路徑沒有任何裝置格；「destroy 時仍 pending」目前無法證明真的發生過

- D2-OOM 只證明 post-schedule 的「等到完成」分支（RETIREMENT PLAN §10.5 自己也這樣寫）。
- 以下都沒有 runtime 證據：already-pending 的自然 requeue 失敗、stalled、scrap、destroy／window close／client disconnect、timeout、loss。
- helper 不會記錄「這次有沒有真的等待」。在這顆 SoC 上 GPU 常常先完成（D2 五格就是這樣），destroy 格即使 PASS，也分不出是走了等待分支還是早就完成。這和 D2-INFLIGHT reject-only 誤紅是同一類「構造證明」問題。
- **建議（D-3）**：新增 append-only 事件 36 `PRESENT_RETIRE(serial, dst, waited=0|1)`，放在 Artifact B。對應裝置格：R7-P1、R7-P2、R8-C3。
- 新增事件屬於架構邊界，需要授權；放在 Artifact B 可以避免重開 R6 的審查。

#### F-8　LOW — 權威文件漂移

| 文件 | 過期或不受證據支持的內容 |
|---|---|
| `HANDOFF.md:117, 170, 393-394`、`HANDOFF-NEXT-AGENT-20260915.md` | 「native code 100% sound」「GPU <0.5 ms vs dispatch 2.5 ms」。GATEA_EVENT 沒有時間戳，retirement plan §5.5 已要求把這些降為推測 |
| `PLANNER-BRIEF:82`、physical race analysis、runtime-95e6f96 doc | 寫「Adreno 830／Snapdragon 8 Elite」；`TEST-MATRIX.md:44, 68` 基線是 **Adreno 840** |
| `HANDOFF.md` Next | 仍是 A／B／C 三選一，沒有反映 retirement writer |
| `GATE-A-P2-R6-DESIGN-20260915.md` §14、`GATE-A-P2-R6-D2-HOLD-20260915.md` 表頭 | 仍寫「wait C 未寫」（§15／§5 已有 errata，但表頭沒改） |
| `TEST-MATRIX.md:3` | 重複「<0.5ms 快於 2.5ms，物理競爭根因已定性」 |

處理方式：獨立複核（A1）通過後，由 parent 一次更新（A8）。歷史結論保留，新增 superseding 註記。

#### F-9　LOW／中風險 — 裝置 512-ring dump 仍未接進 harness

- HOLD §1.5 寫明 ring dump 還沒接；judge 在 seq 有缺口又沒有 `gatea-ring.txt` 時判 FAIL。
- R6 的格子很小（事件數遠小於 512），歷史 cell 都完整擷取，因此 **R6 可以接受這個風險**。
- R7–R10 **不能**接受：fatal 會讓 logcat 尾端遺失；R5 已經證明 follow logcat 會掉事件（ack=4095）。所以列為 Artifact B 的必做項目（B-3）。

#### 裁決 J-1（PLANNER-BRIEF P2-9）：quiescent 分支的嚴格度保留

- 「immediate lifecycle 必須在下一個 Composite REQUEST 之前結束」不是過度擬合。它直接來自 DESIGN §3 的執行緒模型：DoneComposite 同步等待、等待中不 pump client。這和 D1 證明的是同一個不變式。
- 「quiescent 也要有 later Composite ＋ 第二個 lifecycle」屬於 fixture 構造要求（證明 Present 之後 admission 會恢復）。成本很低，保留，但在 judge 註解與 gate 文件標明「構造要求，不是產品 oracle」。

#### 裁決 J-2（PLANNER-BRIEF P2-8）：LEASE_RESERVED 沒有 client sequence

- 在「等待中不 pump client」的不變式成立時，「callback 之後、下一個 REQUEST 之前的第一個 lease」已經足以綁定。
- R6 不改 payload。若要更嚴格，可在 Artifact B 追加 append-only 事件 `LEASE_BIND(clientSeq)`，這是選配。

### 2.4 R6 分項判定

```text
設計（DESIGN §6 雙分支 ＋ OOM）：            PASS（含 J-1、J-2 裁決）
Source（writer diff，未提交）：             HOLD — F-1、F-2 未解；F-3、F-4 建議修
Host 驗證：                                PASS（writer 自報 37/37 等）；但 F-5、F-6 的判準缺口未覆蓋
CI artifact：                              NOT BUILT
Device runtime：                           D1（新 APK）／D2-INFLIGHT（新 APK）／D2-OOM／D3 全部 NOT RUN
Stable／HDMI：                             UNTOUCHED（依 HANDOFF）
R6 總判定：                                NOT PASS
決策：                                     D-1～D-9 已定案（2026-09-15）
下一步：                                   A1 獨立複核（唯讀）→ 申請 G2 source 授權
```

### 2.5 R6 關帳計畫（A0–A8）

每一步做完就停，取得下一步授權後才繼續。

| 步 | 內容 | 執行者 | 前置授權 | 產出 | 驗收 |
|---|---|---|---|---|---|
| **A0** ✅ | 使用者決定 D-1、D-2、D-3、D-4 | 使用者 | — | **DONE 2026-09-15**：照建議定案（D-1=b、D-2=接受、D-3=Artifact B、D-4=R1＋R6 cells），A1 文件須引用 | 四項都有明確答案 |
| **A1** | **獨立複核** writer diff（不能是寫 helper 的那條 session）。逐項核對 F-1～F-7；在 workstation 原始碼補完所有【需原始碼確認】；列出 `lorieCloseScreen`、`present_close_screen`、`present_destroy_window`、`present_free_window_vblank`、`present_vblank_destroy` 的呼叫順序（retirement plan §3.3） | Sol High（Luna 只做 scout） | 唯讀，不需寫入授權 | `p2-r6-closure/GATE-A-P2-R6-RETIREMENT-INDEPENDENT-REVIEW-<date>.md` | 每個 finding 都有 CONFIRMED／FALSIFIED 與 path:line |
| **A2** | 依 D-1=(b) 修正 source：會碰 `InitOutput.c`（Present 專用 wait 語意），超出 writer skill 的允許範圍，需要**新的架構授權**。F-3、F-4 一併處理。先 RED 再 GREEN | 單一 writer（worktree 仍為 `src/f8-ahb-gatea-r6-retire`） | 新 source 授權 | 更新 IMPLEMENTATION 文件 | RED 測試因正確原因失敗 → GREEN |
| **A3** | judge 補 F-5、F-6，並新增負向測試；歷史 D1 PASS／D2 retry1 FAIL 分類不變 | 同 A2 writer（judge 屬允許修改的檔案） | 同 A2 | test log | 原有測試全 PASS，新增負向測試全 PASS |
| **A4** | patch 正規化（F-2 的步驟 1–2） | 同 A2 writer | 同 A2 | patch round-trip 證據 | F-2 列出的所有檢查都通過 |
| **A5** | host gates 全部重跑；`bash -n`；fixture `-Wall -Wextra -Werror`；ARM64 incremental ＋ full-clean（source 凍結後才 build）；warning fingerprint 比對；`git diff --check` | writer 跑，parent 複驗 | 同 A2 | build log | 0 error、0 new warning、diff 範圍只含允許的檔案 |
| **A6** | parent 複核通過 → commit（`fix(gatea): retire Present GPU copies after completion`，body 寫 root cause、驗證 command 與 exit code）→ fork push → CI → artifact qualification | parent | ① commit 授權 ② fork push／CI 授權（分開給） | `p2-r6-retire-ci-<run>/…PROVENANCE…md` | CI `headSha` 等於 commit；APK SHA256、Build ID 兩端一致、signer 延續、versionName 含新 short SHA、helper symbol 存在 |
| **A7** | install（只裝 experimental）→ `runtime-<newsha>/`：R0 → R1 unset → R1 PROTO=0 → R3 → R6-D1 → R6-D2-INFLIGHT → R6-D2-OOM → R6-D3 | Sol High 裁決；可交 [L] 照表執行 | install／device 授權；**R6-D3 另需「display 0 背景化／前景化操作」的明確授權** | 每格一份 gate 文件 | 見下表 |
| **A8** | 寫 R6 關帳 gate 文件；更新 HANDOFF／TEST-MATRIX／AGENTS（F-8）；Stable 前後比對 | parent | — | `GATE-A-P2-R6-CLOSURE-<date>.md` | `GATE A P2 R6 PASS / <sha>`，或保留 FAIL 並停 |

**A7 各格判準**

| 格 | 條件 | PASS |
|---|---|---|
| R0 | artifact／裝置／display 綁定；Stable 只讀 | 全部 MATCH |
| R1 unset／R1 PROTO=0 | Present 路徑對所有模式都改了，**必須重驗** | 1514/1514 exact、stress 100/100/1000、GATEA_EVENT=0、無 fatal、`NO_X3_RESIDUE` |
| R3 | D-4：因 `InitOutput.c` 有改動而加跑；判準同歷史 R3 | X consumed READY；像素 64 exact `00804000`；無 `x-ready-timeout` |
| R6-D1 | 使用 A3 補強後的 judge | `R6_D1_PASS`；像素 `00804000` 家族 exact |
| R6-D2-INFLIGHT | OOM env 必須未設 | busy-reject 或 quiescent-admit 其中一個分支成立 |
| R6-D2-OOM | 新 X PID；`TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL=1` | 33 → (cover、33) 之後才有 34 → later Composite → 目標端 direct SUCCESS；event 32 為 0；等待期間沒有 REQUEST（F-5） |
| R6-D3（D-1=b 已定案，必跑） | PROTO 未設與 PROTO=1 各一格。Present client 持續送畫面 → 只針對 display 0 做 Activity 背景化 → 等 5 s → 回前景 → 停 client | X 存活；GATEA_FATAL_HALT 為 0；Fatal signal 為 0；CompleteNotify 數量等於 Present 數量；回前景後像素 exact；Stable PID／cmdline 不變 |

**R6-D3 的操作限制**：只能用指定 display 0 的方式切換（例如帶 display 參數的 HOME intent 或 `input -d 0`）。只要有任何可能影響 HDMI 或 Stable 的疑慮，立即停下並詢問。

**R3–R5 是否重跑（D-4 已定案）**：D-1=(b) 會修改 `InitOutput.c`，所以 **R3 必跑**（排在 R1 之後、R6-D1 之前）。R4、R5 carry-forward，但 A8 要附「diff 範圍證明」：`InitOutput.c` 的改動只限 Present wait，沒有碰 direct 路徑。**R6-D3 必跑**（D-1=b 已定案）。

**A7 停止條件**：任一格 FAIL、crash、證據缺漏（seq 有缺口又沒有 ring）、env 設錯格、Stable 變動 → 立刻停，不重試。ART JIT 類 SIGSEGV 依 AGENTS 規則：標 OBSERVED，申請一次有界重跑。

---

## 3. 共用基礎：Artifact B（R7–R10 支援 commit）

### 3.1 為什麼要先做一個支援 artifact

R7–R10 共同缺四樣東西：

1. **故障注入 hook**：R7 全部格子、R8 的 pending 格、R9 的 stale replay 都需要。
2. **正向構造證據**：證明「注入真的發生了」「retire 真的等待過」。review skill 規則 8：「env 存在只證明設定，不證明分支有執行」。
3. **不依賴 follow logcat 的計數器摘要**：R5 已證明 logcat 會掉事件；R10 要看資源平衡。
4. **harness 的 ring dump**（F-9）。

把這四樣做成**同一個 artifact**，只需要走一次 CI／install／重驗。

**前置條件**：R6 關帳 commit 已凍結，R6 device cells 已跑完。worktree 從 R6 關帳 commit 另開，例如 `src/f8-ahb-gatea-r7`，branch `qualification/gatea-r7-r10-<date>`。

### 3.2 B-0：ABI／設計審查（先審，才可寫碼）

產出：`p2-r7-design/GATE-A-P2-R7-R10-SUPPORT-DESIGN-<date>.md`，由 Sol High 審查。

必須凍結以下內容：

**1. env 介面**（沿用 20260913 設計的名稱）

- `TERMUX_X11_GATEA_TEST_FAULT=<cell>` 與 `TERMUX_X11_GATEA_TEST_ARM=1`，只由 **X** 讀取。
- 以下任一情況 → **拒絕啟動**（在任何 client 連線前 fatal）：
  - cell 不在 exact allow-list；
  - 只設 ARM 沒設 FAULT，或只設 FAULT 沒設 ARM；
  - PROTO≠1 或 TELEMETRY≠1；
  - 同時設了 `TERMUX_X11_GATEA_R6_PRESENT_REQUEUE_FAIL`。

**2. 傳到 renderer 的方式**

- HANDOFF 已證明 Activity 程序**不會繼承** X 的 env（`dd81ac0` R3 FAIL 的根因），所以 renderer 端的故障不能用 getenv。
- 做法：在 `lorie_shared_server_state` **尾端**追加一段有版本號的區塊（magic、version、cell、armed、consumed、target generation、target ordinal）。
- 不得動 168／40／48 與既有 telemetry／counter 的 layout；對新區塊的 offset 與 size 加 static assert。
- 審查時要確認：X 與 renderer 來自同一個 APK build，兩端 sizeof 必然一致。

**3. 一次性**

- renderer 或 X 以 CAS 把 consumed 從 0 設為 1 才能觸發。
- 觸發前先 trace 事件 35 `TEST_FAULT_FIRED(serial, src=cell, dst=side)`，然後才執行故障效果。

**4. 故障效果只能「替換結果」**

- 不得 sleep 或延遲（遵守 DESIGN §2.2）。
- 「timeout」類故障的做法：扣留目標 serial 的完成發布（不發布 completedSerial），讓 X 端既有的 2000 ms 預算自然到期；或把 fence wait 的結果替換成逾時。**不是**讓 renderer 真的等。

**5. 未 arm 時完全無作用**

- 所有 hook 分支都要先讀同一個 armed 值再判斷。
- 靜態 verifier 必須證明：未 arm 時不會有任何 I/O、配置、等待或影響語意的分支。

**6. 新事件**（append-only，1–34 不動，32 不得挪用）

| 事件 | 內容 | 用途 |
|---|---|---|
| 35 `TEST_FAULT_FIRED` | serial, cell, side | 證明故障真的注入 |
| 36 `PRESENT_RETIRE` | serial, dst, waited 0／1 | 解決 F-7 的構造證明 |
| 37 `LEASE_BIND` | clientSeq（選配，J-2） | 更嚴格的 lease 綁定 |

**7. 計數器摘要 `GATEA_SUMMARY`**

- 時機：clean CloseScreen 時，以及 fatal 前（best-effort）。
- 內容：28 個 counter、overflow、nextSequence、firstFailed、generationFatal、nonce、generation。
- 寫一行 logcat，**同時**寫一個 X 端檔案（X 在 Termux uid，可以從 PRoot 讀取；路徑在設計中凍結）。
- 注意：ring 在一個 X 程序生命期內最多 512 筆（judge `CAP=512`），多輪 R8–R10 必須以計數器為準。

**8. harness**

- 真正擷取 `gatea-ring.txt`：在 clean close 時由 X 把 ring dump 成檔案。
- 所有 judge 的 seq 缺口補齊邏輯改為讀這個檔案。

### 3.3 B-1：稽核項目（先查，有缺陷才修）

| 稽核 | 問題 | 若有缺陷 |
|---|---|---|
| 所有 `lorieGpuCopyWait` 呼叫端 | EXA Copy／Solid／Composite 的 Done 在等待失敗時做什麼？PROTO=1 時會不會提前釋放，讓 `gateAQueueSemanticallyQuiescent()` 看到假的 quiescent？ | 另開 finding，由使用者決定是否納入 B |
| deferred legacy record | pump 在 READY／UNREGISTER 等待時 DEFER、GENERATION_CLOSE 時 CANCEL（xpump handoff）。DEFER 佇列有沒有上限？滿了怎麼辦？ | 列入 R8-D 格的預期 |
| X／renderer registry 容量 | CloseScreen retire 的 snapshot 容量是否等於 registry 容量？registry 滿時是 pre-publish 拒絕還是 fatal？ | 凍結 R8-C5 的預期 |
| server reset | lorie 在最後一個 client 離開時，會不會在同一程序內 regenerate（`serverGeneration` > 1）？ | 決定 R9-3 要不要做 |

### 3.4 B-2：流程與重驗

```text
B-0 審查 PASS → 寫入授權 → 單一 writer RED→GREEN → 靜態 verifier（未 arm 無作用、一次性、事件編號、ABI assert）
→ ARM64 incremental ＋ full-clean（0 new warning）→ parent 複核 → commit → fork push／CI → artifact qualification
→ install → runtime-<shaB>/：R0 → R1 unset／PROTO=0 → R2 → R3 → R4
→（D-5 建議）R5 4096 ＋ R6-D1
```

- 這些重驗格都不得設 TEST env。判準和原本相同，另加：事件 35／36 數量為 0（36 只有在發生退役時才會出現）、`GATEA_SUMMARY` 存在且計數器等式成立。
- 只要有一格 FAIL，就不開 R7。

---

## 4. R7 — 故障注入（fail-stop）

### 4.1 目標

證明「發布之後的每一種失敗」都會 fail-stop，而且注入點之後：

- 沒有 repair、ACK、pending--、relock、lease release；
- 沒有 D0a fallback、replay；
- 同一 generation 不會繼續工作。

另外補上 R6 沒有證明的 Present timeout／loss。

### 4.2 格子

每格：一個 fresh X、只 arm 一個 cell、只跑一次、不重試；PROTO=1、TELEMETRY=1；client 使用單一 direct 交易的 fixture（沿用 R3 的 single-direct）。

| 格 | 端 | 注入點 | 預期終態類別 | 構造證據（必須先出現） |
|---|---|---|---|---|
| R7-01 | renderer | 發布後 source READY lookup 強制 miss | FATAL（DIRECT_LOOKUP_FAIL → renderer fatal） | PUBLISH(S) → CONSUME_DIRECT(S) → 35 |
| R7-02 | renderer | 發布後 destination READY lookup 強制 miss | FATAL | 同上 |
| R7-03 | renderer | entry 的 tuple（nonce／generation）不符 | FATAL（GENERATION） | 同上 |
| R7-04 | renderer | 碰 GL 前 FBO incomplete | FAILED_QUIESCED → X 端非 SUCCESS → fail-stop | PUBLISH(S) → 35 |
| R7-05 | renderer | draw 送出後 GL error（fence 已 satisfied） | FAILED_QUIESCED（firstFailed CAS） | DRAW_SUBMIT(S) → 35 |
| R7-06 | renderer | fence 建立失敗 | FATAL（FENCE） | DRAW_SUBMIT(S) → 35 |
| R7-07 | renderer | fence wait 結果替換為逾時 | FATAL；**不得**發布 completedSerial ≥ S | DRAW_SUBMIT(S) → 35 |
| R7-08 | renderer | consume 之後、fence 之前 renderer fatal | FATAL | CONSUME_DIRECT(S) → 35 |
| R7-09 | X | 收到 generation±1 的 READY／ACK frame | X FATAL（wrong generation） | REGISTER 階段 35 |
| R7-10 | renderer | consume 後 renderer 程序立刻 `_exit`（模擬 Activity 死亡） | X 在 lease 仍存活時看到 HUP → FATAL | CONSUME_DIRECT(S) → 35 |
| R7-11 | X | generation 初始化時把 serial counter 設到接近 `UINT64_MAX` | 發布 serial 0 **之前**就停止；沒有任何 PUBLISH(serial=0) | 35 → 少數幾次正常 PUBLISH → wrap fatal |
| R7-P1 | renderer | 扣留某個 Present copy serial 的完成發布 | helper wait 2000 ms → `x-present-copy-wait` FATAL；沒有 34；沒有 idle／CompleteNotify(S) | Present CALLBACK(S) → 35 →（若有 36 waited=1） |
| R7-P2 | renderer | Present copy 排入後 renderer `_exit` | FATAL；沒有 34、沒有 ACK | Present CALLBACK(S) → 35 |
| R7-12 | X | 在 lease 為 GPU_OWNED 時合成呼叫 DestroyPixmap 的 retire | FATAL；沒有 UNREGISTER_ACK、沒有 normal release（**R8-P1 使用**） | LEASE_GPU_OWNED → 35 |
| R7-13 | X | 在 lease 仍存活時合成呼叫 CloseScreen 的 drain | FATAL；沒有 GENERATION_CLOSED（**R8-P2 使用**） | LEASE_GPU_OWNED → 35 |
| R7-14 | renderer | rebind 後重送一個舊 nonce／generation 的 READY | 拒絕或 FATAL；舊 frame 不得讓新 generation 產生 READY_MARK（**R9-F1 使用**） | 新 bind → 35 |

- 每格的 fatal `what`／`reason` 字串由 B-0 從原始碼**逐格凍結成 exact 值**。本表不猜字串。
- 建議執行順序（由影響小到大）：04 → 05 → 01 → 02 → 03 → 06 → 07 → 08 → 09 → 11 → 10 → P1 → P2。R7-12／13／14 在 R8／R9 時才跑。

### 4.3 共同判準（新 `judge-r7.py`）

**PASS 必須全部成立**

1. `TEST_FAULT_FIRED` 剛好 1 次，cell／side 等於 arm 的值。
2. 構造證據鏈全部出現在 35 之前，且 generation、serial、src／dst 都綁定。
3. 在 35 的 seq 之後，對該 pair／serial 以下事件全部為 0：SEMANTIC_SUCCESS、RELOCK_SRC／DST、REPAIR、ACK、PENDING_DEC、LEASE_RELEASE、serial > S 的 PUBLISH。P 格另外要求 34 為 0；所有格都要求 event 32 為 0。
4. 終態證據：FIRST_FAILED(15) 和／或 GENERATION_FATAL(16)，generation 相同；或 X 端 HUP fatal。`GATEA_FATAL_HALT` 的 what／reason 必須等於凍結值。
5. X 程序在限定時間內結束（例如 10 s）。**X 還活著、還能繼續做 direct → P2 FAIL**（20260913 設計：任何「正常繼續」都是 FAIL）。
6. 程序結束方式必須是 fatal 路徑的 exit，**不得是 signal**（SIGSEGV／SIGABRT 等 → FAIL，或依 JIT 規則標 OBSERVED）。
7. `GATEA_SUMMARY`（fatal 版）存在；或 seq 從 0 起連續（可用 ring 補齊）。都沒有 → **INCOMPLETE**，不是 PASS。
8. `NO_X3_RESIDUE`；Stable 前後一致。

**host 負向測試**（實作 judge 前先寫）

- 35 出現 0 次或 2 次 → FAIL
- 35 之後出現 SUCCESS／ACK／RELOCK／PENDING_DEC → FAIL
- what 不符 → FAIL
- 以 signal 結束 → FAIL
- X 存活並完成後續 direct → FAIL
- 缺構造鏈 → FAIL
- seq 有缺口又沒有 ring → INCOMPLETE
- 正確的 FAILED_QUIESCED 樣本 → PASS
- 正確的 FATAL 樣本 → PASS
- 正確的 wrap 樣本 → PASS

### 4.4 harness：預期會死的格子怎麼收尾

`run-r7.sh` 由 B-0 凍結，流程：

1. R0 綁定 → 記錄 Stable → 啟動 follow logcat → 以 exact env 啟動 X → 回讀 `x-environ-gatea.txt`（必須剛好含 FAULT／ARM，且沒有 R6 env）。
2. 啟動 holder 與 fixture → 等 X 結束（上限 T）。
3. 超過 T 仍存活 → 判 FAIL，才走一般 teardown（holder → X TERM → 等待 X 消失 → force-stop experimental）。
4. X 已結束 → force-stop experimental Activity → 殘留掃描 → Stable 回讀 → 跑 judge。
5. 一次一條會改變裝置狀態的指令，每條回讀後才下一條。

### 4.5 停止條件

- 任一格 FAIL 或 INCOMPLETE
- 出現非預期 signal
- 故障沒有觸發
- env 回讀不符
- Stable 或 display 不符

一律停止，不跑下一格，不重試。

### 4.6 產出

`runtime-<shaB>/r7-<cell>/`（每格）＋ `GATE-A-P2-R7-RUNTIME-<date>.md`（總表）。結論行：`GATE A P2 R7 PASS / <shaB>`。

---

## 5. R8 — Destroy／Close lifecycle

### 5.1 前提

- B4（`15caa00`）已實作 UNREGISTER／ACK、GENERATION_CLOSE／CLOSED、renderer GL thread 反向銷毀（texture → EGLImage → AHB），但**從未做過 runtime qualification**。
- pump 在 UNREGISTER 等待時 DEFER legacy record，在 GENERATION_CLOSE 時 CANCEL。

### 5.2 構造分析（決定 pending 格怎麼做）

- X 只有一條 dispatch thread，DoneComposite 同步等待，等待中不 pump client（DESIGN §3，D1 已證明）。
- 所以**任何 client** 都不可能在 direct 交易進行中讓 DestroyPixmap 或 CloseScreen 被 dispatch。這和 DESIGN §2.3「COPY／SOLID in-flight 不適用」是同一個道理。
- 結論：20260913 設計中「pending 時注入 Destroy／Close」的兩格，改用 R7-12／13 的合成 hook（D-9）。client 驅動版本記為 **N/A-by-construction**，附上靜態證明。
- **可以由 client 構造**的 pending 是 **Present GPU copy**：送出 Present 後立刻 destroy window 或斷線。這正是 retirement helper 要保護的地方（R8-C3）。

### 5.3 格子

每格一個 fresh X；PROTO=1、TELEMETRY=1；不得設 TEST env（P 格例外）。

| 格 | 做法 | PASS |
|---|---|---|
| R8-C1 clean Destroy | single-direct SUCCESS → 依序 FreePixmap src、dst → 再以**新的一對** pixmap 做一次 direct | 每個 buffer：UNREGISTER_SEND → UNREGISTER_ACK → RESOURCE_DESTROY；計數器 X／renderer registry current 回到 0、AHB acquire=release、EGLImage create=destroy、texture create=delete、lease current=0；新 pair 的 REGISTER 與 SUCCESS 正常；像素 exact；X 存活 |
| R8-C2 clean Close | single-direct SUCCESS → holder 離開、X TERM（照一般 teardown 順序） | GENERATION_CLOSE → GENERATION_CLOSED；已註冊的 buffer 全部 retire；`GATEA_SUMMARY` 的 registry=0、各資源成對；X 以 clean 路徑結束（非 fatal、非 signal）；`NO_X3_RESIDUE` |
| R8-C3 Present 退役 | client 送 PresentPixmap（不等 CompleteNotify）→ 立刻 DestroyWindow；另一格改成立刻斷線 | 雙分支都可接受：`36 waited=1` → ACK，或 `36 waited=0`；兩者都要：無 fatal、X 存活、無 event 32、pending 計數歸零；client 斷線版額外要求 X 對其他 client 仍正常（再做一次 direct SUCCESS） |
| R8-C4 註冊但未提交 | 建 pair 並完成 REGISTER／READY，不做 Composite → FreePixmap | UNREGISTER → ACK → RESOURCE_DESTROY；lastSubmittedSerial=0 的分支不做 terminal wait；計數器歸零 |
| R8-C5 容量 | 註冊 K 對（K 由 B-1 從原始碼凍結）→ Close；另一格嘗試第 K+1 對 | K 對全部 retire、registry=0；第 K+1 對依 B-1 凍結的預期（pre-publish 拒絕或 fallback），**不得** fatal，除非凍結值就是 fatal |
| R8-D 延遲 record | 另一個 client 持續送 Present 的同時，FreePixmap 一個 Gate A buffer（等待期間 renderer 會送 GPU_COPY_DONE） | UNREGISTER 完成後，被 DEFER 的 record 都有被處理：CompleteNotify 數量等於 Present 數量；沒有 `x-deferred-record-queue` 類 fatal |
| R8-P1 | R7-12 hook | 見 §4.2 R7-12 |
| R8-P2 | R7-13 hook | 見 §4.2 R7-13 |

**共同禁止（所有格）**：UAF／signal、AHB 提前釋放（計數器不成對）、waiter 卡住（2000 ms 內沒有終態）、stale lease、跨 generation 的 READY、renderer registry 洩漏。

**產出**：`runtime-<shaB>/r8-*/`、`GATE-A-P2-R8-RUNTIME-<date>.md`。結論行：`GATE A P2 R8 PASS / <shaB>`。

---

## 6. R9 — Recreate

### 6.1 R9-0 事前確認（唯讀）

- B-1：lorie 會不會在同一程序內 regenerate？這決定 R9-3 要不要做。
- Activity 重用時，renderer 的 Gate A registry 會不會在 unbind 或 rebind 時清空？只能用 renderer registry current 計數器觀察。
- 身分定義：fresh 程序的 generation 可能從 1 重新開始，所以**身分是 (nonce, generation)**，nonce 必須彼此不同。

### 6.2 格子

| 格 | 做法 | PASS |
|---|---|---|
| R9-1 warm Activity | 3 輪，每輪 fresh X PID，Activity PID 不變：REGISTER → direct SUCCESS（exact）→ clean Destroy → clean Close | 3 個 nonce 互不相同；每輪 bind 時 renderer registry current=0；每輪 SUMMARY 資源成對；每輪 `NO_X3_RESIDUE` |
| R9-2 cold Activity | 同上，但每輪之間 force-stop experimental | 同上；另記錄 Activity PID 每輪都不同 |
| R9-3 程序內重生（R9-0 確認存在才做） | 同一 X：最後一個 client 離開觸發 reset → 新 client 再做 direct | GENERATION_CLOSE／CLOSED 發生在 reset 之前；(nonce, generation) 改變；新 REGISTER 成功；舊 READY 不能滿足新的 lookup |
| R9-F1 stale replay | R7-14 hook | 舊 frame 被確定性拒絕或 fatal；新 generation 沒有因舊 frame 產生 READY_MARK |
| R9-F2 復原 | 緊接在 F1 之後的 fresh session | 正常 REGISTER 與 direct SUCCESS；registry 從 0 開始 |

**判準要點**

- nonce 清單寫進 gate 文件並逐一比對。
- 舊 generation 的 registry 計數在新 admission 前必須為 0。
- F1 屬於「預期會死」的格子時，照 §4.4 收尾。

**產出**：`runtime-<shaB>/r9-*/`、`GATE-A-P2-R9-RUNTIME-<date>.md`。

---

## 7. R10 — 資源殘留

### 7.1 R10-0 可觀測性事前確認

| 指標 | 取得方式 | 讀不到時 |
|---|---|---|
| Gate A 計數器 | `GATEA_SUMMARY`（B-0 第 7 項），clean close 時的檔案版本為準 | 無法判 R10，停 |
| X FD 數 | X 在 Termux uid，從 Termux／PRoot 讀 `/proc/<X>/fd` | 停，先修觀測 |
| Activity FD 數 | debug APK 試 `run-as com.waydefu.x11gpu`；只讀自己的程序 | 寫 `not_observable`，**絕不寫 0** |
| RSS／PSS | `/proc/<pid>/status`、`dumpsys meminfo com.waydefu.x11gpu` | 只記錄，不作 ownership 證據 |
| 殘留 | `:3` socket、程序清單 | — |

如果 Activity FD 讀不到，R10 最高只能判 **PASS WITH OBSERVABILITY LIMITATION**。要不要接受由使用者決定（D-7；先例：HANDOFF 的「S3 RUNTIME CLOSED — PASS WITH OBSERVABILITY LIMITATION」）。

### 7.2 R10-1 多輪 clean recreate

R9 PASS 之後才開始。至少 **5 輪**；每輪 fresh X；warm 與 cold Activity 各佔一部分（例如 3 warm＋2 cold，由 R10-0 凍結）。

每輪在相同的檢查點取樣：

| 檢查點 | 時機 |
|---|---|
| K0 | bind 後、第一個 direct 之前 |
| K1 | 同一對做 N 次 direct 之後（建議 N=64） |
| K2 | FreePixmap 全部完成之後 |
| K3 | clean close 之後（X 已結束） |

**PASS**

1. 每輪 K3：registry X／renderer current=0、lease current=0、AHB acquire=release、EGLImage create=destroy、texture create=delete。
2. 每輪 K2：pending 計數歸零。
3. X FD：各輪 K0 之間不得單調成長（容許值 0；先例：D0a 各輪都是 81 → 81 → 81 → 81）。K2 同樣檢查。
4. Activity FD（可觀測時）：同第 3 條。
5. 每輪 `NO_X3_RESIDUE`、無 fatal、無 signal。
6. RSS／PSS 只記錄趨勢，不作為 PASS 或 FAIL 依據。

### 7.3 R10-2 同程序 registry 輪替（建議加做）

同一個 X 內依序建立並銷毀 4K 對不同的 pixmap（K 為 registry 容量），每對做一次 direct。

PASS：registry current 永遠 ≤ K，最後回到 0；AHB／EGLImage／texture 成對；FD 在第 1K 對與第 4K 對結束時相等。

**產出**：`runtime-<shaB>/r10-round<N>/`、`GATE-A-P2-R10-RUNTIME-<date>.md`。

---

## 8. P2 runtime 關帳條件

以下全部成立，才可寫 `GATE A P2 RUNTIME CLOSED`：

- R0–R10 每一格在綁定的 artifact 上 PASS；carry-forward 的格子附 diff 範圍證明並經使用者接受。
- 所有歷史 FAIL cell 原樣保留，並有 superseding 註記。
- HANDOFF／TEST-MATRIX／AGENTS 已同步；Stable 驗證未碰。

**Production Gate A 仍然 BLOCKED**，理由沿用 PLANNER-BRIEF P3-11：CPU ownership release、import-ready ACK、per-serial 成敗、acquire／release publication、generation drain、imported AHB producer-fence。另加入本計畫新增的缺口：Activity 斷線或重建時的 quiesce＋rebind（D-2）。

---

## 9. Gate H — hybrid／size router

### 9.1 定義與現狀【包內已證】

- **定義**：依操作條件（尺寸／面積、格式、候選路徑）決定走 CPU pixman 還是 GPU 路徑的 router，也包含 lifecycle routing。
- `GATE-A-D-ARCHITECTURE-REVIEW-20260911.md`「Must not change」第一項就是「Gate H/router; size threshold」。
- `D0B-R1-LUNA-E-SCOPE-AUDIT.md`：「No hybrid/lifecycle routing」。
- 狀態：`GATE H HOLD`（HANDOFF）。

### 9.2 現有證據

| 量測 | 結果 | 出處 |
|---|---|---|
| T1 五格（warm reuse、立即 GetImage，每格 500 筆） | R3/CPU 中位數：1x1 **1.07**、5x24 **0.94**、32x32 **0.92**、64x64 **0.94**、256x256 **1.51**；兩邊都有約 2.7–3 ms 的固定成本，與尺寸幾乎無關 | `B3A-T1-5CELL-20260910.md` |
| Tier-1 smoke（另一輪） | 1x1–64x64 **1.22–1.30**（CPU 勝）、128 **0.85**（R3 勝）、256 **1.10**（CPU 勝）；固定成本約 4–5 ms | `B3A-RUN-20260910.md` |
| U4 C2 batch16（64x64，6 組配對） | R3/CPU 中位數 **1.299×**，六組全部 > 1；p95：CPU 4.94 ms、R3 6.61 ms | `GATE-P2-B.3a.md` |
| D0a（64x64 uniform steady-state） | prepare 0.533 → 0.33 ms、clone 0.249 → 0.003 ms、done 0.930 → 0.5–0.65 ms：PERFORMANCE-POSITIVE（僅限此工作量） | `GATE-D0A-DESIGN-20260912.md` |
| Gate A direct | **沒有任何效能數據**（R4／R5 只驗正確性） | HANDOFF |
| Present 1080p、EXA Copy／Solid | GPU 沒有比 CPU 快 | `TEST-MATRIX.md` |
| 可觀測性 | GPU 執行時間 `null`；direct entry 的 `telemetryIndex = INVALID`，B3a phase telemetry 不涵蓋 direct 路徑 | 20260913 設計、B3a |

### 9.3 為什麼仍然 HOLD

1. **沒有穩定的交叉點**：同一尺寸在不同輪次勝負相反（5x24–64x64：0.92–0.94 對 1.22–1.30；256：1.51 對 1.10）。
2. **固定成本淹沒尺寸效應**：每次 2.7–5 ms 的往返加上立即 GetImage 回讀，Amdahl 效應遮蔽了 composite 本身的差異（B3a 自己的註記）。
3. **最有希望的兩個候選缺數據**：D0a 只量過單一尺寸，Gate A direct 沒量過。
4. **router 會新增 ownership 轉換**：同一個 pixmap 在 CPU 與 GPU 路徑之間切換，會和 Gate A 的 pair lease、pending、quiescence admission 互動。沒有設計審查就不能做。

→ 在這些證據下定門檻等於猜測。Gate H 維持 HOLD，先做 H0–H3 量測與裁決。

### 9.4 階段

| 階段 | 內容 | 前置 | 產出 | 出口 |
|---|---|---|---|---|
| **H0 授權與時機** | 使用者決定 D-6 | — | 決策紀錄 | 建議：P2 runtime CLOSED 之後，APK 穩定、可納入 direct 候選、不和 R7–R10 搶裝置時間 |
| **H1 量測設計凍結** | 見 §9.5 | H0 | `gate-h/GATE-H-H1-MEASUREMENT-DESIGN-<date>.md` | Sol High 審查 PASS |
| **H1b 儀器對等** | 以 client 端每次操作的 wall time 當主指標（所有候選一致）；server phase 只當輔助；缺的欄位寫 `null`。若主指標雜訊過大，才提案給 direct 路徑加 phase telemetry（屬架構邊界） | H1 | 設計附錄 | — |
| **H2 普查** | 在已安裝的 P2 關帳 APK 上跑 §9.5 的矩陣；每個 session 一個 fresh X；每 session 先過 1514 oracle；做 exact-count 驗證（`next_record == expected`，沿用 B3a 做法） | 裝置授權 | `gate-h/h2-*/` ＋ 普查總表 | 所有 session 的正確性閘門 PASS |
| **H3 交叉點裁決** | 見 §9.6 決策樹 | H2 | `GATE-H-H3-DECISION-<date>.md` | 使用者確認結果 |
| **H4 router 設計審查** | 只有 H3-B 才進入；約束見 §9.7 | H3-B | router 設計文件 | Sol High 審查＋使用者授權 |
| **H5 實作** | default-off 旗標；單一 writer；靜態 verifier；ARM64 雙 build；CI | H4 | commit／CI／artifact | artifact QUALIFIED |
| **H6 qualification** | 見 §9.8 | H5 | `GATE-H-H6-<date>.md` | `GATE H PASS`，或 FAIL 並回到 HOLD |

### 9.5 H1 量測矩陣（草案，H1 審查時凍結）

**候選**（env 名稱都是包內已有的）

| 候選 | 設定 |
|---|---|
| CPU | `TERMUX_X11_B3A_TELEMETRY=1 TERMUX_X11_B3A_CANDIDATE=cpu TERMUX_X11_DISABLE_EXA_GPU=1` |
| R3 staging | `TERMUX_X11_B3A_TELEMETRY=1 TERMUX_X11_B3A_CANDIDATE=r3` |
| D0a | 在 R3 設定上加 `TERMUX_X11_D0A=1` |
| Gate A direct（僅 qualification，不得進日用） | `TERMUX_X11_GATEA_PROTO=1` |

**尺寸桶**：1x1、5x24、32x32、64x64、128x128、256x256、512x512、1024x1024。1024 以上或全螢幕要先確認記憶體與 display 0 解析度安全。

**模式**

- M1 無回讀吞吐：連續 composite，最後只做一次 GetImage 驗證。**這是主要模式**，用來移除 Amdahl 遮蔽。
- M2 立即 GetImage：和歷史數據對照用。
- M3 cold 與 warm reuse。
- M0 地板：最小操作（例如 1x1 no-op 類），估計固定往返成本。

**統計**

- 排除 warmup；每格至少 500 筆 measured。
- 每個候選至少 3 個配對 session，採 ABBA 排序抵銷溫度漂移。
- 每個 session 記錄 thermal（`dumpsys thermalservice`，唯讀）、充電狀態、螢幕狀態。
- **雜訊帶** = 同一候選重複 session 之間的最大中位數差距。
- 「勝出」必須同時滿足：所有配對中，中位數比值都超出雜訊帶；而且 p95 沒有惡化超過雜訊帶。

**禁止**

- 不得動 predicate，不得擴大 GPU 覆蓋範圍。
- 不測外接 3440×1440（會碰 HDMI 與 Stable 所在環境；需要另開專屬規劃）。
- XFCE 實際負載只能是有時間上限的隔離 session，結束後立即停止（先例：P2-B.2 的 45 s bounded XFCE）。

### 9.6 H3 決策樹

```text
H2 結果
 ├─ H3-A：任何 GPU 候選在任何尺寸桶都沒有穩定勝過 CPU（超出雜訊帶）
 │        → Gate H CLOSED / NOT JUSTIFIED
 │        → 維持現行 predicate＋fallback；投入改為降低固定成本（D0a 擴展、Gate A production 前提）
 │        → 固定成本大幅改變後才重新評估
 ├─ H3-B：某個候選在面積 ≥ T（或某個區間）時，所有重複 session 都穩定勝出
 │        → 進入 H4，門檻表必須附量測條件（APK SHA、解析度、thermal、模式）
 └─ H3-C：結果不一致、被雜訊主導
          → 只允許一次方法修正（例如 M1 的批次大小、固定 CPU 親和性）
          → 有界重測一次；仍然不一致就視同 H3-A
```

### 9.7 H4 router 設計約束（審查必查）

1. **只在 Prepare 決定路由**：在任何 lock／unlock／lease／publish 之前；交易進行中絕不切換。
2. **只選已經 qualified 的路徑**：router 不得放寬 predicate，只能讓原本 GPU-eligible 的操作改走 CPU，不能反過來擴大。
3. **不新增提前釋放**：GPU → CPU 切換沿用既有 Done wait／pending 屏障；Gate A lease 期間 CPU 存取既有的拒絕行為不變。
4. **不改 admission**：`gateAQueueSemanticallyQuiescent()` 語意不變。
5. **加 hysteresis**：避免尺寸交替時讓 D0a 的單格 cache（以 descriptor 為 key）不斷 miss。
6. **Gate A direct 不得進日用 router**：Production Gate A 解除封鎖之前，router 候選只能是 CPU／R3／D0a。
7. **default-off**：旗標名稱在 H4 凍結；OFF 時必須逐 byte 等價（R1 式驗證）。
8. **決策可觀測**：append-only 的 route 事件或 counter（route=cpu|gpu、reason），不改既有 ABI。

### 9.8 H6 qualification

| 類別 | 判準 |
|---|---|
| 正確性 | router OFF：R1 等價（1514 exact、stress）；router ON：1514 exact，negative predicate 仍走 software |
| 跨路徑順序 | 同一個 pixmap 連續操作讓路由在 CPU／GPU 間切換：沿用 R6-D1 式的 REQUEST／CALLBACK／SUCCESS 順序判準，GPU 未完成前 CPU 不得存取 |
| lifecycle | router ON 時跑 R10 式 5 輪殘留檢查 |
| 效能 | router ON 對比每個尺寸桶的最佳固定候選：沒有任何桶惡化超出雜訊帶；混合尺寸工作量勝出超出雜訊帶 |
| 實際負載 | 隔離、有時間上限的 XFCE session：fatal／signal 為 0；結束後停止 |

### 9.9 Gate H 風險

| 風險 | 對策 |
|---|---|
| thermal throttling 讓門檻漂移 | ABBA、記錄 thermal、門檻表附條件、定期重測 |
| 固定成本主導，尺寸效應量不出來 | M0 地板＋M1 無回讀為主 |
| telemetry 本身干擾量測 | 以 telemetry OFF 的 wall time 為主，ON 只做歸因 |
| D0a cache 抖動 | hysteresis、每個尺寸桶單獨量 D0a |
| 門檻過度擬合 fixture | H6 必須包含混合尺寸與實際負載 |
| 誤把 direct 放進日用 | 約束第 6 條＋靜態 verifier |

---

## 10. 決策清單（2026-09-15 使用者「照建議」全部定案）

定案只決定方向，**不是**寫碼、commit、push、CI、install 或 device 授權；那些仍依 §11 逐項申請。之後若要變更，在表下新增「變更」列並寫明理由，不直接改寫原列。

| 編號 | 問題 | 選項 | 定案 |
|---|---|---|---|
| **D-1** | Present GPU copy 碰到「沒有 surface」怎麼處理（F-1） | (a) 維持 fail-stop／(b) 區分 stall 與 loss／(c) 延遲退役清單 | **(b)**；修改 `InitOutput.c` 的 Present wait 語意仍需 G2 授權 |
| **D-2** | Activity 真的斷線時若仍有 pending Present | 接受 fail-stop（qualification）／現在就做 rebind 協定 | **接受**；記入 Production Gate A；用 R7-P2 證明 |
| **D-3** | 事件 35／36（／37）放哪裡 | R6 commit／Artifact B | **Artifact B** |
| **D-4** | retirement APK 要重驗哪些 | 只 R1＋R6 cells／R1–R5 全部 | **R1＋R6 cells**；R3–R5 carry-forward 附 diff 證明；因 D-1=b 會改 `InitOutput.c`，**加跑 R3** |
| **D-5** | Artifact B 要重驗哪些 | R1–R4／再加 R5＋R6-D1 | **R1–R4 必跑，R5＋R6-D1 也跑** |
| **D-6** | Gate H 普查什麼時候做 | P2 關帳後／更早（只測 CPU／R3／D0a） | **P2 關帳後** |
| **D-7** | Activity FD 讀不到時 R10 怎麼判 | 接受 PASS WITH OBSERVABILITY LIMITATION／補觀測後才判 | **先嘗試 `run-as`**；讀不到時停下，再由使用者決定 |
| **D-8** | quiescent 分支嚴格度（J-1） | 保留／放寬 | **保留**，標明為構造要求 |
| **D-9** | R8 pending 格改用合成 hook（§5.2） | 接受／另找 client 構造 | **接受**（client 驅動在單一 dispatch thread 下不可達） |

---

## 11. 授權閘門與執行順序總表

| # | 閘門 | 需要的明確授權 | 解鎖 |
|---|---|---|---|
| G1 ✅ | D-1～D-9 決策 | **DONE 2026-09-15**（照建議） | A1 |
| G2 | R6 source 修正（含 D-1=b 的 `InitOutput.c`）＋judge＋patch 正規化 | source 授權 | A2–A5 |
| G3 | R6 commit | commit 授權 | A6 前半 |
| G4 | R6 fork push＋CI | push／CI 授權 | A6 後半 |
| G5 | R6 install＋R0／R1／D1／D2-INFLIGHT／D2-OOM | install／device 授權 | A7 |
| G5b | R6-D3 背景化操作 | display 0 背景化／前景化的明確授權 | A7-D3 |
| G6 | Artifact B 設計審查結果 | 審查 PASS＋source 授權 | B-2 寫碼 |
| G7 | Artifact B commit、push、CI、install、重驗 | 三段分開授權 | R7 |
| G8 | R7 cells | device 授權（逐批） | R8 |
| G9 | R8 cells | device 授權 | R9 |
| G10 | R9 cells | device 授權 | R10 |
| G11 | R10 cells＋D-7 | device 授權 | P2 關帳 |
| G12 | Gate H H1 設計、H2 普查 | 設計審查＋device 授權 | H3 |
| G13 | Gate H H4–H6 | 只有 H3-B 才申請 | router |

**執行者分工**（AGENTS.md）

- **Sol High**：F-1 裁決、B-0 ABI 審查、R7 各格預期值凍結、H3 裁決、H4 router 設計。
- **Luna Max**：原始碼 scout（【需原始碼確認】項目）、harness／judge 草稿、log 彙整、普查數據整理。同時最多 2 個。
- **writer**：一個 session＝一個 worktree。R6 用 `src/f8-ahb-gatea-r6-retire`；R7–R10 另開 `src/f8-ahb-gatea-r7`；Gate H router 之後再另開。

---

## 12. 風險登錄

| 風險 | 機率 | 影響 | 對策 |
|---|---|---|---|
| F-1 確認為「立即 fatal」，D-1=b 需要改 `InitOutput.c` 而擴大 R6 審查範圍 | 中高 | R6 關帳延後 | A1 先確認；範圍只限 Present wrapper，不動 EXA／direct wait |
| patch 正規化後 CI 仍失敗 | 中 | 多一輪 CI | F-2 的 dry-run／reverse／byte 比對全部在本機先過 |
| 新 APK 的 D2-INFLIGHT 仍走 quiescent 分支 | 高（物理上就是這樣） | 無（雙分支已接受） | 不再嘗試構造 busy 分支；不加 delay |
| fatal 格子 logcat 尾端遺失 | 高 | R7 判 INCOMPLETE | B-0 第 7 項 fatal SUMMARY＋第 8 項 ring dump |
| ART JIT 類 SIGSEGV（`0x4800xxxx`） | 低到中 | 格子中斷 | 依 AGENTS 規則：OBSERVED → 申請一次有界重跑；不改 C |
| 背景化操作誤觸 HDMI／Stable | 低 | 紅線 | 只用指定 display 0 的指令；有疑慮就停；Stable 前後比對 |
| 合成 hook 在未 arm 時改變行為 | 低 | R1 等價失效 | 靜態 verifier＋B-2 的 R1–R4 重驗 |
| R10 的 Activity FD 無法觀測 | 中 | R10 判定受限 | D-7 |
| Gate H 普查被雜訊主導 | 高 | 無結論 | M0／M1、ABBA、H3-C 只允許一次方法修正 |

---

## 13. 文件同步清單（每個關帳點）

| 時點 | 更新 |
|---|---|
| A1 | 新增獨立複核文件；不改權威檔 |
| A8 | `HANDOFF.md`（狀態行、Next、刪除「100% sound」）；`TEST-MATRIX.md:3`；`AGENTS.md`（R6 邊界、R7 解鎖條件）；DESIGN §14 與 HOLD 表頭加 superseding 註記；physical race analysis 的 Adreno 830 → 840 勘誤與時間數據降為推測；`PLANNER-BRIEF` 標記為歷史 |
| B-0 | 新增 `p2-r7-design/`；review skill 加 R7 判準章節 |
| R7／R8／R9／R10 各自關帳 | 對應 gate 文件＋HANDOFF 狀態行 |
| P2 關帳 | `GATE-A-P2-RUNTIME-CLOSED-<date>.md`；TEST-MATRIX 的 Gate A 列 |
| H3 | `GATE-H-H3-DECISION-<date>.md`；HANDOFF 的 `GATE H` 狀態行 |

「Done」的定義沿用 AGENTS.md：gate 文件已更新、依 TEST-MATRIX 做過壓力測試、HANDOFF 的 Next 仍成立、Stable 驗證未碰。
