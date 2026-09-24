# GL-BENCH-01 結果 — 2026-09-24：**GL_INVALID／VK_INVALID**（觸控），不下結論

判準：`GL-BENCH-01-FREEZE.md`（FROZEN）。判定器 `gl_bench_judge.py` SHA256 `366c9050…70a4`（fork `8b905a2`）。
證據：`gate-a-a1/p2-pga-rca/runtime-f592241-gl/gl-bench-01`、`gl-bench-02`；判決輸出 `gl-bench-judge.txt`、`gl-bench-judge-aa.txt`。
兩個 cell 都是 `CMD_CAPTURED`、`fixture_rc=0`。每段前後 Stable 都相同、螢幕亮、無鎖屏、實驗版在前景，thermal 都是 0（沒有等待），
present mode 是 `immediate`，X3 以精確 pid SIGTERM 結束（construction，記在 `x-end.txt`），沒有殘留程序。

## 判決
| | rep 01 | rep 02 | 判決 |
|---|---|---|---|
| GL | 有效 | `gl-gpu` 觸控 80、`gl-cpu` 觸控 289 → INVALID | **GL_INVALID** |
| VK | `vk-cpu` 觸控 1013 → INVALID | `vk-cpu` 觸控 8 → INVALID | **VK_INVALID** |
| A/A | — | — | `GL_AA_INVALID`／`VK_AA_INVALID`（CPU 段本身就有觸控） |

兩個 attempt 凍結，不重跑、不重判。

## 觸控樣態（每段 1–4 次按下）
座標分散在螢幕下半部為主，有長拖曳（例如 `gl-gpu-off` rep 01：y 1351→2552）。每段按下 1–4 次，是真實接觸、不是雜訊；
無法分辨是包包內擠壓還是有人拿起手機。偵測器照設計把這些段排除。

## 描述（**不是判決**，觸控檢查在記憶體中忽略；`gl-bench-describe-ignoring-touch.txt`）
| | 分數 GPU／CPU | 倍數（門檻 ≥1.5） | 每幀 CPU ms GPU／CPU | 倍數（門檻 ≤0.5） | 有效？ |
|---|---|---|---|---|---|
| GL rep 01 | 481.9／142.0 | 3.39 | 1.136／6.885 | 0.17 | **有效** |
| GL rep 02 | 413.9／82.7 | 5.00 | 1.565／12.047 | 0.13 | 觸控 |
| VK rep 01 | 1114.8／269.9 | 4.13 | 0.675／3.945 | 0.17 | 觸控（`vk-cpu`） |
| VK rep 02 | 1153.2／244.2 | 4.72 | 0.651／4.288 | 0.15 | 觸控（`vk-cpu`） |

- 四組數字都遠超過門檻，但只有 GL rep 01 是有效資料；**依凍結規則不能據此宣稱 GPU 收益**。
- llvmpipe 兩次差很多（142.0 對 82.7）：rep 02 的 `gl-cpu` 排最後、那段有 289 筆觸控；thermal status 兩次開跑前都是 0。原因未查。
- 上屏成本（描述）：Zink 關掉上屏（`--off-screen`）分數約 579–610，有上屏 414–482；X3 在 `gl-gpu` 每段吃掉 55–74 CPU 秒，`gl-gpu-off` 只有 4–5 秒——
  和「Zink 經 drisw 由 CPU 複製上屏」的推測一致，**未證實**。
- Turnip headless 約 1190–1251，xcb 上屏約 1115–1153。

## 下一步（待使用者決定）
另開 GL-BENCH-02（門檻、指標、工具照舊，只換 attempt 編號），並在跑的期間確保觸控面板不被碰到。
