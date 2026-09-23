# 兩份 planning manifest 曾經對不上，原因與處置

DATE 2026-09-23  發現者 `tests/p2/p2_ledger.py` 的 EVIDENCE 稽核

## 事實

```
p008-execution-interface/
  sha256sums.txt   寫於 2026-09-21 14:00
  interface.md     改於 2026-09-21 14:19      <- 封存後 19 分鐘又被編輯
p009-judge-fixture-contract-matrix/
  sha256sums.txt   寫於 2026-09-21 14:36
  check-judge-fixture-contract.py  改於 14:38
  matrix.tsv                        改於 14:38  <- 封存後 2 分鐘又被編輯
```

三個檔案的實際 sha256 與 manifest 記載不符。

## 這不是 append-only 違反

`p008` 與 `p009` 是 **planning packet**（execution interface、judge-fixture contract
matrix），不是 device attempt。它們不受「consumed attempt 永久凍結」約束——那條規則
保護的是判決所依據的 runtime 證據。

**沒有任何 runtime evidence manifest 有問題。** 40 份 manifest 全部重算相符，包含
R7 / R8 / R9 / R10 的全部 attempt。

## 處置：修好，不是繞過

第一版 ledger 把這兩份從 required 分流成「planning only」另外報告，讓 EVIDENCE 項
變綠。那太接近「看到 FAIL 就放寬 predicate」，所以改成把 manifest 重新產生：

```
舊 manifest 保留為 sha256sums.txt.stale-20260921
新 manifest 涵蓋目錄內全部檔案，已驗證通過
```

保留舊檔是因為**工具出錯或紀錄失準要留痕**：下一手要能看到「2026-09-21 當天這兩份
文件在封存後又被改過，而 manifest 沒同步」，而不是只看到一份乾淨的新 manifest。

`p2_ledger.py` 仍然把 runtime 與 planning 的 manifest 失敗分開報告，因為兩者的嚴重性
不同；但現在兩類都是空的，EVIDENCE 項不靠分類豁免成立。
