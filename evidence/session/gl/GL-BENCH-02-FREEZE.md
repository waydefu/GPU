# GL-BENCH-02 — GL-BENCH-01 的重跑 attempt（判準完全相同）

**狀態：FROZEN（2026-09-24，使用者：「開跑吧，我盡量不碰」）。**

GL-BENCH-01 兩次重複都因觸控而 `GL_INVALID`／`VK_INVALID`（`GL-BENCH-01-RESULT.md`，已凍結、不重判）。
本 attempt **沿用 `GL-BENCH-01-FREEZE.md` 的全部內容**：門檻（FASTER ≥ 1.5×、EFFICIENT ≤ 0.5×、兩次都要成立）、指標、
有效性條件（含觸控）、組態、順序、判決規則，以及同一組工具，沒有任何修改：

| 檔案 | SHA256（開跑前重新核對，與 GL-BENCH-01 相同） |
|---|---|
| `gl_bench.sh`（fork `8b905a2`） | `393491b86b61adb284d23ea1e4267bc5a9740e107497edb7d4978ede9d9b3eb4` |
| `gl_bench_judge.py`（fork `8b905a2`） | `366c9050752fe7c371fd3b3e028f43abf3cbb344171d32f696d18805961e70a4` |
| `run-gl-bench.sh` | `c5e03c2e16da5b476811d6102e88bd0c576ba55fddefaa736606370b6ce14e16` |
| `exp-pocket-prefs.sh` | `3cd0ba2752a449d94f3a43941e2df0a907b786e3507856421e815f0c1c51d29e` |

## 和 GL-BENCH-01 不同的地方（只有這些）
- 證據目錄：`gate-a-a1/p2-pga-rca/runtime-f592241-gl/gl-bench2-01`（REP=01）、`gl-bench2-02`（REP=02）。兩個 cell 連續執行。
- 手機放置：使用者盡量不碰（不再放包包）。

## 揭露
開跑前已經看過 GL-BENCH-01 的描述數字（觸控作廢、不是判決）：GPU 快 3.4–5.0 倍、每幀 CPU 0.13–0.17 倍。
門檻在那之前就已凍結，本 attempt 不做任何調整；判決只看 GL-BENCH-02 自己的兩個 cell。
