# V2-B3-MATRIX-BIND — P2-B.3 效能矩陣的綁定與取樣策略（計畫書 §12，決策 D-11）

DATE 2026-09-23 · PRODUCT `bfb5769` · 先於任何 B.3 量測凍結
機器可讀：fork `tests/b3/b3-freeze.json`（cell 清單由 `tests/b3/make_cells.py` 以固定 seed 產生，清單 sha 釘在 freeze 裡）

## 1. 問什麼

§12.3：在哪些 (rect, ratio, reuse, batch, residency, readback) 區域 GPU 路徑勝出、哪些落後、交叉點在哪、
交叉點是否穩定。這份結論是 Gate H（D-07 / D-16）的**唯一合法輸入**。

比較的三種產品模式（同一個 APK，只差 X 的啟動環境）：

```
G  TERMUX_X11_GATEA_PROTO=1                Gate A direct；registry 滿或 admission 拒絕時走 D0a staging
S  PROTO 未設                              D0a staging（R3 路徑）——G 的 fallback 路徑，單獨量
C  TERMUX_X11_DISABLE_EXA_GPU=1            全部 EXA 在 CPU（fbComposite/pixman）——router 的另一個選項
```

Gate H 的 router 問題就是「在 G 會被選中的格子裡，C 是否更快」。

## 2. 為什麼不能沿用 B.3a 的 driver

`patches/p_b3a_cost.c` 每個 composite 都 `xcb_request_check`（一次往返），一個 process 只跑一格。
B.3 的時間會被往返主導，batch 維度失去意義。新 fixture `tests/b3/p_b3_cells.c`：一個連線跑整張清單，
batch 內的 composite 不做往返，batch 結束用一次往返（或 GetImage）收尾，client 端 CLOCK_MONOTONIC 計時。

**重要的產品事實（source）：** direct 與 staging 路徑在 `DoneComposite` 都同步等 GPU 完成
（`lorieGpuCopyWait`，InitOutput.c:3717/3752），所以 batch 在 GPU 端**不會** pipeline；batch 只省
client 往返。這會讓「batch 越大 GPU 越划算」的直覺在這個產品上不成立——正是要量的東西之一。

## 3. 因子與水準（§12.1，含 V-9 修正）

```
rect       (11) 1x1 5x24 16x16 32x32 64x64 128x128 256x256 512x512 1024x1024
                fullscreen-internal 1200x2608（offscreen pixmap）· fullscreen-external 3440x1440（offscreen）
ratio       (4) 1x · 4x（src 2w×2h）· 16x（src 4w×4h）· redirected（src = 1200×2191 視窗大小，rect 取其子區）
reuse       (4) 1 · 4 · 16 · 64 組 (src,dst)，輪流使用        ← registry 16 格：16 組以上必然換出
batch       (4) 1 · 4 · 8 · 16 個 composite / 次往返
residency   (4) cold（全新 pair 的第一次）· warm（穩態）· resize（每輪換 dst 尺寸）· recreate（每輪同尺寸重建）
readback    (3) none（GetInputFocus 收尾）· immediate（每 batch 後 GetImage 該區）· delayed（每 8 輪一次 GetImage 全部）
```

**只有內建面板**：外接 3440×1440 目前不存在。`fullscreen-external` 只是 offscreen pixmap 尺寸，
**不代表外接螢幕情境**，結論不得外推到 Gate W 的外接情境（V-9）。

### 構造上不可行、明確剪掉的組合（不影響結論的理由寫在旁邊）

```
src 記憶體 > 64 MB（ratio 16x 配 ≥1024 的 rect、external 配 4x 以上）  → 超出單一 pixmap 的合理範圍，
     日常桌面不會出現；記錄為 NOT_MEASURED，結論不涵蓋
reuse × (src+dst) 總量 > 256 MB                                          → 同上（沿用 B.3a 的上限）
```

## 4. 取樣策略（D-11 的答案）

完整笛卡兒積 8448 格。**不全掃**；改成「主平面＋交互作用平面＋隨機保留驗證」：

```
A 核心平面   rect(11) × batch(4) × readback(3)，其餘取中心（ratio 1x、reuse 1、residency warm）   132 格
B 交互平面   rect × ratio(4)、rect × reuse(4)、rect × residency(4)，其餘取中心                   91 格
             （3 × 44 − 重複的中心列 = 99，其中 8 格被下列可行性規則剪掉，見 pruned.tsv）
C 保留驗證   從剩餘可行的完整矩陣中，以 seed 20260923 均勻抽 40 格                               40 格
合計         263 格（＋中心格 N，每 25 格重測一次）× 每種模式

可行矩陣是 3136 格，不是 8448：reuse 的定義是「輪流使用 N 組**存活中**的 set」，只對 warm 有意義
（cold / resize / recreate 每輪都沒有存活的 set），再加上 src ≤ 64 MB、總量 ≤ 256 MB 的記憶體上限。
```

**剪枝的依據（可被推翻的假設）：** 把 rect 當成交互作用的樞紐——成本對 ratio / reuse / residency 的依賴
可以隨 rect 變，但彼此之間、以及與 batch / readback 之間，**假設沒有顯著的高階交互作用**。
模型：`log t(cell) = A(rect,batch,readback) + ΔB_ratio(rect) + ΔB_reuse(rect) + ΔB_residency(rect)`。

**驗證規則（先凍結）：** 對 C 的每一格，用 A+B 預測 G/C 的勝負與 log 成本：

```
勝負一致率 ≥ 90%     只算實測 |log(t_G / t_C)| > 雜訊帶的格子
預測誤差中位數 ≤ 0.25（|log 預測 − log 實測|，約 1.28 倍）
兩者都成立 → 剪枝成立（D-11）
任一不成立 → 剪枝不成立：依殘差最大的因子補一個完整的二因子平面（Stage D），換 seed 再抽 40 格重驗
```

## 5. 量測協定

```
每格          warmup 3 輪 + 計時 20 輪；統計量 = 每個 composite 的時間中位數（輪時間 / batch）
              另記 p95、每格的 X CPU 時間（/proc/<x>/stat 前後差）、錯誤數、像素抽驗
像素抽驗       每格計時結束後做一次 GetImage 與 CPU 參考值比對（不計時）；不符 = 該格 INVALID_CORRECTNESS
雜訊           中心格（1024x1024、batch 1、none、1x、reuse 1、warm）每 25 格重測一次；
              雜訊帶 = 同一次執行內中心格 max/min 比值
順序           每次執行內 cell 順序以 seed 打亂（避免漂移與順序相關）
執行           G、C、S、G（最後再跑一次 G：看 thermal / 時間漂移下交叉點是否穩定）
telemetry      計時執行**不開** TELEMETRY（產品設定；每個 event 一次 liblog 會扭曲小 rect 的時間）；
              另跑一次 TELEMETRY=1 的歸因執行（每格 3 輪、不計時），記錄每格實際走 direct / staged / CPU
X 啟動         untraced（RCA-XFCE-2）；計時執行不 arm R8，結束時 SIGTERM X（construction，記錄 pid），
              效能執行不做 lifecycle 判定（那是 R8–R10 與 XFCE 的工作）
環境           螢幕 Awake 且未鎖、Stable 不變、每次執行前後各記一次 dumpsys thermalservice
              （雜訊由中心格重測量化，不另取 loadavg；refresh period 不在 fixture 可觀測範圍）
```

## 6. 判讀（先凍結）

```
r = t_G / t_C（每 composite 中位數）
GPU 勝   r ≤ 0.80 且該次執行的中心格雜訊帶 < 1.25
CPU 勝   r ≥ 1.25（同樣的雜訊條件）
平手     其他
交叉點   沿 rect 軸（固定其他因子）：最小的 rect，使得它與所有更大的 rect 都是 GPU 勝
穩定     同一條線在兩次 G 執行、warm vs recreate、internal vs external 尺寸下交叉點相同或相鄰
```

雜訊帶 ≥ 1.25 的執行不下勝負（全部記為 UNJUDGED，不是平手）。

## 7. 產出

`b3-run-<mode>-<n>.jsonl`（每格一行）· `b3-attribution.jsonl` · `b3-analysis.json`（A+B 模型、保留驗證結果、
勝負圖、交叉點、穩定性）· `V2-B3-ANALYSIS.md`（給 Gate H）。

## 8. 不做的事

不改任何產品程式；不量 GPU 執行時間（沒有可攜的 timestamp，null）；不量外接螢幕；不把 B.3 結果當 Gate W。
