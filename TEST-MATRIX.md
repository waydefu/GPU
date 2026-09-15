# TEST-MATRIX.md — POCO F8 Ultra Termux:X11 GPU 研究

權威現況：`HANDOFF.md`（Gate A P2 **裝置**為 `95e6f96` CI **34944171114**。歷史 **R6-D1 PASS** 在凍結 `9369553`。新 APK D2-INFLIGHT 5 格皆保留（COMPLETED serial S PROVEN；GPU 執行 <0.5ms 快於 Xorg CPU 解碼 2.5ms，物理競爭根因已定性）。D2-OOM 未跑。KEEP CI FAIL **34943831800**。R7 STOP。Production Gate A BLOCKED。）。
文件對齊查驗（2026-09-08 15:33 CST）：`git ls-remote`、[PR #1095](https://github.com/termux/termux-x11/pull/1095)、[PR #1114](https://github.com/termux/termux-x11/pull/1114) 頁面與表內 SHA 一致；兩個 PR 目前仍為 open，尚未 merge。P2-B.2 / Stable 基線數值未在 2026-09-14 重測；裝置 PID／experimental 版號以 `HANDOFF.md` 當日 snapshot 為準。

## Control build（Phase 1A，官方 CI）

- fork：`waydefu/termux-x11`（parent `termux/termux-x11`）
- `f8-control`＝`9df8b76`＋空 commit `11b82d9`（僅觸發新 fork Actions 索引，無程式碼差異）
- CI：Build（`debug_build.yml`， Temurin 17＋NDK 29.0.14206865＋AGP 9.3.1），
  `workflow_dispatch` ref `f8-control`，run `34048065064`
- 詳細：`evidence/control/CONTROL-BUILD.md`；✅ run `34048065064` completed/success，
  universal-debug SHA256 `aad3d433…ea98e9`（01:29 CST 已下載驗證，zip OK，未安裝）
- 本機 `src/upstream`：clone 完成、`git status` 乾淨、16 submodule SHA 已凍結（同上檔）

## Stable 凍結（2026-09-07 01:16 CST，歷史紀錄，`evidence/baseline/freeze-phase0.txt`）

以下是 09-07 的凍結紀錄，不代表目前 PID。**現況 PID／包名以 `HANDOFF.md` 為準**（Gate A 輪 2026-09-14：`:1` **16085**，`com.termux.x11` `1.03.01-11b82d9-06.09.26`；09-08 歷史 snapshot 曾為 **26474**）。

歷史覆核（09-07 19:39）：PID **10718** / XFCE **18844** / xfwm **18871**；不可當作目前 PID。

- `termux-x11 :1 -legacy-drawing`（PID 10718）正常，無 `:2`
- `/dev/kgsl-3d0`：`crw-rw-rw-` 可存取
- `f8desk` sha256 `e995a514…`、`f8desk-external` sha256 `c67919ea…`，各含 1 處 `-legacy-drawing`，僅讀取未修改
- **禁止**替換目前 Stable APK `1.03.01-11b82d9-06.09.26`；舊標籤 `1.03.01-6d3c688-27.08.26` 只保留作歷史凍結紀錄；禁止 `adb install` raw CI `com.termux.x11`

## 上游狀態（2026-09-08 15:33 CST 查驗）

| 項目 | 2026-09-07 實測 | SHA |
|---|---|---|
| upstream master HEAD | `ls-remote` | `9df8b767645aa0d0a2f2576767449df55b41962f` |
| PR #1095 head（open，+210/-2，6 files） | `ls-remote`＋`fetch pr-1095`雙驗一致 | `8862681a2396b8494a687af1d2d690d491138e09` |
| PR #1114 head（open，+11/-2，1 file） | `ls-remote`＋`fetch pr-1114`雙驗一致 | `c48e84e63b156be4412004935b6417cbbfebdfe8` |
| 本機 termux-x11-nightly | `dpkg -l` | `1.03.01-6` |
| 本機 Mesa / freedreno ICD | `dpkg -l` | `26.0.6-3` |
| experimental fork HEAD | `f8-p2-b2-over` | **`98224356e40913dcf2188d18748eba9401639850`** |

注意：#1095、#1114 的 upstream PR 仍是 open，這不等於本專案 experimental fork 的 P1/P2 qualification 未完成。#1095 自帶測試需 `--target=aarch64-linux-android26`（用了 Android 26 才有的 AHB API）。舊 `a401b4f` 僅屬 P2-A flight recorder。

## 基線（Stable，損壞即停工）

- `termux-x11 :1 -legacy-drawing` + XFCE：正常（daily driver）
- 裸 `glxinfo -B`：llvmpipe / Accelerated: no（預期內）
- `f8-gpu glxinfo -B`：Zink→Turnip→Adreno 840 / Accelerated: yes / GL 4.6
- `/dev/kgsl-3d0`：`crw-rw-rw-` 可存取
- 指紋：`POCO/myron_global/myron:16/.../OS3.0.302.0`，SDK 36

## 測試矩陣

| Test | Stable legacy :1 | experimental `:3` / f8-ahb | Result |
|---|---|---|---|
| xterm display（resize／redraw／多視窗／create-destroy） | PASS | **P0 CLOSED**：Gate1 matrix PASS；Gate2 xterm ×100 PASS；Gate3 move/expose/overlap/RRSetSize PASS。歷史 +768 僅 regression。 | CLOSED |
| non-legacy root geometry（1B-2） | — | 歷史 +768 曾 2/2。debug5 `c698164` Case A/B/C **3/3** 未重現。 | historical regression |
| window CORE FillRect/PutImage/Segment | — | 已解釋：xterm 外框 `0x20000c` 被 VT `0x20001b` clip，非 server CORE bug。 | 結案 |
| DRI3 pixmap export | BadPixmap error=4，0/100（legacy 預期） | **P1 CLOSED** After AHB export；1×1 DRI3 nfd=1 stride0=256 mmap OK（tiny-pixmap register 3/3） | CLOSED |
| GPU Present | n/a（legacy 關閉 GPU 路） | **QUALIFIED** 1200×2191 / 1280×1024 / 1920×1080；`evidence/present/gate7-close.txt` | CLOSED |
| Fence / FrameTimeline | — | **QUALIFIED** / baseline recorded。1080p solid：GPU 不比 CPU 快。`evidence/fence/gate-close.txt` | CLOSED |
| EXA Copy GXcopy distinct AHB | — | **PASS** 202/202 pixel，203/203 GPU offload；overlap = software。`evidence/exa/copy-gate.txt` | CLOSED |
| EXA Solid GXcopy | — | **PASS** matrix + X-byte repair；unsupported ROP fallback。`evidence/exa/solid-gate.txt` | CLOSED |
| 1×1 pixmap AHB convert/register/Solid/Copy/multi | — | **3/3 each** 無 xfwm。`evidence/session/tiny-pixmap/` | PASS（隔離） |
| XFCE compositor off | PASS（基線 :1） | 舊 crash 已由 P2-A A.3/A.4 定罪為 probe double-wrap；R3 隔離 XFCE 45s：D0/D1/D2/D3、ENTER/RETURN 全通，無 fatal/SIGSEGV/SIGILL。 | **P2-A CLOSED** |
| XFCE compositor on | — | bounded isolated qualification 已 PASS；未列入目前 daily session，不留在 experimental `:3` 常駐。 | bounded PASS / daily not qualified |
| XRender histogram | — | 舊 probe dump 未收集；P2-A 已由 A.3/A.4 關閉，不再以 histogram 作 blocker。 | historical |
| GPU Composite | — | P2-B.2 narrow Over：ARGB→XRGB、無 mask/transform/repeat/componentAlpha、nearest，R3 oracle exact RGB；其餘 cases 仍 software。 | **P2-B.2 PASS (R3)** |
| Gate A P2 runtime（experimental `:3` only） | 禁裝／禁碰 | 裝置 `95e6f96`。D2 5 格皆保留。COMPLETED serial S PROVEN。物理競爭分析已歸檔。D2-OOM 未跑。 | **OPEN**（待 oracle 裁決或 D2-OOM）；Production Gate A **BLOCKED** |
| 10～30 min 穩定性＋CPU/RAM | | | |
| glxinfo bare | llvmpipe（預期） | | | |
| f8-gpu glxinfo | Adreno 840 yes | | | |
| glxgears smoke | PASS（基線） | | | |
| Cursor desktop GL regression | PASS（基線 :1） | | | |
| Chromium 三線 baseline | | | | |

## 歷史 P2-A crash（2026-09-07 18:26 / 18:30；已由 A.3/A.4 關閉）

- 簽名：`Sent shared buffer width 1 stride 64 height 1` → `Fatal signal 11 SEGV_ACCERR`
- Flight last request：`op=138.8` **RENDER Composite** PictOpOver，phase **ENTER**
- 最小重現（無 WM）：`patches/p_render_last.c 1x1` — 兩個 1×1 pixmap picture → Composite Over → 同上 SIGSEGV
- 對照：同一 1×1 的 DRI3/Solid/Copy **不**殺 X
- 當時 experimental `:3` **DOWN**；crash instance 不重啟。這是歷史事故狀態，不覆蓋目前 `HANDOFF.md` 的 `:3` snapshot。

## 失敗紀錄（重現 2 次才立案，一次一變數）

- **已結案（誤判）**：window CORE 靜默消失。實為 xterm parent `0x20000c` 被 VT child `0x20001b` clip。
- **historical-only**：non-legacy +768 曾 2/2。debug5 Case A/B/C + P0 Gates 1–4 皆未重現。P0 CLOSED。
- **P2 OPEN（歷史快照，已 superseded）**：f8-ahb 上 xfwm compositor-off / 1×1 RENDER Composite → SIGSEGV SEGV_ACCERR。勿與目前 P2-A CLOSED、P2-B.2 PASS 混為同一結果。
