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
**（本節參數已由 §9 偏差 1 取代：200 ms／≥150 ms 會把正常探測判成不靈敏。原文保留。）**

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

## 9. 偏差與補充（2026-09-25 實作 T1／T3 時；**仍在任何受判資料之前**）

工具驗證資料在 `evidence/session/xfce-v6/tool-qualification/`（Xvfb `:99`，只在主機上，未碰 `:1`／`:3`／裝置）。

### 偏差 1：§5.2 探測靈敏度檢查的參數錯了，改為 1000 ms／≥ 500 ms
- **錯在哪**：探測每 250 ms 才送一次請求。X 卡 200 ms 時，請求常常落在卡頓後段或完全錯開，量到的延遲介於 0–200 ms 之間，
  很少 ≥ 150 ms。原判準要求 3 次都 ≥ 150 ms，即使探測完全正常也幾乎一定判成 `PROBE_INSENSITIVE`（假紅燈）。
- **實測**（`t3-*.log`，兩份探測同時量）：200 ms × 10 次 → 每次最大延遲 0、162、112、62、11、0、160、109、59、9 ms，
  ≥ 150 ms 只有 **2／10**（兩份探測相同）；1000 ms × 5 次 → 765、999、1000、997、1000 ms，**5／5 ≥ 500 ms**；
  不卡的時段（對照）最大約 1 ms、0 次 > 100 ms。
- **改為**：3 次 `GrabServer`，**每次 1000 ms**，間隔 10 s；每次 grab 在 `[開始 − 0.5 s, 結束 + 1.0 s]` 內，
  **兩份探測都要各有一筆 ≥ 500 ms 的樣本**。理論下限 = 1000 − 250 = 750 ms，500 留有餘量。其他不變。

### 偏差 2：不被追蹤探測改用 TermuxService 啟動（不經 adb）
- 與 X3 的不被追蹤啟動同一機制（`start-x3-untraced.sh`：Termux 自己的 `am startservice` → TermuxService 執行）；
  工具 `tests/xfce_v6/untraced_run.sh`。要求不變：探測必須印 `TRACER 0`。
- 實測（`t1c-untraced-via-termuxservice.log`）：經 TermuxService → `TRACER 0`；**同一個 bionic 執行檔直接在 PRoot 內啟動 → `TRACER 15010`**
  （＝應該要紅的案例確實紅；§3 T1 的負面測試）。Part A 因此也不需要 ADB 來啟動探測。

### 補充（實作需要的精確定義，事前寫下）
1. **觸控**：沿用 `gl_bench.sh` 的偵測器（`getevent /dev/input/event7`，無時間戳），所以計數範圍是**整次擷取**，比「判準窗內」更嚴；
   記錄器中途死掉 → `null` → 該次 INVALID（不是 0）。
2. **樣本數**：Part B 不被追蹤探測 n ≥ 500（150 s 窗，理論 600）；Part A 兩份探測在 240 s 窗各 n ≥ 768（理論 960 的 80%）；
   `traced_lat` 在 Part A 240 s 窗 n ≥ 1920（理論 2400 的 80%），Part B 只描述。
3. **時間窗**：Part B 用 `rca_report.py` 同一定義（`steps.jsonl` 第一行 `t0_epoch_s` 起 150 s），百分位用它的 `pct()`（最近秩）；
   Part A 的 loaded 窗 = sampler 送出第一個啟動指令的時刻起 240 s，baseline 窗 = 其前 60 s。
4. **B3 的 X3 核數**：`rca_report.py` 的 `cpu_cores_window["X3"]`。
5. **被追蹤探測**的 `TRACER` 必須等於該次記錄的 client 追蹤器 pid（§4 第 3 項）；不符 → INVALID。
6. 工具執行檔 sha256（2026-09-25 11:04 建置）：`x_rtt2.glibc` `17700d91…`、`x_grab_stall.glibc` `1004aa87…`、
   `x_rtt2.bionic` `61f51ff3…`、`traced_lat.glibc` `44ea9efb…`；完整值在 `tool-qualification/tool-binaries.sha256.txt`。每次擷取記錄實際使用的雜湊，與此不同 → INVALID。

### 偏差 3：Part A 改由 Claude 執行，使用者只負責重開後打開 Claude（2026-09-25 使用者決定；**Part A 仍無任何資料**）
- 使用者要求「不貼指令」。記錄程式（T5）改由**日常桌面內的 Claude Code session** 啟動：它仍在日常追蹤器底下，§4 第 1 項照驗。
- 三次都是「Claude Desktop 開著、正在等這個記錄程式的工具呼叫」，三次狀態一致；§6.1 的「閒置」改讀為這個狀態。
  （原設計裡使用者自己貼指令時 Claude 真閒置、Claude 跑時不閒置的不對稱因此消失。）
- 切換：Claude 建立／刪除 `~/.f8-proot-stock`（＝「F8 設定」做的事），再經 TermuxService 執行 `f8stop`（＝「F8 工作站 → 關閉桌面」）；
  使用者用「F8 工作站」開回桌面、打開 Claude、叫 Claude 繼續。`f8stop` 會結束 XFCE 與 Stable X `:1`——使用者已同意（本對話）。
- Cursor／Hermes 由記錄程式在擷取結束後關閉（`--close-launched`）：只對啟動時記下的確切 pid 送 SIGTERM，且 cmdline 仍須符合；
  pid、cmdline、結果記入該次 `closed.json`（屬 construction，不是 cleanup）。cmdline 不符的程序不動。

### 補充 7：Part A 補跑規則（新增；原凍結沒有訂，任何一次無效就整個 A INCONCLUSIVE）
- 每一格（v6-1、stock-1、v6-2）**原本那次無效**時，可以補跑 **1 次**（同 kind、新目錄 `<格>-r1`，原無效目錄保留）；
  補跑仍無效 → Part A `INCONCLUSIVE`。原本那次有效時**不得**提交補跑（禁止挑結果）。判定器 `part-a ... slot=<dir>` 實作並有測試。

## 10. 結果 — Part A（2026-09-25；本節在資料之後寫，上面 §1–§9 不改）

### 10.1 擷取（全部由日常桌面內的 Claude Code 以 `daily_sampler_v2.py --close-launched` 執行，偏差 3）

| 格 | 目錄 | 追蹤器（pid／sha256） | baseline → launch → loaded 結束 | 有效 | S1 | S2 | S3 | E |
|---|---|---|---|---|---|---|---|---|
| v6-1 | `part-a/v6-1` | 15010／`2d5596dc` | 16:15:40 → 16:16:41 → 16:20:41 | 有效 | 47 | 1 | 1 | 48 |
| stock-1 | `part-a/stock-1` | 19896／`ea47e17d` | 16:24:33 → 16:25:33 → 16:29:34 | 有效 | 91 | 57 | 1 | 148 |
| v6-2 | `part-a/v6-2` | 27459／`2d5596dc` | 16:35:41 → 16:36:41 → 16:40:42 | **INVALID**（`touch events 533`） | — | — | — | — |
| v6-2-r1 | `part-a/v6-2-r1` | 27459／`2d5596dc` | 16:47:53 → 16:48:53 → 16:52:54 | 有效（補充 7 的唯一一次補跑） | 13 | 1 | 0 | 14 |

- 時間為 Asia/Taipei。v6-2 無效＝無資訊，不列入任何判準或描述；目錄原樣保留。
- 第一次判定 `part-a/part-a-judge.json` = `INCONCLUSIVE`（v6-2 INVALID）原樣保留；本節的判定是補跑後的新檔 `part-a/part-a-judge-r1.json`。

### 10.2 判定

```
xfce_v6_judge.py part-a part-a/v6-1 part-a/stock-1 part-a/v6-2 v6-2=part-a/v6-2-r1
used: v6-1=original stock-1=original v6-2=replacement      verdict JUDGED
```

- **A0 `CONTROL_REPRODUCES`**：E_stock = 148 ≥ 3。
- **A1 `DAILY_STUTTER_REMAINS`**：兩次 v6 的 E = 48、14，都不為 0；max(E_v6) = 48 > 0.25 × 148 = 37，所以不是 `REDUCED`。
  （v6-2-r1 單獨看是 14 ≤ 37，但判準是兩次取最大值，事前凍結，不改。）
- **A2 `X_SERVER_STALLS_PRESENT`**：v6-1 的 S3 = 1（不被追蹤探測 max 185.5 ms）。Stable `:1` 沒有 Gate A，這不是 Gate A 能直接修的。

### 10.3 描述（不改判決）

| | stock-1 | v6-1 | v6-2-r1 |
|---|---|---|---|
| 被追蹤探測 rtt p99／max（ms） | 498.7／1745.1 | 1.49／325.3 | 1.36／112.7 |
| `traced_lat` fstat p99（µs） | 343742 | 163161 | 63857 |
| `traced_lat` getppid p99（µs） | 18.1 | 6.1 | 5.9 |
| 追蹤器核數 baseline／loaded 平均 | 0.348／0.752 | 0.022／0.334 | 0.017／0.197 |
| Stable X `:1` 核數 baseline／loaded 平均 | 0.089／0.020 | 0.129／0.028 | 0.102／0.030 |
| loaded 窗 MemAvailable 最低（MB） | 3586 | 3394 | 3498 |
| loaded 窗 swap 使用最高（MB） | 6988 | 7199 | 7832 |

- **S2 從 57 → 1、1**：PRoot 裡的程式感受到的 X 往返卡頓在 v6 下幾乎消失（被追蹤探測 p99 從 499 ms 降到 1.5 ms）。
- **剩下的 E 幾乎全是 S1**（fstatat > 100 ms：91 → 47、13）。同一窗內 getppid p99 只有 6 µs，
  所以這些停頓不是「整機 CPU 滿到連最便宜的 syscall 都排不到」，而是 fstatat 這條路徑本身等超過 100 ms；
  原因本次未量（追蹤器核數 0.2–0.33，不是滿載），不在本判準範圍。
- 兩次 v6 的 E 差 3.4 倍（48 vs 14），單次變異大；開始時 swap 使用 stock-1 4381、v6-1 5114、v6-2-r1 5881 MB（`precheck.json`），v6-2-r1 起點最高，只描述。
- 三次都是 3 個 Electron（Claude＋Cursor＋Hermes），超過本機「最多 2 個」的容量規則（§6.1 已知干擾）。

### 10.4 v6-2-r1 執行紀錄（事實，不改判決）

- 開跑前檢查：`/proc/self` TracerPid 27459 → `proot-fast6` sha256 `2d5596dc…`；`~/.f8-proot-stock` 不存在；
  MemAvailable 5358 MB（sampler `precheck.json`）；Cursor／Hermes 未執行；ADB lane 5038（server pid 26023）裝置 `10.191.48.13:42435`；
  螢幕 `mWakefulness=Awake`、`isKeyguardShowing=false`；`screen_off_timeout` 600000 ms（大於本次約 320 s）。
- 使用者開跑前在對話中確認 6 分鐘不碰手機；`touch.json` = `{"selftest": true, "events": 0}`。
- 開跑時另有一個 Claude Code 程序（pid 31150，前一個 session，同一 Claude Desktop 29031 底下）存在但閒置：
  5 秒量測 4 ticks（0.008 核）。它不是獨立的 Electron app，sampler 的 `electron_others` = `[]`；只記錄。
- 本次 sampler 以背景工具呼叫執行，Claude 在擷取期間沒有做其他工具呼叫，只等完成通知（偏差 3 所述「等這個記錄程式」的狀態）。
- `closed.json`：Cursor pid 14327、Hermes pid 14329 以 SIGTERM 結束（cmdline 相符，0.5–1.0 s 內消失），只剩 Claude Desktop。
- 結束後確認 `~/.f8-proot-stock` 不存在，日常停在 v6。

## 11. 結果 — Part B（2026-09-25；本節在資料之後寫，§1–§9 不改）

### 11.1 執行

- 一條指令：`SERIAL=192.168.1.100:46297 bash evidence/session/xfce-v6/series-v6.sh`，17:13:16 開始、17:43:18 判定完成，
  資料目錄 `runtime-f592241-v6/`。
- preflight-01 **`PROBE_SENSITIVE`**（偏差 1 的 1000 ms grab ×3）：不被追蹤探測最大 854.2／991.5／992.9 ms，
  被追蹤探測 990.9／991.5／992.7 ms，全部 ≥ 500 ms。`EXPECT_ROOT` = 1200x2464（與 09-25 交接記錄相同）。
- 判準擷取照凍結順序 `C GT GT C C GT`，**6 格全部有效**，沒有使用補跑；最後 G0 一格（有效，只描述）。
- 7 格共同綁定（§4）：client 追蹤器 pid 27459，sha256 `2d5596dc…`；`:3` `xfce4-session` 的追蹤器同為 27459；
  X3 `TracerPid 0`；觸控 `{"selftest": true, "events": 0}`；Stable `com.termux.x11` 前後 pid、cmdline、版本完全相同。
- 開關生效證據（§5.1）：`Sent shared buffer` C = 2／2／2（≤ 5）、GT = 53／53／54（20–200，且有 `GPU min pixels 4097`）、G0 = 2002（≥ 1000）。

### 11.2 判定（`runtime-f592241-v6/part-b-judge.json`）

| 判準 | 結果 | 數字 |
|---|---|---|
| **B1 尾端** | **`GT_NO_TAIL_STALLS`** | 3 格 GT 不被追蹤探測 `over_100ms` = 0／0／0 |
| **B2 p50** | **`NO_SEPARATION`** | C 0.392／1.500／1.119 ms；GT 0.983／1.184／1.557 ms（交錯） |
| **B2 p99** | **`NO_SEPARATION`** | C 13.035／10.387／13.211 ms；GT 12.392／10.712／10.418 ms（交錯） |
| **B3 X CPU** | **`NO_SEPARATION`** | X3 核數 C 0.495／0.566／0.631；GT 0.626／0.625／0.645（min GT 0.625 < max C 0.631） |

verdict **`JUDGED`**。§5.4 事先寫下的三種讀法都**不**適用：沒有 `GT_FASTER`（不能說 GPU 2D 有收益），
也沒有 `GT_MORE_X_CPU` 或 `CPU_FASTER`（不能說 GPU 路徑較差）。字面結論：**v6 環境、凍結的 XFCE 劇本下，
GT 與 C 在不被追蹤探測的延遲與 X3 CPU 上分不出輸贏，GT 沒有尾端卡頓。** 不改 Production 預設或 Gate A 狀態。

### 11.3 描述（不改判決）

| 格 | 共享 | 不被追蹤 p50／p99／max（ms） | 被追蹤 p99／max（ms）／>100 | X3 核 | 追蹤器核 | `xdotool search` p50（s）／>3 s |
|---|---|---|---|---|---|---|
| c-01 | 2 | 0.392／13.035／15.3 | 10.0／13.8／0 | 0.495 | 0.322 | 0.034／0 |
| gt-01 | 53 | 0.983／12.392／39.1 | 10.6／15.2／0 | 0.626 | 0.339 | 0.047／0 |
| gt-02 | 53 | 1.184／10.712／14.7 | 11.1／14.9／0 | 0.625 | 0.365 | 0.046／0 |
| c-02 | 2 | 1.500／10.387／15.9 | 9.0／12.0／0 | 0.566 | 0.395 | 0.059／0 |
| c-03 | 2 | 1.119／13.211／17.2 | 9.3／13.9／0 | 0.631 | 0.421 | 0.052／0 |
| gt-03 | 54 | 1.557／10.418／64.0 | 20.7／182.6／**1** | 0.645 | 0.424 | 0.052／0 |
| g0-01 | 2002 | 1.902／106.84／**448.8** | 107.4／448.9／**6** | 0.672 | 0.443 | 0.060／0 |

- **B3 差一點分開**：3 格 GT 的 X3 核數都在 C 的最高值附近（平均 GT 0.632、C 0.564，多 0.068 核），
  但 gt-02 的 0.625 低於 c-03 的 0.631，規則是完全分開才算，照判 `NO_SEPARATION`。
- **G0 的尖峰在 v6 下還在**：不被追蹤探測 `over_100ms` = 6、max 448.8 ms（共享 2002 次）；
  這是 §5.3 列的描述題「v6 下 G0 的尖峰還在不在」的答案：在。
- gt-03 的**被追蹤**探測有 1 筆 182.6 ms，同一窗內不被追蹤探測 max 64.0 ms；被追蹤探測不入判準，只記錄。
- c-01（第一格）的 p50 0.392 ms 明顯低於其他 5 格（0.98–1.56 ms）；順序設計讓線性漂移對兩組影響相同，這裡只描述。
- 追蹤器核數 0.32–0.44，照擷取順序逐格上升（0.322 → 0.443，7 格單調）；X3 核數也大致隨順序上升（c-01 0.495 → g0-01 0.672）。與舊 `runtime-f592241`（0.55–0.69，推定原版追蹤器）
  追蹤器與探測都不同，**不可合併**，只記錄方向。
- 每格 `raw-logcat.txt` 1.2–1.3 GB（c-01 前 40 MB 取樣：97% 的行是 `gatea-telemetry`）；舊 `runtime-f592241` 該輪以 gzip 保存、約 34 MB／格，原始大小未記錄；
  本地保留原檔、未壓縮、不發佈（`runtime-f592241-v6/PUBLISHED-SUBSET.md`）。

### 11.4 執行紀錄（事實，不改判決）

- ADB：手機換了網路，舊端點 `10.191.48.13:42435` 變 `offline`；以 `adb_find.py`（UDP 取本機 IP＋TCP 掃 30000–50000）
  找到 `192.168.1.100` 的 3 個開放埠，逐一 `adb connect`，只有 46297 成功；舊項目 `adb disconnect`。lane 5038 server 仍是 pid 26023。
- 桌面重開清空了 `/tmp`：`/tmp/p_r10_ledger` 依既有指令重建（`cc -O2 ... tests/r10/p_r10_ledger.c tests/r8/r8_xcb_request.c -lxcb -lxcb-render`），
  sha256 `2aca8ae1…` 與 runner 鎖定值相同。探測執行檔 4 個 sha256 與 `tool-qualification/tool-binaries.sha256.txt` 相符。
- 螢幕：`screen_off_timeout` 600000 ms，但手機接 AC 充電且 `stay_on_while_plugged_in=15`（`mStayOn=true`），整輪沒有熄屏；
  每格 `screen-pre/post` 都是 Awake、未鎖。
- 開跑前 MemAvailable 5874 MB；磁碟 477G 用 89% → 系列後 91%（剩 45G）。
- 系列以 `setsid nohup` 脫離 Claude session 執行；擷取期間 Claude 沒有做工具呼叫，只有一個 `tail -F | grep` 監看 `series.out`
  與一個每 30 s `kill -0` 的等待迴圈。另一個閒置的 Claude Code 程序（pid 31150，見 §10.4）整輪都在。
- 系列結束後：`com.waydefu.x11gpu` 已無程序，前景回到 Stable `com.termux.x11`，無殘留的 runner／探測／mem-guard 程序。
