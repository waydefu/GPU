# 這個目錄裡有什麼，沒有什麼

`sha256sums.txt` 是**完整**的本地清單（763 個檔案，2026-09-25 系列結束後、任何後處理之前計算）。
以下刻意**不**發佈（與 `gate-a-a1/p2-xfce-runtime/PUBLISHED-SUBSET.md` 的慣例一致）：

```
raw-logcat.txt        windowed device log；本輪每格 1.2–1.3 GB（c-01 取樣 97% 的行是 gatea-telemetry），7 格共約 8.4 GB。
                      2026-09-25 經使用者同意，本地改為 raw-logcat.txt.gz（gzip -6，無損；解壓後 sha256 與
                      sha256sums.txt 相同，逐格記在 POST-CAPTURE-CHANGES.md），7 格合計約 250 MB，仍不發佈。
                      preflight-01（原 1.3 MB）同樣處理、同樣不發佈。
x3-launcher.log       > 100 KB 者（本輪只有 xfce-c0-g0-01，813632 bytes）。
```

本輪沒有 `collect-input.txt`、`x3.maps`、APK／.so 副本。
判決依據（part-b-judge.json、series.json、series.log、各格 steps.jsonl、k-K*.json、touch.json、
client-tracer.json、xfce-session-tracer.json、stable-before/after.json、screen-*.json、*.rca/、*.v6/ 等）全部在此。

只驗已發佈的部分（在本目錄內執行）：

```bash
grep -vE '/raw-logcat\.txt$' sha256sums.txt \
  | while read h f; do [ -e "$f" ] && echo "$h  $f"; done | sha256sum -c
```

`x3-launcher.log` 超過 100 KB 的不在 repo，上式以 `[ -e ]` 跳過；它仍列在 sha256sums.txt 裡。
