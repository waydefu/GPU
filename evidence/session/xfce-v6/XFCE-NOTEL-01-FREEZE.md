# XFCE-NOTEL-01 — 關掉 telemetry 重量 XFCE：telemetry 吃多少 X3 CPU、GPU 2D（GT）對 CPU（C）的真實差別（凍結 2026-09-26，任何本輪資料之前）

> 本檔在任何 XFCE-NOTEL-01 資料之前寫定。判準、門檻、順序、有效性條件在資料出現後一律不改；需要改就另立新編號。
> XFCE-V6-BASELINE-01 Part B 的判決（`GT_NO_TAIL_STALLS`、`NO_SEPARATION` ×3）維持原判，不重判；本輪資料不與它合併，只做描述性對照。

## 1. 為什麼要重量

- Part B（`runtime-f592241-v6`）的 runner `run-xfce-v4-v6.sh:359-360` 寫死 `TERMUX_X11_GATEA_PROTO=1 TERMUX_X11_GATEA_TELEMETRY=1
  TERMUX_X11_R8_ARM=1 TERMUX_X11_R8_CASE=R8-C1`（沿用 R 系列診斷 runner）。
- 事後描述（對已凍結資料，不改判決）：`xfce-c0-c-01`（C 組，GPU 關）的 X3 在 190 s 內寫 10,226,980 行 `gatea-telemetry`＝**53,690 行/s**，
  98% 是 `event=30`（`LORIE_GATEA_EVENT_CALLBACK_EXECUTED`）`src=5`（`LORIE_GATEA_XOP_PREPARE_ACCESS`）：EXA 每次讓 CPU 存取 pixmap 都 trace。
- 原始碼（f592241 `lorie.h:1738` `lorieGateATrace`）：telemetry 發佈時每次 trace 都做 ring 寫入＋`__android_log_print`（7 個 64 位元欄位格式化、送 logd）；
  沒發佈時第一行就 return。→ Part B 兩組的 X3 核數（0.495–0.645）含這筆 log 成本，**不能當產品的 X3 CPU**。
- 同一段取樣裡 `R8_OBS` 是 128 行/s（telemetry 的 0.24%）。R8 arm 必須保留：runner 的乾淨關閉（`p_r10_ledger --mode terminate`）
  用 `LORIE-R8-TEST` extension 的 `X_LorieR8Terminate`，R8 不 arm 就不註冊。本輪只改 telemetry 一個變數。

## 2. 兩個問題

| | 問題 | 比較 |
|---|---|---|
| **Q1** | telemetry 開著會多花多少 X3 CPU？ | **CT**（telemetry 開）對 **C**（關），其他完全相同 |
| **Q2** | 沒有 telemetry 時，GPU 2D（GT）對 CPU（C）是贏、平、還是輸？ | **GT** 對 **C**，都關 telemetry |

## 3. 組別與開關證據

- 產品：`f592241`（APK sha256 `f9e35b69…075c`，runner 既有的版本／APK／解析度檢查照舊）；變體 C0；劇本、manifest、X3 啟動方式與 Part B 相同。
- 三組共同：`TERMUX_X11_GATEA_PROTO=1`、`TERMUX_X11_R8_ARM=1`、`TERMUX_X11_R8_CASE=R8-C1`。
  - **C**：`TERMUX_X11_DISABLE_EXA_GPU=1`，`TERMUX_X11_GATEA_TELEMETRY` 不設。
  - **GT**：`TERMUX_X11_GPU_MIN_PIXELS=4097`，telemetry 不設。
  - **CT**：`TERMUX_X11_DISABLE_EXA_GPU=1`＋`TERMUX_X11_GATEA_TELEMETRY=1`（＝Part B 的 C）。
- 開關生效證據（環境變數只證明「有設定」；任一不符 → 該次 INVALID）：
  - `Sent shared buffer`：C、CT ≤ 5；GT 20–200 且 logcat 有 `GPU min pixels 4097`（同 Part B §5.1）。
  - `gatea-telemetry` 行數（raw logcat）：C、GT **= 0**；CT **≥ 1000**（Part B 同設定約 1000 萬行）。

## 4. 有效性（每次擷取；任一不符 → INVALID）

沿用 XFCE-V6-BASELINE-01 §4、§5.1、§9 補充 1–6 的每一項（runner rc 0、`:3` `xfce4-session` 與 runner 同一追蹤器、X3 `TracerPid 0`、
觸控整次 0 筆、螢幕全程亮不鎖、Stable pid 前後相同、mem-guard 未觸發、不被追蹤探測 `TRACER 0` 且 150 s 窗 n ≥ 500、
被追蹤探測 `TRACER` = client 追蹤器、工具執行檔 sha256 與 `tool-qualification/tool-binaries.sha256.txt` 相同、X3 核數可得、X root 各次相同），只改：
1. **client 追蹤器**：runner shell 的 TracerPid → exe sha256 以 `4f9d10ad` 開頭（proot-fast7，2026-09-25 起的日常追蹤器），無三個關閉開關。
2. 開跑前 Cursor、Hermes、ChatGPT 都沒在跑（記錄；避免 `:1` 的重負載與 `:3` 同時）。

## 5. 順序與補跑

- preflight-01（MODE=preflight，C 設定、telemetry 關）：§5.2＋§9 偏差 1 的 1000 ms grab ×3，必須 `PROBE_SENSITIVE`，否則 BLOCKED 不開跑。
- 9 次擷取，拉丁方陣（每組在前、中、後三段各一次）：`C GT CT | GT CT C | CT C GT`。
- INVALID 保留原編號；補一次同組擷取接在最後，全部最多補 2 次。某題需要的組別有效少於 3 次 → 該題 `INCONCLUSIVE`（另一題照判）。
- 每次擷取前等 MemAvailable ≥ 4600 MB 連續 20 s（最多 10 分鐘）。

## 6. 指標與判準（窗：`rca_report.py` 定義，`steps.jsonl` t0 起 150 s；百分位 `pct()` 最近秩）

- **Q1**（CT 對 C，X3 核數 `cpu_cores_window["X3"]`）：`min(CT) > max(C)` → `TELEMETRY_COSTS_X_CPU`；`max(CT) < min(C)` → `TELEMETRY_CHEAPER`；
  其他 → `NO_SEPARATION`。描述：平均差（核）、CT 的 gatea-telemetry 行/s。
- **Q2**（GT 對 C，與 Part B §5.3 相同規則）：
  - **N1 尾端**：3 次 GT 的不被追蹤探測 `over_100ms` 全 0 → `GT_NO_TAIL_STALLS`；否則 `GT_TAIL_STALLS`。
  - **N2 延遲**（不被追蹤探測 p50、p99 各判）：`max(GT) < min(C)` → `GT_FASTER`；`min(GT) > max(C)` → `CPU_FASTER`；其他 → `NO_SEPARATION`。
  - **N3 X CPU**：`max(GT) < min(C)` → `GT_LESS_X_CPU`；`min(GT) > max(C)` → `GT_MORE_X_CPU`；其他 → `NO_SEPARATION`。
- 只描述：被追蹤探測、`traced_lat`、追蹤器核數、共享次數、`xdotool search`、R8_OBS 行數、與 Part B 的方向對照（不合併）。

## 7. 結果怎麼讀（先寫下）

- Q1 `TELEMETRY_COSTS_X_CPU` → Part B 與之前所有帶 telemetry 的 XFCE 的 X3 CPU 都被灌水；往後 CPU 量測預設關 telemetry。
- Q2 `GT_LESS_X_CPU` 或 `GT_FASTER`（且 `GT_NO_TAIL_STALLS`）→ 沒有 telemetry 時 GPU 2D 有可量到的收益，EXA 方向值得繼續。
- Q2 全 `NO_SEPARATION` 或 `CPU_FASTER`／`GT_MORE_X_CPU` → XFCE 的 2D 桌面上 GPU 路徑沒有收益；建議主線 #2 的 XFCE EXA 暫停、
  資源移到主線 #3（DRI3＋AHB，GPU 已畫快但上屏吃 CPU）。**由使用者決定**，不自動改 Production 或 Gate A 狀態。

## 8. 授權與紅線

- 只碰實驗 `:3`（`com.waydefu.x11gpu`）；Stable `com.termux.x11`／`:1` 不動（runner 前後核對）。
- 使用者開跑當下同意；約 40 分鐘，手機插電、不碰。
- 不裝新 APK、不改產品原始碼、不重判舊判決。

## 9. 工具定版（2026-09-26，在任何本輪裝置資料之前）

| 檔案 | sha256 | 說明 |
|---|---|---|
| `evidence/session/xfce-v6/run-xfce-v5-notel.sh` | `c3bf0c66ee2e77e39aec22d8b4246c25363039595bc6b9e32ac0c0f5648d9cc5` | V4 ＋ 兩處改動：client 追蹤器 proot-fast7；`TELEMETRY=0\|1` 取代寫死的 telemetry（`diff` 13 行，含註解） |
| `evidence/session/xfce-v6/series-notel.sh` | `df915146299102f0889b41014f8300d9170b3845d743f88ee6ed7582c2d82b24` | 由 series-v6.sh 衍生：precheck、preflight、拉丁方陣 9 格、補跑 ≤ 2、判定 |
| fork `tests/xfce_notel/notel_judge.py`（`7e9c752`） | `709525f271dc27ac74e6dec71f77e1b4aaedfd57a65af3a9dcab9e18e1ae2232` | §3–§6；Part B 檢查函式匯入、不改 |
| fork `tests/xfce_notel/test_notel_judge.py` | `87571fbf59f2397182135ddedc7a68ceb1057bab922e15e214d1f1ed281aea15` | 18 測試全過 |
| fork `tests/xfce_notel/mutation_check.py` | `91e1fedb782a2375d67a7b60ab893e48a6ef537bb7d4bba11c262246138fd430` | 11 個突變全被抓到、未突變對照綠 |

探測執行檔 4 個 sha256 與 `tool-qualification/tool-binaries.sha256.txt` 相同（`sha256sum -c` 全 OK）。
主機驗證：runner V5 `VALIDATE_ONLY` → `XFCE_RUNNER_V5_VALIDATE_ONLY`（manifest `cdae546d…`）；缺 `TELEMETRY` 或 `TELEMETRY=2` → `XFCE_BLOCKED`（必紅）。
`/tmp/p_r10_ledger` 重建（桌面重開清空 /tmp），sha256 `2aca8ae1…` 與 runner 鎖定值相同。
突變涵蓋：C／GT telemetry 行數忽略、CT 下限忽略、adbd 指令行被算成 telemetry、client 追蹤器停在 v6、CT 用 GT 規則、
CT 的 env 未檢、R8／PROTO env 未檢、Q1 標籤對調、順序未檢、挑結果補跑、PARTIAL 誤報 JUDGED。

## 10. 偏差 1：R8 一律不 arm（2026-09-26，preflight-01 失敗後、**任何受判資料之前**）

- **發生什麼**：`runtime-f592241-notel/preflight-01`（02:01:48，runner V5，C 設定、telemetry 關、R8 arm）X3 起來 0.6 s 後
  `GATEA_FATAL_HALT what=x-r8-env reason=5`（logcat 02:01:58.168，X3 pid 26974）；runner 等不到 X3 → `XFCE_INVALID x3_missing`
  → preflight rc 2 → `PREFLIGHT_INVALID` → 系列停止（`SERIES_STOP`）。沒有任何 X 的量測資料；目錄原樣保留。
- **原因（原始碼）**：f592241 `lorie_r8_obs.c:130` `lorieR8ValidateStartupEnv(proto, telemetry)`：R8 arm 時 `!proto || !telemetry` → -1 →
  `lorie_r8_test.c:407` `lorieGateAFatalHalt("x-r8-env", …)`。**R8 arm 必須同時開 telemetry**；§1、§3 的「R8 保留 arm、只改 telemetry」在產品上不可行（設計時未查到）。
- **改為**：三組（C、GT、CT）都**不 arm R8**（`TERMUX_X11_R8_ARM`／`TERMUX_X11_R8_CASE` 不設），`TERMUX_X11_GATEA_PROTO=1` 照舊；
  telemetry 仍是 C／GT 關、CT 開。Q1 仍只差 telemetry 一個變數；CT 因此**不等於** Part B 的 C（Part B 另有 R8 arm，R8_OBS 約 128 行/s）。
- **後果**：`LORIE-R8-TEST` extension 不註冊 → runner 的乾淨關閉（`p_r10_ledger --mode terminate`）失敗（`|| true`），runner 等 30 s 後由
  EXIT trap 的 `xfce_cleanup` 以驗過 pid 與 cmdline 的 SIGTERM 關 X3、再 force-stop 實驗 app（`cleanup.txt` 記錄，屬 construction）。
  判準窗（150 s 劇本）在此之前；每格多約 30 s。其他啟動檢查已查：`InitOutput.c:2854` 的 test-fault 檢查只在設了 test fault 時生效（本輪都沒設）。
- 判定器：§3 共同 env 改為 PROTO=1、R8_ARM／R8_CASE **必須未設**（設了 → INVALID）。其餘判準、門檻、順序、補跑規則不變。
- 新輸出目錄 `runtime-f592241-notel-b/`（`series-notel-b.sh`）；preflight 重做。

| 檔案 | sha256 |
|---|---|
| `evidence/session/xfce-v6/run-xfce-v5b-notel.sh`（V5 ＋ R8 unset；`diff` 9 行含註解） | `5928814ab856bb89bf1346911674b9872c01f0436f4b758807a9e052a804aae7` |
| `evidence/session/xfce-v6/series-notel-b.sh`（RUNNER＝V5b、OUT＝`runtime-f592241-notel-b`） | `c436701e8a48d42b147872108db0d21ac9b84470fb2d3a88bd21dbff30560fff` |
| fork `tests/xfce_notel/notel_judge.py`（`a72669c`） | `4e894b3a91bb91c9f1abc6e646936da63518014d3eb48867c5bd9f11fb27dd0f` |
| fork `tests/xfce_notel/test_notel_judge.py` | `3fe8824b9675ece4c6997596ef9ae6cebf30c5eb502f80966c8f59787ece7c88` |
| fork `tests/xfce_notel/mutation_check.py`（未變） | `91e1fedb782a2375d67a7b60ab893e48a6ef537bb7d4bba11c262246138fd430` |

主機驗證：18 測試 OK（新增：R8 arm → INVALID、缺 PROTO → INVALID）；突變 11／11 caught、未突變對照綠；V5b `VALIDATE_ONLY` OK。

## 11. 結果（2026-09-26；本節在資料之後寫，§1–§10 不改）

### 11.1 執行

- `SERIAL=10.191.48.13:44925 bash evidence/session/xfce-v6/series-notel-b.sh`（偏差 1：runner V5b），02:08:07 開始、02:49:58 判定完成，
  資料目錄 `runtime-f592241-notel-b/`。開跑前：AC 充電、`mStayOn=true`、螢幕亮、未鎖、MemAvailable 4880 MB、只有 Claude 在跑（`precheck-apps.json`）。
- preflight-01 **`PROBE_SENSITIVE`**（1000 ms grab ×3：不被追蹤 849／993／992 ms，被追蹤 998／993／992 ms）；`EXPECT_ROOT` 1200x2464。
- 9 格照 `C GT CT | GT CT C | CT C GT`（劇本 t0：c-01 02:11:15、gt-01 02:15:36、ct-01 02:19:56、gt-02 02:24:19、ct-02 02:28:39、c-02 02:32:58、
  ct-03 02:37:18、c-03 02:41:36、gt-03 02:45:56）；**9 格全部有效，未補跑**。
- 開關證據：`gatea-telemetry` 記錄 C／GT 全為 0；CT 10,259,076／10,251,853／10,281,771（約 5.4 萬行/s，與 Part B 同量級）。共享 buffer C／CT 2、GT 53／53／54。
- 每格（含 preflight）乾淨關閉都 `FAIL LORIE-R8-TEST missing`（偏差 1 預期），由 runner EXIT trap 以驗過 pid 的 SIGTERM 關 X3（`cleanup.txt` 10 筆）；
  系列後裝置上無 X3，前景回到 Stable；Stable pid 各格前後相同（判定器檢查）。

### 11.2 判定（`runtime-f592241-notel-b/notel-judge.json`，verdict **`JUDGED`**）

| 判準 | 結果 | 數字 |
|---|---|---|
| **Q1** telemetry 成本 | **`TELEMETRY_COSTS_X_CPU`** | X3 核數 C 0.293／0.300／0.300；CT 0.453／0.456／0.520（min CT > max C） |
| **N1** 尾端 | **`GT_NO_TAIL_STALLS`** | GT 不被追蹤 `over_100ms` 0／0／0 |
| **N2** p50 | **`NO_SEPARATION`** | C 0.234／0.265／0.269 ms；GT 0.223／0.219／0.274 ms |
| **N2** p99 | **`NO_SEPARATION`** | C 11.73／11.13／11.04 ms；GT 7.41／9.47／11.49 ms |
| **N3** X CPU | **`NO_SEPARATION`** | C 0.293／0.300／0.300；GT 0.294／0.290／0.301 |

依 §7：
- Q1 → Part B 與之前所有帶 telemetry 的 XFCE 量測，X3 CPU 都被灌水；往後 CPU 量測預設關 telemetry。
- Q2 全 `NO_SEPARATION`（且無尾端卡頓）→ 沒有 telemetry 時，XFCE 2D 桌面上 GPU 路徑**沒有可量到的收益也沒有損失**；
  §7 事先寫下的建議：主線 #2 的 XFCE EXA 暫停、資源移到主線 #3（DRI3＋AHB）。**由使用者決定**，不改 Production 或 Gate A 狀態。

### 11.3 描述（不改判決）

- telemetry 成本：CT 平均 0.476 核、C 平均 0.298 核，差 **約 0.18 核（約 +60%）**；即 telemetry 開時 X3 約 3／8 的 CPU 在寫 log。
- 沒有 telemetry 時 X3 在這個劇本只用 **約 0.29–0.30 核**（C 與 GT 幾乎相同）；Part B（telemetry＋R8、同產品）同劇本 X3 0.495–0.645 核，
  設定不同、不合併，只記方向。
- GT 的 p99 三次中兩次低於所有 C（7.41、9.47 < 11.04），第三次 11.49 高於 C 的最小值 → 未完全分開，照判 `NO_SEPARATION`。
  gt-03 的不被追蹤 max 53.5 ms（其他格 13.5–20.3 ms），`over_100ms` 仍 0。
- 追蹤器（日常 proot-fast7）核數 0.306–0.328，三組相同量級；`xdotool search` p50 24–30 ms。
- 原始 logcat：CT 三格各約 1.31 GB（telemetry），其餘各 3.8–4.7 MB；目錄共 3.8 GB，本地保留、未壓縮、不發佈（PUBLISHED-SUBSET.md）。
