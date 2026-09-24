# MESA-KGSL-UBUNTU-BUILD-01 — 讓 PRoot 的 Ubuntu（glibc）程式碰到 Adreno 840（2026-09-24）

## 結果
| 驗收 | 預設 Ubuntu Mesa 25.2.8（對照） | `/opt/mesa-kgsl`（本次） |
|---|---|---|
| Vulkan（Ubuntu `libvulkan.so.1`，ctypes 列舉） | **0 個裝置** | **1 個：`Adreno (TM) 840`**，type=1（整合 GPU），vendor 0x5143，API 1.4 |
| OpenGL ES（Ubuntu glvnd `libEGL.so.1`，surfaceless，無視窗） | `llvmpipe (LLVM 20.1.2, 128 bits)` | **`zink Vulkan 1.4(Adreno (TM) 840 (MESA_TURNIP))`**，`OpenGL ES 3.2 Mesa 26.0.6` |

兩項都沒有連線任何 X server（`DISPLAY` 已 unset），沒碰 Stable `:1`。
探測程式：`/root/build/mesa-kgsl/probes/{vkprobe.py,eglprobe.py,kgsl_props.c,ioctl_log.c}`。

## 使用方式（opt-in；不取代 Ubuntu 原本的 Mesa）
```
VK_ICD_FILENAMES=/opt/mesa-kgsl/share/vulkan/icd.d/freedreno_icd.aarch64.json
VK_LOADER_LAYERS_DISABLE=*                       # Ubuntu 的隱式 layer 清單（GL-FEASIBILITY-01）
LD_LIBRARY_PATH=/opt/mesa-kgsl/lib               # glvnd 以 libEGL_mesa.so.0 / libGLX_mesa.so.0 名稱 dlopen
__EGL_VENDOR_LIBRARY_FILENAMES=/opt/mesa-kgsl/share/glvnd/egl_vendor.d/50_mesa.json
MESA_LOADER_DRIVER_OVERRIDE=zink  GALLIUM_DRIVER=zink
```
移除：`rm -rf /opt/mesa-kgsl`。GLX 路徑（`__GLX_VENDOR_LIBRARY_NAME=mesa`）尚未驗證。

## 來源與驗證
| 項目 | 來源 | 驗證 |
|---|---|---|
| `mesa-26.0.6.tar.xz`（43.9 MB） | archive.mesa3d.org | SHA256 `1d3c3b8a…3f89` ＝ 官方 relnotes；GPG Good signature，Eric Engestrom `57551DE1…C32428A6`（keys.openpgp.org） |
| `meson-1.12.1.tar.gz`（2.5 MB） | github.com/mesonbuild/meson release | GPG Good signature，Jussi Pakkanen `19E2D6D9…BABB1FE70`（keyserver.ubuntu.com；keys.openpgp.org 的副本沒有 UID 無法匯入）。未安裝進系統，以 `python3 meson.py` 執行 |
| Ubuntu 編譯相依 | Ubuntu noble 官方 | 25＋8＋5 個新套件，共約 9.3 MB，**0 個升級**，`dpkg --audit` 乾淨 |

## 修補（取自 termux-packages commit `cc8bf9d492`＝Termux 打包 26.0.6 的版本；三個都與該版逐位元組相同）
- `0017-preserve-egl-support-in-zink.patch`：Android 沒有 DRM fd，`x11_dri3_open` 失敗時上游會把 EGL 退回軟體；Chromium／Electron 走 EGL，必要。
- `0018-disable-general-layout-in-zink-for-turnip.patch`：Zink 在 Turnip 上的 general layout 會讓合成器（Firefox WebRender）破圖。
- `0019-UBWC_5-and-UBWC_6-support.patch`（Rob Clark，WIP）：**這支手機的 KGSL 回報 `UBWC_MODE=6`**（`kgsl_props` 實測；chip_id `0x44050a31`），
  26.0.6 的 `tu_knl_kgsl_load` 只接受 1–4，否則回 `VK_ERROR_INITIALIZATION_FAILED`，release 版不印任何訊息 → 0 個裝置。
  上游 main 已有同樣處理（`KGSL_UBWC_5_0`／`6_0` 與 4.0 同分支）。
- 沒打的：bionic 專用修補、Adreno 7xx／830／810 支援（Adreno 840 已在 26.0.6 `freedreno_devices.py`）、0014（release 版 assert 已移除）。

## 編譯
`meson setup --wrap-mode=nofallback --prefix=/opt/mesa-kgsl --libdir=lib -Dbuildtype=release -Dplatforms=x11
-Dgallium-drivers=zink -Dvulkan-drivers=freedreno -Dfreedreno-kmds=kgsl -Dllvm=disabled -Dglvnd=enabled -Dglx=dri
-Degl=enabled -Dgbm=disabled -Dgles1=disabled -Dgles2=enabled -Dvulkan-layers=[] -Dvideo-codecs=[] -Dtools=[]
-Dgallium-va=disabled -Dgallium-rusticl=false -Dvalgrind=disabled -Dlibunwind=disabled -Dlmsensors=disabled -Dbuild-tests=false`
- `build-supervised.sh`：ninja -j2、nice 10、MemAvailable < 3500 MB 就結束 ninja 程序群組（精確 pgid），> 4500 MB 持續 60 s 後續編。
  實際：12:22 開始，12:31 可用記憶體 3486 MB → 暫停，12:33 續編，12:41 完成（566/566，8 條 unused-result 警告，0 錯誤）。
- 0019 之後增量重編 3 步。

## 過程中的錯誤與偏差（照實記錄）
1. **未經同意的下載**：第一次 `meson setup` 沒加 `--wrap-mode`，meson 自動抓了 libarchive 3.7.2（GitHub）、libxml2 2.11.6（gnome.org）與兩個 wrapdb patch（約 7.9 MB）。
   兩者都是 `src/freedreno/meson.build` 的**可選**相依（只給解碼工具）。雜湊與簽章 tarball 內 `.wrap` 的 `source_hash`／`patch_hash` 相符。
   已刪除（`subprojects/libarchive-3.7.2`、`libxml2-2.11.6`、`packagecache`、`.wraplock`，皆不在 tarball 中），改 `--wrap-mode=nofallback` 重設，0 次下載。
2. 我一開始說 Ubuntu 的 `libdrm-dev` 已裝——那是 Termux 的 pkg-config 回報的；Ubuntu 側實際缺，後補（0.42 MB）。
3. 我先前推測「PRoot 的遊戲只能走 CPU，因為 Ubuntu 的 Turnip 沒有 KGSL」——前半推測正確（Ubuntu 的 Turnip 確實沒有 `/dev/kgsl-3d0`），
   但「只能」不成立：自編帶 KGSL 的 Mesa 後，PRoot 內的 glibc 程式可以用 GPU。
4. 第一版 vkprobe 沒印 `vkEnumeratePhysicalDevices` 的回傳碼，追查時多繞了一步。

## 還沒做
- GLX（`libGLX_mesa`）路徑、實際開視窗在 `:3` 上繪圖、效能。
- Electron／Chromium：開 GPU 後是否用得到這套驅動、有沒有收益——下一步要先凍結判準。
