# 這個目錄裡有什麼，沒有什麼

失敗的 preflight-01（偏差 1 的起因：x-r8-env，X 從未就緒，無任何量測資料）。`sha256sums.txt` 是完整的本地清單。

```
raw-logcat.txt        不發佈（與其他 runtime 目錄慣例一致）。2026-09-26 更正：此檔曾隨 dc2a32e 推到
                      docs/xfce-notel-01-freeze 分支（公開 repo，未進 main）；內容含附近藍牙裝置的
                      originalAddress（隨機位址）。判決依據是 x-r8-env 的那一行，已記在凍結文件 §10：
                      `02:01:58.168 26974 27183 F gatea-a1: GATEA_FATAL_HALT what=x-r8-env reason=5`
```
