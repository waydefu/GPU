# HANDOFF — 2026-09-24：非同步 EXA 原型已過正確性與延遲判準；PGA-GAP-4 修好

先讀：本檔 → `evidence/session/gate-a-a1/planning-v2/pga/PGA-GAP-2-DECOMPOSITION-01.md`
→ `PGA-GAP-2-ASYNC-EXA-DESIGN.md`（含修訂 1 與各 artifact 結果）→ `V2-PGA-GAP-INVENTORY.md` PGA-GAP-4。

## 使用者目標（2026-09-23 原話摘要）
POCO F8 Ultra 真正的 Linux 全域 GPU 加速（不只過 Gate A）；拆延遲、研究非同步 EXA／批次／DRI3-AHB／Vulkan 合成；
最小原型 → 比較 CPU/GPU 延遲、XFCE 流暢度、資源 → 逐步整合。先以**內建螢幕**為目標（3440×1440 是理想，螢幕未購買）。
全程不碰 Stable :1、只用 :3、不宣稱未實測的效能。

## 現況
```
裝置上的實驗版   1.03.01-11b3b79-23.09.26  CI 35888747835  APK 59e89a9a…7764  Build ID 32555c25…b275
                 fork waydefu/termux-x11 branch feat/exa-async-proto-20260923（worktree src/f8-ahb-exa-async）
開關             X 環境變數 TERMUX_X11_EXA_ASYNC=1（未設 = 同步行為）
正確性           p_async_oracle 2 seed × G/GA/C 全 0 錯；GA X byte 雜湊 = G；p_depth_probe 0 錯；Gate A oracle V3 在 GA 下 ORACLE_PASS
延遲             ASYNC_LATENCY_IMPROVED：solid/copy 64 的 client p50 GA 為 G 的 19–24%（兩組配對）
PGA-GAP-4        depth 32（BGRA AHB）當 GPU 目的地時結果回不到 AHB（83d45a9 既有缺陷）；d1c86dd 改走 CPU，已驗證
手機黑盒子       /data/local/tmp/f8-blackbox（bb.sh，pid 見 pid 檔），凍結/重開後讀 bb.log 與 events.log
Serena           GPU加速 專案 ignore_all_files_in_gitignore=false（每次開 session 不再全樹掃描）
```

## 更新 2026-09-24 02:15 — XFCE 結果與 PGA-GAP-5

```
裝置上的實驗版   1.03.01-709dfac-23.09.26  CI 35896229456  APK ba9e9d40…c7d8（11b3b79 + 門檻實驗開關）
XFCE C0 三方      runtime-11b3b79/xfce-c0-*：XFCE_ASYNC_IMPROVED 否、CPU_PARITY 否（G/GA 50–450 ms 尖峰，C 無）
PGA-GAP-5        小 pixmap 逐一升級 AHB + 向 renderer 登記（每次 XFCE ~2006 次）與尖峰強相關
門檻實驗          TERMUX_X11_GPU_MIN_PIXELS=4097：尖峰消失（p99 9–10 ms、>100 ms 0 次），但凍結判準差 0.145 ms
                 → GAP5_CAUSAL_NOT_SUPPORTED（凍結）
待決定           修正方向：(1) 小 pixmap 留 CPU（路由；使用者先前否決過窄路由）(2) AHB 池／staging atlas 讓升級變便宜 (3) 兩者
工具             p2-pga-artifact/bind-install.sh（下載＋綁定＋衍生安裝腳本＋安裝，每欄核對）；
                 p2-xfce-runtime/xfce-async-series.sh（PRODUCT / ORDER / 組別 G GA GAT C）
```

## 更新 2026-09-24 09:15 — 依尺寸分流（使用者決定）

```
裝置上的實驗版   1.03.01-f592241-24.09.26  CI 35937188670  APK f9e35b69…075c
預設             TERMUX_X11_GPU_MIN_PIXELS=4097（≤64×64 不升級 AHB；0 = 舊行為）；async 仍選用
XFCE C0          ROUTING_REMOVES_SPIKES：G0 p99 63–72 ms → GT 9–10 ms（C 10–11），>100 ms 0 次
描述             GT p50 仍約 C 的 2–3 倍；X3 CPU 0.5 核 > C 0.34 核 → 2D 桌面尚無 GPU 收益
正確性           p_async_oracle 2 seed 全 0 錯；probe 0；oracle V3 GT correctness 全過（attribution 預期 FAIL），G0 PASS
判準文件         planning-v2/pga/PGA-GAP-5-ROUTING-FREEZE.md
```

## 還沒做（建議順序）
1. XFCE 流暢度：GA 對 G 對 C（XFCE-FREEZE-V3 工具在 tests/xfce3；先確認判準仍適用，再凍結新判準）。
2. 「看得到結果」的延遲：GPU 結果仍要等 renderer 下一幀（renderer.cpp:2493-2499 畫面迴圈耦合）；需要新量法（例如 Choreographer/SF layer 時間）。
3. burst16 仍約 CPU 3 倍：佇列容量 LORIE_GPU_COPY_QUEUE_CAPACITY=8 是嫌疑（未證明）。
4. GPU 閒置醒來 7.6–10.9 ms（同步版量到）：非同步後不擋 X，但仍影響上屏時間。
5. Composite（Gate A）仍同步，且入口會 flushAll；XFCE 以 composite 為主 → 非同步效益可能有限，量了再說。
6. PGA-GAP-3 mapping 殘差（~0.01/筆）未解。

## 陷阱（這兩天真的踩過）
- 執行緒身分不要猜：X dix = X3 內被 client 叫醒最多者（X3 leader 是 Android Looper）；renderer = Activity 程序的 `Thread-7`。用 opstream_decompose.py --x3-pid/--act-pid。
- runner 的 exit trap 要 `cleanup || true; b_cleanup || true; mg_stop`（舊 runner 失敗時會留下 X3）。
- adb 不能放在 safe-run（RLIMIT_AS）底下：會一路卡到 timeout。
- 產物流程：artifact-<sha>/install-<sha>.sh 由上一版衍生；sed 全域替換會弄壞 EXPECT_HEAD，要逐欄核對。
- ADB endpoint 會換網段（192.168.1.100 ↔ 10.191.48.13），一律用 `f8-adb-port` 重探（09-26 更正：mDNS 查不到）。
