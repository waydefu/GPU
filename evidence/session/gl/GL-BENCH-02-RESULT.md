# GL-BENCH-02 結果 — 2026-09-24：**GL_GPU_BENEFIT／VK_GPU_BENEFIT**

判準：`GL-BENCH-01-FREEZE.md`（經 `GL-BENCH-02-FREEZE.md` 原樣沿用）。判定器 `gl_bench_judge.py` SHA256 `366c9050…70a4`（fork `8b905a2`）。
證據：`gate-a-a1/p2-pga-rca/runtime-f592241-gl/gl-bench2-01`、`gl-bench2-02`；判決 `gl-bench2-judge.txt`，A/A `gl-bench2-judge-aa.txt`。
產物 `1.03.01-f592241-24.09.26`（APK `f9e35b69…075c`），MODE=G，X root 1200×2416，present mode `immediate`，800×600 視窗。

## 有效性
- 兩個 cell 都是 `CMD_CAPTURED`、`fixture_rc=0`；Stable 前後相同；螢幕亮、無鎖屏；mem-guard 未觸發；結束後沒有殘留程序。
- **判準用的 8 段全部有效**：觸控 0、rc=0、thermal 開跑前都是 0（沒有等待）、每段前後實驗版都在前景、驅動身分相符、33/33 與 13/13 場景共同完成。
- 描述段 `vk-gpu-hl` rep 01 觸控 16 → 該描述值無效；其他描述段有效。

## 判決
| | rep 01 | rep 02 | 判決 |
|---|---|---|---|
| **GL**（Zink＋Turnip 對 llvmpipe） | 分數 480.4／89.3 = **5.38×**；每幀 CPU 1.144／10.920 ms = **0.10×** | 441.5／90.8 = **4.86×**；1.197／10.729 = **0.11×** | **GL_GPU_BENEFIT** |
| **VK**（Turnip 對 lavapipe） | 1146.9／292.2 = **3.93×**；0.647／3.619 = **0.18×** | 903.5／181.2 = **4.99×**；0.878／4.868 = **0.18×** | **VK_GPU_BENEFIT** |

門檻：FASTER ≥ 1.5×、EFFICIENT ≤ 0.5×，兩次都要成立——四組全部成立。

## A/A 對照（CPU 對 CPU）— 通過
- `GL_AA_GPU_NO_BENEFIT`：llvmpipe 兩次 89.3／90.8（0.98×、1.02×），每幀 CPU 1.02×／0.98×。
- `VK_AA_GPU_NO_BENEFIT`：但 **lavapipe 兩次 292.2／181.2，差 1.61×，單看 FASTER 會誤判成立**；是 EFFICIENT（0.74×）擋下的。

## 必須記下的限制
- **凍結文件寫「1.5 倍遠大於重複誤差」，對 CPU 驅動不成立。** lavapipe 重複差 1.61×（本次 A/A），llvmpipe 在 GL-BENCH-01 也曾 142.0 對 82.7（1.72×，該段有觸控，僅描述）。
  判決仍然成立：凍結規則要求兩條同時成立、A/A 也照規則通過；而且實測 GPU 倍數 3.9–5.4×，高於觀察到的 CPU 波動。
  但**不能再把 1.5× 單獨當成「超出雜訊」的依據**；之後的凍結若只用速度一條，需要重新定門檻或加重複次數。
- CPU 驅動大幅波動的原因未查（thermal status 一直是 0；可能是更細的降頻或排程，未證實）。
- 範圍只到 benchmark：800×600 視窗、glmark2 預設清單、vkmark 預設清單。**不代表遊戲、桌面或其他程式**。

## 描述（不進判準）
- 上屏成本：Zink 關掉上屏（`--off-screen`）分數 576／565，有上屏 480／442；X3 在 `gl-gpu` 吃 55–74 CPU 秒、`gl-gpu-off` 只有 4–5 秒。
  和「Zink 經 drisw 由 CPU 複製上屏」的推測一致，**仍未證實**；這正是 DRI3／AHB 零拷貝可以處理的部分。
- 總 CPU（client＋X3，約 330 s 的 glmark2 段）：GPU 174–181 秒、CPU 322 秒——GPU 路徑畫了約 5 倍的幀，總 CPU 只用了約 55%。
- Turnip headless 1258（rep 02，有效），xcb 上屏 903–1147。

## 執行紀錄
- rep 01 → rep 02 的串接守衛在 rep 01 結束的同一秒看到符合 X3 的程序而停止（`gl-bench2-chain.log` `CHAIN_STOP x3_left_after_rep01`）；
  守衛沒有記下符合的程序（工具疏漏）。runner 自己的證據：X3 12924 已送 SIGTERM，trap 收尾時 `b_cleanup` 沒有需要清的 X3；數分鐘後確認沒有殘留。
  rep 02 改為單獨啟動（`gl-bench2-rep02-launch.log`，守衛改為等待 30 s 並記錄符合的程序；前後都沒有符合）。判準、工具與順序都沒有改變。
