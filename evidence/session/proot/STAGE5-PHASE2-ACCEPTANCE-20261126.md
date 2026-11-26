# Stage 5 Phase 2 實測驗收與原生混合／GPU 評估報告（2026-11-26）

> **邊界聲明**：全程於隔離工作目錄（`/data/data/com.termux/files/home/build/proot-stage5-20261126.RgTIR3sp`）與隔離分支 `src/f8-proot-fast-stage5`（`stage5/isolated-fast8-20261126`）執行；**未修改**現役 `out8/` / `shard2/` / `/usr/local/bin/f8-shard`、`src/f8-proot-fast`（`main` `ee603b8`）、Stable `:1`（`com.termux.x11`）或任何凍結 `evidence/` 檔案。

---

## 一、兩支裁判腳本假通過修復（`5b8816d`）

- **修復標的**：[`tests/autoshard_judge.py`](../../../src/f8-proot-fast/tests/autoshard_judge.py) 與 [`tests/shard_judge.py`](../../../src/f8-proot-fast/tests/shard_judge.py)（改動提交於 `src/f8-proot-fast-stage5` `5b8816d`）。
- **修補行為**：
  - `autoshard_judge.py` `main()` 僅在 `verdict == "AUTOSHARD_RULES_PASS"` 回傳 `0`，其餘（`AUTOSHARD_RULES_FAIL`、`AUTOSHARD_INVALID`）一律回傳 `1`。
  - `shard_judge.py` `main()` 對 `capture` 僅在 `valid is True` 回傳 `0`、`series` 僅在 `verdict == "JUDGED"` 回傳 `0`，參數錯誤維持 `64`，失敗／無效（`INCONCLUSIVE`）皆回傳 `1`；既有多數判斷規則與凍結判決詞維持不變。
- **回歸驗證**：於 `tests/test_shard_judge.py` 補入 `CliExitCode`（`capture` / `series` / usage 退出碼）並新增 `tests/test_autoshard_judge.py`（`PASS`→`0`、`FAIL`→`1`、`INVALID`→`1`）；執行 `python3 -m unittest -v test_shard_judge test_autoshard_judge` **29/29 通過**（`2.093s`）。
- **待收斂狀態**：尚在 `stage5/isolated-fast8-20261126`（`5b8816d`），尚未合入 `src/f8-proot-fast` `main`（`ee603b8`）。

---

## 二、`PRoot-fast10` 多行程與記憶體最佳化（`c458d74`）

- **逐組補丁（嚴格基於 `fast9-combined`，以 `patch -p1 --fuzz=0` 套用並提交至 `c458d74`）**：
  - `patches/10-proot-fast10-pid-hash.patch`（LinuxDroid `0001`）：1024-bucket `buckets[]` PID 雜湊表取代線性掃描，`set_tracee_pid()` 維護雜湊與 `terminations_pending` 短路空掃描（建置 `fast10-a-pidhash`，SHA256 `612977e7…`）。
  - `patches/11-proot-fast10-talloc-relatives.patch`（LinuxDroid `0009`）：`nb_children` 跳過無子行程親緣掃描、`talloc_free_children(tracee->ctx)` 重用記憶體收集器，並調整 `Path` 結構欄位排列（建置 `fast10-combined`，SHA256 `4579dc61…`；共用 `loader` `eab6b213…`）。
- **多行程回歸與 5 組交替歸因（`fast10-attribution.json`）**：
  - **21/21 回歸全數 `rc=0`**：`fast9-combined`、`fast10-a-pidhash`、`fast10-combined` 各跑 `fast9_regress`（4 模式）＋ `fast10_mp_bench`（64 子行程、孤兒重託親、200 次 PID 重用，含正常與 `PROOT_NO_SECCOMP=1`）＋ `dpkg-query`，全數 `ALL 7 PASS`。

| 工作負載 | 指標 | `fast9-combined` | `fast10-a-pidhash` | `fast10-combined` |
|---|---|---:|---:|---:|
| **`mp_storm`**（64 子行程 × 1500 mixed syscalls） | 牆鐘中位數 | `9055.69 ms` | `8995.58 ms` (`-0.66%`) | **`8843.53 ms` (`-2.34%`)** |
| | Tracer CPU 中位數 | `8910.0 ms` | `8830.0 ms` | **`8720.0 ms` (`-2.13%`)** |
| | 峰值 RSS (`KB`) | `4708` | `4696` | `4752` |
| **`fork_wave`**（10 波 × 32 並發 `fork/waitpid`） | 牆鐘中位數 | `102.15 ms` | `102.07 ms` (`-0.08%`) | `102.19 ms` (`+0.04%`) |
| | 峰值 RSS (`KB`) | `4268` | `4372` | **`4056` (`-4.97%`)** |

---

## 三、`fast9` / `fast10` 真實 Electron、Playwright Chromium 153 與多代理驗收

於隔離實機 Ubuntu 24.04 rootfs（搭配正確 `/dev/shm` 與 `sysctl_inotify_max_user_watches` bind）執行 **3 組交替配對（+1 warmup）**（`fast9-10-real-workstation-ab.json`）。

- **診斷重點**：
  - `claude-desktop` 在官方二進位已停用 `ELECTRON_RUN_AS_NODE` fuse；改以同一機台上具備 Electron `44.9.1` 且支援 `ELECTRON_RUN_AS_NODE=1` 的 `/opt/antigravity-hub/antigravity` 作為真實 Electron Worker（已事先單獨驗證輸出 `AGY_E 44.9.1`）。
  - Playwright Chromium 153（`chrome-headless-shell-1243`）在缺乏 `/proc/bus/pci/devices` 與系統 D-Bus 時，預設注入 `--enable-unsafe-swiftshader` 會觸發 ANGLE `libpci` `exit(1)` 導致間歇性 GPU 子行程 `exit_code=256` 閃退；改用 `LD_PRELOAD=/root/build/electron-probe/nopci/libnopci.so`＋停用該旗標後 100% 穩定通過。
  - 首版 harness 因 `subprocess.Popen(..., stdout=PIPE, stderr=PIPE)` 未邊讀邊清造成 pipe 死鎖；修復為寫入磁碟暫存檔並加上單次 90s 硬逾時。

| 真實工作站負載（3 配對 + 1 暖機） | 指標 | `fast8` | `fast9-combined` | `fast10-combined` |
|---|---|---:|---:|---:|
| **`playwright_chromium`**<br>（Chromium 153 啟動 + 4 並發分頁 Canvas/DOM） | 牆鐘中位數 | `1564.21 ms` | `1588.53 ms` (`+1.55%`) | `1593.21 ms` (`+1.85%`) |
| | 啟動中位數 | `444.81 ms` | `433.00 ms` | `434.55 ms` |
| | 分頁 `p50` / **`p95`** | `324.13` / `469.10 ms` | `372.54` / **`405.64 ms` (`-13.5%`)** | **`323.62`** / **`405.04 ms` (`-13.7%`)** |
| | **Tracer CPU** | `420.0 ms` | **`320.0 ms` (`-23.8%`)** | **`330.0 ms` (`-21.4%`)** |
| | `vol_ctxt` / `nonvol_ctxt` | `3119` / `594` | `2525` / `822` | `2880` / `845` |
| | 峰值整樹 PSS / RSS | `276.7` / `662.1 MB` | `313.8` / `747.4 MB` | `303.3` / `724.6 MB` |
| | 結束後孤兒行程殘留 | **`0`** | **`0`** | **`0`** |
| **`electron_multi_agent`**<br>（2× Electron 44.9.1 + 2× Python AI Agent + 2× Git CLI 併發） | 牆鐘中位數 | `877.90 ms` | **`666.66 ms` (`-24.06%`)** | `868.13 ms` (`-1.11%`) |
| | **Tracer CPU** | `420.0 ms` | **`320.0 ms` (`-23.8%`)** | **`380.0 ms` (`-9.5%`)** |
| | `vol_ctxt` / `nonvol_ctxt` | `1153` / `265` | `691` / `181` | `1069` / `212` |
| | 峰值整樹 PSS / RSS | `52.8` / `77.0 MB` | `52.8` / `86.0 MB` | **`47.6` / `73.9 MB`** |
| | 結束後孤兒行程殘留 | **`0`** | **`0`** | **`0`** |

- **判定結論**：**`fast9` 群組（`07`–`09`）達成實戰大勝**——真實多代理併發牆鐘縮短 **24.06%**、Tracer CPU 降 **21%–24%**、Playwright 4 分頁 `p95` 降 **13.5%–13.7%**；`fast10`（`10`–`11`）在極高行程數壓測 `mp_storm` 進一步省 2.34% 與多代理降低峰值整樹 PSS（`-9.8%`），可安全疊加且零回歸。

---

## 四、Native Hybrid（Termux Bionic 原生混合分流）實測（`native-hybrid-ab.json`）

在保留 Ubuntu 24.04 桌面不變動下，以 5 組交替 A/B（+1 warmup）對比 Termux 原生 bionic CLI vs `fast8` vs `fast10-combined`：

| 測試項目 | `fast8` 中位數 | `fast10-combined` 中位數 | `termux-native` 中位數 | 原生相對 `fast8` 加速 | 原生相對 `fast10` 加速 |
|---|---:|---:|---:|---:|---:|
| **`git_ops`**（20× `status` + `log`） | `538.93 ms` | `491.54 ms` (`-8.79%`) | **`342.68 ms` (`-36.41%`)** | **`1.57×`** | **`1.43×`** |
| **`python_scan`**（10× 走訪讀檔建索引） | `498.58 ms` | `392.48 ms` (`-21.28%`) | **`61.33 ms` (`-87.70%`)** | **`8.13×`** | **`6.40×`** |
| **`zstd_jq_log`**（5× 解壓 10k JSONL + `jq`） | `128.79 ms` | `118.19 ms` (`-8.23%`) | `159.76 ms` (`+24.05%`) | `0.81×` | `0.74×` |

- **跨邊界實測探針**：
  - **Unix Domain Socket IPC**（Termux 原生 server ↔ PRoot `fast10-combined` Ubuntu client，500 次 JSON-RPC 往返）：**500/500 成功**，總耗時 `26.51 ms`，**`p50 = 41.02 µs`**、**`p95 = 80.00 µs`**。證明 UI/瀏覽器留在 Ubuntu、Agent 後端／CLI 移至 Termux 原生透過 Unix socket 通訊完全低延遲可行。
  - **`.l2s.*` 與 UID 邊界風險實證**：在 PRoot `-0 -l` 下執行 `ln a b` 會在實體磁碟建立 `.l2s.a0001`（symlink → `.l2s.a0001.0002`），Termux 原生側見到的 `a`、`b` 皆為指回 `.l2s.a0001` 的 symlink，且全數持真實 `uid = 10365`（而非 PRoot 內假裝的 `uid = 0`）。因此原生工具**只准讀寫共享工作區檔案，不可直接操作 Ubuntu `/usr` 或 `dpkg` rootfs 內部檔樹**。
- **落地判定**：**`python` Agent／靜態掃描後端與 `git` CLI 立即值得透過 Native Hybrid 分流**（實測 **1.57×–8.13×**），小資料量純管線 `zstd | jq` 若無重度 Python/syscall 則可留於 `fast10`。

---

## 五、`Sprout 0.6.1` 相容性矩陣與真實 `Adreno (TM) 840` Vulkan GPU A/B（`sprout-gpu-compat-ab.json`）

在完全相同的 Ubuntu 24.04 映像與相同 `/opt/mesa-kgsl` Turnip ICD（`freedreno_icd.aarch64.json`，`vk_kgsl_bench` 硬體守衛強制確認 `deviceType=1`、`vendorID=0x5143`、`Adreno (TM) 840`，嚴拒 SwiftShader）下對照：

### 5.1 相容性矩陣（真實執行退出碼）

| 項目 | `fast8` | `fast10-combined` | `sprout-fakeroot` (`-0`) | `sprout-nofakeroot` |
|---|---:|---:|---:|---:|
| **`node_v24`** (`v24.20.0`) | **`0`** (`uid=0`) | **`0`** (`uid=0`) | **`134`** (`uv__close` SIGABRT) | **`134`** (`uv__close` SIGABRT) |
| **`python3_git`** | **`0`** | **`0`** | **`0`** | **`0`** |
| **`electron_as_node`** (Antigravity `44.9.1`) | **`0`** | **`0`** | **`0`** | **`0`** |
| **`chromium_153_shell`** (Playwright 1243) | **`0`** | **`0`** | **`-999`** (TIMEOUT 30s) | **`-999`** (TIMEOUT 30s) |
| **`chromium_153_pw`** (Playwright Launch) | **`0`** | **`0`** | **`134`** (`node` `uv__close`) | **`134`** (`node` `uv__close`) |
| **`vulkan_adreno840`** (`SPROUT_PASSTHROUGH` 路徑) | **`0`** | **`0`** | **`0`** | **`0`** |

- **重要發現**：
  1. `Sprout 0.6.1` 下 `Node v24.20.0` 必現 `../deps/uv/src/unix/core.c:646: uv__close: Assertion 'fd > STDERR_FILENO' failed.`（`rc=134`），且 Chromium 153 `chrome-headless-shell` 卡死逾時；而放在 `-b .../w5-tmp:/tmp` 非 `SPROUT_PASSTHROUGH` 的外部 ELF 執行會遭遇 `Permission denied`（`rc=126`），移入自動納入 `SPROUT_PASSTHROUGH` 的 `$HOME` 後則可順利載入 Turnip。
  2. `fast8` 與 `fast10-combined` 達成 **6/6 全相容**。

### 5.2 真實 `Adreno (TM) 840` Turnip Vulkan 5 組交替 A/B（+1 warmup）

| GPU 基準 | 指標 | `fast8` | `fast9-combined` | `fast10-combined` | `sprout-fakeroot` | `sprout-nofakeroot` |
|---|---|---:|---:|---:|---:|---:|
| **`vk_submit_burst`**<br>（1,000 次真實 `vkQueueSubmit`+fence） | 外部牆鐘中位數 | `1077.57 ms` | `551.60 ms` (`-48.81%`) | **`509.62 ms` (`-52.71%`)** | `513.03 ms` (`-52.39%`) | `540.47 ms` (`-49.84%`) |
| | 驅動內圈耗時 / 加速比 | `957.02 ms` (`1.00×`) | `468.50 ms` (`2.04×`) | **`423.75 ms` (`2.26×`)** | `450.02 ms` (`2.13×`) | `473.70 ms` (`2.02×`) |
| **`vk_gpu_fill_copy`**<br>（200 幀 1080p `VkImage` clear+barrier+copy） | 外部牆鐘中位數 | `381.23 ms` | `255.60 ms` (`-32.95%`) | `254.08 ms` (`-33.35%`) | **`242.03 ms` (`-36.51%`)** | `243.77 ms` (`-36.06%`) |
| | 驅動內圈耗時 / 加速比 | `293.86 ms` (`1.00×`) | **`178.95 ms` (`1.64×`)** | **`179.65 ms` (`1.64×`)** | `180.25 ms` (`1.63×`) | `181.55 ms` (`1.62×`) |

- **GPU 路線重大洞察**：外部資料曾顯示 Sprout 在 Vulkan `vkmark` 相對*未最佳化 PRoot* 達 10.4×，根因在於未經 `ioctl` BPF 放行的 PRoot 對每一次 KGSL ioctl 收取 `ptrace` 往返稅。**實測證實一旦引入 `07-proot-fast9-ioctl-bpf.patch`（`fast9`/`fast10`），KGSL Vulkan 提交與 1080p GPU 渲染內圈耗時立即獲得 `1.64×–2.26×` 加速並與 `Sprout 0.6.1` 完全打平（`423.75 ms` vs `450.02 ms`）**，同時保有 `fast10` 的 **6/6 滿分軟體相容性**（`Node v24` + Chromium 153 + Electron 44.9.1）。

---

## 六、基礎工具補強：`/usr/local/bin/termux-bg-run` 與 `termux-native-runner`

- 為根治背景 `TermuxService` 腳本分離執行後漏設手動 `schedule` 計時器、以及 `PIPE` 緩衝區死鎖的問題，新增跨專案全域 CLI [`/usr/local/bin/termux-bg-run`](/usr/local/bin/termux-bg-run) 與跨端技能 `termux-native-runner`（主源 `/root/.hermes/skills/termux-native-runner/SKILL.md`，同步至 `~/.gemini/config/skills/`、`~/.claude/skills/` 並補充於 `/root/.serena/memories/global/f8-workstation.md`）。
- 實機驗收：4 項探針全過（`rc=0` 0.07s `inotify` 喚醒、`rc=7` 透傳、3s 逾時 `rc=124`、越界路徑拒跑 `rc=2`），並隨即以 `termux-bg-run` 無人工輪詢跑完本輪 24 組真實工作站測試（`31.59s` 自動完成喚醒）。

---

## 七、最終完整性核對與路線結論

- `live.sha256`：**6/6 `OK`**（現役 `out8/`、`shard2/`、`f8-shard` 未變動）。
- 實機 Ubuntu `rootfs` 4 個核心檔（`ubu-core.sha256`）與隔離 `ubuntu-noble-arm64` 4 個核心檔：**全數 4/4 `OK`**。
- `src/f8-proot-fast`（`main` `ee603b8`）`dirty=0`；`src/f8-proot-fast-stage5`（`stage5/isolated-fast8-20261126` `c458d74`）`dirty=0`。
- **綜合計畫決議**：
  - **`PRoot-fast9` (`07`–`09`) + `fast10` (`10`–`11`)**：具備進入主線評估資格（6/6 全相容、真實多代理快 24%、Vulkan 提交快 2.26× 打平 Sprout），下一階段補 Group E/F/G 與 10 分鐘熱穩定度／Phantom Process 壓測後即可核簽升級。
  - **Native Hybrid Phase D1**：確認 `git`（1.57×）與 `python` Agent（8.13×）＋跨邊界 Unix Socket（41 µs p50）即戰力，可按白名單分流無 `.l2s.*` 依賴的專案 CLI／後端。
  - **Sprout 0.6.1**：維持低優先旁線觀察（`Node v24` `uv__close` SIGABRT 與 Chromium 153 逾時為明確淘汰／阻斷主桌面替代的硬證據，且 GPU 提交效能優勢已被 `fast9/10` BPF `ioctl` 追平）。
