# GLIBC-RUNNER-EVAL-01 — 能不能不經 PRoot、在 Termux 原生跑日常 Electron 程式並用 GPU（2026-09-24，只查資料、沒安裝）

## 問題
Claude／Cursor／Codex／Hermes 都是 glibc 版 Electron，目前在 PRoot 內、`--disable-gpu`。
PRoot 的 Ubuntu Mesa 25.2.8 找不到 GPU：Ubuntu glibc loader 列舉到 0 個 Vulkan 裝置；Ubuntu 的 `libvulkan_freedreno.so` 沒有 `/dev/kgsl-3d0` 字串，Termux 的有（本日實測）。
Termux 的 glibc-runner（`grun`）以 `$PREFIX/glibc/bin/ld.so` 直接執行 glibc 程式、不經 ptrace——能不能同時擺脫 PRoot 追蹤器開銷，又拿到 GPU？

## 來源（官方）
- `glibc-repo`（termux-packages）→ apt 源 `https://packages-cf.termux.dev/apt/termux-glibc/ glibc stable`
- termux-pacman/glibc-packages：wiki「About glibc runner (grun)」、`gpkg/mesa/build.sh`、`gpkg/glibc/build.sh`
- apt 索引 `termux-glibc/dists/glibc/stable/binary-aarch64/Packages`（2026-09-24 讀取）

## 發現
1. **官方已有帶 KGSL 的 glibc Mesa**：`mesa-glibc` 24.2.6，`-Dvulkan-drivers=swrast,panfrost,freedreno -Dfreedreno-kmds=msm,kgsl`，
   gallium 含 freedreno、zink；有 egl、gbm、glx=dri。下載 21.2 MB。
2. **glibc 版本**：termux-glibc 是 **2.44**；PRoot Ubuntu 24.04 是 **2.39**。以 2.44 編的函式庫多半要求 `GLIBC_2.40+` 符號，
   推測不能直接載入 PRoot（**未驗證**——要下載 `mesa-glibc` 才能讀它的符號版本需求）。
3. **Electron 硬性依賴，但 termux-glibc 沒有的函式庫**（Claude 與 Cursor 的 `DT_NEEDED` 相同）：
   `libgtk-3`、`libnss3`／`libnssutil3`／`libsmime3`、`libnspr4`、`libatk-1.0`、`libatk-bridge-2.0`、`libatspi`、`libcups`、`libudev`、`libXdamage`。
   有的：glib、pango、cairo、dbus、alsa-lib、libxkbcommon、X11／xcb、mesa（含 gbm）。
4. mesa-glibc 加 glibc-runner 加 vulkan-icd-loader 的相依封閉：68 個套件，下載 154.5 MB，安裝後 878 MB。

## 結論
- **官方套件不足以原生執行 Electron 程式**：缺 GTK3、NSS、ATK／AT-SPI、CUPS、udev、XDamage 共 7 組。
- 能繞的方法：缺的部分借用 Ubuntu rootfs 裡用 2.39 編的函式庫（glibc 向下相容，理論上能在 2.44 上載入）。
  風險在路徑：`/usr/share`（字型、GTK 主題、gdk-pixbuf loaders、gio modules）、`/etc/fonts`、`/tmp`、`/run/dbus` 在 PRoot 外都不存在，要逐一重導。**屬於實驗，不是確定路線。**
- 無論走哪條路，`mesa-glibc` 的編譯設定證明「glibc 版 Turnip＋KGSL」可行；若要在 PRoot 使用，可以用同樣的 meson 設定替 Ubuntu 自己編。

## 下一步候選（需要使用者同意下載）
- A（小）：只下載 `mesa-glibc_24.2.6_aarch64.deb`（21.2 MB）到 scratchpad，不安裝，讀出 `.so` 要求的 GLIBC 最高版本 → 判斷能否直接給 PRoot 用。
- B（大）：在 `:3` 試原生路線：termux-glibc 基本組（約 155 MB）加上借用的 Ubuntu 函式庫，先讓一個 Electron 程式在 grun 下起得來。

## 結果 A（2026-09-24，使用者同意下載 21.2 MB）
下載 `mesa-glibc_24.2.6_aarch64.deb`，SHA256 `fc88e9a3…163ec` 與 apt 索引相符（索引經 HTTPS 取得，未另驗 InRelease 簽章）。只解壓、未安裝。
- 符號版本：`libgallium`／`libEGL_mesa`／`libGLX_mesa`／`libgbm` 最高 `GLIBC_2.38`，`libglapi` `GLIBC_2.34` → **符號上可在 PRoot（2.39）載入**。
- **但沒有 Turnip**：套件內沒有 `libvulkan_freedreno.so`，ICD 只有 `panfrost_icd.aarch64.json`
  （GitHub 上的 build.sh 寫了 `-Dvulkan-drivers=...freedreno -Dfreedreno-kmds=msm,kgsl`，但發布的 24.2.6 二進位沒有——推測 build.sh 在此版之後才改，未查證）。
- gallium 也沒有 KGSL 後端：`libgallium` 內 `/dev/kgsl-3d0` 出現 0 次；「kgsl」字串只來自 `kgsl_dri.so` 這個 kmsro 檔名，走的是 msm DRM render node（Android 上不存在）。
  與 Ubuntu 自帶的 Mesa 同樣碰不到 GPU。

**結論 A：官方 glibc 預編 Mesa 不能解決問題。**要讓 glibc 程式（不論在 PRoot 內或經 grun）碰到 Adreno，都需要自己編一套帶 `-Dfreedreno-kmds=kgsl` 的 Mesa。
這也讓路線 B（grun 原生）失去「順便拿到 GPU 驅動」的好處：B 只剩「擺脫 PRoot 追蹤器」一項收益，而且仍需自編 Mesa。

## 對自編的影響（規劃，未實作）
最小設定就夠：`-Dvulkan-drivers=freedreno -Dfreedreno-kmds=kgsl -Dgallium-drivers=zink -Dllvm=disabled`（Turnip 加 Zink；Zink 和 Turnip 都不需要 LLVM），
比完整 Mesa 小很多、編譯時間短很多（**估計，未量**）。版本對齊 Termux 在這支手機上已驗證可用的 26.0.6。
