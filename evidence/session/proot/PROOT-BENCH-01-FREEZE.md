# PROOT-BENCH-01 — Cursor 在 proot-fast（PF）對系統 proot（P0）下的實際負載：判準凍結

**狀態：FROZEN（2026-09-24，使用者選「1：先做實際程式的對照測試」；門檻由我依下述理由決定）。**
凍結時沒有任何 P0／PF 的 Cursor 量測資料；只有微基準（`PROOT-TRACER-OVERHEAD-01.md`：sendmsg+recvmsg 55.8 → 29 µs）。

## 問題
同一個 Cursor、同一套自動操作，放在修補版 proot（不攔 recv/send/clone）底下，**整體 CPU（Cursor＋它的 proot 追蹤器＋X3）是否明顯較低**、
閒置不變差、畫面節奏不變差、功能正常？範圍：Cursor、日常參數（`--disable-gpu`）、實驗版 X `:3`；不代表其他程式。

## 組態
| 代號 | 追蹤器 |
|---|---|
| **P0** | `/data/data/com.termux/files/usr/bin/proot`（系統 5.1.107.92） |
| **PF** | `~/build/proot-fast/out/bin/proot-fast`（同版本＋`proot-fast-bwrap-compat.patch`，SHA256 `2a513992…5aba`） |
- 兩者都是**另外新開**的 proot 實例（從 PRoot 外經 `adb run-as` 啟動），參數與日常桌面的 proot 完全相同（42 個，`proot-args.txt`），
  只追蹤這一個 Cursor；日常桌面那個 proot 不受影響。`LD_PRELOAD` 在啟動前清掉（`proot-fast-bench-01` 的教訓）。
- Cursor：`--no-sandbox --disable-gpu-sandbox --disable-dev-shm-usage --ozone-platform=x11 --disable-gpu`；
  獨立 HOME／XDG 目錄、獨立 `--user-data-dir`、`dbus-run-session`、guest 內 `setsid`（session id 記在檔案）。
- 負載與量測沿用 ELECTRON-BENCH-01 的 driver（`electron_bench_drive.mjs`，新增選用的 `EXTRA_PIDS`＝該次的追蹤器 pid）：
  載入 60 s → 閒置 60 s → 捲動 30 s（300 次翻頁、每 50 次換方向）→ 打字 30 s（600 字元）。

## 指標與判準（兩次重複都要成立）
`S = 捲動＋打字的 CPU 秒數（Cursor session ＋ 追蹤器 ＋ X3）`；閒置核數同樣三者相加。
- 順序：rep01 `P0 → PF → P0'`，rep02 `PF → P0 → PF'`；`noise = max(|S(P0)−S(P0')|/S(P0), |S(PF)−S(PF')|/S(PF))`。
- **CPU_BETTER**：每次重複 `S(PF) ≤ S(P0) × (1 − max(0.10, 2 × noise))`。
  10% 的理由：追蹤器只是總量的一部分，但對日常程式而言總 CPU 少 10% 已經感受得到；ELECTRON-BENCH-01 的 A/A 是 5.1%，
  屆時 2×noise 很可能主導門檻。
- **IDLE_OK**：閒置 `PF ≤ P0 + 0.05 核`。
- **FRAMES_NOT_WORSE**：捲動 `p95(PF) ≤ p95(P0) × 1.10` 且 `>50 ms(PF) ≤ >50 ms(P0) + 3`。
- 判決：四條（含有效性下的功能正常）都成立 → `PROOT_FAST_BENEFIT`；有效但 CPU_BETTER／IDLE_OK／FRAMES 任一不成立 → `PROOT_FAST_NO_BENEFIT`；
  PF 的 Cursor 當掉、功能失效 → `PROOT_FAST_FAIL`；有效性不成立 → `PROOT_INVALID`。

## 有效性（任一不成立 → 該輪 INVALID；功能類另判 FAIL，見上）
- 觸控 0（錄製器自我測試通過）、thermal 開跑前 0、每階段前後實驗版前景／亮屏／無鎖屏。
- 追蹤器身分：該輪記錄的追蹤器 pid 的 cmdline 第一個參數必須是該組的 proot 路徑；整段期間可讀（`extra_ticks` 非 null）。
- Cursor 身分 `Disabled`（兩組都是 `--disable-gpu`）；編輯器有焦點、第 50 次翻頁第一行 ≠ 1、打的字可見（ELECTRON-BENCH 的「確實生效」）。
- 結束後：Cursor session 殘留 0、追蹤器已結束（或以精確 pid 結束並記錄）。
- runner 層級：Stable 前後不變、X3 未被追蹤、root 1200×2416、mem-guard 未觸發。

## 工具驗證（受判資料之前）
- 判定器合成案例：PF＝P0（必須 NO_BENEFIT）、PF 明顯達標（BENEFIT）、追蹤器身分錯（INVALID）、追蹤器 CPU null（INVALID）、PF 功能失效（FAIL）、noise 大（NO_BENEFIT）。
- 乾跑：P0、PF 各一輪，只檢查欄位與追蹤器身分，不看數字。

## 不在範圍內
換掉日常桌面的 proot（另外決定）、其他程式、bubblewrap 行為。

## 凍結後、資料前的發現（乾跑 `proot-bench-dryrun-01`，不計分）
1. **量測位置錯了**：`adb run-as` 啟動的 proot／Cursor 屬於 SELinux `runas_app`，日常 PRoot（`untrusted_app`）讀不到它們的 `/proc`：
   dry-p0 的 `session_procs=0`、追蹤器 `extra_ticks` 全 null、`tracer_arg0=null`。（反方向可以：runas_app 讀得到 untrusted_app。）
   → 改由 run-as 那側的 Termux 原生 python 計量（`tests/proot/proot_meter.py`，每 200 ms 記累計 ticks），driver 只負責操作與階段時間戳；
   judge 以時間戳在計量曲線上內插。**尚未整合完成**（見交接）。
2. dry-p0 的 Cursor 功能正常（焦點 true、第 50 次翻頁第一行 1621、打字可見、keys 300、chars 600）。
3. dry-pf 開始後 mem-guard 觸發（MemAvailable 2995 < 3000），runner 中止並結束 X3 → Cursor `X connection error`；該輪觸控 1457。
   當時同時有 5 個 Claude Code 程序（本 session＋兩個 RCA session）約 835 MB、Claude Desktop 約 1.1 GB。→ 每輪開跑前要各自等記憶體。
門檻、指標、組態、順序都沒有改。

## 工具修正（2026-09-24 晚，仍在受判資料之前；fork `9f7bad4` WIP）
- **乾跑 01 的 `survivors_after_kill=0` 是假的**：PRoot 側的結束步驟一樣看不到 runas_app 程序，所以什麼都沒結束、也數不到殘留。
  事後從 run-as 側掃描：手機上**沒有**殘留的 Cursor／proot-fast／meter（上一段的「無殘留」結論成立，但當時的量法不可能看到）。
- 計量（`proot_meter.py` → `<run>.meter.csv`）與結束（新 `proot_bench_end.py`：TERM→10 s→KILL 該 session，再等追蹤器；
  signal 前核對追蹤器 arg0；每個 pid／cmdline 記入 `<run>.end.log`）都改在 run-as 側執行。結束未驗證（殘留 ≠ 0 或追蹤器未結束）→ 整個 cell 中止。
- judge 改用 CSV：各階段邊界以兩側樣本線性內插；兩側樣本都須在 0.5 s 內、追蹤器與 X3 ticks 非空、session 程序數 ≥ 1，否則 INVALID。
  合成測試 12/12：新增「邊界附近缺樣本」「session 程序數 0（乾跑 01 的實際狀況）」「CSV 不存在」「結束後有殘留」，四個都必須 INVALID，且逐一確認紅在對的理由。
- 每輪開跑前等 MemAvailable ≥ 4600 MB 連續 20 s（最多 300 s），逾時中止 cell。
門檻、指標、組態、順序都沒有改。下一步：乾跑 02（只看欄位）。

## 乾跑 02（`proot-bench-dryrun-02`，不計分；只看欄位，未印任何 S／idle 數字）
- runner `CMD_CAPTURED` rc=0；Stable 前後 JSON 完全相同；mem-guard 未觸發；每輪開跑前 MemAvailable 5594／5711 MB（各等 20 s）。
- dry-p0：追蹤器 arg0 `/data/data/com.termux/files/usr/bin/proot`；dry-pf：`…/proot-fast/out/bin/proot-fast`；兩輪觸控 0、thermal 0、drive_rc 0。
- meter CSV 927／928 列，樣本最大間隔 203 ms；空值／程序數 0 的列只在 `type.end` 之後（結束步驟之後），量測區間內沒有。
- 結束：dry-p0 session 26 個程序 TERM 後全部結束（無 KILL），`survivors=0 tracer_gone=true`；dry-pf 同；事後 run-as 側掃描殘留 0。
- judge `analyse()`：兩輪 **VALID**、why 空。
- 受判工具（= fork `9f7bad4` 的內容，cell 記錄的 sha256 前 16 碼）：drive `f2c6b96be3ab21b0`、launch `ff6fdce5644866ab`、args `e2865fb8a53fce44`、
  meter `74ee1cdfb8f3e8d2`、end `102df646589aca59`、cell `09fb812be93d03a6`、judge `86f0159baf0dd593`；proot p0 `ea47e17da8e6ff48`、pf `2a5139922f4c1533`；
  WS `879dd353…`。正式 rep01／rep02 必須用這組雜湊，任何一個不同 → 不得計分。
