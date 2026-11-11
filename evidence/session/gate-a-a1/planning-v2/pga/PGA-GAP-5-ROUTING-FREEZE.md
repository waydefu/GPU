# PGA-GAP-5 依尺寸分流 — 決定與凍結（2026-09-24，任何分流預設版資料之前）

## 決定（使用者，2026-09-24）
方向選「依尺寸分流」：寬×高 < 4097（≤ 64×64）的 pixmap 不升級成 AHB（留在 CPU），較大的仍走 GPU。
依據：PGA-GAP-2-ASYNC-XFCE-FREEZE.md（XFCE 尖峰與小 pixmap 升級強相關；門檻實驗尖峰消失但凍結判準差 0.145 ms）；
op 層小操作在 GPU 上最多與 CPU 持平（11b3b79 opstream）。與先前否決的「窄路由」不同：大面積操作仍走 GPU。

## 產品改動
`TERMUX_X11_GPU_MIN_PIXELS` 預設 4097；設 `0` 關閉（= 11b3b79/709dfac 的舊行為）。非同步（`TERMUX_X11_EXA_ASYNC=1`）仍為選用。
對 Gate A 的影響：來源 ≤ 64×64 的 composite 不再升級 → 不走 direct（收窄），oracle V3 的歸屬檢查預期改變；像素正確性仍為硬性要求。

## 比較（同一 artifact，變體 C0）
組別：**G0**（`GPU_MIN_PIXELS=0`，舊行為）、**GT**（預設）、**GAT**（預設 + async）、**C**。順序 `G0 GT GAT C C GAT GT G0`。
有效性同 PGA-GAP-2-ASYNC-XFCE-FREEZE（rtt n ≥ 500、Stable 不變、螢幕亮、開關在 logcat 可見／不可見）；rca_sampler 用 9422f6b（x_rtt 重試）。

## 判準（兩次重複都必須成立）
- **ROUTING_REMOVES_SPIKES**：GT 的 `rtt p99 ≤ 0.5 × 同一 rep 的 G0 p99`，且 GT 的 `over_100ms == 0`。
- 描述（不作判準）：GT／GAT 對 C 的 p99、max；共享 buffer 次數；各程序 CPU 核數；async 在 GT 之上的增減。
- rep 01 = 前半（G0-01、GT-01、GAT-01、C-01），rep 02 = 後半（C-02、GAT-02、GT-02、G0-02）。

## 正確性（必要）
- p_async_oracle seed 11、12：GT、GAT、C 全 0 錯；GT 與 GAT 的 X byte 雜湊相同。p_depth_probe GT：0 錯。
- Gate A oracle V3（GT）：correctness 類檢查必須全過；attribution 類的變化照實記錄，不判 FAIL（預期收窄）。

## 正確性結果 · f592241（CI 35937188670，APK f9e35b69…075c）— 全部達成

| 檢查 | 結果 |
|---|---|
| p_async_oracle seed 11/12，GT（run-async-proto MODE=G）· GAT（MODE=GA）· C | RGB 錯 0 / 0 / 0；GT = GAT X byte 雜湊（`fc22db73…`、`6a0b5095…`） |
| p_depth_probe GT | 0 |
| Gate A oracle V3，GT（預設分流） | correctness 全過；**attribution FAIL（預期）**：event5 = 0——oracle 的來源都 ≤ 64×64，全部改走 CPU |
| Gate A oracle V3，G0（`GPU_MIN_PIXELS=0`） | **ORACLE_PASS**（36 fresh direct）：直通路徑本身未受影響 |

- 被擋下、不消耗：`runtime-f592241/*.blocked-landscape*`（手機橫向，X root 2464×783）、`oracle-c-s11-01.blocked-logcat-race*`。
- 描述：GT 下 oracle 的 xnz_px 996440（CPU composite 寫入 x8r8g8b8 的 X byte 非 0），G0 直通路徑為 0；oracle 判準不含此項。
- **意涵**：預設分流下，oracle V3 不再覆蓋 Gate A 直通（需要 > 64×64 的來源才會觸發）。之後若要以預設設定驗 Gate A，需要大於門檻的案例。

## XFCE 結果 · f592241（runtime-f592241/xfce-c0-*，8 次全部有效）— **ROUTING_REMOVES_SPIKES**

| | G0-01 / G0-02 | GT-01 / GT-02 | GAT-01 / GAT-02 | C-01 / C-02 |
|---|---|---|---|---|
| rtt p99 ms | 62.972 / 71.968 | **10.139 / 8.994** | 8.868 / 9.551 | 9.696 / 10.996 |
| rtt max ms | 438.7 / 208.1 | 15.2 / 20.4 | 22.6 / 13.3 | 16.6 / 16.2 |
| >100 ms | 3 / 4 | **0 / 0** | 0 / 0 | 0 / 0 |
| rtt p50 ms | 1.234 / 1.845 | 0.763 / 1.269 | 0.722 / 0.473 | 0.436 / 0.341 |
| 共享 buffer | 2006 / 2003 | 54 / 55 | 55 / 55 | 3 / 3 |
| X3 CPU 核 | 0.542 / 0.595 | 0.513 / 0.569 | 0.545 / 0.434 | 0.347 / 0.339 |

- rep 01：GT p99 10.139 ≤ 0.5×62.972；>100 ms 0 ✓。rep 02：8.994 ≤ 0.5×71.968；0 ✓ → **ROUTING_REMOVES_SPIKES**。
- 同一 artifact 只切換門檻即消除尖峰——PGA-GAP-5 的機制在此得到直接支持（709dfac 的 GAP5_CAUSAL_NOT_SUPPORTED 維持原判，那是另一個判準）。
- 描述（不下結論）：GT/GAT 的 p99 與 C 同級；**p50 仍約為 C 的 2–3 倍；X3 CPU 約 0.5 核，高於 C 的 0.34**。
  2D XFCE 下 GPU 路徑已不再造成尾端卡頓，但尚無可量到的收益。async 在 GT 之上的差異在兩次重複間不一致（p50 0.72 / 0.47 對 0.76 / 1.27）。
