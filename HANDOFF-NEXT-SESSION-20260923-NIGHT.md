# HANDOFF — 2026-09-23 夜：卡頓的真正瓶頸可能是 PRoot 追蹤器，不是 X／GPU

先讀：本檔 → STATUS-HANDOFF-20260921.md 最上面的 STATUS 區塊 → 記憶 `gpu-path-slower-than-cpu`、`lmk-kills-termux-stable`。

## 使用者的真正目標（原話）

「解決卡頓問題並解放 CPU 壓力」。使用者已否決：A（預設走 CPU＝維持現狀）與 C（窄路由＝幾乎用不到）。
決策備忘（Google 文件，使用者雲端硬碟）：「V1-Core 方向決策備忘：GPU 路徑 vs CPU（2026-09-23）」。

## 今晚的新證據（重要）

```
18:43  只開 Claude Desktop + Claude Code：PRoot 追蹤器 0.97 核；Claude Desktop 畫面 ~0.3 核；Stable X 0.03–0.04 核
19:13  Claude Desktop 剛重開：PRoot 追蹤器 1.01 核（pid 24406，Threads: 1 -> 單執行緒已滿載）
       Claude Desktop gpu-process 0.26 核、renderer 0.19 核（RSS 521 MB）、Stable X 0.14 核
追蹤器參數  proot --kill-on-exit --link2symlink --sysvipc ... -L --change-id=0:0（proot-distro ubuntu）
```

假設（未證明）：PRoot 內所有程式（Claude Desktop、Cursor、Hermes 等 Electron app，全部 `--disable-gpu`）的系統呼叫都經過
這條單執行緒追蹤器；它滿載時所有視窗一起卡，開 Cursor + Hermes 會更嚴重。GPU 加速 X server 碰不到這個瓶頸。

使用者回報：19:03 左右 Termux:X11 桌面卡爆黑屏（手動重開手機，logcat/dropbox 已清空，無手機端證據）；
19:15 左右 Claude Desktop 視窗本身卡爆全黑（關窗重開恢復）。這個 session 的對話極長，Claude Desktop 渲染負擔大。

## 下一步（建議順序，每一步先告知使用者）

1. **量測（第 0 階段）**：`src/f8-ahb-gatea-r7-p1-arm/tests/pga/daily_sampler.py`（**未提交**，WIP）。
   改版要點：手機端 CPU 改用一條常駐 `adb shell` 迴圈（不要每秒 spawn adb）；每 5 s 記手機端前幾名 CPU（含 com.termux.x11、
   surfaceflinger）；手機端 kill 事件（`logcat -b events` 的 killinfo / am_proc_died / am_kill）即時寫進硬碟證據目錄（不是 /tmp）；
   MemAvailable < 1500 MB 停。流程：基準 60 s → 使用者同意後同時開 Cursor（`cursor-f8`）與 Hermes（`hermes-desktop-f8`）→ 240 s。
   要回答：卡頓時追蹤器是否在 100%？X :1 往返延遲尖峰是否與追蹤器滿載同步？
2. **若追蹤器是瓶頸**：先做可逆、設定層級的實驗（逐一、每次告知）：確認 proot 的 seccomp 加速有開（未設 PROOT_NO_SECCOMP）；
   評估拿掉 `--sysvipc`／`--link2symlink` 的影響（會影響哪些程式要先查）；評估把重的 app 改用 Termux 原生套件（不經 PRoot）。
   這些都不動 Stable X、不動 GPU 專案。
3. GPU 專案（Gate A）狀態不變：PGA-GAP-2（同步等待）未修；PGA-GAP-3 記憶體洩漏已修（83d45a9 已裝）、mapping 殘差未解；
   B 方案（非同步 GPU 完成）屬「大改架構」停止條件，要使用者再次確認才可動。

## 環境

- ADB lane 5038：`10.191.48.13:40037`（手機 19:10 重開過；mdns 用 python zeroconf 瀏覽 `_adb-tls-connect._tcp.local.`）
- 手機重開後 `/tmp/p_r10_ledger` 等 fixture 可能不見：重建指令見記憶 `device-run-hazards-20260923`
- 所有主機分析經 `tests/common/safe-run.sh`；所有裝置 runner 內建 `tests/common/mem-guard.sh`
- 回覆一律繁體中文；使用者要求簡單白話的進度說明
