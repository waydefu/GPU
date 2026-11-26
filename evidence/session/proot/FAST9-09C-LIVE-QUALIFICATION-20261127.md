# F8 fast9+09c 正式部署與實機驗收 — 2026-11-27

## 版本與正式來源

[PR #42](https://github.com/waydefu/GPU/pull/42) 已合併至 `waydefu/GPU/main`，merge commit `d5ddc730156d5f82a81e8a56f9819a2641d789a5`。從合併提交的 `core-src/f8-proot-fast/` 建置，來源 tree 與 `23f9bdc` 一致。PR 與合併後 `main` 的治理及凍結證據檢查都通過。 [PR CI](https://github.com/waydefu/GPU/actions/runs/45860492551) · [main CI](https://github.com/waydefu/GPU/actions/runs/45861156333)

正式 `out8/bin/proot-fast8` 版本為 `5.1.107.92-fast9`，補丁 `01..09 + 09b + 09c`，SHA256 `4a6bc67723d9517771ea602e61caa98a4ac7cb7cf75f932d85fa1a5038ae7660`。正式路徑 dry-run 與實際安裝的二進位一致，部署清單 3/3 通過。上一版 fast9+09b 備份在 `/data/data/com.termux/files/home/build/proot-fast/backups/out8-previous-20261127-004529.KNBzD8mu`，雜湊 5/5。既有 `LATEST_FAST8_BACKUP` 仍指向 fast8，雜湊 4/4。

## 隔離驗證與回退

- 原生 ARM64 建置與零 fuzz 套用通過。實機 socket FD 重用後回傳 `AF_UNIX`，且 datagram 到達另一端。fast9 regress 4/4、Terra FD 7/7 通過。
- 手機隔離目錄實際注入 loader 改名失敗，部署回傳 77 並輸出 `RECOVERY_PASS`。舊 binary、兩個 loader 和 manifest 正確回復。
- 正常隔離部署保留 fast8 回退指標，手動回退演練逐檔比對與套件探針通過。
- 部署測試 6/6 通過。Claude headless 模式的啟動返回碼 127 會被拒絕。隔離與正式 Xvfb smoke 皆通過，正式部署後套件探針讀到 1514 件。

## Stable :1 桌面驗收

XFCE tracer 由 PID 30164 更換為 24811。XFCE session、視窗管理器和面板由新 tracer 執行，實測 `/proc/24811/exe` 雜湊與正式二進位一致。`org.xfce.SessionManager` 已註冊。原 Stable Termux:X11 伺服器 PID 30202、其啟動時間及 X1 socket inode 1784454 均吻合重啟前。X11 查詢與 `xrandr` 通過。桌面工作階段切換時，Codex 也重新連線到新版 tracer。

## 30 分鐘壓測

- 經 `f8-shard` 綁定正式版本，在單一獨立 workload tracer 執行 Chromium、Electron Node 模式、Python、Git 和 Vulkan 負載。整段 1805.76 秒，514/514 批通過，Vulkan 7/7。
- 最大活孤兒程序數為 0。shard daemon 全程單一實例、7 個 FD。Ubuntu core 4/4、正式部署檔案 3/3 雜湊通過。
- 批次牆鐘中位數 2489.54 ms，p95 2574.09 ms。Chromium rAF p95 中位數 16.7 ms。

## 效能對照

同機、相同 workload，以 09b → 09c → 09c → 09b 交錯執行，另有每區塊一次暖身，每版取 10 批。

| 指標 | 09b | 09c | 變化 |
| --- | ---: | ---: | ---: |
| 批次時間中位數 | 2490.57 ms | 2495.91 ms | +0.21% |
| tracer CPU 中位數 | 860 ms | 860 ms | +0.00% |
| 尖峰 PSS 中位數 | 291.0 MB | 282.6 MB | -2.89% |
| Chromium 啟動中位數 | 173.59 ms | 179.78 ms | +3.57% |
| rAF p95 中位數 | 16.7 ms | 16.7 ms | +0.00% |
| 點擊 p95 中位數 | 79.22 ms | 68.66 ms | -13.33% |

樣本顯示整體時間及 tracer CPU 接近。首區塊溫度高於其餘區塊，啟動及點擊差異需更多樣本確認。

## 待追蹤

桌面工作階段切換後，原 `termux-bg-run` 路徑未收到 TermuxService 執行回報。以相同啟動方式對照 09b 與 09c 皆未出現執行標記，目前原因未確認。正式壓測與效能對照已由 `f8-shard` 完成。

原始證據目錄為 `/data/data/com.termux/files/home/build/proot-fast9-09c-20261127.yXdNteSr`，含 `rollback-lab.log`、`deploy-live.log`、`verify-stable-after-soak.log`、`live-fast9-soak30m-summary.json`、`perf-abba-summary.json` 與 `launcher-ab.log`。
