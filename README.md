# waydefu/GPU — POCO F8 Ultra Termux:X11 研究紀錄與接續包

完整 runtime 權威樹在工作站 `/root/projects/GPU加速`。
這裡是 GitHub 上可把專案交給下一手的切面：**Markdown + 凍結 judge + 證據 + harness + core-src + skills**。

本倉庫 **沒有** GitHub status checks。Docs PR 綠燈 ≠ 裝置 qualification。
`termux-x11` fork 的 artifact CI 是 **另一個倉庫**。

## 先讀

1. **[`STATUS-HANDOFF-20260921.md`](STATUS-HANDOFF-20260921.md)** ← 入口（含 §6.5 R9 / §6.6 D-06 / §6.7 R10）
2. [`V1-CORE-EXECUTOR-MASTER-PLAN-V2.3.md`](V1-CORE-EXECUTOR-MASTER-PLAN-V2.3.md) — 計畫書；**§8/§9 有部分已被 R9/R10 取代，以 handoff 的 SUPERSEDED 標記為準**
3. [`ADB-CONNECT.md`](ADB-CONNECT.md) — 連線（endpoint 每次都變，一律用 mdns 重探，不要沿用舊值）
4. [`WORKTREE-MAP.md`](WORKTREE-MAP.md) — source SHA / 遠端
5. [`HANDOFF.md`](HANDOFF.md) — 完整歷史 ledger

## 現況（2026-09-22）

| 項目 | 狀態 | 綁定的 artifact |
|---|---|---|
| R6 | PASS / 凍結 | `0f1e546` |
| R7 | **13/13 PASS**（凍結，永不重跑） | `a4c8177f` 系 |
| R8 | **10/10 PASS** | `b984ded` |
| R8 於 current artifact | **僅 2 格 smoke**（R8-D、R8-P2）+ offline judge replay 10/10 一致 | `dc94485` |
| R9 | **2/2 PASS**；另 6 格 source-proven 不可構造 | `dc94485` |
| R10 | **4/4 PASS**（A/B/C/E），無 leak | `dc94485` |
| D-01 `-noreset` | ACCEPTED | — |
| D-02 multi-epoch 觀測 | IMPLEMENTED + SMOKED | `dc94485` |
| D-06 V1 lifecycle | **DECIDED**：不做 generation 2，採 fresh-process recovery | — |
| D-04 resource leak disposition | **OPEN**（R10 帶一個 maps drift 過去） | — |
| P2 closure | **未完成** | — |
| Production Gate A | **BLOCKED** | — |
| V1-Core | **NOT QUALIFIED** | — |

### 兩個 artifact 權威，不可混判

```
b984ded   R7 與 2026-09-22 之前所有 R8 證據的權威
dc94485   R9 / R10 / D-02 的權威。CI 35673085569
          APK SHA256 1bd8bef0909249737ea43acf0a35f3c995d941e1badbfcf370e5cd854f4bb8a3
          versionName 1.03.01-dc94485-22.09.26
```

兩邊的證據 **NOT poolable**。上表把「R8 10/10」和「R8 於 current artifact」分兩列，
就是因為前者綁 `b984ded`——那是 P2 closure 要處理的 carry-forward 決策，不是已完成項。

R8 還有一條 claim-scope：10/10 是在 **沒有 `-noreset`** 的歷史啟動設定下取得的，
其 claim 不包含 same-process DE_RESET continuity。R8 與 R9/R10 的證據在這個軸上
**configuration-distinct**，同樣不可混判。

## 三條紅線

```
Stable       com.termux.x11 / DISPLAY :1 是日常使用中的機器，絕對不碰
實驗只在      com.waydefu.x11gpu / DISPLAY :3
ADB lane     只用 5038；5037 不殺不重用
證據          consumed attempt 永久凍結，不重判、不重跑、不改寫
```

## Gate A 三個會反覆咬人的事實

1. **Gate A 只加速 `PictOpOver`**，而且來源必須 `a8r8g8b8`、目的必須 `x8r8g8b8`。
   其他組合靜默走 CPU fallback，量到的東西跟 Gate A 無關。
2. **沒有可到達的 generation boundary。** 每個 X process 只 bump 一次 generation，
   第二次到不了。`x-bump-unterminal` / `x-share-in-lease` / `r-rebind-busy` 都是純防禦碼。
   逐行證明：[`COLD2-ROUTE-SEARCH.md`](evidence/session/gate-a-a1/planning-v2/r9-fixture/COLD2-ROUTE-SEARCH.md)
3. **counter 索引會騙人。** `c18`/`c19` 才是 registry-current，`c25`/`c26` 是
   UNREGISTER / RESOURCE_DESTROY。讀錯的話，一個完全乾淨的 close 會被判成漏 8 個。
   對照表與靜態檢查在 termux-x11 fork 的 `tests/common/gatea_counters.py`
   （branch `feat/gatea-r8-lifecycle-support-20260918`），不在本 repo。

## 主要產出位置

```
R9   evidence/session/gate-a-a1/planning-v2/r9-agg/V2-R9-AGG.md
R10  evidence/session/gate-a-a1/planning-v2/r10-agg/V2-R10-AGG.md
     evidence/session/gate-a-a1/planning-v2/r10-design/V2-R10-DESIGN.md
D-06 evidence/session/gate-a-a1/planning-v2/d06/D-06-DECISION.md
runner evidence/session/gate-a-a1/p2-r9-runtime/run-r9-one-cell-dc94485.sh
       evidence/session/gate-a-a1/p2-r10-runtime/run-r10.sh
```

## 證據發佈範圍

裝置證據只發佈**判決所依據的那一份**，不含 bulk capture：
沒有 `raw-logcat.txt`、`collect-input.txt`、`x3.maps`，`env.txt` 縮成 `env-cell.txt`
（只留 `TERMUX_X11_*` 與 `CELL_ID`/`DISPLAY`，其餘是 session 內部狀態）。
`sha256sums.txt` 仍是**完整**的本地清單；R9 與 R10 的 runtime 目錄各有一份
`PUBLISHED-SUBSET.md`，附一行可直接跑的 `sha256sum -c` 驗證實際推上來的部分。

不含：完整 git worktree、xserver submodule、APK、unstripped ELF、`.gradle`。

## Docs PR 圖

```
#1  R6 PASS 0f1e546                                   merged
#2  B-2 RCA + EXA Composite timeout-repair             merged
#3  27d8d1b stall observation                          merged
#4  feeaa56 CASE_LOOP                                  closed，未 merge
#5  B-2 PASS 7549e36                                   merged
#6  fdfb1ce R7-04 PASS + 接續包                         merged
#7  V1-Core 執行計畫                                    merged
#8  R8 lifecycle qualification 設計                     merged
#9  5a782f6 install + R8-C1 attempt-05 INVALID          merged
#10 b984ded install + R8-C1 ADB restored                merged
#11 R8 10/10 PASS — 套件原本量的是 CPU fallback          merged
#12 R9 2/2 PASS + Gate A 沒有可到達的 generation boundary merged
#13 D-06 定案 + R10 依實際可達 lifecycle 重建            merged
#14 R10 完成：四個 series 全 PASS，無 leak               merged
```
