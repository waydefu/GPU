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
