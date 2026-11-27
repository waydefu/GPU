# POCO F8 Ultra 工作站效能工程｜獨立架構審查

2026-11-27，台北時間。對象為 Android 16、非 Root、Termux app UID 下的 aarch64 工作站。決策對象是日用互動、開發工具與工作期間的資源共存。影音與本地推理另設工作負載。

施工順序、交付物與停止條件見[隔離驗證計畫](../planning/F8-WORKSTATION-VALIDATION-PLAN-20261127.md)。

## 決策摘要

**保留 Fast9+09c。下一筆工程預算優先給 Hybrid 的資料邊界、資源預算及同版本驗收。** 對大量掃描、雜湊及部分唯讀 Git，已有值得保留的工具級收益；對 CPU JSON、短 CLI、多客戶端、LLM 端到端回合，證據支持不同的路由。Fast10 只批准熱點歸因，暫無足以承擔換版成本的候選。維持 Gate A 與 GL/VK 上屏暫停。影音有實際播放或轉碼需求時先於 NPU，兩者均不進桌面關鍵路徑。

### 證據與版本

| 核對對象 | 本輪所見 | 可支持的判斷 |
|---|---|---|
| Fast9 | 現役 `out8/` 對凍結清單 5/5，tracer SHA-256 `4a6bc67723d9517771ea602e61caa98a4ac7cb7cf75f932d85fa1a5038ae7660`。本輪讀取程序的實際 tracer 經 /proc/PID/exe 驗得相同完整雜湊；Stable X1 socket 身份與同日驗收紀錄相符。 | 檔案身份本輪重驗。514/514 批、1,805.76 秒、Vulkan 7/7 是已記錄的 09c 驗收。09b→09c 中位 +0.21%，rAF p95 同為 16.7 ms。 |
| GitHub | main `40edf9127968a4f7a768cdebbf19015f4742a0f4`；PR #53 OPEN，候選 `abe9fefdac4dfb61fb63493010d6fbb1d350a7f2`。該 SHA 的 pull_request CI 實跑 Hybrid、敏感內容、凍結證據三個步驟。 | 7.3 已合併。7.4 候選 PRoot/Native 各 25/25 為既有隔離紀錄。7.5 待驗。 |
| 實際工具副本 | 對 policy、relay、daemon、tools 四檔逐檔 SHA-256。工作站 `scripts/` 與 Termux `build/proot-fast/tools/hybrid2/` 互相相同，**四檔均不同於 PR HEAD**。例如 policy 為 `3cb8e9ff99b9…`，PR 是 `abf63d766695…`。 | 從預設路徑啟動不能當成驗證候選。這是檔案身份的差異，沒有據此推定正在運行哪份 daemon。 |
| 試算表（原審快照） | 讀取當時六張表；總進度第 8–50 列 43 項、外部研究第 5–73 列 69 項、深度裁決第 5–38 列 34 項、候選索引 1,046 資料列。 | 32 項「已部署＋已驗證」合併兩種狀態。索引中 997 筆屬未確認 parent 的 fork 搜尋結果。原審獨立裁決的分母是 34；雲端增補見第二節。 |
| 原始資料 | 7.3 公開 ABBA JSON 的 SHA-256 `6f495bb8fcbf41d640638fb4a6328d8e4351c286669ed453ba12387dc7dbfa34` 與清單相符；重算 15 種單路工作負載 × 10 對的中位倍率與配對結果。另查 Stage 5 convergence、6.2 判決、GPU 驗收、PR 安全實作及外部原始檔。 | 150 對的工具結果摘要全部相符。這是重算舊原始資料。本輪沒有新增裝置跑分、功耗、熱態或攻防測試。 |

工作表《深度研究｜移植裁決》的 R01–R34 及對應原始來源列於第二節。部分 Stage 5 逐步量測檔只保存在工作站，公開連結指向倉庫內的 Phase 3 結案報告。

資料入口與版本證據：[主倉庫](https://github.com/waydefu/GPU)、[Fast9 實機驗收](../evidence/session/proot/FAST9-09C-LIVE-QUALIFICATION-20261127.md)、[7.3 原始樣本](../evidence/session/proot/stage7-3-runs-20261127/stage7-3-abba.public.json)、[PR #53](https://github.com/waydefu/GPU/pull/53)、[該 SHA 的 CI](https://github.com/waydefu/GPU/actions/runs/45988222601)。

## 一、架構與瓶頸

### Fast9 與 Fast10

Fast9 把可安全略過的處理移出 tracer 熱路徑。03/04 已做 stat/statx enter-time；07 在 AArch64 BPF 過濾 ioctl，保留需轉譯的 ioctl；08 減少 GETEVENTMSG 與暫存器重讀；09 移除 close 停點並處理 FD 狀態；09c 用 socket inode 校正 FD 重用。auto-shard 解決部分 GUI/terminal 共用單一 tracer 的競爭；多出 tracer、常駐 daemon 與啟動成本，管線、helper 與互動式程式的語意需維持。再做 stat shim 的增量只能來自**消除仍存在的 stop**，或降低仍需轉譯的成本。不能再計入上述補丁已省的時間。[Fast9 patch 系列](https://github.com/waydefu/GPU/tree/40edf9127968a4f7a768cdebbf19015f4742a0f4/core-src/f8-proot-fast/patches)、[逐補丁歸因](../evidence/session/proot/STAGE5-ISOLATED-20261126.md)。

Fast10 已有反證。9 對樣本中，PID hash、talloc-only、合併版對 Fast9 的 mp_storm 中位差為 +1.4%、−2.4%、−0.7%，各 p=0.51；Electron inner 三版均較慢。這支持停止這三個候選。另一類 stat-heavy 任務仍有研究價值。用同一工作負載的可消除串行牆鐘比例 f、局部加速 s、額外時間 h/T 建模，總倍率為 1/(1−f+f/s+h/T)。例如假設 s=2 且 h=0，須有至少 20% 牆鐘落在該段，總牆鐘才會下降 10%。多核 tracer CPU 秒、GPU busy、handler 時間都不能直接代入 f。[Fast9/10 配對結果](../evidence/session/proot/STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md)。

### Hybrid 的收益與成本

| 7.3 歷史同機工作 | PRoot 常駐 → 原生常駐，牆鐘中位 | 倍率 | 解讀 |
|---|---:|---:|---|
| 4,469 檔、51.35 MiB 全樹雜湊 | 1,876.79 → 327.07 ms | 5.738× | 大量檔案系統操作最值得分流；`rg --files` 只列名且有忽略規則。 |
| 固定文字，2,280 個 C/H 檔 | 1,494.83 → 592.62 ms | 2.522× | 直接 PRoot `rg` 的獨立 CLI 對照是 596.00 ms。若呼叫者本來就使用 rg，節省牆鐘的空間小得多。 |
| Git grep／log --stat／ls-files | 54.25→14.23／399.09→199.58／11.46→9.91 ms | 3.814／2.000／1.156× | 小任務只有 1.55 ms 餘裕，新版每次 Git metadata 驗證都可能改變排序。 |
| 六步工具序列 | 3,760.51 → 1,370.87 ms | 2.743× | 觀測峰值總 PSS 37.1→75.9 MiB。這六步不含認證、推理等待及 GUI。 |
| 9.44 MiB JSON | 150.80 → 225.29 ms | 0.669× | PRoot tracer CPU 約 1.1 ms，單靠省掉 tracing 幾乎無法縮短該段。 |
| 四客戶端交錯混合工作 | 4,557.82 → 7,495.55 ms | 0.608× | 0/5 勝，雙尾 p=0.0625；峰值總 PSS 86.46→139.55 MiB。證據支持保留分流，無法定量歸因給單一 GIL。 |

這些是 7.3 的 A1 對 B。單路 ABBA 驗證的是解析後的 payload 經 canonical digest 相符，四路程式確認呼叫成功、丟棄結果，不具有同級逐結果比對。牆鐘亦包含客戶端解析及在單路試驗計算摘要的成本。PSS 採樣可漏短命子程序，讀取失敗的 PID 在加總中被略過。四路輪轉含 Git 子程序、雜湊、I/O、Python 與不同版本 runtime，缺同 binary、固定路由、固定並行模型的因果對照。正式宣稱應限於觀察到的特定工作。若工具原佔整個 AI 回合 20%，即使該部分達 2.743×，其餘不變，整回合理論上約 1.15×，尚未扣冷啟動。該 20% 是敏感度範例。[基準實作](https://github.com/waydefu/GPU/blob/40edf9127968a4f7a768cdebbf19015f4742a0f4/scripts/stage7_3_bench.py#L576-L625)、[四客戶端序列](https://github.com/waydefu/GPU/blob/40edf9127968a4f7a768cdebbf19015f4742a0f4/scripts/stage7_3_bench.py#L814-L865)、[CLI 與客戶端驗收](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/evidence/session/proot/STAGE7-4-ISOLATED-PILOT-20261127.md)。

Stage 5 的重型掃描已勘誤為 1.89×，與 7.3 的 5.738× 對應不同測試。兩者各自保留原對照。[Stage 5 數字勘誤](../evidence/session/proot/ERRATUM-STAGE6-HYBRID-SPEEDUP-20261127.md)。

歷史冷拉原生 daemon 中位 1.125 秒。忽略其他成本，在當時的暖態差值下，一次重型全樹掃描可攤回；每次只省 1.55 ms 的 ls-files 則約需 726 次。這是情境估算；新的 policy、客戶端啟動及閒置存活率均會改變轉折點。更早的 Stage 5 逐命令橋接已用 SCM_RIGHTS 交接 stdio，仍出現 trivial jq 0.62×、zstd/jq 0.47×。優先改變一次請求的工作量，避免為每條短 CLI 新增一次跨程序往返。[Stage 5 原生橋接 A/B](../evidence/session/proot/STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md)。

### Hybrid 安全、取消與資源治理

1. **已確認的修復。** Daemon worker 在清理路徑釋放全域名額，啟動失敗亦歸還；取消時用 request key 管理狀態。pack 及 loose fan-out／直屬物件的靜態 symlink 已列入檢查與回歸。UDS peer UID、0700/0600、子程序環境與 Git 命令 allowlist 能減少誤用。Daemon 全域執行上限預設 16、連線上限 32；relay 本地上限預設 8，作用域不同。八個獨立 relay 的本地工作不共用這 16 個名額。[daemon](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_daemon.py#L116-L198)、[pack 與 loose 測試](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/test_f8_hybrid2.py#L259-L310)。
2. **路徑信任仍須裁決。** 預設映射到整個 `/root/projects`，而同 UID 的客戶端共享宿主身份。預檢後由 Git 自行開檔，不能保證觀察與使用的是同一棵樹；對直接讀取，`O_NOFOLLOW` 保護最後一段，無法鎖定全部祖先。願意接受同 UID、受信任且穩定的 checkout，可採明確的最小映射；必須讀取不受信任或同時被修改的 repo，則應拒絕該路由，或另設可證明的穩定快照／隔離邊界。對自有讀檔可評估 dirfd 與核心支援的受限解析；它不會自動約束另一個 Git 程序。回退端須服從同等策略。[policy](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_policy.py#L535-L652)、[openat2 語意](https://man7.org/linux/man-pages/man2/openat2.2.html)。
3. **資源上限尚有兩個具體缺口。** 選擇性 relay 將 UDS 資料追加至 `uds_buf`，在完整行出現時才取出。此分支未對未完成 frame 的累積長度設硬上限；stdout 水位不能代替入站 frame 限制。Daemon 在建立 client thread 後才檢查 session 數，故 `max_clients` 約束登記成功的 session，不能當作在途 thread 的硬上限。這是本輪原始碼判定，未量化 PSS 損害。建議把 framing 及連線准入提前，對合法滿載仍提供可辨識的拒絕與回收。[relay 接收分支](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_relay.py#L526-L542)、[daemon 准入順序](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_daemon.py#L480-L505)。
4. **R09 的 256 MiB 只能當容量情境。** raw relay 雙向各 8 MiB、daemon session 輸出 16 MiB，8×(8+8+16)=256 MiB。這不含 replay buffer、選擇性 relay 的拆幀與本地佇列、每子程序 stdout/stderr 2 MiB/256 KiB、JSON 物件、執行緒、kernel socket buffer。記憶體配置、RSS、總 PSS、Private_Dirty、SwapPss 是不同量。應對每個模式計入在途 bytes、等待工作與總裝置負載，為單一 client 保留公平性；把單次突增與清空後漂移分開驗收。[raw relay](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_relay.py#L604-L627)、[子程序監督](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_tools.py#L570-L644)。
5. **Git 安全修補改變了性能模型。** `validate_git_ro` 每次執行 `git_cfg_scan`，枚舉 pack 及 loose fan-out 直屬目錄項，成本隨物件目錄項數增長；該段沒有傳入 RequestContext，工作量大時取消反應時間亦待測。小 repo 的 25/25 只支持已測語意。應將小型/大型、packed/loose 的 policy 時間與 Git 本體分列。禁止以未驗證路徑或可變 repo 的跨請求快取省略檢查。[檢查迴圈](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_policy.py#L597-L631)、[實際 Git 工具入口](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_tools.py#L700-L713)。

### GPU、影音、運算與宿主

- **顯示。** 應用程式 OpenGL 經 Zink→Turnip→KGSL 與原生 Vulkan 均可使用 Adreno 840。XFCE 2D、小 pixmap、X server present、Chromium WebGPU 是不同交付點。歷史 1080p 五對 A/B 已有 Mesa 27 native Freedreno 成功記錄；該建置的 Zink GL 測項多約 62 MiB PSS，WebGL2 的 WebGL renderer 有硬體，測得的 WebGPU adapter 為 SwiftShader。不能把這個 PSS 差一律歸於 Mesa 版本，該包同時導入 LLVM 相依。[Mesa 本機對照](../evidence/session/proot/STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md)、[Mesa Freedreno](https://docs.mesa3d.org/drivers/freedreno.html)。
- **所有權與同步。** 本機已測 X3 的 Android EGL/GLES 匯入路徑不接受所需 client dma-buf；Vulkan 可作 buffer copy。AHardwareBuffer 能分享 handle，仍需相容的格式、usage、stride/modifier、生命週期及 acquire/release fence。DMA_BUF_IOCTL_SYNC 管 CPU 存取一致性；producer 完成、consumer 可用及 buffer 可重用須各有順序保證。既有 EXA wait 的 timeout 走 fatal；把 timeout 當完成會改變正確性。60 fps、1200×2464 將整個 copy 歸零的估算上限約 0.05–0.11 核；實際 Vulkan copy 還需 GPU 約 1.19 ms/frame。小 op、不同解析度與輸入延遲需分開。歷史約 89% pixmap ≤64×64、停 telemetry 已省約 0.18 核，現無重開依據。[X3 原始裁決](../evidence/session/gl/X3-DIRECT-FEAS-RESULT.md)、[核心同步文件](https://www.kernel.org/doc/html/latest/driver-api/dma-buf.html)、[AHardwareBuffer](https://developer.android.com/ndk/reference/group/a-hardware-buffer)、[EXA wait 核心契約](https://github.com/waydefu/GPU/blob/40edf9127968a4f7a768cdebbf19015f4742a0f4/core-src/lorieGpuCopyWaitForCompositeOrFatal.c)。
- **影音。** MediaCodec 是值得獨立評估的專用硬體。從 bitstream 解碼到可顯示表面，途中可能有色域轉換、memfd 傳輸、stride 重排與再上傳。播放輸出若可直交 Surface，與需要 CPU 可讀 NV12 的轉碼或分析是兩個方案。Termux:VA 的 8 槽 SHM 透過 FD 傳遞，失敗可退 inline；測試必須辨認此次實際 codec 名、硬體屬性、profile、Surface/bytebuffer 及 SHM/inline。F8 的指定組合目前沒有本輪可信的耗電或畫質數字。[MediaCodec](https://developer.android.com/reference/android/media/MediaCodec)、[硬體識別](https://developer.android.com/reference/android/media/MediaCodecInfo)、[Termux:VA 協定](https://github.com/lfdevs/termux-va/blob/main/doc/protocol.md#L87-L113)。
- **GPU/NPU 運算。** OpenCL 上游列出 A840，HTP 後端有 v81 等建置與 operator 路由；裝置、ABI、vendor linker namespace、FastRPC 和 SELinux 決定 Termux app UID 真正能使用多少。模型權重、KV cache、host staging 及 offload 分界可佔共享 DRAM；多搬一次中間 tensor 或退回 CPU 就可能抵銷局部 kernel 速度。推理的 prefill、decode、首 token 延遲、桌面卡頓、持續功耗各自驗收。純文字掃描、一般 Git、XFCE 合成缺乏交給 NPU 的理由。[OpenCL backend](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/OPENCL.md)、[Snapdragon backend](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/snapdragon/README.md)。
- **宿主。** Stage 6 電源模式前 30 秒 +6.39%／+6.45%，90–180 秒兩次越過專案 CPU 85°C 門檻，其中一次大核降至 2.23 GHz。均衡為基準。Antigravity 547.6/711.9 MB UID PSS，4→2 任務以 +43.4% 牆鐘換 −39.5% 峰值 PSS；512 MB V8 heap cap 已有 OOM。應先調可並行的工作量、閒置 daemon 與冷啟動策略，保持 Android 前背景生命週期可重連；不建議固定大核、調 governor、調 Phantom 或擴全域 heap。PSI/zram 詳情在 app UID 的權限缺口應保留 null。RSS 加總有共享頁重複計數；整機 pgmajfault 含背景程序。CPU 時間下降也無法單獨推算電池續航。[Stage 6 熱態](../evidence/session/proot/STAGE6-2-POWER-MODE-RESULT-20261127.md)、[PSS 與 OOM](../evidence/session/proot/STAGE6-3-4-CLOSURE-20261127.md)、[Android 記憶體管理](https://developer.android.com/topic/performance/memory-management)。

## 二、原審 R01–R34 與雲端增補 R35–R40

GO 表示已有理由投入指定的工作；CONDITIONAL GO 僅限表列前提的隔離試驗；HOLD 要等具體需求或先決證據；NO-GO 停止表列方案。代號沿用原表，維持原分母。「源」指作者原始實作、文件或具體 PR。表中的收益數字僅在標出的載具內成立。

| ID／原表領域 | 獨立裁決 | 判斷、證據與修正 |
|---|---|---|
| R01 Fast10 · syscall 熱點 | GO | 沿用 Pons 0002 的修正版，按 tracer/PID 分攤 stop。它在 CURRENT 暫存器組取樣，非攔截事件不計；計數關閉後才報牆鐘。先找已分流後仍慢的 import、git、du；DroidDeck 的 ADB shell 時間不能作 F8 門檻。 [源](https://github.com/Droid-Deck/DroidDeck/blob/main/docs/development/proot-performance.md) |
| R02 Fast10 · NeoPRoot stat shim | CONDITIONAL GO | 下調「受控移植」為 ABI 與回退契約先行。NeoPRoot 改過濾規則，preload 重做 bind 與 fake_id0，L2S 用 sentinel 轉回通知。只搬 shim.c 不成立，不能讓靜態 ELF／直接 syscall 喪失原語意。作者 du 33.3→14.4 s，編譯 18.2→18.3 s；只對確知可攔的動態程式、唯讀絕對路徑立案。 [源](https://github.com/Raymer8639/neoproot/blob/master/stat-shim/shim.c#L1-L27) |
| R03 Fast10 · 相對路徑與 cwd | HOLD | 絕對路徑通過後，再獨立評 cwd。chdir/fchdir、共享 fs 狀態、rename、fork/exec、dirfd 與相對路徑需同時與原 Fast9 比對；漏攔一個變更點即保留 tracer。cwd cache 只省可安全重用的翻譯。 [源](https://github.com/Raymer8639/neoproot/blob/master/stat-shim/shim.c#L455-L535) |
| R04 Fast10 · DroidDeck fastpath | HOLD | DroidDeck fastpath 包含固定映射、stub 及 RW→RX、ABI/FEX 守衛；與 Fast9 的 BPF/使用者態路徑處理重疊。先證明 app UID 可用、未攔系統呼叫仍正確；不批准整套注入。狹窄 libc 路徑勝出後才可能輪到它。 [源](https://github.com/Droid-Deck/DroidDeck/blob/main/tools/proot/fastpath/fastpath.c#L224-L250) |
| R05 Fast10 · 目錄 FD cache | HOLD | 64×2×4096 + 256×4096 + 256×512 = 1.625 MiB/程序，是三組陣列容量估算。新增 FD、失效成本及多程序 Private_Dirty 都需量；fork 後 COW、dup/close/reuse、rename、跨 bind 先過，再談命中率。 [源](https://github.com/Droid-Deck/DroidDeck/blob/main/tools/proot/fastpath/fastpath.c#L420-L566) |
| R06 Fast10 · 長 UDS、FEX | GO（相容門檻） | 長 UDS 有 sockaddr_un 長度限制，外部 #839 是 FEXServer 相容性證據。冷啟、抽象/檔名 socket、拒絕與清理應有對照。FEX32 的 SIGILL 風險限對應 ABI；不以修正相容性折成加速。 [源](https://github.com/Droid-Deck/DroidDeck/blob/main/tools/proot/fastpath/fastpath.c#L1710-L1775) |
| R07 Fast10 · USER_NOTIF vs ptrace | NO-GO（全面替換） | USER_NOTIF 仍有喚醒、跨執行緒/核心、指標複製與回覆成本。外部同核和未綁核排序不同；不能以綁同核微測替日用下結論。僅當 R02 特定回退通道需要時保留研究。 [源](https://github.com/Droid-Deck/DroidDeck/blob/main/docs/development/proot-performance.md) |
| R08 Hybrid 7.4/7.5 · 路徑策略 | GO（收斂策略）；HOLD 上線 | pack/loose 修補及全域 worker 名額已有獨立回歸。預掃之後交給 Git 的信任邊界、同 UID、映射過寬與本地 fallback 等價性仍須決策。接受可信資料的操作範圍須原文揭露；對無法約束的倉庫拒絕。 [源](https://github.com/torvalds/linux/blob/master/Documentation/userspace-api/seccomp_filter.rst) |
| R09 Hybrid 7.5 · 資源上限與背壓 | GO（列為 7.5 首關） | 把 raw、選擇性、本地 fallback 拆開核算。未完成 UDS frame 上限及 thread 前置准入是具體缺口；全域 worker 數無法界定所有 relay 的 bytes 或 Android 總 PSS。高水位、排空後漂移、FD、孤兒分別驗。 [源](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/evidence/session/proot/STAGE7-4-ISOLATED-PILOT-20261127.md) |
| R10 Mesa 27 · native GL vs Zink | HOLD；NO-GO 該版全域升級 | 補入已有 F8 本機五對 Mesa 26/27 與原生 Freedreno 測試。Zink GL 約 +62 MiB PSS、無重複顯著牆鐘改善；外機 glmark2 與同源轉載只算一條線索。僅新實際應用與不同打包成本可提出例外。 [源](https://github.com/lfdevs/mesa-for-android-container/blob/adreno-main/.github/README.md#L140-L153) |
| R11 Mesa 27 · Present wait fence | GO（保留同步）；NO-GO 全域關閉 | 上游 #96 與 #111 有明確呈現正確性及回歸脈絡。等待可能揭露既有 producer 延遲；去掉等待可讓提交率升高卻產生錯幀。用實際呈現、撕裂、fence 生命週期裁決，A830 外部退化不能套 F8。 [源](https://github.com/lfdevs/mesa-for-android-container/pull/96) |
| R12 GPU · KGSL surfaceless | HOLD 新顯示工程 | surfaceless EGL 選載 KGSL 可證明離屏入口；本機已有 native GLES 及 Turnip 工作。要證明上屏還缺 WSI/import、modifier、acquire/release 及可見幀驗收；單純讓 renderer 字串改變無新增收益證據。 [源](https://github.com/lfdevs/mesa-for-android-container/blob/adreno-main/src/egl/drivers/dri2/platform_surfaceless.c#L381-L414) |
| R13 GPU · 2D / Wayland / DMA-BUF | NO-GO（日常 2D 重開） | Wayland compositor 能改 producer/consumer 拓撲，但更換協定本身無法消掉格式轉換、複製、同步、輸入整合。現行 XFCE 的小 pixmap 分布及 X3 拷貝量支持維持暫停；外接高解析是新 workload。 [源](https://github.com/lfdevs/anland-termux/blob/main/scripts/startplasma-anland.sh) |
| R14 Hybrid 3.0 · 原生 glibc | CONDITIONAL GO | 按應用挑原生 bionic CLI，遇到實際 glibc-only 相依才選獨立 loader/prefix。驗 PT_INTERP、dlopen、NSS/DNS/TLS、subprocess、socket、檔案視圖與更新。外機 Steam menu 的 tracer 佔比不能推桌面 FPS。 [源](https://github.com/huntergdavis/termux-glibc-compat/blob/main/docs/BASELINE.md) |
| R15 Hybrid 3.0 · 原生 Node/CLI | CONDITIONAL GO | 只挑長鏈、高頻、無額外憑證遷移的 Node/CLI。固定 node、native addon ABI、shebang、子程序和版本；比完整工作與首個有效結果。Stage 5 的短 CLI 有明確負收益，故不同意全域 wrapper。 [源](https://github.com/dbgid/claude-code-native-termux/blob/main/README.md) |
| R16 Runtime · /etc redirect | HOLD | /etc redirect 分 bionic interposition、靜態 Go 及 musl 等途徑；作者有 ptrace/SIGSYS 處理，musl 直發 syscall 亦可繞過 PLT。只有個別程式 DNS/TLS 相容需求才用；禁用須還原原憑證查找語意。 [源](https://github.com/rios0rios0/termux-etc-redirect/blob/main/README.md) |
| R17 Runtime · Proroot / 全替代 | NO-GO | Proroot 缺可審查、可重建且可維護的完整來源；其他假 chroot 不提供 Android kernel namespace 權限。已有可回退 Fast9，沒有替換理由。另將 Sprout 0.6.1 列為已有本機反證，詳後。 [源](https://github.com/Droid-Deck/DroidDeck/blob/main/docs/development/proroot-analysis.md) |
| R18 評估方法 · 公平基準＋回退 | GO（修訂量測定義） | 採固定 SHA、實際 route、輸出 oracle、熱態配對與故障回退。單路 canonical JSON digest 不驗原始 framing；四路現有程式未逐結果比對；小樣本不能估可靠 p99。工具級與真客戶端回合各設終點。 [源](https://github.com/Droid-Deck/DroidDeck/blob/main/docs/development/proot-performance.md) |
| R19 Hybrid · CPython 建置差異 | CONDITIONAL GO | 本機 sysconfig 可核對 3.14 computed-goto=0、3.12=1；readelf 顯示前者連 libpython、Ubuntu 執行檔沒有該 NEEDED。PGO、LTO、dispatch、libc、allocator、版本均可混淆。_json 有 C 熱路徑；tail-call 需合適 Clang/preserve_none，屬替代 dispatch。先同版同 libc 分因素試。 [源](https://docs.python.org/3.14/using/configure.html#performance-options) |
| R20 Hybrid · GIL／工作負載路由 | GO（維持選擇性）；HOLD 增池 | 現有四客戶端是四種工具輪轉，p=0.0625。GIL 是可信解釋之一；排程、版本、I/O 仍同時變動。先比較純 Python／釋放 GIL 的原生工作／Git 子程序，才談 process pool 或 free-threaded。後者要獨立驗擴充 ABI、實際 GIL 狀態及額外 PSS。 [源](https://docs.python.org/3.14/using/configure.html) |
| R21 Hybrid · Git commit-graph／MIDX | HOLD；限自有快照研究 | commit-graph 影響歷史遍歷，MIDX 影響多 pack 物件定位；工作樹 grep 或 untracked 掃描不因有圖就變快。先計 policy 掃描與 subprocess 時間。維護是在 repo 寫索引，只能由另行授權的離線流程做。 [源](https://git-scm.com/docs/git-maintenance) |
| R22 硬體影音 · Termux:VA | CONDITIONAL GO（需求觸發） | 先對一條 FFmpeg 解碼鏈比較軟解與實際硬解；播放再比較 Surface 與需取回像素的路徑。逐 codec/profile 查硬體，AV1 encode 無此橋接支援；瀏覽器 VA build、X11 encode、首幀 stall 各自驗。 [源](https://github.com/lfdevs/termux-va/blob/main/README.md) |
| R23 硬體影音 · memfd slots | GO（媒體驗收前置） | 協定指定 8 槽、NV12 及 stride/height 對齊；1080p 約 23.91 MiB、4K 約 95.63 MiB/會話，另有 4 KiB 控制頁，四捨五入可相同。此為 pool 容量，實際 resident、Codec buffer、GPU、FD 和 inline fallback 另記。 [源](https://github.com/lfdevs/termux-va/blob/main/doc/protocol.md#L87-L113) |
| R24 2D · On DeX glamor GLES | HOLD | On DeX glamor patch 的 client-copy 有 glFinish、DMA_BUF_IOCTL_SYNC 與逐列 memcpy，root 發布也有 glFinish。部份 EXA 能落 GPU 與整條顯示鏈零複製是兩個命題。本機小圖元主導，無新需求不重啟。 [源](https://github.com/PietroCav501/termux_on_dex/blob/v2/x11/patch/termux-x11.patch#L404-L436) |
| R25 2D · glamor A840 正確性 | GO（正確性限制）；HOLD 移植 | 另一個 patch 以 glReadPixels 讀一像素強制完成，並修 row length 等。單像素也可能等待整個 producer；測錯列、alpha、不同 stride、重用、黑屏、p99，而非只讀 FPS。 [源](https://github.com/PietroCav501/termux_on_dex/blob/v2/x11/patch/xserver-glamor.patch#L86-L109) |
| R26 Runtime · On DeX native XFCE／fakechroot | HOLD 整桌面；CONDITIONAL GO 單 app | On DeX 的 Android patched loader/fakechroot 是一套分發架構。動態符號攔截不等於完整 rootfs 語意；外機 20 萬查找 10→0.13 s 不可折算本機啟動。先挑一個 glibc app，子程序、相容與回退皆通過才續。 [源](https://github.com/PietroCav501/termux_on_dex/blob/v2/README.md#L24-L45) |
| R27 GPU · Mesa shader cache | HOLD 至確有編譯卡頓 | shader cache 只幫可重用的編譯工作。以隔離 cache-dir、固定 driver 與 shader corpus，分首用/重用；測 miss/compile、磁碟寫量與 frame-time tail。沒有 stutter 證據就不改全域 cache。 [源](https://docs.mesa3d.org/envvars.html) |
| R28 GPU 運算 · Ollama Android Vulkan | HOLD 安裝器；CONDITIONAL GO 獨立 Vulkan backend | 同型號 Ollama 只證明路線值得看。第三方方案會更新/移除 loader 或 GPU 套件，與基準衝突；用既有合格 ICD 的隔離應用，核對 GPU 實際 offload、fallback 與模型輸出。 [源](https://github.com/josedav29/ollama-vulkan-adreno-support/blob/main/README.md#L188-L274) |
| R29 GPU 運算 · llama.cpp OpenCL | CONDITIONAL GO（推理首選對照） | llama.cpp OpenCL 明列 A840 和多種量化；部分預編譯 kernel 只為 X2，不能全套外推。先驗 app UID 能載入 vendor OpenCL、實際 operator 分派及相同 GGUF；與 CPU、現有 Vulkan 同機比較。 [源](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/OPENCL.md#L46-L84) |
| R30 GPU/NPU · llama.cpp Hexagon | HOLD；僅能力查核 | Hexagon HTP 有 v73/75/79/81 對應庫、FastRPC 共享記憶體和算子回退，後端仍有實驗性。需 stock app UID、允許的 DSP domain、正確 toolchain、模型算子覆蓋；任一不通停止，不改 SELinux。 [源](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/snapdragon/README.md) |
| R31 GPU 運算 · GPU offload 共存 | CONDITIONAL GO（共存實驗） | 外部案例 prefill +23%、decode 下降而 CPU-s 明顯減少，說明優化目標可衝突。以固定模型精度的 pp/tg、TTFT、GUI p95、總 PSS、J/token 比較；工作站使用者應先定可接受的 decode 退化。 [源](https://github.com/ArborPopuli/termux-harness/blob/main/README.md#L14-L36) |
| R32 宿主 · ADPF Thermal／Performance Hint | GO 既有熱態紀律；HOLD 新排程控制 | ADPF 對有能力的 app/session/thread 提示工作時間；不提供跨 app CPU 所有權，Thermal headroom 也不是攝氏溫度。以 Stage 6 均衡作基準，先減同時背景工作；kernel I/O、CPU 總量與 wall 分記。 [源](https://developer.android.com/games/optimize/adpf) |
| R33 GPU 顯示 · 剩餘上屏收益界線 | NO-GO（既有顯示戰線重開） | 本機 60 fps 估算即使消除整段 copy 也只省 0.05–0.11 核；GPU copy 還花 1.19 ms。支持目前場景繼續暫停。EGL 未呈現屬功能缺口；有獨立需求才立項，不能從 GL 離屏分數推論。 [源](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/docs/GPU-PIPELINE-LEVER-INVENTORY-20261127.md) |
| R34 顯示／輸入 · unbuffered dispatch | HOLD | patch 呼叫 unbuffered dispatch，可能改變觸控事件批次與喚醒率。只在可重現的 input-to-photon 瓶頸下量事件→合成→呈現、掉事件及 CPU 成本。無理由替換 Stable APK。 [源](https://github.com/PietroCav501/termux_on_dex/blob/v2/x11/patch/termux-x11-mouse.smali.patch) |

### 雲端版本差異與施工對照

2026-11-27 合併前核對。《深度研究｜移植裁決》目前第 5–44 列有連續的 R01–R40；原審快照為第 5–38 列 R01–R34。第 39–44 列是雲端依 Astra 複審增列的六項；另新增《Astra｜7.3 樣本重算》。以下保留各項證據的版本與驗收缺口。重算 7.3 的 15×10 對單路與 5 對並發樣本，不能替 7.4 候選新增一次裝置驗收。

| 雲端新增 ID | 決策來源與適用範圍 | 對應施工順序及完成證據 |
|---|---|---|
| R35 候選身份 | 既有工作站複審記錄四個副本與候選的差異。雲端更新未重新量測裝置。 | 1：六檔 SHA、程序身份與每請求實際路由一致後才計入樣本。 |
| R36 選擇性 relay 入站 frame | 固定候選的未完成 frame 缺少累積上限，峰值代價待量。 | 2：合法邊界可完成，超限有界拒絕，排空後回收。 |
| R37 daemon 准入 | 候選在登記 session 前已建立 thread，准入期也消耗 FD。 | 2：建立 thread 前預留名額，啟動失敗、拒絕及關閉都歸還。 |
| R38 Git 信任與預檢成本 | 靜態 pack/loose 回歸通過，執行前快照仍有競態；大型 repo 成本未知。 | 3：依信任矩陣決定路由，分列 metadata 預檢與 Git 執行時間。 |
| R39 掃描、配置與序列化 | 7.3 有工具級收益及 PSS 代價。分段歸因與新版實測待做。 | 5：相同輸出下比較配置、峰值 PSS 與尾延遲。 |
| R40 Fast9 殘餘熱點 | 沿用 Fast9+09c 凍結基線與舊 Fast10 反證。 | 6：在仍走 PRoot 的實際操作估可消除時間，再裁決單一 shim。 |

資源預算、Git 三類路由、驗收指令及 GPU 重新立案條件見[施工計畫](../planning/F8-WORKSTATION-VALIDATION-PLAN-20261127.md)。

### 額外更正兩條工作表中的待辦

- 「再確認 Sprout 原始版本」已落後於本機 Phase 2／3 驗收。Sprout 0.6.1 有真 Adreno Vulkan 通過紀錄，同一矩陣的 Node v24 出現 `uv__close` SIGABRT、Chromium 153 headless 逾時。判為 **NO-GO 整工作站替換**；保留成功/失敗組合，不因上游版本或同名專案而抹除歷史。[Phase 2 相容性矩陣](../evidence/session/proot/STAGE5-PHASE2-ACCEPTANCE-20261126.md)、[Phase 3 結案](../evidence/session/proot/STAGE5-PHASE3-CONVERGENCE-ACCEPTANCE-20261126.md)。
- 「7.4 CI 綠即進 7.5」應加上基線身份與信任模型。歷史 benchmark 的 B arm 使用 `--no-fallback`，候選的選擇性路由仍可把 JSON 正常送至本地。重播 7.3 與評估 7.4 應分別明示 all-native／selective、每項實際 route 及 daemon 身份。原 harness 的 OUT_JSON 指向既有 evidence 目錄，直接重跑有覆寫風險。日後使用新隔離輸出目錄並分配唯一 run ID。[benchmark 路徑及 client 參數](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/stage7_3_bench.py#L327-L350)、[7.5 原始 gate](https://github.com/waydefu/GPU/blob/40edf9127968a4f7a768cdebbf19015f4742a0f4/evidence/session/proot/STAGE7-NATIVE-HYBRID-2.0-PLAN-20261127.md#L62-L81)。

其他關鍵核對來源：[DroidDeck 長 UDS issue #839](https://github.com/Droid-Deck/DroidDeck/issues/839)、[Mesa fence 變更 #96](https://github.com/lfdevs/mesa-for-android-container/pull/96)、[A830 回歸 #111](https://github.com/lfdevs/mesa-for-android-container/issues/111)、[Pons 診斷補丁固定提交](https://github.com/tedin7/pons/blob/77369df51d3fc98b19ddb2385ebf6d5b7c620053/tools/proot/0002-syscall-stats.patch)、[XFCE telemetry 關閉的裁決](../evidence/session/xfce-v6/XFCE-NOTEL-01-FREEZE.md)。

## 三、原審提出的施工方向

**把成本歸給真正付費的階段。** 同一請求分出 guest 編解碼、relay 排隊、policy、Git 啟動/執行、回覆排隊、客戶端消費。優先記單調時鐘、進出 bytes、實際 route 和少量直方圖；只在抽樣請求打點。舊版 syscall 計數器曾有 −5.04% 到 +21.84% 的配對波動，X server telemetry 也曾吃掉 0.18 核。用無追蹤配對估計觀測負擔，超過預設噪聲門檻就停用該探針。

**先省掉「結果已經用不到」的計算。** `_fit_json_payload` 先完整 dumps/UTF-8 encode，再二分裁 entries 或 matches，多次重編碼；`_tool_tree_scan` 最多可先保留 50,000 筆 entry，傳輸文字上限僅 1 MiB。`_run_text_search_sync` 對每檔先讀 bytes、解碼，再 splitlines。建議依呼叫目的提供保留原格式的有界結果生成；只要檔數/總量/摘要時避免建立逐檔列表，仍需完整雜湊時仍讀每個 byte。需逐檔清單時保留排序、編碼轉義、truncated 及超長行語意。固定字串使用 rg 須對齊 ignore、binary、Unicode、行長與 errors。先對相同結果測分配次數、峰值 PSS、輸出大小；無證據前不換整個語言或協定。[序列化與裁切](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_tools.py#L214-L258)、[樹掃描與行搜尋](https://github.com/waydefu/GPU/blob/abe9fefdac4dfb61fb63493010d6fbb1d350a7f2/scripts/f8_hybrid2_tools.py#L412-L535)。

**優先消除重複走訪，再評估常駐索引。** 同一份 *明示不可變* 的 checkout 若在一次工具序列內先列舉再搜尋，可共用這一次的已授權列舉，保留順序與每工具輸出；能在單次呼叫分批消費就不需長期 cache。Git HEAD 無法代表未追蹤、dirty、權限變動或工作樹 metadata。可變資料的查詢先維持獨立校驗，不把安全檢查快取當作加速方案。現階段沒有本機可報的加速比。

## 四、投資矩陣

按「正確性是否為前置條件 → 可覆蓋的已測工作 → 峰值記憶體 → 維護負擔」排序。成本低指可在單一工具/載具隔離回退，中指跨 relay、daemon 或多 ABI，高指更換 runtime 或跨驅動。箭頭代表可檢驗的方向；沒有電力計或同熱態對照的方案，一律保留功耗、溫度未知。

| 優先 | 工作與裁決 | 性能／瓶頸與上限 | 記憶體、FD、硬體與熱 | 安全／相容與成本、回退 |
|---|---|---|---|---|
| 1 | 固定執行版本與每請求 route，GO | 消除錯量版本；本身沒有使用者加速承諾 | 少量抽樣 CPU、I/O；關閉觀測量 overhead | 低；獨立 harness／輸出目錄 |
| 2 | 7.5 的 frame、准入、全域資源預算，GO 設計 | 慢讀與並發時保 p95、取消與服務可用性；硬限可能犧牲部分吞吐 | 限制 relay＋daemon 總在途 bytes、thread、FD；分開記 RSS、PSS 高水位/尾端 | 中；原有客戶端對 busy、cancel、EOF 的反應必驗；原生停用可回退 |
| 3 | Git 信任範圍及新 policy 成本，GO | loose 項數增加會吃掉短 Git 命令收益；以 policy/child 分計 | CPU、readdir I/O、取消延遲是主成本；不用 GPU/NPU | 中；對不合前提 repo 拒絕，禁止弱化 guard 換分數 |
| 4 | 同語意的 selective、原生工具與低分配結果，CONDITIONAL GO | tree/hash 有強證據；regex 直接 rg 可能已勝。只省重複走訪、編解碼與程序切換份額 | 目標降低 CPU、短命分配及 PSS；常駐約 19 MiB 底噪仍在。按 session 攤銷 | 低至中；工具可各自停用，完整保留 fallback 與輸出 oracle |
| 5 | Fast9 residual heatmap；絕對 stat shim 分兩關，GO／CONDITIONAL GO | 熱點定出 f 後用 Amdahl；PID hash/talloc 退休 | profiler 有擾動；shim 增每程序映射/私頁、FD cache 另計 | 探針低，shim 高；per-app opt-in、保留原 tracer |
| 6 | 宿主工作併發／I/O 紀律，GO 維持 | 滿記憶體時以延遲換存活；避免同步掃描、索引、模型載入同時競爭 UFS/page cache | 4→2 有 PSS 降幅及 wall 代價；熱、major faults、SwapPss 同看 | 低；按工作調整，維持 balanced |
| 7 | CPython 同版對照，CONDITIONAL GO | dispatch 只影響執行迴圈份額；大量 C _json／I/O 效果另驗 | PGO/LTO 影響 text、編譯資源、冷啟；更多 interpreter 增 PSS/FD | 中；獨立 prefix，C 擴充與 toolchain pin，PRoot Python 保底 |
| 8 | 已識別影音需求的 MediaCodec，CONDITIONAL GO | 持續解碼/轉碼可移走 CPU；frame copy、轉色或等待形成新上限 | 專用 codec、共享 DRAM、每會話 24/96 MiB 級 SHM、FD、熱/功耗待量 | 中；獨立 codec/FFmpeg，退軟解 |
| 9 | 單一長壽 glibc app，CONDITIONAL GO | 可消除 traced syscall，啟動、插件、子程序鏈可能吃回收益 | 多 runtime、DSO、page cache 及常駐私頁；GPU 依原 app | 中高；獨立 loader/prefix，可移除路由；全桌面替換 NO-GO |
| 10 | OpenCL/Vulkan 推理，CONDITIONAL GO；HTP HOLD | 先分 prefill/decode；頻寬受限的 token 生成與批量矩陣乘不同 | GPU/NPU、CPU fallback、KV cache 及共享 DRAM；J/token 與熱降頻未知 | 中高；獨立後端，不更換系統 loader；退 CPU |
| 11 | 桌面 2D、Present 重構、Mesa 全域升版，NO-GO | 現有 XFCE 未分出淨益；整段 X3 copy 的 CPU 節省有明確上限 | GPU copy 約 +1.19 ms/frame；指定 Mesa 包有 GL PSS 退化 | 高；fence/ownership/ABI 及外接 display 風險。保留凍結資產 |

## 五、演進順序與可重現驗收

以下是下一輪**提案**。已存在的 Stage 7.5 數字明確標示；新數值只供預先註冊。所有實驗使用新的隔離目錄與快照。此輪只讀，沒有啟動 7.5、GPU/NPU 或效能實驗。

1. **版本與工作定義。** 每次記二進位和六個 Hybrid 腳本 SHA、repo HEAD/dirty、實際 maps、Git/Python/libc/loader、UID、TracerPid、renderer/codec/backend、電源模式、起始溫度與可用記憶體。固定檔集、輸出語意、大小分層、路由紀錄及總回應數。拒絕把 fallback 當 native，也拒絕把 ADB shell 能力當 app UID 能力。先做 A/A 檢測噪聲。若觀測使 wall 中位改變 >3%（提案），減少抽樣後重新建立基線。
2. **先收斂 7.4 候選，合併另行批准；再做 7.5 隔離異常驗收。** 現有 gate 是至少 1,000 ops、RSS 漂移 ≤10%、FD 回 baseline、子程序與孤兒為零，停機清除 socket/pidfile、原生關閉後回退成功。按 1/2/4/8 個客戶端分層，區分長會話、反覆連線、慢消費、正常半關閉、超時、取消、閒置/喚醒；只用合成、獲授權資料驗證拒絕與正常輸出。量 session/worker 配額、未完成 frame、全域/每客戶端 bytes、FD、RSS、總 PSS、Private_Dirty、SwapPss、可用記憶體。以同一暖機後的 quiescent 時點計漂移；峰值預算需按裝置留給桌面/工具的餘裕事先定。任一授權邊界、資料完整性、取消或回收不合格即停止並保留失敗結果。容量未知時不得核准日用。
3. **在同一候選版比較路由。** A=PRoot resident，B=候選 selective，C=原生直接執行，D=既有最佳 CLI；重播舊 all-native 獨立成 E。每種負載分冷/暖，預先固定至少 20 對實際操作、ABBA/BAAB 平衡，重跑區塊/日期，報 paired delta、區間、p50/p95；p99 用有足夠獨立請求的 soak，再報樣本數及熱態。Git 加入 loose 數量級與多 pack、狀態/歷史/grep；掃描分列名、metadata、全文雜湊；真實客戶端量第一個有效結果及完整任務，等待模型的時間另列。提案採用線為代表工作 wall 至少降 10% 且配對區間支持改善、p95 退化 ≤5%；若主目標是釋放 CPU，預先選 tracer/總 CPU 下降 ≥15% 且 wall/互動不劣。完整多輪或 GUI 未驗，只記工具級通過。
4. **Fast10 及 CPython 僅在歸因成立後施工。** 計數版先校驗 stop 類別與漏報；關閉計數才計時。選發生在殘餘 PRoot 內的 du、匯入、工作樹查詢及低 syscall CPU 控制；保留 cwd/dirfd、bind、L2S、errno、fork/exec、FD reuse 全語意。任一輸出或錯誤不同即停。CPython 固定相同 minor/patch、libc、編譯器、allocator、C 擴充與代表性 profile，依序只改 computed goto、PGO、LTO，tail-call 用適配編譯器對同樣 PGO 控制組。分拆記憶體內 _json、Python 迴圈、檔案 IO、完整 RPC，覆蓋 1/4 client。測試釋放 GIL 與未釋放 GIL 的工作；free-threaded 獨立驗 ABI、單線回歸與記憶體。收益僅有 microbench 或越過熱/記憶體門檻即保留 Fast9/原 Python。[CPython 建置選項](https://docs.python.org/3.14/using/configure.html#performance-options)、[C JSON 實作](https://github.com/python/cpython/blob/3.14/Modules/_json.c)。
5. **媒體與推理依需求並列，顯示保持凍結。** 影音先用同一 1080p60 檔與相同輸出格式，軟/硬各跑持續 30 分鐘才考慮 4K；記實際硬體 codec、首幀、PTS、drop/duplicate、閒置後 FD、pool、PSS、CPU、溫度。有損編碼以相同品質或 bitrate 加畫質指標比較；解碼用相同像素格式、色域與容許誤差的 oracle。若硬體/格式不支援、掉幀或畫質不合即退軟解。推理固定 GGUF SHA、量化、上下文、prompt、batch、採樣設定，比 CPU→OpenCL／Vulkan→能力允許才比 HTP，紀錄實際 offload 比例、fallback、prefill、decode、TTFT、品質、PSS、外部記憶體和桌面 p95。暫定採用線是相同品質下持續吞吐或 J/token 改善 ≥10%、主要互動 p95 不劣 >5%；若無可用電力計或可信能量來源，功耗保持 UNKNOWN。CPU/GPU 溫度與 Android thermal status 分列，沿用已定 CPU 85°C、電池 42°C 保護線及降頻停止原則。沒有可重現實際需求不開硬體線。
6. **發佈邊界。** PR CI、7.5 壓測、客戶端功能、部署批准各自記錄。Hermes 已驗 MCP 生命週期，完整對話 UNKNOWN；Claude Code 實際對話 BLOCKED_NO_AUTH；Codex app-server 的取消 UNSUPPORTED；Desktop/AGY 的 GUI 仍 UNVERIFIED。以上任何一項都不能由 CI 代簽。原生服務停用、每工具回到 PRoot、實驗 prefix 可卸離是必要回退。Stable :1、已封存 Gate A 與 GL/VK 不作試驗目標。

## 六、最優先的五項改進

1. **建立能證明執行版本、實際路由與輸出一致的載具。** 第一個交付物是一份同 SHA 的 A/B 收據；涵蓋並發逐結果比對與量測缺值。這可立即消除舊副本及錯誤路由造成的假綠。
2. **補上 Hybrid 整體資源預算。** 先限制選擇性 relay 的入站 frame，將連線准入前移，逐 session 限額加上跨 relay/daemon 高水位與公平性驗收；以 7.5 的清空、取消及 FD gate 證明可長駐。
3. **為 git_ro 確立受信資料範圍，量出檢查成本。** 分開量 metadata 預掃及 Git 本體；不受信、可變資料必須有可證明的隔離或拒絕路由。此項是上線前置條件，即使個別命令因此回到 PRoot。
4. **對已證明值得分流的工具減少重複分配與資料搬移。** 先以 tree/hash 與 fixed search 測一次性有界結果生成、摘要模式、原生工具對照，保留 digest、排序、截斷與取消語意。以總 PSS 與端到端 wall 決定是否保留。
5. **對仍留在 PRoot 的真實操作做 Fast9 殘餘熱點圖。** 只在可消除的 wall 份額過門檻後，試一個動態程式的絕對 stat 快路徑。若熱點不足，結束 Fast10 這一輪，把工程時間留給應用層。

**最終裁決。** GO 保護現役 Fast9 與完成 Hybrid 驗收工程；CONDITIONAL GO 限於有可量工作負載的原生工具、stat shim、codec 與 GPU 推理；HOLD 全系統 Python／glibc 變更與 Hexagon；NO-GO 舊 Fast10 組合、全域注入、該 Mesa 27 包全域升級、重開日常 2D 與 GL/VK 上屏。沒有測得的全機 FPS、功耗、NPU 收益及真實 LLM 回合改善均保持未知。
