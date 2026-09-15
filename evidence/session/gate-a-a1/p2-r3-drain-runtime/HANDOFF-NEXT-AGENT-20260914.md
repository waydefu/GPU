# Gate A P2 runtime — 交接（2026-09-14 12:17 CST 使用者暫停）

> Unique entry is now
> `../p2-r3-terminal-runtime/HANDOFF-NEXT-AGENT-20260914.md`
> (`88e3f17` CI QUALIFIED, **not installed**). This file is the frozen
> `8479997` runtime pause + R3 FAIL record. Do not rewrite the R3 FAIL.

給下一位：先讀本檔，再讀 `HANDOFF.md`「Next」。**不要從聊天記憶接續。**
本輪已停：不重跑 R3、不裝新 APK、不改 source，除非下一位帶著新授權繼續。

```
STATUS: PAUSED by user 2026-09-14 12:17 CST
ARTIFACT: 8479997 INSTALLED (experimental only)
R1 oracle/stress: PASS (T2 6/6 NOT rerun on this APK)
R2 imported-AHB rejection: PASS
R3 single-direct: FAIL (GATEA_DRAIN ran; READY never published)
Production Gate A: BLOCKED
Stable :1 PID 16085: UNTOUCHED
HDMI: observe-only
```

## 1. 任務（未完成）

把 Gate A P2 runtime 從歷史 `15caa00` R1 PROTO=0 SIGSEGV 走到 **R1–R10 + bounded XFCE**，結束條件是 **P2 RUNTIME CLOSED/PASS**。Production Gate A 維持 **BLOCKED**。永不 enable Production，永不碰 Stable `:1` / HDMI，永不裝未資格化 APK。螢幕關閉／鎖定 ≠ PASS。

目前卡在 R3：drain-wait 已證明會跑，REGISTER 進 GL drain 後沒有 READY。

## 2. 權威與樹

| | |
|---|---|
| 專案根 | `/root/projects/GPU加速`（**不是** Git repo） |
| 活躍 worktree | `/root/projects/GPU加速/src/f8-ahb-gatea-a1` |
| branch | `qualification/gatea-a1-microprobe-20260912` |
| HEAD | `84799977fdf2923c352cf1a86c00cb7e153189bf` clean |
| remote | fork only `https://github.com/waydefu/termux-x11.git`（禁 `origin`、禁 PR） |
| 讀檔順序 | `HANDOFF.md` → 本檔 → `TEST-MATRIX.md` → 下列 GATE 檔 → `/root/.serena/memories/global/f8-workstation.md` |
| ADB SOP | `/root/projects/GPU加速/ADB-CONNECT.md` |

Closed 不准重開：P0 / P1 / P2-A / P2-B.1 / P2-B.2 / S3 / D0a。Predicate 維持窄：mask / two-pass / transform / bilinear / repeat / componentAlpha 仍 software。禁止 `±1 UNORM` 當 PASS。禁止本機 ninja `.so` 當 APK。

## 3. 現裝 APK（唯一 T2-授權產物）

| Field | Value |
|---|---|
| HEAD | `84799977fdf2923c352cf1a86c00cb7e153189bf` |
| message | `fix(gatea): drain REGISTER on Gate A wake, not only on draw` |
| CI | **34791993198** `workflow_dispatch` success，first attempt，headSha match |
| APK SHA256 | `0a9d91f6fb26ee445935d5243f0b80b3f7e0c76574fdbebcc02f0d92f20323a2` |
| versionName | `1.03.01-8479997-14.09.26` versionCode 15 |
| Build ID | `b072c9d2ff12f0a92258086a609b22744359654a` MATCH on-device |
| signer | `b6da0148…ee5e1` CONTINUITY PASS |
| lastUpdateTime | 2026-09-14 12:06:59 |
| package | `com.waydefu.x11gpu` only |
| evidence | `p2-r3-drain-ci-34791993198/` + `p2-r3-drain-runtime/r0/` |

Formal zipalign 在 aarch64 仍 BLOCKED，不稱 PASS。

### 已凍結、禁止再裝／禁止再跑該 APK 的 R3

| HEAD | 角色 | 禁止 |
|---|---|---|
| `15caa00` APK `d69aff2c…` Build `33a3b67f…` | 歷史 Phase 1 | R1 PROTO=0 SIGSEGV PID **31807** OBSERVED |
| `dd81ac0` | R1/R2 PASS | R3 FAIL：Activity getenv 跳過 bind |
| `98b0011` | getenv 修復 | R3 FAIL：bind live、無 REGISTER_READY。**勿重跑 R3** |
| `6c7ee6f` | peek-diag | R3 FAIL：HANDLE live、GL drain 沒跑。**勿重跑 R3**。T2 B2 SIGSEGV PID **21977** JIT OBSERVED |

PID **21977**：`PC=0x4800226c` / `si_addr=0`，live maps 在 unset X 上是 `[anon_shmem:dalvik-jit-code-cache]`。同類 B3a U4 / A1 `0x4800xxxx`。**不是 libXlorie / 不是 Gate A C++。** 後續 T2 rerun-1 6/6 PASS（21977 NON-REPRODUCED on that rerun）。使用者：沒有**新** crash 就不要重跑完整 T2 6/6。

## 4. 8479997 本輪 runtime

Stable：`com.termux.x11` `1.03.01-11b82d9-06.09.26` PID **16085** DISPLAY `:1`，lastUpdateTime 2026-09-07 22:55:03。每次 teardown `STABLE 16085` + `NO_X3_RESIDUE`。

最後一次 ADB serial（會變，重連必須現抓）：`192.168.1.100:46385` `device` product `myron_global` model `25102PCBEG`。WiFi 當時 `192.168.1.100`，port **46385**。

### R1 PASS（oracle/stress，不是 T2 6/6）

Evidence: `r1-unset-oracle/`、`r1-proto0-oracle/`。

| cell | X PID | oracle | x100 | mixed100 | x1000 | GATEA_EVENT |
|---|---|---|---|---|---|---|
| unset | 26155 | 1514 fail=0 maxΔ=0 Xnz=0 | 100/100 | 100/100 | 1000/1000 | 0 |
| PROTO=0 | 27458 | 同上 | 100/100 | 100/100 | 1000/1000 | 0 |

### R2 PASS

Evidence: `r2-imported-reject/`。X PID **28794**。modifier 1255 ×2（logcat 重複 → 4 行，assert `n>=2`）。兩 cell `exact_px=64 maxΔ=0 got0=00804000`。`GATEA_EVENT=0`（rejection，預期）。`TERMUX_X11_DEBUG=1` 才能看到 DRI3 **server** import log。R2 另見 `GATEA_DRAIN controls=1`（type=6），drain 路徑對 control 也有跑。

### R3 FAIL — 停在這裡

Evidence: `r3-single-direct/` + `GATE-A-P2-R3-RUNTIME-20260914.md`。

```text
12:11:38.037 pid=27805 GATEA_BIND bound=1
12:11:45.063 pid=27805 GATEA_PEEK magic=1 bound=1
12:11:45.063 pid=27805 GATEA_HANDLE type=1 id=6
12:11:45.063 pid=27805 tid=31188 GATEA_DRAIN imports=1 overflow=0   ← GL thread
12:11:47.063 pid=31408 GATEA_FATAL_HALT what=x-ready-timeout reason=4
12:11:47.082 pid=27805 GATEA_FATAL_HALT what=r-hup reason=6
```

- Activity PID **27805**，X PID **31408** died
- fixture `FAIL GetImage`
- `GATEA_EVENT=0`（無 REGISTER_READY）
- 無 `r-unbound-frame`、無 `r-import-enqueue`、無 `r-ready-send`
- drain 在 **tid 31188**，looper 在 27805 — wake/drain-wait **已證明有效**（相對 6c7ee6f「GL 從沒 drain」已翻頁）

**禁止**在 `8479997` 上 silent-retry 這一格 R3。要新的、已證明的 repair APK，且先過 R1/R2 requal。

## 5. 已證明的 R3 失敗鏈（勿重判）

1. **dd81ac0**：Activity 不繼承 `TERMUX_X11_GATEA_PROTO` → bind/peek getenv-gated。
2. **98b0011**：bind live（`r-hup`），無 READY。Peek-true + unbound 可能把 REGISTER 當 `lorieEvent` 吃掉。
3. **6c7ee6f**：BIND + PEEK magic=1 bound=1 + HANDLE type=1 id=6，然後 2s timeout。`shouldWait` 把 `wakeGateA` 當 spurious → `gateADrainPendingImports` 沒跑。
4. **8479997**：`gateAHasPendingDrain()` 讓 `shouldWait` 在 pending import/control/overflow 時回 false（**不含** ready-registry；`lorieGateAImportBusy` 會在第一次 READY 後空轉）。DRAIN 已跑。READY 仍未送出。

## 6. 下一位要證的事（未證明 — 不是授權去改架構）

`gateADrainPendingImports` 記了 `imports=1` 之後呼叫 `gateAValidateImport`。2s 內沒有 READY / REGISTER_FAILED / `GATEA_EVENT` / `r-ready-send`。X timeout 代表 X **沒收到** READY **也沒收到** FAILED（FAILED 會 `WAIT_FAILED`，不是 2s timeout）。

未證明假說（優先看 source，不要先重跑同一格）：

1. **Silent drop**：`gateAValidateImport` 在 GL thread 上 `lorieGateABoundTuple` mismatch → `gateAReleaseTrackedAhb` 後 **return，不送 READY/FAILED**（`renderer.cpp` ~394–397）。註解寫「stale nodes die quietly」，但這次 REGISTER 時 X 正在等，quiet drop 會變成 timeout。
2. **EGL 未 current**：`eglGetCurrentDisplay() == EGL_NO_DISPLAY` 或缺 EGLImage PFN → `gateASendRegisterFailed`。若 `conn_fd == -1` 或 write 失敗，可能幾乎無 log（FAILED send fail 只有 `loge`）。X 仍可能 timeout。drain 在 `threadLoop` 裡、`refreshContext`/`eglMakeCurrent` **之後**才跑；若本圈沒 make current，這條成立。
3. **Validate 卡在 EGL**（`eglCreateImageKHR` / `glEGLImageTargetTexture2DOES`）直到 X 2s timeout，然後 `r-hup` 殺掉 Activity。時間戳精確 2.000s，符合 X waiter，不證明 hang，也不排除。
4. READY 已送但 X demux miss — 較弱：renderer 成功路徑會 `lorieGateATrace(REGISTER_READY)`，本格 `GATEA_EVENT=0`。

`conn_fd`：Activity 與 X 是**不同 process** 的同名 BSS。Activity 由 `connect_()` 設定；HANDLE 能讀 socket，故 HANDLE 當下 Activity `conn_fd` 不是 -1。`gateASendMutex` 包 GL 端 write。

**下一個合理動作（恢復後）：** 在 `gateAValidateImport` 出口加可觀測 log（bound match / display / send READY vs FAILED vs silent-tuple-drop），證機制 → 窄修 → incremental `:lorie:buildCMakeDebug[arm64-v8a]` → commit → push **fork** → CI qualify → 只裝該 APK 到 experimental → R1/R2 requal → 再 R3。不要關測試、不要吞錯、不要 CPU-fallback-as-PASS、不要拿掉 fail-stop、不要無證明加長 timeout。

## 7. 恢復後的操作紅線

HARD STOP：Stable `:1`、HDMI、Production enable、frozen ABI break、破壞性 git、無法解釋的 user overwrite、不可逆裝置動作、重開 protocol。

- 實驗只在 `com.waydefu.x11gpu` / `:3` / Android **display 0**。
- Launcher：`evidence/session/gate-a-a1/p2-runtime-phase1/runner/start-x3.py`（不強制 PROTO）。
- Kill X 只認 cmdline 前綴 `termux-x11gpu com.waydefu.x11gpu :3`。禁 `pkill -f f8-x11gpu`。禁 `logcat -c`。
- `am force-stop com.waydefu.x11gpu` only。永不碰 X1 socket。
- `am start --display 0 -W -n com.waydefu.x11gpu/com.termux.x11.MainActivity`
- logcat `-T` 日期必須是**一個**參數：`ADB shell "date '+%m-%d %H:%M:%S.000'"`
- tags 含 `LorieNative`、`gatea-a1`、`gatea-telemetry`（不要 `*:S` 吃掉 fatal）
- fixtures：`evidence/session/gate-a-a1/p2-r1-diag-runtime/fixtures/`
- R2 helper：`/data/data/com.termux/files/home/r2-ahb-helper/` + `patches/p_r2_imported_ahb.c`
- 需要 `p_b3a_hold`，否則 client 之間 X 會 reset
- PROTO/TELEMETRY 必須精確 `"1"`。`TERMUX_X11_DEBUG` 是 presence-sensitive
- 一次一個重裝置指令
- 本輪 scripts：`p2-r3-drain-runtime/run-r1-oracle.sh`、`run-r2.sh`、`run-r3.sh`（裡面的 serial 可能已過期）

ADB：native `/data/data/com.termux/files/usr/bin/adb`，`HOME=/data/data/com.termux/files/home`，isolated `-L tcp:5038`，永不 5037。`f8-adb-port` PRoot wrapper 無效（`libc.so.6`）。從 PRoot 發現 port：Termux python + ctypes shim（`find_library("c")` → `"libc.so"`），再 `connect IP:PORT`。禁掃 port。配對碼永不離開本機 prompt。

R3 PASS 之後（使用者已下令、不必再問）：R4 1514 direct oracle exact → R5 same-AHB 4096-cycle ownership → R6 cross-op 雙向 → R7 deterministic fail-stop → R8 DestroyPixmap/CloseScreen → R9 generation recreate + stale reject → R10 residue/leak → bounded XFCE。設計：`GATE-A-P2-RUNTIME-QUALIFICATION-DESIGN-20260913.md`。

## 8. 本輪應對齊的檔

| 檔 | 角色 |
|---|---|
| `/root/projects/GPU加速/HANDOFF.md` | runtime 權威；banner + Next |
| `GATE-A-P2-R1-R2-REQUAL-20260914.md`（本目錄） | 8479997 R1/R2 |
| `GATE-A-P2-R3-RUNTIME-20260914.md`（本目錄） | 8479997 R3 FAIL |
| `r0/INSTALL-8479997-20260914.md` | 安裝綁定 |
| `../p2-r3-drain-ci-34791993198/P2-R3-DRAIN-CI-ARTIFACT-PROVENANCE-20260914.md` | CI |
| `../GATE-A-P2-R3-DRAIN-WAIT-IMPLEMENTATION-20260914.md` | drain-wait 修法 |
| `/root/projects/GPU加速/TEST-MATRIX.md` | 閉閘不變；Gate A P2 runtime 指標 |
| `/root/projects/GPU加速/ADB-CONNECT.md` | 連線 SOP |

Serena project 名的舊指示 `gpu-f8-ahb` **不可直接使用**；它目前指向 D0a
worktree，不是 Gate A。詳見下方 §10。子代理最多 2 個 Luna Max；Gate A /
AHB / ownership / fence / lifecycle 裁決留主控模型。

## 9. 單一路徑接手契約（Grok 4.6 / next agent）

**本檔是唯一入口：**

```text
/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-drain-runtime/HANDOFF-NEXT-AGENT-20260914.md
```

先完整讀完本檔，再依本檔列出的精確 reference 查證；不要從聊天摘要、模型記憶、
`README.md` 或歷史報告的 present-tense「Next」自行恢復工作。本檔沒有授權動作：
目前仍是 `PAUSED`。未收到使用者新授權前，只能讀 source/evidence、檢查 Git 與本機
process；禁止 source/doc mutation、build、push、CI、ADB、install、runtime、Stable、
HDMI。

判定順序：

```text
HANDOFF.md top banner + Current snapshot + current Next
→ 本檔
→ TEST-MATRIX.md current Gate A row
→ 本檔 §8 的本輪 Gate / CI / install evidence
→ source at exact 8479997
```

若 lower historical section 與本檔衝突，以本檔和 `HANDOFF.md` 頂部 current snapshot
為準，但要回報矛盾，不可靜默選一邊。

## 10. 工具與環境矩陣（2026-09-14 13:11 CST 唯讀重查）

### Host / build

| 項目 | 現況 |
|---|---|
| Host | POCO F8 Ultra，Android 16 + Termux + Ubuntu 24.04 ARM64 PRoot |
| Kernel seen in PRoot | `Linux 6.17.0-PRoot-Distro aarch64 GNU/Linux` |
| Working root | `/root/projects/GPU加速`（不是 Git repo） |
| Active Git worktree | `/root/projects/GPU加速/src/f8-ahb-gatea-a1` |
| Active branch / HEAD | `qualification/gatea-a1-microprobe-20260912` / `84799977fdf2923c352cf1a86c00cb7e153189bf` clean |
| Fork remote | `fork/qualification/gatea-a1-microprobe-20260912` = exact `8479997`; 禁 `origin`、禁 PR |
| D0a control | `/root/projects/GPU加速/src/f8-ahb` / `a6cc7952861b8a63740d42bf78553573cfa0eec0` clean，不得改 |
| Python | `python3 3.12.3`; `python 3.14.6`；PEP 668，需套件時用 venv/uv |
| Git | `2.43.0` |
| Java | OpenJDK `21.0.12`（現行 shell）；CI authority 仍以 workflow 實際 Temurin/toolchain provenance 為準 |
| CMake / Ninja | `3.28.3` / `1.11.1` |
| Android NDK | `/root/android-sdk/ndk/29.0.14206865` present |
| Hermes | `v0.21.2`；若派 Luna，必須顯式 `gpt-5.6-luna-900k` / `openai-codex` / `--reasoning max`，同時最多 2 個 |

本機 ARM64 native task 可用：

```text
./gradlew --no-daemon --no-build-cache :lorie:buildCMakeDebug[arm64-v8a]
```

但目前 paused，未授權 build。APK packaging 的 Android `aidl` / formal `zipalign`
仍受 x86-64 host binary on aarch64 限制；不要裝隨機替代品、不要把 formal zipalign
冒稱 PASS。完整 APK 使用 fork GitHub Actions x64/multi-ABI CI；任何未來 artifact 必須
重新綁定 exact HEAD、run headSha、APK hash、signer、embedded/unstripped Build ID。

### Device / display（只保存 snapshot，不是 13:11 live query）

```text
Device: 25102PCBEG / myron_global / Android 16 / SDK 36
Experimental package: com.waydefu.x11gpu only
Experimental display: :3 only
Activity target: Android displayId=0 only
Stable: com.termux.x11 / :1 / recorded PID 16085 — NEVER TOUCH
HDMI: observe-only; never change mode/window/projection
```

最後 ADB endpoint `192.168.1.100:46385` 已過期可能性高；任何恢復都必須 live-fetch，
禁止硬編、禁止掃 port。ADB authority：

```text
/data/data/com.termux/files/usr/bin/adb
HOME=/data/data/com.termux/files/home
-L tcp:5038 only
never 5037
```

`/usr/local/bin/f8-adb-port` PRoot wrapper 無效。配對碼／token／credential 永遠不得進
chat、log、文件或模型。一次只做一條 device command，確認輸出再下一條。

### 可用工具與正確使用

- Source/evidence：bounded file read、content search、`git show/log/status/diff`；先追 symbol
  definition/callers，再判斷，不可先猜。
- Git：read/edit/test/branch/commit/push/CI 可在使用者授權範圍內；本專案禁 PR；
  `merge`、force push、history rewrite 禁止未批准，永禁 `reset --hard`。
- Build：只接受未經 pipe 吃掉 exit code 的 Gradle 真實 exit status；log capture 必須
  `pipefail` 或記 `PIPESTATUS`。
- Artifact：不得用 local ninja `.so` 代替 CI APK；不得用舊 APK 代替新修正。
- Runtime：purpose-built evidence > process liveness > bounded full logs > filtered/tail logs。
- Browser Automation 可用；Computer Use 在 ARM64/PRoot 未安裝。

### Serena 陷阱（先修或繞過，不得讀錯樹）

已確認：

```text
gpu-f8-ahb
  → /root/projects/GPU加速/src/f8-ahb (D0a a6cc795)
  → C/C++ server
  → read_only=true

f8-ahb-gatea-a1
  → active Gate A worktree
  → language_servers: java      # 錯，無可靠 C/C++ symbols
  → read_only=false             # 不符合 read-only scout
```

因此 AGENTS 舊 scout 範本若指定 `gpu-f8-ahb` 會讀到 D0a；直接改用
`f8-ahb-gatea-a1` 又會遇到 Java-only index。未修 Serena config 前，對 Gate A source
使用精確 worktree path 的 bounded reads/search；每個結論必須附該 worktree 的
`git rev-parse HEAD`。任何 Serena 結果若 root/HEAD 不等於 `8479997`，立即丟棄。

## 11. 2026-09-14 13:11 唯讀稽核發現（恢復前必讀）

### P0 — RESOLVED 13:57：四個 orphan `adb logcat` 已停止

13:11 audit 時的 live process（歷史 snapshot）：

```text
PID 25867 PPID 1  R1 unset collector
PID 27365 PPID 1  R1 PROTO=0 collector
PID 28785 PPID 1  R2 collector
PID 31372 PPID 1  R3 collector
```

保存的 `logcat.pid` 是 25866 / 27364 / 28784 / 31371，實際 adb child 全部多 1；
script kill 到 shell function wrapper，沒有 kill/wait 到 adb child。四個
`logcat-follow.txt` 在 13:11 合計已達 **464,786,295 bytes** 且仍增長。

13:57 cleanup follow-up（已由 parent agent 獨立複核）：

```text
25867 / 27365 / 28785 / 31372: STOPPED
remaining matching adb-logcat collectors: NONE
3-second size recheck: STOPPED
final observed sizes:
  R1 unset    167899170
  R1 PROTO=0  153406287
  R2          134926282
  R3          133397225
Gate A: 8479997 clean
D0a: a6cc795 clean
Device / Stable / HDMI: not touched by cleanup
```

Operational leak 已止血；原 scripts 的 PID/trap 缺陷仍未修。上述 PID 與 13:11
「正在寫」狀態只保留作歷史 root-cause evidence，下一位不得再次 kill 已不存在或可能
被重用的 PID。

影響：曾造成磁碟消耗、raw evidence 跨 cell 污染、全機 tag-filtered log 可能混入
其他 app 資料。不要再讀取或傳送這些檔的無關內容。保留既有 evidence，不得刪除、
截斷或為了縮小空間改寫它。

Harness 修正：用 `exec` 讓保存 PID 等於 adb、安裝 `trap`、`kill` 後 `wait`、驗證
collector 已退出；每個新 commit 使用新 evidence directory，禁止覆寫本輪 cell。

### P1 — renderer telemetry flag 沒有跨 process 啟用

`lorieGateATelemetryEnabled()` 仍讀 process-local
`TERMUX_X11_GATEA_TELEMETRY`（`lorie.h:217-227,1007-1035`）。Activity/renderer
不繼承 X launcher environment；PROTO 已在 `98b0011` 改成 shared tuple，telemetry
沒有。因此 renderer-side `lorieGateATrace()` 可能全部 silent。

結論：`GATEA_EVENT=0` + X timeout 可證明 X 未完成 READY wait，但不能單獨證明
renderer 沒走到 trace call。下一個診斷必須使用 bounded unconditional
`LorieNative` stage log，或先把 telemetry enable 綁到 shared generation；不可只加
既有 telemetry event。

### P1 — REGISTER validation 有無終態路徑

`renderer.cpp:376-570`：

1. bound tuple mismatch（`:389-397`）release AHB 後 silent return；沒有 READY、FAILED、
   fatal/HUP 或 waiter wake。
2. `gateASendRegisterFailed` send failure（`:314-320`）只 log，不 fail-stop。
3. duplicate READY（`:472-482`）只 publish shared fatal 後 return，不保證 renderer exit /
   HUP / waiter wake。
4. X READY waiter（`InitOutput.c:2377-2395`）timed wait 返回後，在宣告 timeout 前未再
   acquire-read shared fatal，可能把真正 fatal 誤標為 timeout。

這些是 source-level protocol/observability gaps；是否命中本次 R3 尚未證明。

### P1 — R3 最強但未定罪的機制候選

`gateADirectTryPrepare` 明確先確保 source/destination CPU-locked
（`InitOutput.c:2624-2639`），再 `gateAEnsureReady()`（`:2648-2653`）；真正 checked
unlock 延到第一個 publish（註解 `:2583-2586`）。A1 成功 microprobe 則是 CPU write
後先 unlock 再 EGLImage import。故 renderer 可能在 `eglCreateImageKHR` /
`glEGLImageTargetTexture2DOES` 面對仍 CPU-locked AHB 而阻塞；這是強候選，**不是已證
root cause**。

正確當前措辭：

```text
REGISTER received and drained on GL thread.
No READY/REGISTER_FAILED terminal response was observed by X before 2 s timeout.
Actual post-drain stage/root cause is NOT PROVEN.
```

不要寫成已證明「READY 從未 publish」，也不要靠加長 timeout 或 silent retry 判定。

## 12. Evidence / qualification 缺口（不推翻既有 bounded verdict）

- R2 imported rejection 是間接 proof：真 modifier 1255 ×2 + exact pixels + X-side
  Gate A events 0；沒有專用 `ADMIT_REJECT` event。維持 PASS with limitation。
- R2 app-process exit code未獨立寫檔；`set -euo pipefail` 與後續 assertions存在，可推論
  command success，但 future harness 要保存 exact exit code。
- R0 已證 APK/on-device base APK hash及 Build ID；R1/R2/R3 未保存 live X3 PID 的
  `/proc/<pid>/maps` artifact binding。future runtime 每格補上。
- R1 缺每格執行前 Stable PID/cmdline preflight；只有 teardown `STABLE 16085`。
- `NO_X3_RESIDUE` 只證 process scan，不證 UNREGISTER/EGLImage/AHB/generation clean
  lifecycle；R3 未宣稱 lifecycle PASS，維持。
- R3 尚未到 direct publish，所以 B1/B2/B3 runtime、fence、semantic SUCCESS、relock/
  repair/ACK及 B4 clean retirement 全部仍未驗。
- `run-r*.sh` 硬編 8479997、舊 endpoint和既有 evidence path；只作歷史重現材料，
  禁止原地執行。
- Activity placement evidence 顯示 target Activity `displayId=0`，但 scripts 沒有一致的
  machine assertion；future harness 必須 fail closed。

## 13. 文件 drift（以本檔為準，但恢復後應修）

`HANDOFF.md` 頂部與 current Next 正確；其歷史編號段仍有 present-tense stale 句：

```text
HANDOFF.md:317-320  current source lacks READY/result/lifecycle（已被 15caa00 靜態取代）
HANDOFF.md:359-362  next is design / do not write code（已過期）
HANDOFF.md:492      dd81ac0 is only T2-authorized APK（已過期）
```

非權威 `README.md` 與 `P2-A-DEEP-REPORT.md` 仍把 P2-B.3 寫成 current next。不要讓這些
歷史敘述覆蓋本檔 Gate A P2 R3 pause。

## 14. 精確恢復順序（只有使用者重新授權後）

```text
0. git rev-parse HEAD / git status --short / git diff --check
   require clean exact 8479997; unexpected dirty → STOP
1. confirm the resolved orphan adb-logcat state remains NONE; do not reuse old PIDs
2. create a new TODO + new evidence directory bound to the next commit
3. add bounded post-drain stage observability:
   ENTER / tuple result / current EGL display+context / native-client-buffer /
   createImage enter+return / image-target enter+return+GL error /
   READY-or-FAILED send enter+return+errno
4. close silent terminal paths without weakening fail-stop or changing frozen ABI
5. ARM64 incremental + full-clean build; compare warning baseline
6. commit; push fork only; exact-head multi-ABI CI; qualify APK/unstripped ELF
7. install experimental package only after artifact qualification
8. fresh R1/R2 requal; T2 6/6 only if user requests/new crash policy requires it
9. exactly one new R3 cell; never rerun R3 on 8479997/6c7ee6f/98b0011
10. R3 PASS才進 R4–R10 + bounded XFCE；Production Gate A仍 BLOCKED
```

不得以以下方式「修綠」：加長 timeout、重試舊 APK、CPU/D0a fallback 當 direct PASS、
skip/disable assertion、吞 send/EGL error、清 logcat、覆寫 raw evidence、降低 exact pixel
要求、碰 Stable/HDMI。
