# 交接：V1-Core 最終收斂工程（2026-09-23）

你接手的是 **waydefu/GPU 的 V1-Core 最終收斂工程**。目標不是做完下一個 packet，
而是一路自主執行到 **V1-Core 最終 acceptance / release decision**。

---

## 0. 先讀這三個，然後就開始動手

```
1. /root/.claude/CLAUDE.md                          全域規則 + 這個專案的結構與紅線
2. /root/projects/GPU加速/STATUS-HANDOFF-20260921.md 現行狀態（§6.5 R9 / §6.6 D-06 / §6.7 R10 / §6.8 GAP-4 / §6.9 P2）
3. evidence/session/gate-a-a1/planning-v2/p2-closure/P2-CLOSURE-REPORT.md
```

**不要重讀整棵 evidence 樹再開始。** handoff 的 §6.x 就是現行結論，舊敘述都已標 SUPERSEDED。

## 1. Current authority

```
repo authority    waydefu/GPU 最新 main（2026-09-23 時為 f6f23ef，PR #17 已合併）
產品 artifact     dc94485a7ef4f74cada36ea3c1d35d0aa0f48693
                  APK 1bd8bef0909249737ea43acf0a35f3c995d941e1badbfcf370e5cd854f4bb8a3
                  CI 35673085569 · versionName 1.03.01-dc94485-22.09.26
tooling fork      waydefu/termux-x11 @ eb7435e
                  branch feat/gatea-r8-lifecycle-support-20260918
```

```
R7   13/13 PASS   CARRY_FORWARD 到 dc94485（13/13 predicate intact，4 個已實機重現）
R8   10/10 PASS   CARRY_FORWARD 到 dc94485（claim scope：無 -noreset，不含 DE_RESET continuity）
R9   2/2 PASS     直接綁 dc94485
R10  4/4 PASS     直接綁 dc94485（A/B/C/E），無 leak
D-06 DECIDED      V1 不做 generation 2 / same-X reconnect，採 fresh-process recovery
p2_runtime_closed = TRUE（17/17）
production_gate_a_closed = false
v1_core_qualified        = false
```

## 2. 你的授權範圍（使用者 2026-09-23 明確給的）

可自行：查 source、查 runtime evidence、查 upstream、建 design packet、改 planning/docs/tooling、
新增 fixture/judge/verifier、移除已被 source proof 證明不可構造的測試、定義 metric 與 noise/tolerance、
做 RCA、實作必要 product fix、build、CI、安裝 experimental artifact、跑 X3 runtime qualification、
建 evidence、開 commit/branch/PR、更新 handoff、**直接簽 carry-forward approval**。

遇到問題的流程：**查 product source → 查 runtime evidence → 查官方/upstream → 自己判斷 → 記錄理由 → 繼續施工**。
不要每做一小步就停下來問。

### 只有這些情況才停

必須碰 Stable `:1` · 必須重新引入 generation 2 · 必須大改 Gate A architecture ·
必須破壞 public ABI/protocol · 必須降低 safety invariant · 必須刪除或重分類 frozen evidence ·
必須做不可逆高風險裝置操作。其他全部自行處理。

## 3. 下一階段（依序）

```
XFCE baseline → B.3 telemetry / performance → Production Gate A gap inventory
→ 必要 RCA / patch / CI / install / requalification → Gate H（僅需要時）→ Gate W
→ V1 acceptance audit → release decision
```

**XFCE 有硬前置**：計畫書 §11 規定 `V2-XFCE-DESIGN-FREEZE` 之前不得執行任何 XFCE session，
且必須先凍結 13 項參數（duration / resolution / compositor / window choreography / terminal …）。
未凍結的兩次執行不可比較。先做 design freeze。

### 兩個 OPEN 項目

```
D-04   R10 帶過去的 activity.maps_count 跨 session 上飄（+10～+22 / 5 輪，idle 帶寬 2）。
       不是 Gate A 記帳問題（同輪 counter 精確，且 R10-C 每輪 process 全新也照樣飄）。
       要收斂：20+ session 長序列 + /proc/<pid>/maps 差分。
R-30   三個 ahb_*_fence_fd metric 在 dc94485 完全沒有 trace site，凍結為 null。
       要答 fence-fd ownership 必須改產品（D-12 類決策）。
```

## 4. 這個專案的陷阱（我這幾輪真的踩過）

```
Gate A 只加速 PictOpOver，且必須 a8r8g8b8 → x8r8g8b8。其他組合靜默走 CPU fallback。
counter 索引：c18/c19 才是 registry-current，c25/c26 是 UNREGISTER/RESOURCE_DESTROY。
              讀錯的話，一個完全乾淨的 close 會被判成「每邊漏 8 個」。
              對照表：src/f8-ahb-gatea-r7-p1-arm/tests/common/gatea_counters.py
dump 只在 fatal / clean close / terminate 時寫。健康的 cell 沒有 GATEA_SUMMARY 是正常的，
              不是漏抓；要改讀 GATEA_BIND 與 live telemetry 事件。
別用 SIGTERM 逼 dump：到不了 CloseScreen，還會讓 renderer 吃 r-hup。
X:3 的 dump sink 是本機路徑，不是 device——別用 adb shell cat。
R7-era 證據格式不同：judge.txt / installed-package.txt / logcat-follow.txt。
              只認 R8+ 的檔名會讓整包 R7 從掃描裡消失（我踩過，61 → 114 attempts）。
ADB endpoint 每次都變，一律 mdns 重探；lane 只用 5038。
```

## 5. 證據紀律（違反就等於作廢）

```
frozen attempt      永久保留，不重判、不重跑、不改寫。工具改了也不回頭改判決。
null ≠ 0            量不到寫 null。
INVALID ≠ FAIL      payload 沒走到那條路 = INVALID（無資訊），不是失敗。
expected fatal      某些 cell 的 PASS 條件就是「那個 halt 有出現」。
先定 threshold      tolerance 必須在看到受判資料前凍結；事後調 = 整批作廢。
工具出錯要留痕      修正寫進 commit / 報告，錯誤版本不抹除。
不會失敗的對照組    不是對照組——驗證工具時一定要有一個「應該要紅」的案例。
```

最後一條我在 P2 closure 踩到兩次：`verify_r7_predicates` 第一版對 R7 全回 INTACT，
**同時**對唯一一個 token 被移進 `#else` 的 cell 也回 INTACT——那批結果不能用。
另一次是 EVIDENCE 項，我第一版把對不上的 manifest 分流成「planning only」讓它變綠，
**那是放寬 predicate**，後來改成把 manifest 真正修好。兩次都寫在 P2-CLOSURE-REPORT.md §「第一次跑是紅的」。

## 6. 怎麼推 evidence

`/root/projects/GPU加速` **不是 git repo**。流程：clone `waydefu/GPU` 到 scratchpad →
複製檔案 → branch → PR。evidence 只推判決依據那一份（不含 `raw-logcat.txt` /
`collect-input.txt` / `x3.maps`），`sha256sums.txt` 仍是完整本地清單，另附 `PUBLISHED-SUBSET.md`。

## 7. 現在就可以開始

裝置乾淨（無 X3 殘留、Stable pid 20881 未動）、fork 無未提交變更、PR 全部已合併。
建議第一步：**`V2-XFCE-DESIGN-FREEZE`** —— 先把 13 項參數凍結，才有資格跑任何 XFCE session。
