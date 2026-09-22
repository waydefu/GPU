# 這個目錄裡有什麼，沒有什麼

`sha256sums.txt` 是**完整**的本地證據清單（所有 series 的全部檔案，加上 runner）。
以下三類 capture 刻意**不**發佈，與本 repo 既有慣例一致（`p2-r8-runtime`、
`p2-r9-runtime` 底下同樣沒有 `raw-logcat.txt`）：

```
raw-logcat.txt      每個 series 數 MB 的 windowed device log
collect-input.txt   raw-logcat + ring + summary 的逐位元串接，無新資訊
x3.maps             X process 的位址空間對照表
```

runner 從一開始就只寫 `env-cell.txt`（`CELL_ID`、`DISPLAY`、全部 `TERMUX_X11_*`），
不曾寫出完整環境，所以沒有 R9 那種 `env.txt` 縮減問題。

判決所依據的東西**全部在這裡**：`ledger.json`、`judge.json`、每個取樣點的
`sample-*.json`、`gatea-summary.txt`、`gatea-ring.txt`、`client.jsonl`、
`terminate.jsonl`、`identity-before.txt`、`ending.txt`、`h-construction.txt`、
`logcat-offset-*.txt`、`stable-before.json` / `stable-after.json`、`run-binding.json`、
`installed-apk.sha256.txt`、`fixture.sha256.txt`。

驗證已發佈的這一份：

```bash
grep -vE '/(raw-logcat\.txt|collect-input\.txt|x3\.maps)$' \
  runtime-dc94485/sha256sums.txt | sha256sum -c
```

從 `evidence/session/gate-a-a1/p2-r10-runtime/` 執行，每一行都必須通過。
被略過的檔案仍然列在 `sha256sums.txt` 裡，所以它們所屬的那份本地集合一樣被釘住。

## 關於空的 `gatea-ring.txt` / `gatea-summary.txt`

`noise-01` 的每一輪都是空的，這是**正確的**，不是漏抓。
`lorieGateADumpSummary` 只在 fatal、clean close 或 terminate 時才寫這兩個檔，
而 noise 跑的是 idle workload、且它不被判決。判決用的 series（A / B / C / E）
每一輪的 close 都有完整的 summary 與 ring。

## `r10-e-01`

凍結為 INVALID，保留全部檔案。它的 `SERIES-FROZEN-INVALID.md` 說明中斷原因，
以及它的 E1 回合其實已經正確捕捉到 F 結尾這件事——記錄，但不當作 verdict。
