# GL-BENCH-01 — glmark2／vkmark：GPU（Zink／Turnip）對 CPU（llvmpipe／lavapipe）判準凍結

**狀態：FROZEN（2026-09-24，使用者核准門檻「照這門檻跑」）。**凍結時沒有任何 glmark2／vkmark 的量測資料。
凍結後不得修改門檻、指標或有效性條件；要改就整批作廢，另開 GL-BENCH-02。

## 揭露：寫判準時已經看過的資料
- `GL-FEASIBILITY-01.md` 的 demo 數據：glxgears 單次 537 對 483 fps（約 1.1 倍）、vkcube 兩邊都卡在約 60 fps；client CPU 約減半到 1/5。
- glmark2／vkmark：只跑過 `--help`、`--version`，並從執行檔裡抽出輸出格式字串（`strings`）；**沒有任何分數或場景輸出**。
- root 探測 cell（`runtime-f592241-gl/gl-bench-rootprobe.blocked-expected`）只跑了 `xdpyinfo`。
- 門檻不是從上面的 demo 數據推算的；理由見「判準」各條。

## 問題
在實驗版 X `:3` 上，一般 3D 程式改用 GPU 驅動（GL 用 Zink＋Turnip、Vulkan 用 Turnip），
**比 CPU 驅動（llvmpipe／lavapipe）更快、每一幀花的 CPU 也更少嗎？**
範圍只到 benchmark 層級，**不代表遊戲、桌面或其他應用程式的結論**。

## 環境（固定）
| 項目 | 值 |
|---|---|
| 產物 | `1.03.01-f592241-24.09.26`，CI 35937188670，APK SHA256 `f9e35b6907df36fc4f4d5a0440147c3e9b746356776beb3217431b48fa01075c`，MODE=G（預設分流 `TERMUX_X11_GPU_MIN_PIXELS=4097`） |
| runner | `evidence/session/gl/run-gl-bench.sh`（由 `run-async-proto.sh` 衍生，只改一行：`EXPECT_ROOT` 改從環境變數讀）`KIND=cmd` |
| X root | **1200×2416**（直向、按鍵列隱藏；2026-09-24 root 探測實測）。不是這個尺寸 runner 會 BLOCKED |
| 包包模式 | 只改實驗版的設定：`evidence/session/gl/exp-pocket-prefs.sh apply`——按鍵列隱藏（上面的 ESC 會關掉 benchmark）、下滑／返回無動作、`screenIdleTimeout=Never (keep screen on)`（視窗旗標 `FLAG_KEEP_SCREEN_ON`，不需充電）。原值存在 `exp-pocket-prefs.saved`，`restore` 還原 |
| client | Termux 原生 `glmark2` 2023.01-3（GLX flavor）、`vkmark` 2025.01-3、Mesa 26.0.6-3；從 PRoot 啟動 |
| 視窗 | 兩者都用預設 800×600、預設 benchmark 清單（不帶 `-b`），加上 `--show-all-options`（讓每個場景印出 duration） |
| 共同 env | `vblank_mode=0`；**每個 Vulkan 相關執行**（Zink、Turnip、lavapipe）都帶 `VK_LOADER_LAYERS_DISABLE=*` |

## 受比較的組態
| 代號 | 指令（摘要） | 角色 |
|---|---|---|
| `gl-cpu` | `LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe glmark2` | GL 對照 |
| `gl-gpu` | `MESA_LOADER_DRIVER_OVERRIDE=zink GALLIUM_DRIVER=zink VK_ICD_FILENAMES=<freedreno_icd> glmark2` | GL 受測 |
| `vk-cpu` | `VK_ICD_FILENAMES=<lvp_icd> vkmark --winsys xcb -p <PM>` | VK 對照 |
| `vk-gpu` | `VK_ICD_FILENAMES=<freedreno_icd> vkmark --winsys xcb -p <PM>` | VK 受測 |
| `gl-gpu-off` | `gl-gpu` 加 `--off-screen` | **只描述**：扣掉上屏後的算圖能力 |
| `vk-gpu-hl` | `vk-gpu` 改 `--winsys headless` | **只描述**：同上 |

- **present mode `<PM>` 在任何 benchmark 之前決定**：cell 開頭對兩個 ICD 各跑一次 `vulkaninfo`（`:3` 的 xcb surface），
  兩邊都支援 `IMMEDIATE` → `immediate`；否則兩邊都支援 `MAILBOX` → `mailbox`；再不然 `fifo`。兩邊一定用同一個模式，並記在 `cmd.out` 的 `PRESENT_MODE` 行。
- ICD 路徑：`/data/data/com.termux/files/usr/share/vulkan/icd.d/{freedreno,lvp}_icd.aarch64.json`。

## 量測量（每一段執行各自量）
- **分數**：每個場景的 FPS（glmark2 `FPS: %s FrameTime: %s ms`、vkmark `FPS: %u FrameTime: %.3f ms`）。
- **client CPU**：`getrusage(RUSAGE_CHILDREN)` 的 user＋sys 秒數（每段一個新的 python wrapper）。
- **X3 CPU**：該段前後各讀一次 `/proc/<x3-pid>/stat` 第 14＋15 欄（ticks，CLK_TCK=100）。
- **幀數**：該段**所有完成場景**的 Σ（FPS × duration）。duration 取 `--show-all-options` 印出的值；**有任何完成場景沒印出 duration，該段就是 INVALID**（不猜預設值）。
  幀數涵蓋整段，是為了和同樣涵蓋整段的 CPU 時間對齊。
- **每幀 CPU**：`cpu_ms_per_frame =（client user+sys ＋ X3 CPU）× 1000 / 幀數`。
- 量不到的欄位寫 `null`，不可寫 0；判準用到的欄位是 null，該段就是 INVALID。
- 只描述、不進判準：Activity 程序的 CPU（透過 adb 讀 `/proc/<act-pid>/stat`）、thermal、`*-off` 和 `*-hl` 的分數。

## 判準（兩次重複都必須成立）
對 GL（`gl-gpu` 對 `gl-cpu`）與 VK（`vk-gpu` 對 `vk-cpu`）各自判定：

- **FASTER**：`score_gpu ≥ 1.5 × score_cpu`。
  1.5 倍遠大於同一組態重複執行常見的幾 % 誤差，而且是使用者感受得到的差距。
- **EFFICIENT**：`cpu_ms_per_frame_gpu ≤ 0.5 × cpu_ms_per_frame_cpu`。
  用「每幀」是因為兩邊都沒有幀率上限：跑得快的一邊幀數也多，比較總 CPU 會懲罰較快的一方；
  實際遊戲多半鎖 60／120 fps，這時真正決定負載的就是每幀成本。
  0.5 的依據：PRoot 追蹤器已經長期吃掉約 1 核，GPU 路徑至少要省下一半才有實質意義。
- `score` 定義：該次重複中，**兩邊都有完成的場景**的 FPS 算術平均（兩邊場景集合相同時，等於工具自己印的 Score）。
  只有一邊完成的場景要列出來；共同完成的場景少於兩邊中較長清單的 80% 時，該組比較判為 INVALID。

判決 token（`gl_bench_judge.py` 輸出）：
- `GL_GPU_BENEFIT`：兩次重複 FASTER 和 EFFICIENT 都成立。
- `GL_GPU_NO_BENEFIT`：兩次重複都有效，而且至少一次有一條不成立（註明是哪一條、哪一次）。兩次結果不一致也算這一類。
- `GL_INVALID`：**任一次重複**的比較無效——沒有資訊，**不是 FAIL**。另一次的數字照印，但只作描述。
- VK 同理：`VK_GPU_BENEFIT`／`VK_GPU_NO_BENEFIT`／`VK_INVALID`。

## 有效性（任一條不成立 → 該段 INVALID）
- **驅動身分**：`gl-gpu`／`gl-gpu-off` 的 `GL_RENDERER` 要含 `zink` 和 `Adreno`；`gl-cpu` 要含 `llvmpipe`；
  `vk-gpu`／`vk-gpu-hl` 的 `Device Name` 要含 `Adreno`；`vk-cpu` 要含 `llvmpipe`。**payload 沒走到宣稱的路徑 = INVALID。**
- 工具 `rc=0` 且沒有逾時（glmark2 900 s、vkmark 600 s）；沒有無法解析的場景行。
- **thermal**：開跑前 status 必須是 0。和上一段至少間隔 30 s，之後每 10 s 查一次，最多等 300 s。
- **防誤觸（手機放包包）**：整段用 `getevent /dev/input/event7`（focaltech_ts）錄觸控，**有任何 EV_KEY／EV_ABS 事件就 INVALID**。
  錄製器 2 s 後仍在執行、沒有開檔／權限錯誤、而且結束時仍在執行，觸控計數才有效；否則計數是 `null`，同樣 INVALID。
  偵測器的正向對照：`touch-detector-control-20260924.txt`（真人觸控 3 s 錄到 294 筆）。
  原本想注入無作用的 `EV_SYN` 做每段自我測試，但 adb shell 沒有寫入權限（SELinux），改用上述條件。
- **前景與螢幕**：每段前後，實驗版 `MainActivity` 都要在前景（`mCurrentFocus`），`mWakefulness=Awake`，而且沒有鎖屏。
- runner 層級：Stable 前後不變、X3 未被追蹤、root 1200×2416、mem-guard 未觸發、APK SHA256 相符。

## 順序與證據位置
- 每次重複一個 runner cell（`REP=01|02`），cell 內依序執行 6 段；rep 02 把判準用的 4 段倒過來排，抵消熱累積：
  - rep 01（`evidence/session/gate-a-a1/p2-pga-rca/runtime-f592241-gl/gl-bench-01`）：`gl-cpu → gl-gpu → vk-cpu → vk-gpu`，然後 `gl-gpu-off → vk-gpu-hl`
  - rep 02（`…/gl-bench-02`）：`vk-gpu → vk-cpu → gl-gpu → gl-cpu`，然後 `gl-gpu-off → vk-gpu-hl`
- `CMD_TIMEOUT=3600`。每段的原始輸出、`.touch` 錄檔、SEG 行都在 cell 目錄。

## 工具（凍結的版本）
| 檔案 | 位置 | SHA256 |
|---|---|---|
| `gl_bench.sh` | fork `tests/gl/`，commit `8b905a2`（本地，未 push） | `393491b86b61adb284d23ea1e4267bc5a9740e107497edb7d4978ede9d9b3eb4` |
| `gl_bench_judge.py` | fork `tests/gl/`，commit `8b905a2` | `366c9050752fe7c371fd3b3e028f43abf3cbb344171d32f696d18805961e70a4` |
| `run-gl-bench.sh` | `evidence/session/gl/` | `c5e03c2e16da5b476811d6102e88bd0c576ba55fddefaa736606370b6ce14e16` |
| `exp-pocket-prefs.sh` | `evidence/session/gl/` | `3cd0ba2752a449d94f3a43941e2df0a907b786e3507856421e815f0c1c51d29e` |

## 工具驗證（受判資料產生之前）
- **判定器 `--selftest` → `SELFTEST_PASS`**，7 個合成案例：
  (a) GPU＝CPU → `NO_BENEFIT`（**應該要紅，確實紅**）；(b) 驅動身分不符 → `GL_INVALID`；(c) 明顯達標 → `BENEFIT`；
  (d) 有觸控 → `INVALID`；(e) 觸控計數 null → `INVALID`；(f) 快 1.4 倍但 CPU 省很多 → `NO_BENEFIT`（不能只靠 EFFICIENT 過關）；
  (g) A/A 對照 → `*_AA_GPU_NO_BENEFIT`。
- **外圍儀器乾跑**（`GL_BENCH_DRYRUN=1`，一段 `sleep 5`，沒有 benchmark）：thermal、focus（當時前景是 Stable → 正確判為 false）、
  觸控錄製（錄到 310 筆真人觸控）、錄製器以精確 pid 收掉，主機端與手機端都沒有殘留的 `getevent`。
- 審查時抓到並修掉的錯誤（都在任何 cell 之前）：`touch_start` 原本在 `$(...)` 裡呼叫，錄製器 pid 會遺失，導致每段都是 null 並遺留程序；
  `exp-pocket-prefs.sh restore` 的 `am` 吃掉迴圈 stdin，只還原第一項（存檔已照第一次讀到的原值手動補正，見 `exp-pocket-prefs.saved.NOTE`）。
- 資料產生後：**A/A 對照**（`gl_bench_judge.py --aa gl-bench-01 gl-bench-02`）必須是 `GL_AA_GPU_NO_BENEFIT` 與 `VK_AA_GPU_NO_BENEFIT`，
  否則判定器作廢，這一批不下結論。

## 不在範圍內
上屏延遲、DRI3／AHB 零拷貝、遊戲、全螢幕 1200×2416 的數字（之後可另開凍結）、Stable `:1`。
