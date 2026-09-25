# TRACER-SHARD-01 — 追蹤器分流：Cursor／Hermes 各用自己的 proot 追蹤器，日常卡頓會不會消失（凍結 2026-09-25，任何分流資料之前）

> 本檔在任何 TRACER-SHARD 裝置資料之前寫定。判準、門檻、順序、有效性條件在資料出現後一律不改；
> 需要改就另立新編號，舊的照實保留。XFCE-V6-BASELINE-01 的 Part A 判決（`DAILY_STUTTER_REMAINS`）維持原判；
> 本輪資料不與 Part A 合併，只做描述性對照。

## 1. 為什麼

- XFCE-V6-BASELINE-01 Part A（v6，§10）：日常卡頓 E = 48、14，剩下的幾乎全是 S1（`traced_lat` 的 fstatat > 100 ms），
  getppid p99 約 6 µs。
- 事後描述（對已凍結資料的交叉比對，不改判決；`evidence/session/xfce-v6/part-a/` 的 `samples.jsonl` × `traced-lat.txt`）：
  v6-1 的 47 次停頓 **47 次**、v6-2-r1 的 13 次 **12 次**（stock-1 91 次中 87 次）落在「那一秒追蹤器用掉的 CPU ≥ 停頓長度」的秒；
  停頓集中在開 app 後 6–21 s 與 36–43 s（Cursor、Hermes 啟動），那幾秒追蹤器 0.6–1.1 核。
- 解讀（假說，本實驗要驗的就是它）：日常所有 PRoot 程式共用**一個單執行緒**追蹤器；Electron 啟動時大量被攔截的 syscall
  把它塞滿，其他程式的被攔截 syscall 只能排隊。

## 2. 修法（本實驗的處置，主機端已驗證；裝置資料之前）

- **`f8-shard <program>`**：讀呼叫者 shell 的追蹤器（`/proc/<TracerPid>` 的 cmdline 去掉 guest 指令、environ、rootfs），
  經 TermuxService 在所有 proot 之外重建一個相同的追蹤器，以呼叫者的環境與 cwd 執行 `<program>`。共用 rootfs、`/tmp`、X `:1`、D-Bus。
  前景等待程式結束，SIGTERM／SIGINT／SIGHUP 轉給程式（呼叫者持有 f8-shard 的 pid 就持有程式）。Termux 端 `shard-run.sh`。
  已知限制：`--sysvipc` 模擬是每個追蹤器各自一份，分流程式與桌面其他程式之間的 SysV IPC 不通。
- **proot-fast7**（`out7/bin/proot-fast7` sha256 `4f9d10ad…`）＝ v6 ＋ `evidence/session/proot/proot-fast7-peercred.patch`：
  fake_id0 的 `SO_PEERCRED` 對「不是自己 tracee、但真實 uid 與 proot 相同」的對端，給呼叫者自己的假身分。
  原因（原始碼 `extension/fake_id0/getsockopt.c`，實測）：沒有它，日常追蹤器下的 dbus-daemon 看到分流程式是真實 uid，
  拒絕其 EXTERNAL 驗證（宣稱 uid 0）→ 28 ms 內斷線。
- 主機驗證（`evidence/session/proot/shard/`）：
  - `test_shard.sh`：`TEST_SHARD_PASS`（分流、同一追蹤器 sha、DISPLAY、cwd、rootfs、SIGTERM 轉送、追蹤器結束）；
    直接執行的對照判 `NOT_SHARDED`（必紅）；不分流的突變 `f8-shard` → `TEST_SHARD_FAIL`（必紅）。
  - `test_dbus_cross.sh`：v6 `same=OK cross=FAIL`（必紅）、v7 `same=OK cross=OK`。
  - v7 功能：`stat_smoke`／`smoke`／`daily_check` 與 v6 逐字相同（59／23／17 行）；故意壞的 v6b 三項都不同（必紅）。
  - `smoke_electron.sh`（Xvfb `:99`、v7 私有 D-Bus）：Cursor、Hermes 都 `SMOKE_ELECTRON_PASS`（主程序與 renderer 在分流追蹤器下、
    有視窗、SIGTERM 經 f8-shard 後 2 s 內程式與追蹤器都結束）。只剩 system bus 錯誤（PRoot 本來就沒有 system bus）。

## 3. 問題

日常追蹤器為 **proot-fast7** 時，以 `f8-shard` 啟動 Cursor 與 Hermes（**S**）相對於直接啟動（**P**），
**留在日常追蹤器底下的程式**感受到的卡頓次數 E 是否消失或減少？

## 4. 綁定與有效性（每次擷取都記錄；任一不符 → 該次 INVALID）

沿用 XFCE-V6-BASELINE-01 §4、§9 補充 1–6 的每一項（觸控整次擷取 0 筆、螢幕全程亮不鎖、無外接螢幕、
開始時 MemAvailable ≥ 4500 MB、不被追蹤探測 `TRACER 0`、被追蹤探測 `TRACER` = client 追蹤器、各探測 n 門檻、
工具執行檔 sha256 與 `tool-qualification/tool-binaries.sha256.txt` 相同、Cursor／Hermes 開始前沒在跑、Claude Desktop 開著、無其他 Electron），
只把 client 追蹤器的要求改為：
1. **client 追蹤器**：sampler 所在 shell 的 TracerPid → exe sha256 必須以 `4f9d10ad` 開頭（proot-fast7），environ 不含三個關閉開關。
2. **分流工具**：`f8-shard` 與 `shard-run.sh` 的 sha256 記錄於每次擷取，須等於本檔 §11 寫定值（工具定版後補寫於 §11，仍在任何裝置資料之前）。
3. **app 真的起來了**（避免「沒啟動所以不卡」）：loaded 窗結束時，Cursor 與 Hermes 各有主程序存活，且各有 ≥ 1 個 renderer
   （zygote 的子程序；它沿用 zygote 的 cmdline）與主程序掛在同一個追蹤器下。
4. **組別真的生效**：P 組兩個主程序的 TracerPid = 日常追蹤器；S 組兩個主程序的 TracerPid ≠ 日常追蹤器、
   = 該次啟動記錄的分流追蹤器，且分流追蹤器 exe sha256 以 `4f9d10ad` 開頭。

## 5. 組別與順序

- **P**：`/root/.local/bin/cursor-gpu`、`/root/.local/bin/hermes-gpu`（Part A 相同）。
- **S**：`f8-shard /root/.local/bin/cursor-gpu`、`f8-shard /root/.local/bin/hermes-gpu`。
- 每次擷取：baseline 60 s → 兩個 app 同時啟動 → loaded 240 s → 關閉（P 與 Part A 相同的 `--close-launched`；
  S 對記錄的 f8-shard pid 送 SIGTERM，cmdline 須含 `/f8-shard `，記入 `closed.json`，屬 construction）。
- 順序 `P S S P P S`。INVALID 的擷取保留原編號；補一次同組擷取接在最後，全部最多補 2 次；補完仍不足 3 P／3 S → `INCONCLUSIVE`。
- 每次擷取前等 MemAvailable ≥ 4600 MB 連續 20 s（最多 10 分鐘，否則停），並確認 Cursor／Hermes 已不在。

## 6. 指標（與 XFCE-V6-BASELINE-01 §6.3、§9 補充 3 定義相同）

- loaded 窗 = 第一個啟動指令送出起 240 s。
- **S1**：`traced_lat` fstatat > 100 ms 次數；**S2**：被追蹤探測對 `:1` rtt > 100 ms 次數；**S3**：不被追蹤探測 rtt > 100 ms 次數。
- **E = S1 + S2**（留在日常追蹤器底下的程式感受到的）。S3 分開報。
- 描述（不判）：日常追蹤器核數、分流追蹤器核數（每秒）、Stable X 核數、MemAvailable、swap、`getppid` p99。

## 7. 判準

- **T0 對照有效**：3 次 P 的 E 最小值 ≥ 3 → `CONTROL_REPRODUCES`；否則 `WORKLOAD_DOES_NOT_REPRODUCE` → `INCONCLUSIVE`。
- **T1 分流效果**（T0 有效時）：3 次 S 的 E 都 = 0 → `SHARD_REMOVES_STUTTER`；
  否則 `max(E_S) ≤ 0.25 × min(E_P)` → `SHARD_REDUCES_STUTTER`；其他 → `SHARD_NO_CLEAR_EFFECT`。
  （用 P 的最小值、S 的最大值：兩邊都取對 S 不利的一端。0.25 與 Part A A1 的「至少少 4 倍」相同。）
- **T2 X 本身**：任一次 S 的 S3 > 0 → `X_SERVER_STALLS_PRESENT`；否則 `X_SERVER_NO_STALLS`（Stable 沒有 Gate A，只記錄）。

## 8. 結果怎麼讀（先寫下）

- `SHARD_REMOVES_STUTTER`／`SHARD_REDUCES_STUTTER` → 提議把日常 `cursor-gpu`、`hermes-gpu`（與其他重 Electron 啟動器）改經 `f8-shard`；
  由使用者決定，不自動改。
- `SHARD_NO_CLEAR_EFFECT` → 啟動負載不是唯一來源（或分流沒帶走它），下一步看追蹤器每次停頓的成本（被攔截 syscall 的種類與路徑轉換）。
- 任何結果都不改 Stable、Production、Gate A。

## 9. 授權與紅線

- 碰到日常桌面：在 `:1` 上開關 Cursor 與 Hermes（至少 6 次）、對 `:1` 兩個唯讀探測——使用者要在開跑當下明確同意。
- 日常追蹤器換成 proot-fast7 由使用者同意、使用者自己用「F8 工作站」重開桌面。
- 只對記錄的 pid 送 SIGTERM（Cursor／Hermes 主程序或 f8-shard）；不殺其他程序、不動 Stable `com.termux.x11`。

## 10. 預估

6 次 × 約 5.5 分鐘＋間隔，約 40 分鐘；需要 ADB（觸控與螢幕）、螢幕全程亮（插電）、手機放著不碰。

## 11. 工具定版（2026-09-25，在任何裝置資料之前）

工具在 fork `tests/tracer_shard/`（`feat/exa-async-proto-20260923`），重用 `tests/xfce_v6/` 的探測、Part A 檢查函式（匯入，不改）。

| 檔案 | sha256 | 用途 |
|---|---|---|
| `f8-shard` | `b2f11d3dffcb3ac7cfd8c71cfd87d7704b096e7cbf754e9d69fb6ee5c46e5b8e` | 分流啟動器（§2）；判定器凍結值 |
| `shard-run.sh`（安裝於 `~/build/proot-fast/shard/`） | `1b65ac6deab8c5b93a0dbe4b2a6d15b404d6f891ad176e86ce6a7ac270fea912` | Termux 端；判定器凍結值 |
| `daily_sampler_v3.py` | `f98cc5918ebcbbd37474c397f5cfb6af5c7d12c1322f499ba8466e1714910118` | 擷取（§4–§6） |
| `shard_judge.py` | `a2e80ca24a2dd862ef68028e15075a5ff188f4f2c8ae04bbe4f1c3d0b8f65ada` | 判定（§4–§7） |
| `series-shard.sh` | `9b83f56d2b3a0ff7907ba0ed54adfaca2c244113ad9364a6d67387ebaa0643df` | 一條指令跑完 §5 |
| `test_shard_judge.py` | `98163395b7b046b7f31109d50034fcc7af411166a307d35355e69dd25d3ff662` | 26 個測試，全過 |
| `mutation_check.py` | `cad074a3ce0d231cb079da7b0ae2bea85db9698feb3c6213df41daefc0de69af` | 10 個突變全被抓到、未突變對照綠 |
| `host_selftest.sh` | `fc2e580bb4005cd3290e0add9f830c4145bb2c0c47ed4bf0187ac38bf37e17cd` | 主機端到端（v7 測試追蹤器、Xvfb `:99`、私有 D-Bus） |
| `out7/bin/proot-fast7` | `4f9d10ad2f78e1eef3907eea1ef761b4b8265c9d7cbd5779df48b4f8cb756058` | client 追蹤器（§4 第 1 項） |

主機驗證（`evidence/session/proot/shard/host-qualification/`）：
- 判定器：26 測試 OK；突變 10／10 caught（S 組 app 在日常追蹤器、P 組 app 被分流、renderer 檢查、缺 app、v6 追蹤器、
  未凍結工具、門檻 0.5、無對照、挑結果補跑、E 計入 S3）。
- `host_selftest.sh`：`HOST_SELFTEST_PASS`——P 組 Cursor／Hermes 主程序都在 sampler 的追蹤器下（各 2 個 renderer）；
  S 組各在自己的分流追蹤器下、與 f8-shard 記錄相同；判定器除主機模式預期理由（test_mode、無 adb 的螢幕／觸控、短窗樣本數）外無其他理由。
  途中修正（事前、非受判資料）：Cursor 的輔助程序用同一執行檔且無 `--type=`（ELECTRON_RUN_AS_NODE），以 cmdline 猜主程序會找到 3 個；
  改為 P 用啟動記錄的 pid、S 用 f8-shard job 的 `app.pid`，再核對 cmdline。
- 裝置執行需要：日常追蹤器為 proot-fast7（使用者同意＋重開桌面）、ADB、使用者開跑當下同意（§9）。
