# POCO F8 Ultra GPU 加速與工作站架構橫向整合報告（第 1+2 批共 60 項｜2026-11-26）

> **定位與研究紀律**：本報告整合第一批 PRoot／替代 Runtime 調查（[`EXTERNAL-RUNTIME-PROOT-LANDSCAPE-20261126.md`](EXTERNAL-RUNTIME-PROOT-LANDSCAPE-20261126.md)）與本輪第 36～60 項 GPU 驅動／Chromium／Termux:X11／Wayland／Zero-Copy 專案，對照本機權威 [`HANDOFF.md`](../../../HANDOFF.md) 與 [`X3-DIRECT-FEAS-RESULT.md`](../gl/X3-DIRECT-FEAS-RESULT.md)。
> - 所有外部專案數據僅作外部宣稱或前置證據記錄，**絕不當作 F8 Ultra 實機已完成**。
> - 未修改任何現役檔案、[`src/f8-proot-fast`](../../../src/f8-proot-fast/)、[`src/termux-proot-upstream`](../../../src/termux-proot-upstream/) 或 `com.termux.x11` Stable（`:1`）。
> - Stage-1 預抓快照存放於會話暫存區 ``scratch/gpu-landscape/`` (local sparse snapshot)。

---

## 一、Stage-1 & Stage-2 總清冊（第 36～60 項 + 配套分支）

> Stage-2 狀態標籤嚴格採用：`已完成`｜`已部分完成`｜`可直接使用`｜`可移植`｜`需要重新實作`｜`不相容`｜`尚未驗證`｜`已被實測否定`

| # | 專案 | 分支 / HEAD SHA（日期） | 授權 | Stage-2 狀態 | 核心機制與 F8 Ultra 關鍵證據（簡摘） |
|---|---|---|---|---|---|
| **36** | `watq/gpu-desktop-for-android-container` | `main` `657e3ad9be` (2026-10-27) | `MIT` | **可移植** | `fakepci.c:20-58` 攔 `/proc/bus/pci/devices`；`electron-gpu.sh:96-171` 按 Chromium 版本分檔（≤144 走 KGSL；**≥145 因 `/dev/dri/renderD128` `EACCES` 只能退回 `swsafe` SwiftShader**）；`Mesa 27` 消 GL+KGSL 黑幀（`14/240→0/240`）；`CompareFB 0` 與多 display D-Bus 隔離（Redmi K90 / A830 實測）。 |
| **37** | `lfdevs/mesa-for-android-container` | `adreno-main` `88bc9c3320` (2026-11-22) | `NONE` | **可直接使用** | `README.md:25,140,153` 明列 **Adreno 840** OpenGL / GLES / Turnip Vulkan 全支援（OnePlus 15 PRoot `glmark2=3574`）；Freedreno KGSL 原生 GL + `27.0.0-devel` 預設啟用 `present wait fence`（`b2a59a4f`）；提供 Ubuntu Noble ARM64 `.tar.gz`/`.deb`（`build.yml:252-366`）。未於 F8 實機驗證且 Mesa C diff 未完全 clone。 |
| **38** | `MaterDev/turnip-kgsl-shim` | `main` `d210b66520` (2026-09-19) | `MIT` | **可移植** | `src/shim.c:60-85` 濾掉 `VK_KHR_display` 等 6 個擴充修補無 DRM master 失敗（真實根因、可設 `TURNIP_SHIM_REAL` 用於 glibc）；`shim.c:88-145` 僅對 Dawn 偽裝 SwiftShader ID + `no-dlopen.c` 攔內建 SwiftShader + canvas `putImageData` readback，屬 bionic Termux Chromium 149 專項 hack，**不解 Ubuntu Chromium 145+ `renderD128` `EACCES`**。 |
| **39a** | `termux/termux-x11` PR `#1153` | `OPEN` (`dirty`, `24ce2076fe` 基線) | `GPL-3.0` | **需要重新實作** | Xorg Glamor GLES3 加速（`glamor_support.c`, `copy_fence_fd`）。現與上游 `dirty` 衝突；且 `HANDOFF.md:10`（`XFCE-NOTEL-01`）已證實 2D 桌面 GPU 加速在關閉 telemetry 後與 CPU 打平。 |
| **39b** | `termux/termux-x11` PR `#1095` | `OPEN` (`dirty`) | `GPL-3.0` | **需要重新實作** | 新增私有 DRI3 opcode 200（`fds_from_pixmap` Server→Client 匯出 AHB）；與我方 `X3-DIRECT-FEAS`（Client→Server modifier 1255/1256）方向相反且衝突，不解 Android EGL 不收 dma-buf 問題。 |
| **39c** | `termux/termux-x11` PR `#1178` | `OPEN` (`unstable`, 2026-11-25) | `GPL-3.0` | **可移植** | `+35/-3` 行於 `LorieBuffer_waitFence`（`buffer.c:41-51`）對 `importedFd` 做 `poll(&pfd, 1, 250)`，在 `loriePrepareAccess` 與 `uploadDamagedRows` 前等 GPU dma-buf 寫完，**精準補齊 [`X3-DIRECT-FEAS-RESULT.md:33`](../gl/X3-DIRECT-FEAS-RESULT.md#L33) 所記的缺口**（僅可進 `:3` 實驗）。 |
| **40** | `lfdevs/anland-termux` | `main` `186447add6` (2026-11-16) | `GPL-3.0` | **尚未驗證** | 非 Root `EGL_PLATFORM=surfaceless` + KGSL KWin/Weston/Mutter（`ANLAND_SKIP_IMPLICIT_SYNC_WAIT=1`），`targetSdk=37`。缺 `display_consumer.c` 實作未抓、僅預包 Debian 13/Ubuntu 26.04（非 24.04）、未驗 Adreno 840 與外接 3440×1440。 |
| **41** | `lfdevs/xwayland` | `debian-unstable` `0c42ac5a99` (2026-10-08) | `NOASSERTION` | **可移植** | `debian/patches/0001`–`0007` 實作 KGSL surfaceless glamor + `eglExportDMABUFImageMESA` + `/dev/kgsl-3d0` DRI3 + Present Copy（`check_flip` 強制 `FALSE`）+ fence lifetime 修復；明確關閉 `wp_linux_drm_syncobj_v1`。需搭配支援 exporter 的 `#37` Mesa。 |
| **42** | `HomuHomu833/termux-wayland` | `master` `cf890ba599` (2026-10-29) | `GPL-3.0` | **尚未驗證** | `README.md:164` 明言**尚未於手機實機測試**。`server.c:348-356` 檢查 `/dev/dri/renderD128` 才開 `linux-dmabuf`；F8 Android EGL 失敗後永久關掉 `dmabuf_import`（`render.c:440`）退回 `vkcopy.c`（同 `X3` GPU copy 開銷）或 CPU `wl_shm`；單螢幕且缺 `syncobj`。 |
| **43** | `piperella/piperella-wayland-compositor` | `main` `df06380a7c` (2026-08-07) | `GPL-3.0` | **可移植** | C++20/GLES3/Choreographer + `syncobj.cpp`（但需 `/dev/dri/*` `DRM_CAP_SYNCOBJ`）。無 XWayland、`import_dmabuf` 在 F8 Android EGL 失敗、`import_ahwb` 無 fd→AHB 轉換器、單 `SurfaceView`、`wl_shm` 走 CPU R↔B 交換迴圈。僅 VSync/`syncobj` 寫法可參考。 |
| **44** | `Shelnutt2/wldroid` | `main` `9560e767bb` (2026-05-22) | `MIT` | **可移植** | `wlroots 0.19.2` + XWayland + VirGL AHB registry；但 `android_output.c` 終端以 **`AHardwareBuffer_lock` + CPU `memcpy` 寫入 `ANativeWindow`**（`compositor-architecture.md:74-78`，非端到端零複製），`TURNIP_DIRECT` 遇 F8 EGL 牆、無 `syncobj`、無外接螢幕。 |
| **45** | `localdesktop/localdesktop.github.io` | `main` `ac6295674c` (2026-11-22) | `GPL-3.0` | **尚未驗證** | Rust `NativeActivity` + `winit` + `Smithay` + Arch PRoot，具備 `ExternalDisplay.java` / `external_display.rs`（`_tree.txt:1868-1869`）外接螢幕架構。但 `hardware_buffer.rs` 與 `kopper` patch 未預抓，Zero-Copy 真偽與 A840 相容性未知。 |
| **46 / 46.5** | `kde-yyds` & `afeimod/android-vulkan-bridge` | `main` `0018873fff` (2026-01-09) | `NONE` | **不相容** | 兩者完全同 commit（#46 已 ARCHIVED）。硬性要求 **Root** 掛 `/system`/`/vendor`/`/apex` 與替換 `libc.so`，主攻 Mali GPU，且 Chrome 開合成器必當。 |
| **47** | `fish4terrisa-MSDSM/vulkan-wsi-layer` | `main` `3eeca40148` (2026-06-15) | `NOASSERTION` | **不相容** | `README.md:21,103-122` 明言**不支援 Turnip**、要求 Qualcomm 專有 glibc 驅動與 `/dev/dma_heap/system`、會導致 Termux:X11 segfault。 |
| **48** | `RandomCoderOrg/mesa-gfxstream` | `tensor-g1` `4a03b179a9` (2026-08-17) | `NONE` | **不相容** | 實為 Google Tensor G1 (Mali-G78 `/dev/mali0`) Panfork/Mali HAL 橋接；且 `README.md:48-49` 自述 Termux:X11 終端仍是 server-side copy。 |
| **49** | `wmww/libhybris` (`tawc` fork) | `master` `ac17d9e228` (2026-10-13) | `NOASSERTION` | **可移植** | **目前唯一完整驗證免 Root 原廠 Android 16 + PRoot 的 True Zero-Copy 橋接層**：17 個 patch 解 TLS/CFI + Gralloc4 AHB v3 + Vulkan `sync_wait` + `android_wlegl` + X11 `TAWC-DRI`。限制：僅有 Android EGL/GLES & Vulkan（無桌面 GL），且須搭配合成端與驗證 HyperOS static TLS 上限。 |
| **50** | `mekhontsev/magicdesk` | `main` `4277e9fd76` (2026-11-24) | `GPL-3.0` | **尚未驗證** | Batch 1 已有 `Shroot`。Display 層明確支援 **外接螢幕 1080p60 / 虛擬螢幕 / `QualcommDisplayModeBackend` / Shizuku 多視窗**；但同時含 `dmabuf.c` 與 `readback.c`（未預抓檢視），F8 A840 與 3440×1440 未驗證。 |
| **51** | `DroidNative/DroidNativeApp` | `main` `fa591010d6` (2026-10-24) | `GPL-3.0` | **可移植** | C99 Wayland + `dn-xwm` + `TextureView`（Buffer **複製進 GLES 紋理**、Mesa WSI CPU 等同步）。極具價值的 PRoot 相容技巧：`libdn-appenv`、綁空 `/proc/bus/pci`、Fcitx5 `text-input-v1` 修 Chromium 密碼欄、`MOZ_SHM_NO_SEALS=1`。 |
| **52** | `Droid-Deck/Drivers` | `main` `87afeda858` (2026-11-26) | `GPL-3.0` | **可移植** | 追隨上游 `mesa/mesa` `main` 雙編 Ubuntu 24.04 glibc + Android bionic Turnip，含清晰可審計 `patches/linux/0001..0005`（A8xx `cube_coord_hang_quirk`, `SP_*_BINDLESS_INVALIDATE`, `KGSL_MEMFLAGS_VBO` IB alias）。**僅建 Turnip（無 KGSL Gallium GL）**，未實測 F8。 |
| **53** | `faux123/turnip-faux123-driver` | `main` `27953a99af` (2026-11-05) | `NOASSERTION` | **不相容** | 僅產出 Android bionic AdrenoTools `.adpkg.zip`（且補丁在私有伴隨庫），不可用於 Ubuntu 24.04 glibc PRoot（Linux 版另在 `turnip-faux123-droiddeck`）。 |
| **54 / 54.5** | `whitebelyash/mesa-unified` & `AdrenoToolsDrivers` | `8a394162c7` / `258fc21943` | `NONE` / `GPL-3.0` | **已部分完成 / 不相容** | `#54` 為早期 Gen8 Turnip 分支（A8xx 主體已上游化並被 `#37`/`#52` 超越）；`#54.5` 為 Android bionic AdrenoTools `.adpkg.zip` CI 打包器。 |
| **55** | `Azkali/phosh-termux-gpu` | `main` `35519672cf` (2026-06-03) | `NOASSERTION` | **已被實測否定** | 強迫應用程式走 `GSK_RENDERER=cairo` 純 CPU 繪圖，再做全幀 `vkCmdCopyImageToBuffer` + `memcpy` 經 XShm 送 Termux:X11，Adreno 830 冷啟動 ~1/4 當機，對 3440×1440 完全不可行。 |
| **56** | `J-x-Z/termux-wayland` | `master` `e917fed1d7` (2026-09-24) | `GPL-3.0` | **需要重新實作** | Alpha；公開 Termux 僅走 TCP inline pixels，即使搭未上游化 Plugin Broker 傳 linear dma-buf fd 仍走 **100% CPU `mmap` 軟體合成**、無 fence、無 damage、不支援 UBWC。 |
| **57** | `yanghoeg/usix-termux` | `main` `1b7d6dceff` (2026-11-25) | `MIT` | **可移植** | 可借鏡把 `#37` 隔離裝入 `/opt/termux-xfce-mesa` 與 Termux:X11 `sharedUid`/`/top-app` 經驗；自備 `wayland-anland.md` 亦誠實記錄 Anland Plasma popup 與 A7xx Xwayland abort blocker。 |
| **58** | `sabamdarif/termux-desktop` | `main` `09fcf0cd43` (2026-11-24) | `GPL-3.0` | **可移植** | `docs/hw-acceleration.md` 與 `35265567`/`5b5a68b9` 可參考 `/opt/mesa-freedreno` 升版 `27.0.0-devel` 與移除 `MESA_GL_VERSION_OVERRIDE`；安裝器架構本身不需套用。 |
| **59** | `BlackFireAlex/omarchy-android` | `main` `0f4cee8336` (2026-10-08) | `MIT` | **可直接使用** | **已實機驗證 Adreno 840**（`README.md:29`）跑 Turnip KGSL + Hyprland + XWayland + Chromium ANGLE/Vulkan（需關 sandbox）；但經 Termux Weston `x11-backend.so` 吐回 Termux:X11 XShm（非零複製）、綁 Arch ARM、未驗 3440×1440。 |
| **60** | `Xtr126/wlroots-android-bridge` | `master` `52178bb20b` (2026-01-18) | `GPL-3.0` | **不相容** | 雖採用 `ASurfaceTransaction_setBuffer` 真零複製路線，但硬解讀 Intel GPU `minigbm` 的 `cros_gralloc_handle_t`（`README.md:8,17-20`），與高通 Adreno 840 / Android 16 gralloc 不相容。 |

---

## 二、60 項專案收斂為 12 條技術主線（跨批次完全去重）

> **誠實聲明**：第 1 批清單共 35 項中，已於本會話完成源碼精讀與對照者為 **`#1 termux/proot`、`#2 Sprout`、`#3 LinuxDroid`、`#7 Pons`、`#8 DSH Mobile`、`#9 Cortex`、`#11 Tawc`**；經第 2 批姊妹倉連帶掌握方向者為 **`#4 DroidDeck`（`#52`）、`#10 Shroot`（`#50`）**；其餘 `#5 WinNative`、`#6 NeoPRoot`、`#12`–`#35` 屬第 1 批尚未排入精讀的條目（若需掃描可直接套用三層漏斗 0-token 預篩）。

| 主線 | 歸併專案（去重後核心代表） | 對 F8 Ultra 工作站的核心意義與本機現況 |
|---|---|---|
| **1. PRoot 核心與 syscall 最佳化** | `#1 termux/proot`（至 `0e42875`）、`#3 LinuxDroid`、`#7 Pons`、`#8 DSH Mobile` + 本機 `f8-proot-fast` | 本機 `v5`/`v6`（seccomp enter 代答 `stat`/`fstat`/`statx`）與 `auto-shard` 仍深於上游；**可立刻零風險移植**：上游 `48c903d54`（停攔 `close`）、`4006c630f`（免 `GETEVENTMSG`）、Pons `0002`/`0004`/`0005`（`ioctl` BPF 放行 + `brk` + 統計）、LinuxDroid `0001`/`0009`（O(1) PID hash）、上游 `execve` 批次化與 `-0 -l` `lstat` 重用。 |
| **2. 進程內快速路徑與替代 Runtime** | `#2 Sprout`（`preload` + `user_notify`）、`#11 Tawc` (`tawcroot`)、`#9 Cortex`、`#10 Shroot`（via `#50`）、`#3`/`#7` fastpath | `Sprout` 在同機 **`25102PCBEG`** 上無 ptrace `vkmark` **10.4×**、spawn **5.86×**；`tawcroot` 以 `SECCOMP_RET_TRAP`+IP 白名單理論覆蓋面更全但未驗 Ubuntu/HyperOS A16。`LinuxDroid`/`Pons`/`Cortex` 的 `LD_PRELOAD` 會與 Chromium sandbox 或 `-0` 衝突。 |
| **3. Freedreno / Turnip GPU 驅動** | **`#37 lfdevs/mesa`（主幹）+ `#52 Droid-Deck/Drivers`（A8xx 補丁源）**；去重 `#53`/`#54`/`#54.5`/`#57`/`#58` | `#37` `27.0.0-devel` 已帶 **Adreno 840** + Freedreno KGSL 原生 GL + Turnip + `present wait fence`；`#52` 的 `patches/linux/0001..0005` 追蹤最新 Mesa main 的 A8xx 修正（cube/bindless/IB alias）。`#53`/`#54.5` 僅限 Android bionic。 |
| **4. Chromium / Electron 硬體加速** | **`#36 gpu-desktop` (`fakepci.c`)** + **`#51` (`libdn-appenv`/空 `pci`/Fcitx5)** + `#59` | `#36` 的 `fakepci.c` + 版控啟動參數可解 **Chromium ≤144**；**關鍵硬牆**：Ubuntu 24.04 PRoot 下 **Chromium ≥145 改開 `/dev/dri/renderD128` 撞 SELinux `EACCES` 而退回 `swsafe` SwiftShader**，且全數 PRoot 環境仍需 `--no-sandbox`。 |
| **5. ANGLE / Dawn / WebGL / WebGPU** | **`#38 turnip-kgsl-shim`** + `#36` + `#59` | `#38` Layer 1（過濾 `VK_KHR_display` 等 6 個延伸）修補真實 Mesa/KGSL 無 DRM master 缺陷，可設 `TURNIP_SHIM_REAL` 移入 glibc 供 `wgpu`/ANGLE/Dawn 測試；Layer 2–4（Dawn SwiftShader 偽裝 + canvas readback）為 bionic Termux Chromium 149 專項權宜法，非通用正式方案。 |
| **6. Termux:X11 / Glamor / DRI3** | **`#39` (`#1153`, `#1095`, `#1178`)** + `#41` + 本機 Gate A / Track #3 | PR **`#1178`** 直接修復 `X3-DIRECT-FEAS-RESULT.md:33` 記下的 `LORIEBUFFER_FD` 缺 `poll` sync 缺口；PR `#1153`/`#1095` `dirty` 且對 F8 收益與協定不符；Gate A `XFCE-NOTEL-01` 已證實純 2D GPU 與 CPU 打平。 |
| **7. AHB / DMA-BUF / GPU Copy / Zero Copy** | `#49 wmww/libhybris`、`#42`、`#43`、`#44`、`#55`、`#56`、`#60` + 本機 `X3-DIRECT-FEAS` | **核心物理實證**：Android vendor EGL 不收 `dma-buf`（`HANDOFF.md:11`、`#42`、`#43` 共同印證）。`#44`/`#55`/`#56` 終端皆為 CPU `memcpy`/readback；`#42` 落入與 `X3` 同樣的 `vkcopy`；`#60` 綁 Intel `cros_gralloc_handle_t`；**僅 `#49` `libhybris`（`android_wlegl`/`TAWC-DRI`）走原生 AHB 零複製**。 |
| **8. Wayland / XWayland Compositor** | `#40 Anland` + `#41 lfdevs/xwayland`、`#43`、`#44`、`#45`、`#50`、`#51`、`#59` | `#41` 提供非 Root KGSL surfaceless XWayland，但強制走 Present Copy（無 `syncobj`）。現有 Wayland App 若非未測手機能（`#42`）、只收 single `SurfaceView`（`#42`/`#43`/`#44`），就是綁非 Ubuntu 24.04 發行版（`#40` Debian 13/U26.04、`#45`/`#59` Arch）。 |
| **9. Android 原生 Vulkan / `libhybris`** | **`#49 wmww/libhybris`**（主動維護）、去重 `#46`/`#46.5`/`#47`/`#48` | `#46`/`#47`/`#48` 均因 Root/專有驅動/Mali 而**不相容**；唯 `#49` 跑通非 Root Android 16 + PRoot AHB/Vulkan 橋接，惟無桌面 GL 並需特製 compositor。 |
| **10. CPU / GPU / RAM 調度與多工** | 本機 **`f8-shard` v2 + `shard-daemon.sh` fix 4** + `#51` Phantom Process 警告 + `#57` `sharedUid` | F8 已有最強多行程 PRoot 分流與 fd 衛生保護；外部項目補充了 Android 12+ 32 子行程 Phantom Process 殺手與 `sharedUid`/`/top-app` 排程參考。 |
| **11. 外接螢幕與桌面工作站** | `#36` 雙顯示隔離 + **`#45 localdesktop`** (`ExternalDisplay`) + **`#50 MagicDesk`** (1080p60 / Qualcomm backend) | Termux:X11 已內建外接副屏呈現基礎，且 `#36` 已解雙顯示 D-Bus 腦裂；`#50`/`#45` 提供專用外接觸控板與 Shizuku 視窗架構，但在 **3440×1440@60Hz（~1.19 GB/s）** 尚無任何外部專案提交實機證據，CPU copy 路線將直接爆頻寬。 |
| **12. 效能測試、正確性與安全治理** | `#36` 20px 黑幀測試 + `#2 Sprout` `benchmarks.md` 更正 + `#59`/`#51` 沙盒局限 + 本機 `TEST-MATRIX.md` | 外部一致證實：**所有非 Root PRoot / Preload 環境均須關 Chromium `--no-sandbox`**（`#59`、`#51`、`#36`）；另需防 Chromium ≥145 靜默退回無硬件加速之 SwiftShader（`#36`）。 |

---

## 三、Stage-4 三條工作站路線客觀對比（對照 Stage-7 驗收目標）

> 不預設任何一條路線為贏家；每項皆標出「實證優勢」與「已確認硬風險／待驗證缺口」。

| 評估維度（Stage-7 驗收目標） | **路線 A：現役架構精進**<br>Termux + Ubuntu 24.04 + `f8-proot-fast`（升級 `v9`/`v10`）+ XFCE + Termux:X11（+ `#37`/`#36`/`#38 L1`/`#39-1178`） | **路線 B：新世代 Runtime + 既有顯示**<br>`Sprout`（次選 `tawcroot`）替代 `proot` 引擎 + Ubuntu 24.04 + XFCE + Termux:X11（+ `#37`/`#36`） | **路線 C：原生 GPU Wayland + XWayland**<br>Anland（`#40`+`#41`）或 `termux-wayland`/`wldroid`/`localdesktop`/`MagicDesk` 取代 Termux:X11 |
|---|---|---|---|
| **多 Electron + Playwright + Node/Git/Python** | **最高穩定性**：`f8-shard` v2 專治 Electron/Agent 多核排隊；`apt`、`-0`、`l2s`、D-Bus `SO_PEERCRED` 全熟；移植上游 `close`/`GETEVENTMSG`/Pons `ioctl`/PID hash 可再顯著降 syscall 稅。 | **理論吞吐更高、相容未知**：Node/Git/Python 免 ptrace 極快（`Sprout` `5.86×` spawn）；但 **Ubuntu 24.04 Electron/Chromium 多行程 + Android `RET_KILL` vs `user-notify` 尚未實機驗證**，D-Bus/shm 細節可能踩雷。 | **遷移風險高**：許多合成器為單 `SurfaceView` 設計；多數僅驗證 Arch/Debian13（`#40`/`#45`/`#59`）或需 Shizuku（`#50`）；且各合成器 Chromium 輸入法（密碼欄需 key fallback）、Phantom Process 均需重驗。 |
| **多 AI Agent 併發** | **已實機驗證**：`shard-daemon` fix 4 單 daemon 穩態 + `auto-shard` 自動分流，不佔用風險預算。 | 待驗多 Agent 子樹高頻 `execve`/static Go binary 在 `sprout-stub` `user-notify` 下的穩定性。 | 與 Wayland 顯示層正交，仍取決於底層選 PRoot 或 Sprout。 |
| **Chromium WebGL / WebGPU（含 145+ 現實限制）** | **≤144 可用 KGSL/`#36`；≥145 仍撞 `/dev/dri/renderD128` `EACCES`**（因 Android SELinux 與 PRoot 無關）；`#37` Mesa 27 解決 GL+KGSL 14/240 黑幀；`#38 L1` 可給 `wgpu`/ANGLE 試用；仍需 `--no-sandbox`。 | 即使免 ptrace，**`/dev/dri/renderD128` 仍被 Android SELinux 擋住**，Chromium ≥145 同一硬牆仍在；唯 Turnip `vkmark` / KGSL `ioctl` 密集提交**實測快 9.9–10.4×**（`25102PCBEG`）。仍需 `--no-sandbox`。 | `#41` XWayland 走 `/dev/kgsl-3d0` surfaceless，但 Chromium 仍找 `renderD128` 且 `#46` 警告透明合成器會炸 Chromium GPU；Firefox 在 `tawcroot`/`libhybris` 有成功案但 Chromium/Playwright 實證極少。 |
| **World-Unbound 高畫質遊戲（不降畫質）** | 受限於 PRoot `ptrace` 對密集 Vulkan/KGSL `ioctl` 與 XCB 的高稅率（`Sprout` 實測同機 `vkmark` 755 vs 7,883 差距來源之一）；若走 Termux:X11 非零複製上屏亦有系統 copy 損耗。 | **Vulkan / KGSL 提交瓶頸消除（同機實測 10.4× `vkmark` 差距）**；可不降畫質直跑 Turnip，但上屏若走 Termux:X11 仍受該 XServer 搬運機制限制，且須先確認本機 `/dev/kgsl-3d0` SELinux 權限。 | 若採 **`#49` `libhybris` (`android_wlegl`/`TAWC-DRI`)** 理論可達真 AHB 零複製；但現有直接可用的 Wayland 專案多半退為 CPU copy（`#44`/`#55`/`#56`）或未驗證，實際反而比路線 B 慢且不穩。 |
| **外接螢幕 1080p → 3440×1440@60Hz（~1.19 GB/s）** | Termux:X11 本身有穩定的外接螢幕與視窗呈現（配合 `#36` `CompareFB 0` + `#39-1178` 同步修復）；高解析度 60Hz 的每幀軟體/GPU 搬運負載仍高，需實測 3440×1440 實際表現。 | 與路線 A 同一個 Termux:X11 呈現管線，優點是**應用與驅動側 GPU 提交延遲大幅下降**，把節省的 CPU/IPC 預算留給高解析度顯示。 | 3440×1440 下任何 CPU copy（`#44` `memcpy`、`#55`/`#56`）必定不可用；僅 `#45 localdesktop` / `#50 MagicDesk` 原生設計外接螢幕模組，但零複製實相皆 `尚未驗證`。 |
| **免 Root / 保護 Stable `:1` / 工程投資成本** | **最低投資、零破壞風險**：完全在現有 `f8-proot-fast` 與 `:3`/測試目錄增量迭代。 | **中等投資、可完全隔離**：`Sprout` 可與 `proot-fast8` 並存於測試複本 rootfs，先做 Electron/Turnip 跑分對比，**不影響主力桌面**。 | **極高工程成本**：須更換顯示伺服器 APK、桌面環境（Ubuntu 24.04 缺 `#40` 預建套件）與全套輸入法/視窗/D-Bus 調適，且大多數專案在 F8/A840/3440×1440 上仍屬未知。 |

---

## 四、Stage-5 建議驗證藍圖與最終路線確認

綜合 60 項專案去重與紅線約束，目前呈現清晰的**「雙軌漸進式決策架構」**——既有最低風險保底升級（**路線 A+**），也為高畫質 3D/Vulkan 負載與 WebGPU 保留零風險的驗證通道（**路線 B / 局部 C 技術探針**）：

1. **立即落地（路線 A 低風險強化，獨立測試、不碰 Stable `:1`）**：
   - **PRoot 引擎升級**：以 `Pons 0002`（syscall 統計）定位剩餘熱點 → 移植上游 `48c903d54`（停攔 `close`）+ `4006c630f`（免 `GETEVENTMSG`）+ `Pons 0005`（AArch64 `ioctl` BPF 放行）+ `LinuxDroid 0001`/`0009`（PID hash）。
   - **GPU 與顯示試驗（僅測試容器 + `:3` `com.waydefu.x11gpu`）**：試驗安裝 `#37` `lfdevs/mesa-for-android-container`（`27.0.0-devel` Noble `.deb`/`.tar.gz`，含 Adreno 840 與 `present wait fence`）+ `#36` `fakepci.c` & `electron-gpu.sh`（並實測 Chrome ≤144 Electron GPU vs ≥145 限制）；可視需求在 `:3` 實驗分支驗證 `#39-PR1178`（`LORIEBUFFER_FD` fence wait）。
2. **高天花板對照試驗（隔離複本 rootfs 實測路線 B：`Sprout`）**：
   - 在複製的 Ubuntu 24.04 **測試 rootfs**（絕不碰生產 rootfs）跑 3 個最小探針：
     1. 確認本機當前 `/dev/kgsl-3d0` 對 Termux `untrusted_app` 之 SELinux `O_RDWR` 權限；
     2. 實測 `Sprout` vs `proot-fast` 在 `vkmark`（Turnip）、`node`/`playwright` 啟動的真實加速比；
     3. 實測 **Electron + Chromium 多行程** 在 `Sprout` 下是否穩定無 `SIGSYS`/`RET_KILL`。
3. **關於路線 C（Wayland + XWayland）的務實保留條件**：
   - 僅當「路線 A+ / B 在 3440×1440@60Hz 或 World-Unbound 仍因 Termux:X11 非零複製上屏達不到目標幀率」時，才需切入路線 C；且切入前只需先做最小探針：**對 `#40 Anland`（檢視 `display_consumer.c`）/ `#45 localdesktop` / `#50 MagicDesk` 與 `#49 libhybris` 做真零複製與 Adreno 840 / Ubuntu 24.04 實機檢核**，避開已被證偽的 CPU/XShm copy 合成器（`#44`/`#55`/`#56`）。
