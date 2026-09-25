# 這個目錄裡有什麼，沒有什麼

`sha256sums.txt` 是**完整**的本地清單（962 個檔案，系列結束後、任何後處理之前計算）。以下刻意**不**發佈
（與 `runtime-f592241-v6/PUBLISHED-SUBSET.md` 的慣例一致）：

```
raw-logcat.txt        windowed device log；CT 三格各約 1.31 GB（gatea-telemetry，約 5.4 萬行/s），
                      C／GT／preflight 各 3.3–4.7 MB。本地保留、未壓縮（evidence 壓縮需使用者同意）。
```

本輪沒有超過 100 KB 的 `x3-launcher.log`，也沒有 `collect-input.txt`、`x3.maps`、APK／.so 副本。
判決依據（notel-judge.json、series.json、series.log、各格 env-x3.txt、steps.jsonl、k-K*.json、touch.json、
client-tracer.json、xfce-session-tracer.json、stable-before/after.json、screen-*.json、cleanup.txt、terminate.out、*.rca/、*.v6/）全部在此。
注意：telemetry 行數（判定器的開關證據）要從 raw-logcat 重算；發佈的 `notel-judge.json` 記有每格的 `telemetry_lines`。

只驗已發佈的部分（在本目錄內執行）：

```bash
grep -vE '/raw-logcat\.txt$' sha256sums.txt | sha256sum -c --quiet
```
