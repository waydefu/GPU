# XFCE-V6-BASELINE-01 — proot-fast v6 下重量 XFCE 基線：凍結（2026-09-25，任何 v6 XFCE 資料之前）

> 本檔在看到任何本輪資料之前寫定。判準、門檻、順序、有效性條件在資料出現後一律不改；
> 需要改就另立新判準、新編號，舊的照實保留。舊判決（`XFCE_ASYNC_IMPROVED` 否、`GAP5_CAUSAL_NOT_SUPPORTED`、
> `ROUTING_REMOVES_SPIKES`）全部維持原判，不重判；本輪資料不與舊資料合併，只做描述性對照。

## 1. 為什麼要重量

- **舊 XFCE 資料被 PRoot 追蹤器壓著**：`gate-a-a1/p2-xfce-runtime/runtime-f592241` 八格 C0 的 RCA `cpu_cores_window`：
  追蹤器 0.554–0.687 核，X3 0.339–0.595 核——**每一格追蹤器都比 X server 本身吃得多**，C／G0／GAT／GT 都一樣。
  當時 runner 只驗 X3 未被追蹤（`x3-tracer.txt`），沒有記錄 XFCE client 是哪個 proot 在追蹤（時間早於 v2 上日常，推定原版）。
- **舊的 rtt 探測本身也被追蹤**：`rca_sampler.py` 在 PRoot 內啟動 `x_rtt`，每次往返都要 socket 收發。
  原版 proot 會攔 socket 收發（bwrap 相容；`proot/PROOT-TRACER-OVERHEAD-01.md`：同一 socket 上 send+recv 55.5 µs 對 write+read 1.56 µs，約 35 倍），v6 不攔；
  所以舊 rtt 含有「探測程式自己排隊等追蹤器」的時間，跨版本比較 rtt 有系統性偏差。
  （xcb 等回覆時用的 `ppoll` 在原版會不會被攔，未實測。）
- **日常現況**：2026-09-25 09:46 起日常追蹤器是 `proot-fast6`（sha256 `2d5596dc…`），30 s 窗 0.007 核（原版同法 0.360）。

## 2. 兩個問題，分開判、分開報

| | 問題 | 會影響的決定 |
|---|---|---|
| **A** | 日常 Stable `:1`（官方 `com.termux.x11`，**沒有 Gate A**）在 v6 下，使用者回報的卡頓情境還卡不卡？ | 主線 #2 的理由是「修卡頓」還是「讓 GPU 分擔 2D」——由使用者決定 |
| **B** | 實驗 `:3`（`f592241`）在凍結的 XFCE 劇本下，v6 環境裡 GT（預設分流）對 C（全 CPU）是贏、平、還是輸？ | EXA／Gate A 2D 還值不值得修、修哪裡 |

兩部分互不代替：B 的結果不能回答日常卡不卡（Stable 沒有 Gate A），A 的結果不能回答 GPU 2D 值不值得。

## 3. 量測工具（開跑前完成；每項都要有「應該要紅」的測試）

| 代號 | 工具 | 內容 | 必須變紅的測試 |
|---|---|---|---|
| T1 | `x_rtt` v2 | 與 `tests/pga/x_rtt.c` 相同的 `GetInputFocus` 往返（每 250 ms），啟動時多印一行 `TRACER <TracerPid>`（讀 `/proc/self/status`）。編兩份：**glibc 版**（PRoot 內執行＝「被追蹤探測」）與 **bionic 版**（Termux `clang`＋`libxcb`；經 `adb run-as com.termux` 以 `setsid nohup` 從 Termux 端啟動＝「不被追蹤探測」） | bionic 版若從 PRoot 內啟動 → 印出 `TRACER` ≠ 0 → 驗證器必須判該次 INVALID |
| T2 | `traced_lat`（既有 `tests/pga/traced_lat.c`） | 在 PRoot 內每 100 ms 量一次 `fstatat("/usr/bin")`（經追蹤器）與 `getppid()`（不經追蹤器，對照） | 無（它本身就是對照設計）；輸出行數不足 → 該次 INVALID |
| T3 | `x_grab_stall`（新，xcb 小程式） | 對指定 display 做 `GrabServer` → 等 D ms → `UngrabServer`，每 P s 一次，共 N 次；印每次的起訖時間 | 用於探測靈敏度檢查（見 §5.2）；探測若看不到 → BLOCKED |
| T4 | runner `run-xfce-v4-v6.sh` | 由 `run-xfce-v3-f592241.sh` 衍生；劇本、變體 C0、凍結 manifest、X3 啟動方式**不變**；只加：§4 的綁定欄位、T1 兩份探測、T2、觸控偵測（沿用 `tests/gl/gl_bench.sh` 的 getevent 偵測）、`EXPECT_ROOT` 由 preflight 決定、§5.2 的 preflight 模式（起 X3、不開 XFCE、跑 T3） | 單元測試見 T6 |
| T5 | `daily_sampler.py` v2（Part A） | 由既有 v1（fork `0d74fe2`，WIP、從未執行）衍生：加 T1 兩份探測（對 `:1`）、T2、§4 綁定、分段（baseline／loaded） | 單元測試見 T6 |
| T6 | 判定器 `xfce_v6_judge.py`＋單元測試 | 實作 §5、§6 的規則；測試必須呼叫真的判定器 | 見下表 |

**T6 判定器測試（最少）**

| 案例 | 預期 |
|---|---|
| 3 GT 全部低於 3 C（p50） | `GT_FASTER` |
| 3 GT 全部高於 3 C | `CPU_FASTER` |
| 交錯 | `NO_SEPARATION` |
| 某次 client 追蹤器 exe sha ≠ `2d5596dc…`（B） | 該次 INVALID |
| 追蹤器 environ 含 `PROOT_STAT_AT_ENTER=0`／`PROOT_KOMPAT_FULL=1`／`PROOT_BWRAP_COMPAT=1` | 該次 INVALID |
| 不被追蹤探測印 `TRACER 1234` | 該次 INVALID |
| C 組 `Sent shared buffer` = 54 | 該次 INVALID（開關沒生效） |
| GT 組 `Sent shared buffer` = 2006 | 該次 INVALID（分流沒生效） |
| 不被追蹤探測 n < 500 | 該次 INVALID |
| 觸控事件出現在判準窗內 | 該次 INVALID |
| 有效擷取少於 3 C 或 3 GT | 該部分 `INCONCLUSIVE`，不用較少的樣本判 |
| 歷史 `runtime-f592241` 擷取（缺本輪新欄位） | INVALID（證明缺資料會判不過，而不是被當成通過） |

## 4. 共同綁定與有效性（每次擷取都記錄；任一不符 → 該次 INVALID，不消耗判準）

1. **Client 追蹤器身分**：runner（或 sampler）所在 shell 的 `TracerPid` → `/proc/<pid>/exe` 路徑與 sha256；
   B 另記 `:3` 上 `xfce4-session` 的 `TracerPid`，必須是同一個追蹤器。
   - v6 擷取：sha256 必須以 `2d5596dc` 開頭（`~/build/proot-fast/out6/bin/proot-fast6`）。
   - 原版對照（只有 A）：必須是 `$PREFIX/bin/proot`，sha256 以 `ea47e17d` 開頭。
2. **追蹤器環境**：記錄追蹤器的 `PROOT_*` 環境變數；v6 擷取不得出現三個關閉開關（見 T6）。
3. **不被追蹤探測**：`TRACER 0`；記錄 bionic 版 sha256。被追蹤探測記錄 `TRACER` 值（必須等於第 1 項的追蹤器 pid）。
4. **裝置狀態**：螢幕全程亮、未鎖；判準窗內 0 觸控事件；無外接螢幕（沿用 runner 檢查）。
5. **資源**：開始時 MemAvailable ≥ 4500 MB（`safe-run.sh --floor-mb 4500`）；mem-guard 照舊。
6. **X root**：`EXPECT_ROOT` 在 preflight 讀一次（09-25 交接記錄為 1200×2464），同一部分內每次擷取必須相同。

## 5. Part B — 實驗 `:3`

### 5.1 綁定與組別
- 產品：`f592241`（APK sha256 `f9e35b69…075c`，Build ID `1b80cabb…fedf`，CI 35937188670）；runner 既有的版本／APK／解析度檢查照舊。
- **C**：`TERMUX_X11_DISABLE_EXA_GPU=1`。**GT**：預設（`TERMUX_X11_GPU_MIN_PIXELS=4097`）。
  **G0**（描述用，不入判準）：`TERMUX_X11_GPU_MIN_PIXELS=0`。
- **開關確實生效的證據**（環境變數只證明「有設定」，所以另外要求路徑證據）：
  - C：`Sent shared buffer` ≤ 5（f592241 的 C 兩次都是 3）；
  - GT：logcat 有 `GPU min pixels 4097`，且 `Sent shared buffer` 在 20–200（f592241 為 54／55）；
  - G0：`Sent shared buffer` ≥ 1000（f592241 約 2006）。
  不符 → 該次 INVALID。
- 順序：`C GT GT C C GT`，最後 `G0` 一次。INVALID 的擷取保留原編號；補一次同組擷取接在 G0 之前，每部分最多補 2 次；
  補完仍不足 3 C／3 GT → Part B `INCONCLUSIVE`。
- 判準窗：劇本視窗 150 s（`rca_report.py` 同一定義）。

### 5.2 探測靈敏度檢查（preflight，判準擷取之前；不過 → BLOCKED，不開跑）
在 `:3`（C 設定、不開 XFCE）上跑 T3：3 次 `GrabServer`，每次 200 ms，間隔 10 s。兩份 `x_rtt` 同時量：
**每一次 grab 都必須在 ±1 s 內各有一筆 ≥ 150 ms 的樣本**（兩份探測都要）。任一份沒看到 → `PROBE_INSENSITIVE` → Part B 不開跑，先查工具。
這一項確保「0 次尖峰」代表 X 真的沒卡，而不是探測看不到。

### 5.3 判準（主要指標：**不被追蹤探測**的 rtt）
- **B1 尾端**：3 次 GT 的 `over_100ms` 全為 0 → `GT_NO_TAIL_STALLS`；否則 `GT_TAIL_STALLS`（列出次數）。
- **B2 延遲**（p50、p99 各判一次）：`max(GT) < min(C)` → `GT_FASTER`；`min(GT) > max(C)` → `CPU_FASTER`；其他 → `NO_SEPARATION`。
  3 對 3 完全分開：在「兩組沒差別」的假設下，某一個方向剛好完全分開的機率是 1/20＝0.05，兩個方向合計 0.10（每個指標各自計）。
  不另設倍數門檻——上一輪的教訓是 C 自己的 p99 就在 8.1–12.1 ms 浮動，固定 1.25 倍比雜訊還窄；這裡的雜訊直接由組內三次呈現。
  順序 `C GT GT C C GT` 讓線性漂移對兩組的影響相同。
- **B3 X CPU**：X3 在判準窗的核數，同 B2 規則 → `GT_LESS_X_CPU`／`GT_MORE_X_CPU`／`NO_SEPARATION`。
- **只描述、不判**：被追蹤探測的 rtt、`traced_lat`、追蹤器核數、xfwm4 核數、共享次數、`xdotool search` p50／over_3s、
  G0 的全部數字（「v6 下 G0 的尖峰還在不在」）、與 f592241 的對照（追蹤器與探測都不同，不可合併）。

### 5.4 結果怎麼讀（先寫下，避免事後解讀）
- `GT_FASTER`（p50 或 p99）且 `GT_NO_TAIL_STALLS` → v6 下 GPU 2D 有可量到的收益；主線 #2 可往 EXA 非同步／減少同步等待走。
- `NO_SEPARATION`＋`GT_MORE_X_CPU` → GPU 路徑沒贏、還多花 X CPU；對「省 CPU」的目標是負的。
- `CPU_FASTER` → GPU 2D 路徑在 v6 下仍比 CPU 慢。
- 任何結果都**不**自動改 Production 預設或 Gate A 狀態，由使用者決定。

## 6. Part A — 日常 `:1`

### 6.1 情境（使用者 09-23 回報：「兩個都開就開始卡」）
- 前提：Claude Desktop 開著但閒置（不在產生回覆）；Cursor、Hermes **都沒在跑**（否則啟動只是交給舊視窗，不產生負載）；
  沒有其他 Electron app；MemAvailable ≥ 4500 MB。
- 流程（T5）：baseline 60 s → 用日常啟動器 `cursor-gpu`、`hermes-gpu` 開啟兩個 app → loaded 240 s。app 保持開著，由使用者自行關閉。
- **已知干擾**：Claude＋Cursor＋Hermes 是 3 個 Electron，超過本機「最多 2 個」的容量規則；換頁（swap）是同時存在的原因。
  每秒記 MemAvailable 與 swap 使用量，只描述。
- 執行方式：使用者在日常桌面的終端機執行一條指令（sampler 因此跟日常 app 在同一個追蹤器底下）；
  不被追蹤探測由 sampler 經 `adb run-as com.termux` 從 Termux 端啟動，桌面重開也不受影響。

### 6.2 對照與順序
- `v6-1` → `stock-1` → `v6-2`（ABA，分攤漂移）。
- 切換由使用者操作：「F8 設定」切原版／加速版 →「F8 工作站」關閉再開啟。每次之間使用者關掉 Cursor 與 Hermes。
- stock 擷取的追蹤器必須是原版（§4 第 1 項）；v6 擷取必須是 `proot-fast6`。

### 6.3 量什麼（loaded 240 s 窗）
- **S1** `traced_lat` 的 `fstatat` > 100 ms 次數：PRoot 裡的程式等追蹤器等超過 100 ms。
- **S2** 被追蹤探測對 `:1` 的 rtt > 100 ms 次數：PRoot 裡的程式感受到的 X 往返卡頓。
- **S3** 不被追蹤探測對 `:1` 的 rtt > 100 ms 次數：X server 本身的卡頓。
- 描述：`getppid` 對照的 p99（區分「整機 CPU 滿」與「追蹤器排隊」）、追蹤器核數、Stable X 核數（經 adb 讀 `/proc`）、MemAvailable、swap。
- **卡頓事件 E = S1 + S2**（使用者在 PRoot 程式裡感受到的）；S3 分開報。100 ms 是一般人看得出停頓的門檻，與舊判準的 `over_100ms` 一致。
- 門檻理由：A0 要求 E ≥ 3，是為了不讓 240 s 裡單獨一次偶發停頓就算「重現」；A1 的 0.25 倍＝卡頓次數至少少 4 倍才叫「減少」。

### 6.4 判準
- **A0 對照有效**：`stock-1` 的 E ≥ 3 → 劇本重現得出已知的卡頓；否則 `WORKLOAD_DOES_NOT_REPRODUCE` → Part A `INCONCLUSIVE`
  （量不到原版的卡頓，就不能用它宣稱 v6「不卡了」）。
- **A1 日常卡頓**（A0 有效時）：兩次 v6 的 E 都 = 0 → `DAILY_STUTTER_GONE`；
  `max(E_v6) ≤ 0.25 × E_stock` 但不為 0 → `DAILY_STUTTER_REDUCED`；其他 → `DAILY_STUTTER_REMAINS`。
- **A2 X 本身**：任一次 v6 的 S3 > 0 → `X_SERVER_STALLS_PRESENT`（Stable X 本身會卡；注意 Stable 沒有 Gate A，這不是 Gate A 能直接修的）；
  否則 `X_SERVER_NO_STALLS`。

## 7. 授權與紅線

- Part B：實驗 `:3` 的裝置執行，照既有流程（ADB、螢幕亮、使用者開跑前說「好」）。
- Part A：**碰到日常桌面**（對 `:1` 連兩個唯讀探測、在日常桌面開 Cursor 與 Hermes、使用者自己重開桌面兩次），要使用者在開跑當下明確同意。
  不殺、不裝、不改 Stable 的任何東西；重開桌面由使用者透過自己的小工具操作。
- 不做：C1 變體、GA（async）、Production 預設、Stable 改動、舊判決重判。

## 8. 執行順序與預估

1. T1–T6 完成、單元測試全部照預期（紅的紅、綠的綠）——只在主機上做，不碰裝置。
2. Part B：preflight（§5.2）→ 7 次擷取（每次約 5 分鐘，共約 40 分鐘）。需要 ADB、螢幕亮、手機放著不碰。
3. Part A：約 20 分鐘，需要使用者在旁操作（兩次重開桌面）。
4. 結果寫在本檔之後的「結果」段落；判決用本檔的名稱，資料目錄 `evidence/session/xfce-v6/`。
