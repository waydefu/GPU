# PGA-GAP-2 非同步原型 · XFCE 三方比較 — 凍結（2026-09-24，任何 GA 的 XFCE 資料之前）

## 目的
非同步原型（`TERMUX_X11_EXA_ASYNC=1`）在 op 層已過 ASYNC_LATENCY_IMPROVED。本輪回答：**在凍結的 XFCE 劇本下，X 的反應是否跟著改善**。
不是 baseline qualification，不與 XFCE-FREEZE-V3 的 baseline 資料合併。

## 方法（與 RCA-XFCE-3 相同，保可比性）
- runner：`p2-xfce-runtime/run-xfce-v3.sh` 衍生版 `run-xfce-v3-11b3b79.sh`（只換產物綁定；劇本、設定、凍結工具清單不變）。
- 取樣：`tests/pga/rca_sampler.py`（x_rtt 每 250 ms 一次 X 往返、每 3 s 一次 choreo 相同的 `xdotool search`、每 5 s CPU）；
  彙總：`tests/pga/rca_report.py`（choreography 視窗 150 s）。
- 產品：`11b3b79`（APK `59e89a9a…7764`）。三組只差 X 環境：
  - **G**：runner 原樣（PROTO=1）
  - **GA**：G + `TERMUX_X11_EXA_ASYNC=1`
  - **C**：G + `TERMUX_X11_DISABLE_EXA_GPU=1`
- 已知偏差：runner 固定開 Gate A 遙測（TELEMETRY=1，clean close 所需），三組同樣帶著；報告註明。
- 變體與順序：先 **C0**（compositor off，日常 :1 的設定），順序 `G GA C C GA G`（交錯分攤漂移）；時間允許再做 C1，同順序。

## 有效性（每一次擷取）
- `XFCE_CAPTURED`、Stable pid 前後相同、螢幕全程亮；rca `rtt_ms_window.n ≥ 500`。
- GA 必須在 logcat 看到 `EXA async enabled`，G / C 必須看不到；否則該次 INVALID。
- 劇本本身判 INVALID（例如找視窗超過 3 s）**不使擷取無效**——那正是要量的反應性（同 RCA-XFCE-3）。

## 判準（每個變體分別判；兩次重複都必須成立）
- **XFCE_ASYNC_IMPROVED**：GA 的 `rtt_ms_window.p99 ≤ 0.5 × G`，且 `p50 ≤ G`。
- **XFCE_ASYNC_CPU_PARITY**：GA 的 `rtt_ms_window.p99 ≤ 1.25 × C`，且 GA 的 `xdotool_search_window.over_3s == 0`。
  （只回答「是否到達 CPU 等級的反應」；不因此宣稱比 CPU 快。）
- 其他指標（p90、search p50、各程序 CPU 核數、SF 幀資料）只描述。

## 偏差 1（2026-09-24 00:49，任何 XFCE session 啟動之前）
第一次嘗試 `xfce-c0-g-01` 在 XFCE 啟動前 BLOCKED（不消耗）：`verify-xfce-support.py` 的 `product_tree_unchanged_since_binding`
要求產品樹等於 freeze 綁定的 bfb5769，對 11b3b79 不可能成立（其餘 73 項 PASS）。衍生 runner 改為**只**容許這一項失敗，
其他任何失敗照樣 BLOCKED；完整輸出仍寫入每次擷取的 `verify-xfce-support.txt`。runner 在建立證據目錄前就停下；其 runner.log／rca.log 改名為 `xfce-c0-g-01.blocked-verify.*` 保存，編號沿用。

## 結果 · C0（runtime-11b3b79/xfce-c0-*，6 次全部有效）— **XFCE_ASYNC_IMPROVED：否；XFCE_ASYNC_CPU_PARITY：否**

| | G-01 / G-02 | GA-01 / GA-02 | C-01 / C-02 |
|---|---|---|---|
| rtt p50 ms | 0.401 / 1.029 | 0.534 / 1.034 | 0.635 / 0.972 |
| rtt p99 ms | 96.293 / 46.553 | 55.034 / 69.515 | 9.183 / 8.735 |
| rtt max ms | 445.7 / 105.3 | 407.7 / 292.7 | 17.0 / 19.4 |
| >100 ms 次數 | 5 / 1 | 4 / 2 | 0 / 0 |
| search over 3 s | 0 / 0 | 0 / 0 | 0 / 0 |

- rep 01：GA p99 55.0 > 0.5×G 48.1；rep 02：GA p99 69.5 > 0.5×G 23.3 → IMPROVED 否。GA p99 對 1.25×C（11.5 / 10.9）→ PARITY 否。
- 描述：三組 p50 相近；**GPU 兩組都有 50–450 ms 的尾端尖峰，C 沒有**。非同步原型沒有消除尖峰。

## PGA-GAP-5 因果檢驗 — 凍結（2026-09-24，新 artifact 建置前、任何門檻資料之前）

- 開關：X 環境變數 `TERMUX_X11_GPU_MIN_PIXELS=4097`（寬×高 < 4097，也就是 ≤ 64×64 的 pixmap 不升級成 AHB）。門檻取自 C0 資料：
  G/GA 每次共享的約 2006 個 buffer 中 89% ≤ 64×64。這是**實驗**，不是路由決定。
- 組別：**GAT** = GA + 門檻；**C** 對照（新 artifact 不與 11b3b79 合併，C 重跑）。變體 C0，順序 `GAT C C GAT`。
- 有效性同上，另加：GAT 必須在 logcat 看到 `GPU min pixels 4097`。
- 判準（兩次重複都必須成立）：
  - **GAP5_CAUSAL_SUPPORTED**：GAT 的 `rtt_ms_window.p99 ≤ 1.25 × C`，**且** GAT 的「Sent shared buffer」次數 ≤ 200（≤ 11b3b79 G 的 10%）。
  - 只有 p99 達標而共享次數沒降 → 不支持（機制不符）；共享次數降了而 p99 沒達標 → 否證「升級是主因」。
- 正確性：p_async_oracle seed 11 在 GAT 必須 0 錯（門檻不得改變像素結果）。

## 偏差 2（2026-09-24 01:37，因果檢驗的第一次嘗試，X3 未啟動）
`runtime-709dfac/xfce-c0-gat-01` 在啟動 X3 之前結束，runner.log 無任何訊息、raw-logcat 0 bytes：harness 的 `verify_logcat_pid`
在 `start_logcat` fork 出的子程序尚未 exec adb 時檢查 `/proc/<pid>/exe`，在 set -e 下無聲結束（既有競態）。等同 BLOCKED、不消耗；
目錄改名 `*.blocked-logcat-race*` 保存。`run-xfce-v3-709dfac.sh` 在驗證前最多等 2 s 讓 exec 完成，驗證函式本身不變。

## 因果檢驗 · 第一輪（runtime-709dfac/xfce-c0-{gat,c}-0{1,2}）
- **GAT-01 INVALID（凍結）**：rtt.txt 只有 `RTT_CONNECT_FAIL`（rca_sampler 在 X 接受連線前就啟動 x_rtt、且不重試），`rtt_ms_window.n` = 0 < 500。
  其 search p50 0.119 s、over_3s 0，共享 buffer 55 次（僅描述）。rca_sampler 已改為重試（fork 9422f6b）。
- 有效：C-01（p99 12.075）、C-02（p99 10.243）、GAT-02（p99 9.324、max 83.9、>100 ms 0 次、共享 55 次）。
- rep 02（GAT-02 對 C-02）：p99 9.324 ≤ 1.25×10.243 = 12.80 ✓；共享 55 ≤ 200 ✓。
- **補跑規則（在看到任何補跑資料之前寫下）**：rep 01 改由新的一對 `GAT-03` 對 `C-03`（順序 GAT-03, C-03）取代；
  GAT-01 / C-01 不再用於判準。判準本身不變。

## 因果檢驗 · 結果 — **GAP5_CAUSAL_NOT_SUPPORTED**（凍結，不重判）

| 配對 | GAT p99 | C p99 | 1.25×C | 共享次數 GAT | 判定 |
|---|---|---|---|---|---|
| GAT-03 / C-03（rep 01 取代） | 10.213 | 8.054 | 10.068 | 55 | **p99 未過（差 0.145 ms）** |
| GAT-02 / C-02（rep 02） | 9.324 | 10.243 | 12.804 | 55 | 通過 |

- 依凍結判準（兩組都須成立）→ NOT_SUPPORTED。不放寬、不重跑成另一個判定。
- 描述（不作判準、跨產物不可合併）：11b3b79 的 G/GA p99 47–96 ms、每次 1–5 次 >100 ms、max 105–446 ms；
  709dfac 的 GAT 三次有效擷取 p99 9.3–10.2 ms、>100 ms 0 次、max 26–84 ms；C 五次 p99 8.1–12.1 ms。
  共享次數從約 2006 降到 55，與預測的機制一致。
- 判準的敏感點：C 本身的 p99 在 8.1–12.1 ms 之間浮動，1.25 倍的容忍帶小於 C 自己的變異。若要再檢驗，
  須另立判準（例如與同一 artifact 上的 G 比較），並在新資料之前凍結；本輪判定維持原樣。
