# Native Hybrid 2.0 Stage 7.4 補驗

2026-11-28 隔離驗收。候選程式提交 `8dde475c162d3a858b944b74406f3eb2983bf0a8` 的六個腳本均與 Termux 副本逐檔比對。原生 daemon 的 TracerPid 為 0。Stable X1 的 socket 身份通過前後比對。

## Git 設定與回退

透過受控 launcher 為 relay、controller 與原生 daemon 設定同一份 `F8_HYBRID2_TRUSTED_GIT_ROOTS`。值是 JSON 字串陣列，例 `["/fixture"]`。每一項是各路由映射到同一份受控 checkout 的絕對客體根。清單空白、無效或未登記時會拒絕 Git。設定由管理者提供，適用於讀取期間能排除外部寫入的普通非 bare checkout。linked worktree 仍待核准。設定變更後須重啟隔離 daemon，既有程序仍使用啟動時解析的路徑。

原生與回退路徑共用 Git 策略。Git 可能已執行而回應尚未送達時，relay 以明確錯誤結束。當原生服務在建立連線前不可用，以及本地政策與信任條件成立時，可使用本地路由。PRoot L2S loose object 若指向映射外，維持拒絕。這份信任清單要求管理者能證明輸入穩定，Git 仍自行開啟檔案。

## 連線與回收

PRoot 32/32（29.105 秒），Termux Native 32/32（20.204 秒）。回歸涵蓋兩條路由拒絕未登記 checkout、准入達上限、thread 啟動失敗、idle backlog、半關閉、逾時及斷線回收。直接啟動的 daemon 由 controller 保留子程序 handle 並等候回收。兩條測試紀錄均未再出現先前的 subprocess ResourceWarning。隔離 socket、pidfile、ready 檔清除成功。

## 資源樣本

每個客戶端透過 PRoot relay 發送 24 次四工具交替請求，合計 360 次。八個客戶端均使用同一份原生建立的 Git fixture。daemon、relay 和能讀取的子程序自 /proc 約每 10 ms 取樣。下表是各指標各自的觀測最大值。

| 客戶端 | 呼叫 | PSS KiB | RSS KiB | 執行緒 | FD |
|---|---:|---:|---:|---:|---:|
| 1 | 24 | 41,701 | 49,424 | 5 | 24 |
| 2 | 48 | 57,188 | 71,860 | 7 | 42 |
| 4 | 96 | 84,725 | 114,428 | 12 | 54 |
| 8 | 192 | 120,570 | 168,464 | 17 | 62 |

每組回收後，daemon 回到 1 個執行緒、6 個 FD。此 fixture 的取樣上限是 256 MiB PSS、64 個執行緒、192 個 FD。先前兩次取樣因 PID 初始化／退出期間的 FD 讀取權限不足而停下，重測逐筆統計缺測。表列完成批次在可枚舉的 PID 中沒有讀取受限的樣本，仍可能漏掉採樣間隔內結束的子程序。

每個 selective relay 的 16 MiB 入站 frame 與 24 MiB + 64 KiB stdout 停止門檻合計約 40 MiB。八組容量情境約 320.5 MiB，daemon、其他緩衝、JSON 解析及子程序另計。這些數值用於訂定 7.5 預算。日用工作負載的裝置餘裕、整體硬上限，以及 ≥1,000 ops 的異常與長時間驗收仍待定案。
