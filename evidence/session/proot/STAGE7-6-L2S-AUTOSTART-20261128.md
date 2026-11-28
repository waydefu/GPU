# Stage 7.6 — 原生 git_ro 相容 PRoot link2symlink、PRoot 路由越界修補、治理 auto-start 與日誌輪替（2026-11-28）

凍結門檻：[Stage 7.6 freeze](../../../docs/F8-HYBRID2-STAGE76-FREEZE-20261128.md)（含勘誤 E1、F15 修訂、A3）與 [F13 freeze](../../../docs/F8-HYBRID2-F13-L2S-FREEZE-20261128.md)；資源門檻沿用 [7.5 tiered freeze](../../../docs/F8-HYBRID2-STAGE75-TIERED-FREEZE-20261128.md)（256 MiB PSS／64 threads／192 FD，G1–G5 不變）。原始資料見 [`stage7-6-20261128/`](stage7-6-20261128/PUBLISHED-SUBSET.md)。

**全程隔離**：已部署的四路試點（`tools/hybrid2/`、`~/.f8hyb2*`、`~/.claude.json` 的 `hybrid2`）、Stable `:1`、Fast9+09c 都沒有改動；每次執行使用自己的 run 目錄、socket、預算目錄與 daemon。

## 候選

| 項目 | 值 |
|---|---|
| 受治理腳本 | `f8_hybrid2_{budget,ctl,daemon,policy,relay,tools}.py`，最後修改於 `c583002`；雜湊彙總 `6ebf7354…`（`c583002` 與之後只改載具／文件的 `771bd50` 相同） |
| 安全判決執行 | `s76-sec.hcvaffxi`（S1–S7，候選 `c583002`）；S5 attempt 2 `s76-sec.fzyyr4yr`（`771bd50`，同腳本） |
| 矩陣 | `771bd50`（受治理腳本同 `c583002`）：`s75g-m4.YUQebl`、`s75g-m2.YPlF2l`、`s75g-m6.gZ0DwI`；fixture repo 由 PRoot git 建立，含 5 個 l2s 物件；4 路重跑（A4）`s75g-m4.G8Vp1B`，`83514c3`，受治理腳本相同 |

## 稽核發現與修補

| # | 發現 | 修補前影響 | 修補 | 路由 |
|---|---|---|---|---|
| F13 | PRoot 內 git 寫入的物件在宿主側是 `→ <rootfs>/.l2s/.l2s.tmp_obj_*NNNN → *.NNNN` 兩跳連結；原生信任檢查判為越界 | 原生 `git_ro` 對所有 PRoot 寫過的 repo 一律 `symlink-escape`（本機 9 個獨立物件庫全中） | 只放行**精確兩跳形狀**：位置限 loose object 與 `pack/*.{pack,idx,rev}`；hop1 是 `<l2s>` 目錄下 `.l2s.tmp_<kind>_<6 英數><4 位數>` 且 kind 與位置相符；hop2 為同目錄 `<hop1>.<4 位數>` 一般檔案；實際路徑必須等於 hop2。其他任何形狀維持拒絕。**沒有**把 `.l2s` 目錄列入信任 | 原生 |
| F14 | PRoot（proot-fast9）對目標名以 `.l2s.` 開頭的連結，`lstat` 會 `EPERM` 或回報目標，`os.path.realpath`／`islink` 因此被騙 | PRoot 路由（fallback 與 relay 本地）四個工具都能讀到映射根目錄外，也能繞過 PROTECTED。7.5 程式在 S3 對照組實測洩漏 | `resolve_path`／`is_link` 改用 `readlink()` 判斷連結 | PRoot |
| F15 | （DRY-1 S3 發現）在 Termux home 掛載下，PRoot 把「連結 → `.l2s.*` 符號連結」鏈**整個隱藏**：`readlink` EINVAL、`lstat` 給最終目標，但目錄項 `d_type` 仍是 `DT_LNK` | F14 的 readlink 判斷仍被繞過，`text_search /ws3/evil-dir` 讀到外部檔案 | PRoot 下 `resolve_path` 遇到「`d_type` 是連結但 `readlink` 失敗」的路徑元件即拒絕（`hidden-link`）；唯一例外是 Git 物件目錄內最後一個元件（PRoot 自己的物件硬連結，只交給 git 物件解析器讀，與 7.6 前相同）。工具走訪改以目錄項類型判斷連結 | PRoot |
| R1 | （子代理審查）`resolve_path` 先以 `abspath` 字面折疊 `..` 再跟隨連結 | `.git` 檔 `gitdir: esc/../x` 可讓檢查落在映射內的誘餌目錄，git 實際走連結到外部 | 不做字面正規化，連結先解析再處理 `..`；以隨機連結樹對 `os.path.realpath` 做性質測試 | 兩側 |
| R2 | git 參數前綴檢查仍用 `lexists`／`islink`（lstat） | PRoot 下相對參數的連結前綴可能漏判 | 改用 `is_link` | PRoot |
| R3 | `append_rotating` 重試用盡或短寫時無聲丟失 | 稽核紀錄可能缺行 | 完整寫入迴圈；重試用盡改拋 `OSError` | 兩側 |
| R4 | auto-start 的預算目錄只檢查前綴 | 可指向 PRoot rootfs（guest 可寫）或權限寬鬆的目錄 | 拒絕 rootfs 內目錄；要求呼叫者擁有且權限 0700 | 兩側 |
| A1 | TermuxService bootstrap 不傳 `F8_HYBRID2_BUDGET_DIR`，治理模式因此禁止 `--auto-start` | 重開機後 daemon 不會自動恢復；若強行 auto-start，daemon 會不受治理 | bootstrap 匯出已驗證的預算目錄；relay 不再拒絕治理模式 auto-start | 兩側 |
| A2 | relay `--route-log` 無上限；直接啟動的 `daemon.out` 跨重啟持續累加。daemon `audit.jsonl` 原本已有 5 MiB 輪替，但多程序不安全 | 長期日用下檔案無上限成長 | `append_rotating`：flock＋inode 重檢、保留一代 `.1`；`daemon.out` 超過 1 MiB 時輪替 | 兩側 |

**更正**：[試點部署紀錄](STAGE7-5-PILOT-DEPLOY-20261128.md)原寫「`audit.jsonl` 不輪替」有誤，已加勘誤，錯誤版本保留。

負向對照：還原 F13 → U1 變紅；還原 F14 → 15 項安全子測試變紅；關閉 F15 → 6 項變紅；恢復字面 `abspath` → 2 項變紅；舊 relay／ctl → 2 項 auto-start 測試變紅。

## 安全驗收（實機，隔離）

| 閘門 | 結果 | 依據 |
|---|---|---|
| S1 真 repo 對照 | **PASS** | 21 個信任根：9 個含 l2s 物件的獨立 repo，原生與 `F8_NO_HYBRID=1` 的 5 個指令逐位元組一致（原生 git 2.55、PRoot git 2.43）；12 個 worktree 兩側同樣拒絕（`gitfile-absolute`，勘誤 E1） |
| S2 原生應紅 | **PASS** | (a) PRoot 硬連結的非 git 檔、(b) 偽造於 `.l2s` 外的兩跳鏈、(c) 最終是目錄：皆 `symlink-escape`，無標記外洩。資訊項 (d)：形狀完全合格但內容為純文字 → git `inflate` 錯誤，無標記外洩 |
| S3 PRoot 路由應紅 | **PASS** | 候選：7 個呼叫零外洩（`l2s-path`／`hidden-link` 拒絕）。對照組（7.5 腳本）：`text_search` 兩次讀到外部標記（預期紅） |
| S4 競態 | **PASS** | 300 次 `cat-file` 期間另一程序在原生側不斷把物件換成指向外部純文字秘密的連結：正確 58、拒絕 194、git 錯誤 48、**含標記 0**；daemon 存活，物件已還原 |
| S4 資訊項 | 殘餘風險 | 換成外部**合法** git 物件時，300 次中 63 次回傳了該物件內容：檢查到 exec 之間的時間窗。這與 7.6 前所有符號連結檢查同類，前提是攻擊者能同時寫入該 repo 的 `.git/objects`（同 uid） |
| S5 惡意物件 | **PASS（attempt 2）** | 損壞 zlib → git 128；64 MiB 零值炸彈 → `subprocess-output-limit`（約 30–50 ms）；`cat-file -s` 正確；daemon 存活。記憶體：daemon+relay 61.0 MiB＋git 子程序 4.2 MiB＝**65.3 MiB** ≤ 256。第一次判決執行未觀測到子程序，記為 INVALID（A3）；attempt 2 的輪詢實際只取到 17 輪、命中 8 次，真實峰值可能落在取樣間隙 |
| S6 回退與 auto-start | **PASS** | 治理 relay `--auto-start`：daemon 經 TermuxService 啟動，`TracerPid 0`，環境含 run 的預算目錄，持有 daemon 租約，`governed=true`、`max_clients=4`；`ctl stop` 後下一個 relay 重新拉起新 pid，結果相同；`disable` 後走 PRoot，結果相同 |
| S7 效能（資訊） | — | 見下表 |
| 紅線 | 不變 | 每次執行開始／結束：Stable `X1` inode 2300674、Fast9+09c 3/3、試點腳本雜湊、試點 daemon pid 15369 存活、`~/.claude.json` 在單次執行內不變 |

### S7 延遲（n=20，毫秒，資訊用）

| repo：指令 | 原生 p50／p95 | PRoot p50／p95 |
|---|---:|---:|
| f8-proot-fast：`log -n 20 --stat` | 43.9／56.1 | 451.5／652.2 |
| f8-proot-fast：`cat-file -p` | 37.6／51.2 | 351.2／355.4 |
| upstream：`log -n 20 --stat` | 404.1／478.1 | 1,904.2／2,256.4 |
| upstream：`cat-file -p` | 466.0／472.9 | 1,803.9／2,157.9 |

原生政策掃描（`validate_git_ro`，5 次）：upstream（1,439 個 l2s 物件）442.7–462.3 ms，f8-proot-fast 38.4–151.3 ms。upstream 原生延遲大多花在物件逐一檢查。PRoot 路由因 F15 多了目錄項檢查而變慢（f8-proot-fast `log --stat` p50 從 DRY-1 的 300.9 ms 升到 451.5 ms，非同一判決，僅供參考）。

## 資源驗收矩陣

同一候選、同一套 G1–G5 與 256 MiB／64／192 門檻；矩陣的 `git_ro` 走原生 F13 路徑（fixture 物件是真的 PRoot l2s 連結）。

| 模式 | relay／執行槽 | 理論 PSS／threads／FD | 實測峰值 PSS／threads／FD | RSS drift（三輪） | 判決 |
|---|---|---|---|---|---|
| 2 | 2／2 | 160.1 MiB／13／63 | 87.8 MiB／7／51 | +5.4／+6.4／−4.5% | **GO** |
| 4（第一次判決） | 4／2 | 227.3 MiB／21／87 | 124.9 MiB／15／69（soak SwapPss 32.1 MiB） | +2.5／−7.7／−3.7% | **HOLD**：soak 熱閘 FAIL（保留） |
| 4（A4 重跑） | 4／2 | 217.8 MiB／21／87 | 127.7 MiB／15／73（SwapPss 峰值 62.8 MiB） | +3.5／+1.5／+5.9% | **GO** |
| 6 | 6／1 | 250.0 MiB／27／95（餘 6.0 MiB） | 164.3 MiB／20／83 | +4.8／+4.2／+4.4% | **GO** |
| 8 | — | 未重跑 | — | — | 維持 7.5 HOLD |

**4 路 HOLD 的原因**：G1–G4 全部通過；600 秒 soak 本身也完成（16.51 次/秒、p50 35.5 ms／p95 121.5 ms／p99 146.5 ms，CPU 最高 79.1 °C，電池 34.5 °C，未觸發停機閘）。但凍結的 soak 熱閘要求最後三個 20 秒窗的 CPU 溫度中位數差距 ≤ 2 °C，實測 **50.9 → 40.7 → 39.7 °C**（差 11.2 °C）。溫度是**下降**而非上升：這輪接在前一次 4 路執行因過熱停機（`U9MxFV`）之後才開始，soak 期間機器仍在降溫。依凍結規則仍判 FAIL，不改判；這是 FAIL 不是 INVALID，所以不依 A2 重跑。G5（提案，未採用）同輪為 FAIL：三輪保有量 23,835 → 24,171 → 25,155 KiB 單調上升且超過閒置值的 2%。

同一 4 路的執行先前還有兩次未判決的嘗試：`BW38kj`（串接腳本漏傳信任根變數，矩陣未開始，ABORTED）與 `U9MxFV`（C1 第 3 輪 CPU 85.7 °C，A2 重跑時電池 48.0 °C，INVALID，鏈停止）。兩者都保留在本機。

**A4 重跑（使用者授權）**：依修訂 A4，先等裝置熱穩態（12:34 達成：最後三窗 CPU 中位數皆 24.3 °C、最後一窗最高 47.1 °C、電池 21.6 °C；中間一窗曾瞬間到 65.6 °C），再跑一次全新的 4 路完整矩陣，判決門檻不變。**環境差異**：使用者表示先前幾次執行有外接散熱器（確切開關時間不明），這次重跑時已關閉。結果：G1–G5 全部 PASS，所有 cell 都是第一次即通過，沒有用到 A2 重跑；C1 三輪 14.85 次/秒、p95 104.8／121.1／115.7 ms；C2 最大負載 CPU 最高 84.1 °C（停機閘 85 °C）；soak 600 秒 16.52 次/秒、p95 116.8 ms，最後三窗 **32.4 → 32.0 → 32.0 °C**，通過。保有量 24,593／24,333／25,316 KiB（G5 PASS）。SwapPss 峰值 62.8 MiB 高於前幾輪，屬系統換出，PSS 峰值仍只有 127.7 MiB。

依 [Stage 7.6 freeze](../../../docs/F8-HYBRID2-STAGE76-FREEZE-20261128.md) 的結論規則「F13 只有在 S1、S2、S4、S5 通過且矩陣維持原判決時才是 GO」：安全閘門全數通過，矩陣 2／4／6 路都是 GO（4 路以 A4 重跑為準，第一次的 HOLD 紀錄保留）——**F13 判 GO（隔離驗收）**。日用部署是另一個決定，本報告寫成時尚未替換。

## 殘餘限制

- **檢查到使用的時間窗（TOCTOU）**：所有符號連結檢查都在 git 執行前完成；能同時寫入 repo `.git` 的同 uid 程序可以在中間換掉檔案。S4 證實純文字秘密不會經 git 物件解析器外洩，但合法的外部 git 物件可以。唯一的根本解法是讓 git 讀私有快照，範圍外。
- **PRoot 路由的物件檔無法驗證來源**：PRoot 隱藏自己的硬連結，fallback 只能放行 Git 物件目錄內最後一個元件，內容只交給 git 物件解析器（與 7.6 前相同）；原生路由則有嚴格兩跳檢查。
- **F13 未涵蓋的形狀一律安全失敗**：`.bitmap`／`.mtimes`（cruft pack）、`git clone --local` 的硬連結（hop1 不是 `tmp_` 名）會回 `symlink-escape`。目前本機 9 個物件庫都沒有，要支援需另行調查後擴充。
- **mid-session daemon 消失**：relay 仍照 7.4 設計退出、不重送；恢復發生在下一次 relay 啟動（A1）。
- **git 子程序記憶體**仍無程式上限，只有輸出上限與逾時；S5 量到的子程序峰值受取樣限制。
- 配額仍是合作式；auto-start 只在 daemon 不存在時傳遞預算目錄，連到已在執行、但不受治理的 daemon 時無法察覺。
- Mode 8 未重跑：HOLD 來自理論總和（G3），本輪修改無法降低它。

## 結論

| 項目 | 判決 |
|---|---|
| F13 安全性（S1、S2、S4、S5） | 全部通過 |
| F14／F15 PRoot 路由越界 | 已修補，S3 通過（7.5 對照組實測會洩漏） |
| A1 治理 auto-start、A2 日誌輪替 | S6 與單元測試通過 |
| 資源矩陣 | 2 路 GO、6 路 GO、4 路 GO（A4 重跑；第一次 HOLD 保留）、8 路維持 HOLD |
| F13 整體 | **GO（隔離驗收）** |
| 日用版本 | **未替換**（待使用者決定）；PR #55 **未合併** |
| 回歸 | PRoot 63/63（連跑 2 次）、Termux 原生 63/63（另於每個矩陣模式各跑一次）；GitHub 治理 CI 在 `c583002`、`771bd50` 通過（CI ≠ 實機驗收） |

## 回退

尚未替換日用版本。日用試點的回退方式不變：`f8_hybrid2_ctl.py disable` 或 `claude mcp remove hybrid2 -s user`。
