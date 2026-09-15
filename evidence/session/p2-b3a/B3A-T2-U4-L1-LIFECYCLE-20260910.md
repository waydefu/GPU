# B3a U4-L1 lifecycle — R3 create/use/release/teardown/recreate

日期：2026-09-10（Asia/Taipei）  
範圍：Experimental `com.waydefu.x11gpu` / `DISPLAY=:3`；無 source mutation、無
Stable operation。

## Artifact and runner binding

- APK version：`1.03.01-1954f82-09.09.26`（versionCode 15）
- Installed APK SHA256：`5cc87f4121bfe52e7504348e36c36421b28355549b3b26fe031f175a234c1dce`
- Device/serial at preflight：`25102PCBEG / myron`，`10.56.180.219:39035`，`adb get-state=device`
- Source-tree HEAD：`98224356e40913dcf2188d18748eba9401639850`（既有 local telemetry/E1b worktree；本輪未改 native source）
- Oracle source SHA256：`bfaa869d683f4e9175d1e388e0843e81ef18a405cc7e1625fa7a0c2c40d878c4`
- Rebuilt oracle SHA256：`19154bf222b3c1e8c033bad2101bcd7e2f56fb23e486c4d8b6be651ca7eec726`
- Rebuilt driver source SHA256：`need2d66b34a5a8d6207346b8f62ff230f0a4551c0df9fd1003597fb5c2be7477`
- Rebuilt holder source SHA256：`e7bf002edba7275ae2a801c2149e28c4c5b669ad4db941291d910a5f59dcc722`
- Final session runner SHA256：`c0c8751fd7ef2531d3b36315cb7fc62cd1fb7216532e36616912624c1b2e0c1c`

`p_b2_oracle`、`p_b3a_cost`、`p_b3a_hold` 均由 frozen `patches/` 重建為
`-O2 -Wall -Werror`，rc=0。runner 每 session 先顯式將 Activity 放在
`displayId=0` 並驗證 `RESUMED`／`reportedDrawn=true`，再啟動 X3；每 session
使用 persistent holder 避免 oracle disconnect 觸發早期 telemetry dump。

## Test protocol

三個獨立 R3 server sessions，固定 cell：

```text
64×64; mode=1 immediate GetImage; reuse=1; batch=1; cold=1;
warmup=0; count=1
```

每輪完整走：

```text
Activity displayId=0
→ X3 launch
→ holder
→ 1514-case oracle
→ one cold create/use/release cell
→ holder release
→ exact launcher teardown
→ NO_X3_RESIDUE
→ next server recreate
```

Expected telemetry record count：`1519 oracle + 1 cell = 1520`。

## Results

| session | actual X PID | oracle | cell first-pixel | records / dropped | R3 fallback | telemetry X FD | final residue |
|---|---:|---|---|---:|---:|---|---|
| r3-1c | 30844 | PASS (`1514/1514`, fail=0, maxΔ=0) | PASS (`00807f00`) | 1520 / 0 | 0 | 79 → 89 | `NO_X3_RESIDUE` |
| r3-2 | 2882 | PASS (`1514/1514`, fail=0, maxΔ=0) | PASS (`00807f00`) | 1520 / 0 | 0 | 79 → 89 | `NO_X3_RESIDUE` |
| r3-3 | 11183 | PASS (`1514/1514`, fail=0, maxΔ=0) | PASS (`00807f00`) | 1520 / 0 | 0 | 79 → 89 | `NO_X3_RESIDUE` |

- 兩個 package/activity pre-launch conditions 均由每輪的 `display.out` 保存；三輪各有
  unique X PID，證明重新建立的不是上一輪殘留 process。
- telemetry record candidate 全為 `r3`；cell fallback 全為 `0`。
- `Gcomp FDCLONE=1516` 且 `Gcomp Done=1516`，三輪皆相等。這是 clone/complete event
  平衡的操作性證據；它**不是** explicit buffer release counter。
- telemetry queue state、GPU exec 均為 `null / NOT OBSERVABLE`；renderer RSS/FD metadata
  都是 0，依現行 schema 表示 renderer attribution 未填，不能解讀成 renderer 無成本或無 FD。

## Resource interpretation

- adb shell 讀取 live `/proc/<X_PID>/status` 可得 actual-PID RSS；三輪 T0/T1/T2/T2-holder-release
  都已保存，T3 是 X3 process 不存在。
- adb shell 無法取得 live `/proc/<X_PID>/fd` directory count；runner 因此輸出 `fd=NA`，
  而不是 false 0。早期 runner outputs 的 `fd=0` 已保存在 `runner-bringup/`，不納入本結論。
- authoritative server-side telemetry metadata 每輪都是 `x_fd_start=79, x_fd_end=89`。
  下一個獨立 server 又從 79 起算，加上每輪 process teardown 無 residue，表示**未觀察到跨 recreate
  的 FD retention**。但沒有 per-buffer release counter，不能宣稱已直接量到每個 AHardwareBuffer/FD 的 release。
- telemetry X RSS start/end 分別為：214126592→231047168、215490560→231219200、
  212512768→227282944 bytes。這些是 lifecycle boundary snapshots，不作 single-cell performance 判決。

## Runner bring-up exclusions

三個 L1 runner-integration attempts 在 X3 launch 前失敗或在 post-teardown local validation
誤判，均已保存於 `runner-bringup/`：

1. PRoot 的 Ubuntu `/usr/bin/env` 在 fakeroot 後誤載入 Termux library（invalid ELF）。
2. fakeroot IPC reset（`libfakeroot: read: Connection reset by peer`）。
3. telemetry `exact_fail/max_delta/x_nz=null` 是 schema 定義的 `NOT OBSERVABLE`，不是 nonzero failure。

修正均限於 `/tmp/p2b3a_session.sh` measurement harness：使用 absolute Termux `env`、移除不必要
fakeroot、把 null 及不可讀 `/proc/fd` fail-closed 標示。沒有啟動 X3 的兩輪不納入 runtime；post-teardown
validator failure 的一輪 raw session 保留但不納入三輪 aggregate。

## Verdict

```text
U4-L1 lifecycle: PASS WITH OBSERVABILITY LIMITATIONS
create/use/release/recreate: 3 independent X server lifecycles PASS
correctness: oracle exact PASS + driver first-pixel exact PASS
telemetry: 3 × 1520/1520, dropped=0
R3 route: fallback=0
teardown: 3 × NO_X3_RESIDUE
cross-recreate FD retention: NOT OBSERVED
explicit buffer registration/release counters: NOT OBSERVABLE
renderer queue/GPU exec: NOT OBSERVABLE
Stable: UNTOUCHED
```

這個 verdict 只證明 bounded lifecycle 無 blocking defect；它不代表 R3 的 cold/warm end-to-end
performance 已經 qualified。下一個授權單位是 cold-N5。

## Evidence

- Raw directory：`t2-u4-l1-lifecycle/`（55 files, including runner bring-up red evidence）
- Machine-readable aggregate：`t2-u4-l1-lifecycle/U4-L1-SUMMARY.json`
