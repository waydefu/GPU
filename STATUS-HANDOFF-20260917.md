# 狀態交接 — 2026-09-17（完整接續包）

這是 **waydefu/GPU** 給下一手代理／工程師的權威入口。
它是紀錄與接續套件，**不是** qualification，也 **不是** 授權去跑 R7-05。

```text
倉庫：https://github.com/waydefu/GPU（docs + 接續套件；沒有 PR status checks）
工作站權威樹：/root/projects/GPU加速
程式碼遠端：https://github.com/waydefu/termux-x11（fork artifact CI ≠ 本倉庫）
本快照分支：docs/fdfb1ce-r7-04-handoff-20260917
PR：https://github.com/waydefu/GPU/pull/6（紀錄；未 merge；不是 qualification）
```

**先讀本檔。** 然後：`CONTINUATION.md` → `HANDOFF.md` → `WORKTREE-MAP.md` →
`evidence/session/gate-a-a1/p2-r7-design/HANDOFF-NEXT-AGENT-20260916.md`。

---

## 鎖定狀態（2026-09-17 01:00 UTC+8 現場）

```text
R6:                 PASS / 凍結  0f1e54699d0b11a781f2c044fbc77505f8a53bd8
RCA-1 timeout→Done: FIXED / DEVICE-PROVEN  0d72332
CASE_LOOP:          DEVICE-VALIDATED  7549e36（feeaa56 歷史 DEVICE-PROVEN 凍結；327b028 SUPERSEDED）
B-2:                PASS  runtime-7549e36/b2-requalification-02/  X 32228
                    b2-requalification-01 = INVALID 凍結（當時無 TLS）
歷史 R7-04:         有效 FAIL halt_mismatch  7549e36 X 31122  凍結未覆寫
新 R7-04:           PASS  fdfb1ce X 9891  runtime-fdfb1ce/r7-04-requalification-01/
R7 overall:         IN PROGRESS / NOT YET PASS
R7-05 … P2:         NOT RUN
R8 / R9 / R10:      NOT STARTED / NOT AUTHORIZED
Production Gate A:  BLOCKED
timeout:            2000 ms 未改
CASE_LOOP idle cap: 8 ms CLOCK_MONOTONIC 未改
Stable :1:          com.termux.x11  1.03.01-11b82d9-06.09.26  PID 24999  未碰
HDMI:               observe-only 未改
```

裝置 experimental（已安裝、本任務後留下）：

```text
package:      com.waydefu.x11gpu
versionName:  1.03.01-fdfb1ce-16.09.26
versionCode:  15
SHA:          fdfb1ce44b429897eda17c43bf33fbd37afe67f3
parent:       7549e3667ec03b8b5e50d2e5befe03065840bbd9
branch:       fix/gatea-r7-fatal-propagation-20260916
CI:           https://github.com/waydefu/termux-x11/actions/runs/35103216566  success
APK SHA256:   5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c
signer:       b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1
Build ID:     1d6bf3cd0eb06d12804e690679211ee7f34f998e
lastUpdateTime: 2026-09-17 00:54:07
```

最後 ADB（會變，接續時必須 live-fetch，禁止寫死）：

```text
10.191.48.13:41361
_adb-tls-connect._tcp.local.  adb-51c6f1fe-ZtRPH4
identity: myron / 25102PCBEG
```

---

## 這一手證明了什麼

歷史 R7-04（`7549e36`）是 **有效 FAIL**：renderer 已發出
`GATEA_FATAL_HALT what=r-gatea-DIRECT_LOOKUP_FAIL reason=2`，X 隨後又發出
`GATEA_FATAL_HALT what=x-direct-not-success reason=4`。凍結合約 judge 看 **最後一筆 halt**，因此 `halt_mismatch`。
fail-stop 本身當時就成立（無 ACK / 無 Gcomp Done / 無 success completion）。

修復 `fdfb1ce`：已發布的 `generationFatal` 為權威；X 不再合成衝突的 timeout reason=4；
`gateAXFatal` 在 published≠0 時只 dump `x-observe-fatal` 然後 `_exit(127)`，不發第二個 halt。

裝置複測格 `runtime-fdfb1ce/r7-04-requalification-01/`：

- 新鮮 X **9891**，Activity **23139** TID **8877**，DISPLAY `:3`
- `EXACT_R7_04_ENV`（PROTO=1 TELEMETRY=1 TEST_FAULT=fbo-incomplete TEST_ARM=1）
- 觸發 `p_r3_single_direct` **恰好一次**
- PUBLISH serial=9 → CONSUME → LOOKUP_OK → event 35 恰好一次 → 最後 halt `r-gatea-DIRECT_LOOKUP_FAIL reason=2`
- `x-direct-not-success reason=4` = **0**
- 凍結 `judge-r7.py` → `R7_PASS fbo-incomplete`
- 歷史 `7549e36` 同一支 judge 仍 → `R7_FAIL halt_mismatch what=x-direct-not-success reason=4`
- `NO_X3_RESIDUE`；Stable PID 24999 不變

**這不是完整 R7 PASS。** B-2 不因本格而降級，也不重跑。

---

## 下一手要做什麼（未授權，禁止從本 PR 執行）

凍結合約順序：04 → **05** → 01 → 02 → 03 → 06 → 07 → 08 → 09 → 11 → 10 → P1 → P2。

下一 mandatory 格：

| 格 | selector | 觸發 | 凍結 judge 最後 halt |
|---|---|---|---|
| R7-05 | `post-draw-gl` | `p_r3_single_direct` ×1 | `x-direct-not-success` reason=**2**（QUIESCED；與 R7-04 的 renderer FATAL reason=2 不同） |

細節、命令、禁區見 `CONTINUATION.md`。沒有新的顯式授權就 **STOP**。

---

## 讀檔順序

1. 本檔 `STATUS-HANDOFF-20260917.md`
2. `CONTINUATION.md`（怎麼接、什麼不能做）
3. `WORKTREE-MAP.md`（source / SHA / 遠端）
4. `HANDOFF.md`（完整 ledger）
5. `AGENTS.md` + `TEST-MATRIX.md`
6. `ADB-CONNECT.md`（接裝置；IP/port 當次現抓）
7. R7 凍結合約：`evidence/session/gate-a-a1/p2-r7-design/GATE-A-P2-R7-R10-SUPPORT-DESIGN-20260916.md`
8. R7-04 修復 RCA：`.../GATE-A-P2-R7-FATAL-PROPAGATION-REPAIR-20260916.md`
9. 新格 packet：`.../runtime-fdfb1ce/GATE-A-P2-R7-04-REQUALIFICATION-01-20260917.md`
10. 歷史 FAIL packet：`.../runtime-7549e36/GATE-A-P2-R7-QUALIFICATION-01-20260916.md`
11. B-2 PASS packet：`.../runtime-7549e36/GATE-A-P2-B2-REQUALIFICATION-02-20260916.md`（凍結，不重跑）

歷史 `STATUS-HANDOFF-20260916.md` 停在「B-2 PASS、R7 未開」，**已被本檔取代為入口**，保留作歷史。

---

## 本倉庫有什麼 / 沒有什麼

**有（足夠接續）：**

- 全部現行權威 Markdown（HANDOFF / AGENTS / TEST-MATRIX / 契約 / RCA / packets）
- 凍結 `judge-r7.py` + `test-judge-r7.py` + 兩格 logcat-follow（可獨立重判）
- R7-04 新格與歷史 FAIL 格的完整文字證據
- 修復 core-src（classifier + `gateAXFatal` / `gateADoneDirect` 摘錄 + host test）
- 裝置資格 runner、`start-x3.py`、`harness-lib.sh`、fixture ELF、ADB mDNS helper
- R6 / CASE_LOOP skills 與 portable evidence-first skills
- CI 35103216566 產地證明（不含 APK 本體）

**沒有（刻意；改去 fork CI / 工作站）：**

- APK / `libXlorie.so`（15MB / 3.6MB；從 termux-x11 Actions **35103216566** 下載）
- 完整 xserver submodule / `.gradle` / build
- B-2 stress1000 原始 logcat（73MB；B-2 已 PASS 凍結）
- `logcat-dump-unfiltered.txt`（與 follow 重複；SHA256 記在格內 MANIFEST）
- Stable APK、配對碼、token

在 F8 上，**工作站樹 `/root/projects/GPU加速` 仍是 runtime 權威**。本 GitHub 快照對齊該樹在 2026-09-17 的交接切面。若從空目錄接續，把本倉庫 clone 到那個路徑，再依 `WORKTREE-MAP.md` 拉 `waydefu/termux-x11` worktree。

---

## 紅線（狀態，不是步驟）

- 不准碰 Stable `com.termux.x11` / `:1` / HDMI 設定。
- 不准 `termux/termux-x11` origin PR／merge／force。
- 不准改 2000 ms timeout、不准改凍結 `judge-r7.py`、不准改 R7 契約。
- 不准 overlay：`b2-requalification-01/02`、`repair-validation-01`、歷史 `r7-qualification-01`、`r7-04-requalification-01`、任何 `stall-obs-01`。
- 不准 silent-retry 歷史 FAIL。不准從本 PR 自動開 R7-05 / R8+。
- 不准把 docs merge 當成 R7 PASS 或 Production enable。
- 不准 `±1 UNORM` 當 PASS。
- ART JIT `0x4800xxxx` / `dalvik-jit-code-cache`：OBSERVED，禁止因此改 C。

---

## 還沒做

- 另開授權後的 R7-05 `post-draw-gl` 以及後續 mandatory 格
- 完整 R7 PASS
- R8–R10、Gate H、Production enable

**STOP。沒有新授權就不要跑裝置格。**
