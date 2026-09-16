# F8 本機環境盤點（2026-09-08 16:59 CST）

這是對目前可讀取的本機 F8/Termux/Ubuntu PRoot 環境所做的檔案與套件盤點。它描述本機環境，不取代 `HANDOFF.md` 的 runtime snapshot，也不把歷史 log 當成目前手機狀態。

## 目錄與工作樹

| 用途 | 路徑 | 查驗結果 |
|---|---|---|
| Termux home | `/data/data/com.termux/files/home` | 存在；有 `.shortcuts`、F8 App cache、Mesa shader cache |
| Termux prefix | `/data/data/com.termux/files/usr` | 存在；F8 啟動器與 `termux-x11` 在此 |
| Ubuntu PRoot rootfs | `/data/data/com.termux/files/usr/var/lib/proot-distro/containers/ubuntu/rootfs` | 存在；有 XFCE、Mesa、F8 wrapper |
| 研究工作區 | `/root/projects/GPU加速` | 文件與 evidence 在此 |
| 實驗 source | `/root/projects/GPU加速/src/f8-ahb` | `f8-p2-b2-over` @ `98224356e409`，工作樹乾淨 |
| debug source | `/root/projects/GPU加速/src/f8-ahb-debug` | `f8-ahb-debug` @ `c698164956a5`，工作樹乾淨 |
| upstream control | `/root/projects/GPU加速/src/upstream` | `f8-control` @ `11b82d96f07`，工作樹乾淨 |

這幾個路徑是同一份 F8 工作的不同角色，不能當成「電腦本身」：`GPU加速` 是文件/evidence 協調根目錄，不是要拿來編譯的 source checkout；`f8-ahb` 是目前實驗 target，也是已驗證的 Serena/clangd target；`f8-ahb-debug` 是獨立 debug worktree；`upstream` 是 control/upstream worktree。`/root/projects/f8-hermes-spec` 是 Hermes 規格專案，和 F8 source 分開。相對地，`/root/android-sdk`、`/data/data/com.termux/files/usr` 與 Ubuntu PRoot rootfs 是本機/電腦環境，不能在文件中當成專案目錄。

目前已知的本機 Git/工作專案還包括 `/root/projects/clinic`、`clinic-ui-ux-redesign`、`clinic-web-p0-01`、`clinic-web-p0-02-03` 與 `/root/projects/wt-wb02-semantics`；它們是另一組 clinic 工作，不連到 F8 的 Serena project 或 source checkout。F8 的文件只引用上列 F8 worktree，避免把不同專案的環境誤認成同一台電腦的狀態。

## 本輪完成的 Android/NDK 建置環境

| 元件 | 路徑/版本 | 根據 |
|---|---|---|
| SDK root | `/root/android-sdk` | 本機 ARM64 相容組裝；不是標準 x86_64 CLI 安裝 |
| Android platform | `android-34` | 官方 `platform-34-ext7_r03.zip`，SHA-1 `1f2e9478d6a7601425ceaa553311dc43191f103d` |
| Build Tools | `35.0.0` | 官方 `build-tools_r35_linux.zip`，SHA-1 `2cfaa0bbb2336e9ec18ed3ecea84fa2e2af607bc` |
| NDK/sysroot | `29.0.14206865` | Termux `ndk-sysroot` 的 `ndk-version.h`（major 29, minor 0, build 14206865） |
| CMake | SDK 入口 `3.22.1`；實際 `/usr/bin/cmake` `3.28.3` | AGP 套件入口為 symlink，實際 compiler/build tool 是本機 ARM64 二進位檔 |
| Ninja | `/usr/bin/ninja` `1.11.1` | Ubuntu package `ninja-build` |
| Bison | `/usr/bin/bison` `3.8.2` | 只用來產生 build-tree 的 `xkbparse.c`，沒有修改 source |
| Gradle wrapper | `9.7.0` | `f8-ahb/gradle/wrapper/gradle-wrapper.properties`；wrapper 實際存在 |

NDK 目錄下的 `linux-x86_64`/`linux-x86` 是主機 tag 相容 symlink，實際執行檔仍是 ARM64 Termux clang/lld；只提供 `arm64-v8a`，不能宣稱其他 ABI 已安裝。`local.properties` 僅存在於 `f8-ahb` worktree，指向 `/root/android-sdk`，沒有提交到 Git。

## Compilation database 與驗證

在 `/root/projects/GPU加速/src/f8-ahb` 已完成：

```text
./gradlew --no-daemon :lorie:tasks --all                         PASS
./gradlew --no-daemon :lorie:configureCMakeDebug[arm64-v8a]      PASS
```

根目錄的 [`compile_commands.json`](src/f8-ahb/compile_commands.json) 是 AGP metadata 的實際副本，來源為 `lorie/.cxx/tools/debug/arm64-v8a/compile_commands.json`：498 筆、每筆使用 `aarch64-linux-android24`、所有 source file 目前存在、沒有 `/tmp/` 路徑。它已加入 `upstream/.git/info/exclude`，只供本機 clangd/Serena 使用。compile database 不會改變 APK 或 runtime 效能；Serena/clangd 建索引時才會使用額外 CPU、RAM 與磁碟。

本輪曾以 `serena project health-check` 驗證 clangd `21.1.8` 與該資料庫，結果通過；檢查留下的 repo-local `.serena/` 和 `.cache/clangd/` 已刪除，避免把一次性索引殘留當成專案檔案。中央 Serena 設定位於 `/root/.serena/projects/`。

## Termux 端已安裝版本

以下讀自 `/data/data/com.termux/files/usr/var/lib/dpkg/status`，沒有執行套件更新：

| 套件 | 版本 |
|---|---|
| `termux-x11-nightly` | `1.03.01-6` |
| `mesa` | `26.0.6-3` |
| `mesa-vulkan-icd-freedreno` | `26.0.6-3` |
| `clang` | `21.1.8-3` |
| `android-tools` | `36.0.1+really35.0.2-1` |
| `proot-distro` | `5.8.0` |
| `proot` | `5.1.107.92` |
| `vulkan-loader` | `0.0.3` |
| `vulkan-tools` | `1.4.361` |

Ubuntu rootfs 的已安裝版本查到 Mesa `25.2.8-0ubuntu0.24.04.2`、`mesa-vulkan-drivers` 同版、OpenJDK 21.0.12、XFCE 4.18 與 `dbus-x11`。這是 PRoot 內的套件版本，不能和 Termux host 套件混寫。

## F8 啟動與 GPU 路徑

- `/data/data/com.termux/files/usr/bin/f8desk`：啟動 Stable `termux-x11 :1 -legacy-drawing`，再進 Ubuntu 的 `/usr/local/bin/f8-xfce-session`。
- `/data/data/com.termux/files/usr/bin/f8desk-external`：同樣維持 `:1 -legacy-drawing`，另以 `f8-adb-port` 找 Wireless ADB 後把 Termux:X11 主畫面送到外接 display。
- `/data/data/com.termux/files/usr/bin/f8-x11gpu`：實驗啟動器，使用 `loader.apk` 與 `com.waydefu.x11gpu` 命名空間；這條路徑給 `:3`，不覆寫 Stable。
- `/data/data/com.termux/files/usr/bin/f8stop`：停止 XFCE 與 Stable `:1`；未執行。
- `/data/data/com.termux/files/usr/bin/f8-adb-port`：以 `_adb-tls-connect._tcp.local.` mDNS 找 Wireless ADB port。
- Ubuntu `/usr/local/bin/f8-gpu`：設定 `VK_LOADER_LAYERS_DISABLE="~implicit~"`、Zink、Freedreno ICD 與 `TU_DEBUG=noconform`，再執行指定程式。
- Ubuntu `/usr/local/bin/f8-doctor`：檔案內容標示為 read-only health check；本輪只讀其內容，沒有執行它，避免觸碰現有 `:1` runtime。

## 本輪讀取到的本機狀態

- `/data/data/com.termux/files/home/.cache/mesa_shader_cache` 存在。
- `/data/data/com.termux/files/home/.cache/f8-external-apps/apps.tsv` 與 `components.sha256` 存在，代表 F8 外接 App 清單快取已建立。
- `/data/data/com.termux/files/home/x11gpu-r3-stdout.log` 存在，大小 `34,881,009` bytes，mtime `2026-09-08 07:39:57 CST`，SHA-256 `b76e59536d13facd1b702d4e44640dada67f99e55c7b7c5707f2c945475a5624`。它是 R3 證據 log，不是本輪重新執行結果。
- 本輪 `adb devices` 沒有列出任何裝置。因此沒有用這次查詢更新手機上的 package、PID、display、`/dev/kgsl-3d0` 或 SurfaceFlinger 狀態；這些仍以 `HANDOFF.md` 的 07:40 snapshot 為準。
- source checkout 與本機 Serena 設定都沒有產生程式碼變更；沒有 `adb install`、沒有啟停 X11、沒有執行 `f8-doctor` 或 `f8-gpu glxinfo`。

## Hermes、Serena 與 Cursor

Hermes 的 `/root/.hermes/config.yaml` 現在以 `serena start-mcp-server --context codex --project-from-cwd` 啟動 Serena；因此 Hermes 在 F8 worktree 中會依目前 cwd 選擇對應的 Serena project。`f8-ahb`、`f8-ahb-debug`、`upstream` 各自有中央 `/root/.serena/projects/` 設定，互不共用 source 狀態。Cursor 保留內建索引，刻意沒有接 Serena MCP。

Serena 目前的完整 C/C++ database 只在 `/root/projects/GPU加速/src/f8-ahb` 驗證；不要把這份 database 複製給其他 worktree，除非在該 worktree 重新產生。設定與限制見 [`SERENA-SETUP.md`](SERENA-SETUP.md)。

Codex 的 `/root/.codex/config.toml` 仍固定把全域 fallback Serena 指到 `/root/projects/GPU加速/src/f8-ahb`，所以目前 F8 主線一定吃到該 compilation database；同時，八個現有 coding repo 已各自建立被 Git exclude 的 `.codex/config.toml`，從 repo 內執行 `codex mcp get serena` 會改用 `--project-from-cwd`。Hermes 已實測能在有 `.git` 且已註冊的 clinic/F8 repo 依 cwd 選擇正確 project；docs-only 目錄沒有 repo marker 時只會連上 MCP，不會自動啟用專案。新 repo 可執行 `/root/.local/bin/serena-project-init --name <名稱> --language <語言> --trust-codex /絕對路徑`，再完成一次 onboarding/index。

## 舊安裝殘留與歷史路徑判讀

- `/usr/lib/android-sdk` 由 Debian `aapt`/`apksigner` 套件管理，仍是系統套件，不是本輪要刪除的「舊 SDK 殘留」。
- evidence/CI 文件裡的 `/usr/local/lib/android/sdk` 是歷史 CI runner 路徑；它不代表本機 SDK，也不應改寫成 `/root/android-sdk`。
- 本輪下載 Android 官方 archive 的 `/tmp/platform-34-ext7_r03.zip`、`build-tools_r35_linux.zip` 與 repository XML 已在驗證完成後清除；SDK 內保留的檔案才是目前使用的環境。
- Gradle cache、`.cxx/` 與 build output 是目前驗證產物；不把它們誤刪成「舊安裝」。

後續若要更新 runtime，先依 [`HANDOFF.md`](HANDOFF.md) 的安全規則重新建立 ADB 連線，再單獨記錄新的 device probe；不要把本機盤點時間戳直接改寫成手機現況。

## S4 native ADB recovery — 2026-09-12

這個 Termux session 會自動進入 Ubuntu PRoot，所以 prompt 看到
`.../ubuntu/rootfs $` 是目前啟動設定，不代表 native Termux binary 不能在
此環境直接執行；不需要用 `exit` 關閉介面。native ADB authority 是：

```text
path: /data/data/com.termux/files/usr/bin/adb
format: ELF ARM64 / Bionic
version: 35.0.2-android-tools
```

`/usr/local/bin/f8-adb-port` 是 PRoot wrapper，會用 Ubuntu
`/usr/bin/python3` 執行 Termux helper，不能作 authority。直接執行 Termux
helper 時，`zeroconf/ifaddr` 受 PRoot 的 library lookup 影響，出現：

```text
dlopen failed: library "libc.so.6" not found
```

這不代表 native ADB binary 失效；不要修改 helper。相關 PRoot-native
shim 與限制見 `android-device-qualification` 的
`references/proot-host-device-evidence.md`。

### Isolated ADB server

為避免污染既有 5037 server，本次使用獨立 listener：

```text
listener: tcp:5038
server-status: PASS
version: 35.0.2
mdns_backend: OPENSCREEN
os: Linux 6.17.0-PRoot-Distro (aarch64)
devices -l before candidate: empty
```

native adb 的 `-L tcp:127.0.0.1:5038` 會拒絕指定 hostname；在這個版本
正確的 local bootstrap 是 `-L tcp:5038 server nodaemon`。本輪 server
由本輪 process identity 精確終止；5037 沒有被 kill、重啟或查詢。

### Discovery and candidate result

adb 35.0.2 client 不支援以下 mDNS 子命令：

```text
mdns check: unsupported
mdns track-services --proto-text: unsupported
mdns services: unsupported
```

使用者提供的 `10.56.180.219:46761` 在 isolated server 上重新嘗試一次，
TLS authentication 仍失敗：

```text
SSLV3_ALERT_CERTIFICATE_UNKNOWN
transport: already offline
```

它不是已驗證的 device endpoint，不能進行 `get-state`、model/device
identity、package query 或 install。這次分類為：

```text
DEVICE AUTH FAILURE / ADB DISCOVERY BLOCKED
```

沒有猜測其他 port、沒有重用歷史 endpoint、沒有記錄或處理配對碼。若需
配對，配對碼只能在 native Termux 的互動提示中由使用者本機輸入；完成後
回到 Wireless Debugging 主頁取得新的 connect endpoint。

Current boundary:

```text
S4 source/native/CI/provenance: PASS
S4 runtime: BLOCKED — ADB discovery/authentication
D0a: HOLD
Stable com.termux.x11 / :1: UNTOUCHED
```

## Serena「假死」教訓 — 2026-09-12

MCP 連續報 `unreachable` 時，server 進程其實全活著（分屬 luna×2、gateway 的活 session，一個不能殺）。真正原因是 project 註冊名：本線叫 `gpu-f8-ahb`，不是 `f8-ahb`；再加熔斷器要等冷卻（約 50 秒）才能重試。用對名字＋等冷卻後一次啟用成功，cpp 語言伺服器與 symbol 查詢都正常。下次先查進程歸屬與註冊名，不要直接判死。
