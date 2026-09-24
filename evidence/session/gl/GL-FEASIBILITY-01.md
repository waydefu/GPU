# GL／Vulkan 可行性 01 — 2026-09-24（描述性，非 benchmark）

## 問題
PRoot 裡的 GL／Vulkan 程式現在用什麼渲染？這支 Adreno 840 有沒有可用的 GPU 驅動路徑？

## 環境
實驗版 X `:3`（f592241，G 模式），Termux 原生 Mesa 26.0.6（Turnip KGSL 後端）、client 從 PRoot 啟動；
`/dev/kgsl-3d0` 在 PRoot 可讀寫開啟。證據：`p2-pga-rca/runtime-f592241-gl/gl-feas-g-0{1,2}`，腳本 fork `tests/gl/gl_feasibility.sh`。

## 結果
- `vulkaninfo`：Turnip 找到 `/dev/kgsl-3d0`，`Adreno (TM) 840`，Vulkan 1.4.335，conformance 1.4.0.0。
- **預設 GL 渲染器是 llvmpipe（CPU）**（g-01）。
- Zink 第一次失敗：`vkCreateInstance` → `VK_ERROR_LAYER_NOT_PRESENT`。原因：PRoot 的 Ubuntu Mesa 在 `/usr/share/vulkan/implicit_layer.d/`
  放了 `VkLayer_MESA_device_select.json`，Termux 的 loader 找得到清單卻載不到 .so。`VK_LOADER_LAYERS_DISABLE=*` 後（g-02）
  GL 渲染器為 **`zink Vulkan 1.4(Adreno (TM) 840 (MESA_TURNIP))`**，且關掉隱式 layer 後 Mesa 預設即選 Zink。

| g-02（單次） | 幀率 | client CPU（user+sys） |
|---|---|---|
| glxgears llvmpipe，12 s | 481–484 fps | 9.84 s |
| glxgears Zink/Turnip，12 s | 537 fps | 4.74 s（sys 3.40） |
| vkcube lavapipe，600 幀 | 10.28 s（≈58 fps） | 4.68 s |
| vkcube Turnip，600 幀 | 10.11 s（≈59 fps） | 0.83 s |

## 解讀限制
- demo 程式、各一次，**不作效能結論**。glxgears 場景過小；vkcube 兩者都卡在約 60 fps（推測為呈現節奏限制，g-01 的 lavapipe 曾 5.9 s）。
- Zink 走 `drisw`（軟體呈現）路徑、sys 時間高：推測每幀由 CPU 複製上屏——這正是 DRI3／AHB 零拷貝要處理的點，**未證實**。

## 下一步
代表性負載（需要安裝 benchmark，例如 glmark2／vkmark——下載需使用者同意）、呈現路徑拆解（drisw vs DRI3）、遊戲負載。
