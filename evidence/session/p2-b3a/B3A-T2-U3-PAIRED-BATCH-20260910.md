# B3a Tier-2 U3 — 64x64 短窗配對 batch（2026-09-10）

- ADB：`192.168.1.101:45279`；本輪開始前確認 `25102PCBEG / myron`，Experimental
  Activity 在 displayId=0、RESUMED、`reportedDrawn=true`。
- Stable `com.termux.x11` / `:1` 未操作。
- 每個 server session 均以 holder 維持 X client 連線；oracle 1514/1514 PASS 後才跑 cell，
  holder 釋放後驗 exact-count。每個 server 都精確停止，最終 `NO_X3_RESIDUE`。
- `surfaceAvailable` 沒有輸出成可直接讀取的 telemetry 欄位，因此此輪只能記作
  `not_directly_observed`；X 可連、oracle/cell 完成與 R3 fallback=0 是行為證據，
  不得把它寫成內部 flag 已直接觀測。

## U3 batch=1，64x64，warm / immediate GetImage

順序：CPU-A → R3-A → R3-B → CPU-B。四輪皆為 warmup 100 + measured 500，
reuse=1、batch=1、cold=0；每輪 telemetry `2119/2119`（oracle 1519 + cell 600）。
CPU cell fallback=1；R3 cell fallback=0（600/600），各 oracle PASS。

| session | wall median (ms) | cell fallback |
|---|---:|---:|
| CPU-A | 2.211 | 1 |
| R3-A | 3.060 | 0 |
| R3-B | 3.140 | 0 |
| CPU-B | 2.733 | 1 |

短窗配對：

| pair | R3/CPU | 判讀 |
|---|---:|---|
| CPU-A → R3-A | 1.384x | R3 慢 |
| R3-B → CPU-B | 0.870x | R3 快 |
| aggregate（兩 CPU vs 兩 R3） | 1.229x | 僅描述，不裁勝負 |

兩個配對方向相反，依 U3 凍結規則判為 `noise-sensitive / INCONCLUSIVE`；不能拿
aggregate 1.229x 當架構勝負。R3 cell 的 phase median：prepare 0.508ms、
clone 0.286ms（16384 bytes）、DoneComposite 0.706ms、repair 0.003ms。
queue / draw-submit / GPU-exec / fence-wait 均為 `null / not_observable`，沒有以 0 取代。

原始證據：`t2-u3-paired-batch1/`（四輪 JSON/CSV、oracle/cell stdout）。

## U3 batch=4，64x64 — 測量完整性 STOP

第一輪 R3-A oracle PASS，但 batch=4 cell 在第一個 measured op 精確檢查失敗：

```text
CELL u3-batch4 MISMATCH got=00f00f00 expected=00807f00
```

telemetry 仍完整保存：`1923/1923`（oracle 1519 + warmup 100 × batch4 +
首個 measured op × batch4）。R3 fallback=0。這不是 GPU route 或畫面正確性的判決。

根因已由測量 driver 原始碼和 CPU reference 重算確認：
`patches/p_b3a_cost.c:166-168` 只算單次 Over 的 expected `00807f00`，但
`:212-221` 每 op 實際發出 `batch` 次 Composite，且 `:231-242` 在第一個 measured op
仍把結果與單次 expected 比較。四次連續 Over 的 CPU reference 依序為
`00807f00 → 00c03f00 → 00e01f00 → 00f00f00`，完全吻合本次 got。

因此 batch>1 的 correctness coupling（正確性耦合）目前無效；需要極窄 driver-only
修復，令 expected 隨 batch 重複套用，然後重新編譯 driver、先以 CPU/R3 重跑 batch=4
首格證明 coupling 恢復，才可繼續 batch 量測。依 STOP 規則，本輪未改 source，
GPU-only / cold 尚未開始。

失敗原始證據：`t2-u3-paired-batch4-fail/`（JSON/CSV、oracle/cell stdout）；
hash 記錄在本輪終端輸出。最終 teardown：`NO_X3_RESIDUE`。

## batch driver 窄修復與重新資格

僅修改 `patches/p_b3a_cost.c`：既有 `ref_over_x8` 對 initial destination 重複
套用 `batch` 次。未改 R3 / Xserver / telemetry / fence / AHB / predicate。`cc -O2
-Wall -Werror` 重編 `/tmp/p_b3a_cost` PASS。

CPU 與 R3 各跑一 session：oracle + batch=1 + batch=4；兩邊皆 4519/4519
（1519 + 600 + 2400）。batch=1 `CELLSPEC expected=00807f00`，與修前相同；
batch=4 `CELLSPEC expected=00f00f00`，兩邊 cell exact PASS。CPU fallback=1，
R3 batch=1/batch=4 均 fallback=0（600/600、2400/2400）。因此
`U3 batch=4 failure: MEASUREMENT DRIVER BUG — CLOSED`；R3 runtime regression
`NO EVIDENCE`。原始證據：`t2-u3-batch-driver-requal/`。

## U3 GPU-only 64（mode=0、warm、batch=1）

四個短窗（R3-A → CPU-A → CPU-B → R3-B），每輪 oracle PASS、2119/2119，
R3 fallback=0（各 600/600）。mode=0 排除 immediate GetImage，但 driver 每 op
仍以 X round-trip 做 connection liveness，故僅能稱為「no-readback wall path」，
不能當作 direct GPU-exec measurement。GPU-exec / queue 均 null/not_observable。

| pair | CPU ms | R3 ms | R3/CPU |
|---|---:|---:|---:|
| R3-A ↔ CPU-A | 3.921 | 4.477 | 1.142x |
| CPU-B ↔ R3-B | 3.772 | 4.546 | 1.205x |
| aggregate | — | — | 1.168x |

兩個方向一致：不含 GetImage 的完整 request/liveness path 仍較慢。這排除「immediate
readback 是全部差距」的說法，但不證明 shader/GPU-exec 慢；H3 維持 OPEN。
原始證據：`t2-u3-paired-gpuonly/`。

## U3 cold 64（mode=1、batch=1）

四個短窗（CPU-A → R3-A → R3-B → CPU-B），每輪 oracle PASS、2119/2119；
R3 fallback=0（各 600/600）。

| pair | CPU ms | R3 ms | R3/CPU |
|---|---:|---:|---:|
| CPU-A ↔ R3-A | 4.031 | 15.075 | 3.739x |
| R3-B ↔ CPU-B | 3.777 | 15.877 | 4.203x |

兩個方向均重現 cold R3 約 3.7～4.2x 回歸。R3 phase median：prepare 5.138ms、
promotion 3.354ms（AHB allocate 2.141ms、lock 0.209ms）、clone 0.407ms、
DoneComposite 6.552ms、repair 0.006ms；GPU-exec null/not_observable。這是目前
最強的 lifecycle cost signal，支持 H1 的 staging/clone/sync/lifecycle 候選，
但尚不裁 Gate A/D/H。原始證據：`t2-u3-paired-cold/`。

本輪所有 session 最終 `NO_X3_RESIDUE`；Stable 未碰。
