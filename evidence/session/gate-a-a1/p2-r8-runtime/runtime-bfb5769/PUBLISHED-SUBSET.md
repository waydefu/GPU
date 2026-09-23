# 這個目錄裡有什麼，沒有什麼

每個 run / probe / attempt 目錄的 `sha256sums.txt` 是**完整**的本地清單。以下刻意**不**發佈
（與 p2-r8/r9/r10-runtime 的慣例一致，另加兩類大型或二進位檔）：

```
raw-logcat.txt        windowed device log（XFCE 一輪可達 194 MB）
collect-input.txt     raw-logcat + ring + summary 的逐位元串接
x3.maps               X 的位址空間
x3-launcher.log       > 100 KB 者（xfce-c1-03 為 132 MB 的診斷 stamp）；
                      xfce-c1-02 的 28 行崩潰片段 < 100 KB，照常發佈——它就是 R-31 的證據
*.apk / *.so          CI 與裝置讀回的 APK、libXlorie.so（sha 記在 artifact-binding.json 與
                      sha256sums.txt；CI run 35811368916 仍可下載）
x_rtt.bin             RCA 探針的編譯產物（原始碼在 fork tests/pga/x_rtt.c）
```

判決依據（steps.jsonl、k-K*.json、xfce-run.json、xfce-verdict.json、gatea-summary.txt、
sf-polls.txt、stable-before/after.json、run-binding.json、*.rca/ 等）全部在此。

只驗已發佈的部分（在含 sha256sums.txt 的目錄內執行）：

```bash
grep -vE '/(raw-logcat\.txt|collect-input\.txt|x3\.maps|x_rtt\.bin|[^/]*\.apk|[^/]*\.so)$' sha256sums.txt \
  | while read h f; do [ -e "$f" ] && echo "$h  $f"; done | sha256sum -c
```

`x3-launcher.log` 超過 100 KB 的不在 repo，上式以 `[ -e ]` 跳過；它們仍列在 sha256sums.txt 裡。
