# V2-XFCE-DESIGN-FREEZE — XFCE-FREEZE-V1

DATE 2026-09-23 · PRODUCT `dc94485` / APK `1bd8bef0…b8a3` · 計畫書 V2.3 §11
**凍結時間點：任何 XFCE session 執行之前。** probe-01 / probe-02 都沒有啟動任何 XFCE 元件。

```
凍結物        tests/xfce/xfce-design-freeze.json          （13 項參數 + 判準 + 變體 + 執行順序）
設定覆蓋層    tests/xfce/config/{xfwm4-C1,xfwm4-C0,xfce4-session,xfce4-panel,xfce4-terminal}.xml
工具          tests/xfce/{choreo.py,term_load.sh,session_wrapper.sh}           執行
              tests/xfce/{xfce_collect.py,judge-xfce.py}                       判定（先於資料凍結）
              tests/xfce/{test_xfce.py,mutation_check.py,verify-xfce-support.py} 驗證
清單          tests/xfce/FROZEN-SHA256SUMS  （runner 釘它的 sha，改任何一個檔 runner 就 BLOCKED）
runner        evidence/session/gate-a-a1/p2-xfce-runtime/run-xfce.sh
probe         evidence/session/gate-a-a1/p2-xfce-probe/probe-01, probe-02   （非 XFCE）
```

## 1. 為什麼要先 probe，以及 probe 量到什麼

13 項裡有 4 項不能靠讀 source 決定，必須量：X root 尺寸、X 有哪些 extension、
frame timing 從哪裡來、GPU／thermal 讀不讀得到。probe 只起 X3 + Activity，跑一個
R10 workload unit 讓畫面有幀，再用 R10 的 terminate 關掉。

```
X root         開機 1280x1024 → Activity 綁上後 1200x2191（native mode，內建面板）
               2608 − 2191 = 417 px 是系統列／cutout。**尺寸檢查一定要在 Activity 之後。**
               RandR output "builtin" @ 119.93 Hz
extension      GLX · Present · Composite · DAMAGE · DRI3 · RENDER · XTEST · XFIXES · SHAPE …
frame timing   dumpsys SurfaceFlinger --latency "<…SurfaceView[…](BLAST)#N>"
               可讀，每幀 desired / actual present（CLOCK_MONOTONIC ns），環形 128 幀。
               layer 名的 #N 每個 Activity instance 都不同 → 必須執行期重探。
               present lag 實測 12–18 ms（約 2 個 vsync）
monotonic      SF 的 timestamp 155974 s 與 PRoot time.monotonic() 156362 s 同為
               CLOCK_MONOTONIC（同一個 kernel）→ choreo 用 monotonic 記 T0 就能直接切幀
時區           PRoot 與裝置都是 +0800 → logcat 本地時間可直接對 epoch
GPU            /sys/class/kgsl/kgsl-3d0/gpubusy 可讀（busy total），會動；系統層級
thermal        dumpsys thermalservice 的 HAL 區段可讀（skin / CPU* / GPU*）；
               "Cached temperatures" 區段是舊值，不能用
Activity CPU   adb shell cat /proc/<pid>/stat 可讀（utime/stime）
clean close    兩次 probe 都是 c12..c17 平衡、c18/c19/c20=0、c27=1，Activity 存活
```

### probe-01 的工具錯誤（留痕）

`probe-xfce-env.v1.sh`（sha `7fe0212e…`）在 `while read` 迴圈裡呼叫 `adb shell`，
**adb 讀 stdin，把剩下的 layer 清單吃掉了**，只查到第一個 layer——沒有 buffer、全 0
的 `Background for …`。v1 因此會得出「SF latency 讀不到」的錯誤結論。v2 加 `</dev/null`
並單獨查 `(BLAST)` layer，probe-02 讀到 9 幀。probe-01 的其他量測不受影響，保留不改。
**runner 裡所有在迴圈或背景中的 adb 呼叫都加了 `</dev/null`。**

### 另一個新陷阱：mdns 同時廣播兩筆

`_adb-tls-connect._tcp` 回了兩筆（41637 與 33331），第一筆是 refused 的舊 endpoint。
STATUS-HANDOFF §2 的探測腳本只取 `F[0]`，會踩到。要逐筆試 connect。

## 2. 十三項凍結參數

| # | 參數 | 凍結值 | 理由 |
|---|---|---|---|
| 1 | duration | ready 上限 90 s · settle 20 s · choreography **150 s** · logout 上限 45 s · 任何一步遲到 > 2 s = INVALID | 時間表本身就是 workload；遲到代表 workload 沒照凍結發生 |
| 2 | resolution | 內建面板 1200×2608 @120 Hz、rotation 0、無外接；pref `native`；**X root 1200×2191** | probe 實測值；不符 → BLOCKED（XFCE 還沒起，不消耗） |
| 3 | compositor | xfwm4 4.18.0-1build3；**兩個變體 C1（on）/ C0（off）**；`vblank_mode=off` | 見 §3 |
| 4 | window choreography | 3 個 terminal，固定 geometry；開 5 關 5、focus 15、move 20、resize 10；全部由 `choreo.py` 依 JSON 時間表執行 | 無手動、無 XTEST 輸入 |
| 5 | terminal | xfce4-terminal 1.1.3-1build1 `--disable-server`；Monospace 12、80x24、不閃游標；指令 `term_load.sh`：每 100 ms 一行固定 60 字元 | `--disable-server` 讓每個視窗是自己的 process，關窗 = 可觀測的 exit code |
| 6 | open / close | 開：0 / 5 / 10 / 105 / 120 s；關：100 / 115 / 135 / 137 / 139 s；關法 = flag 檔讓 client 自己 exit 0 | client 端 destroy 是正常路徑，不用 WM kill、不用 signal |
| 7 | resize | T1 在 900×700 與 640×480 間交替 10 次（70–92.5 s，每 2.5 s），結尾 640×480 | 換尺寸 = 新 pixmap = registry 進出 |
| 8 | redraw | terminal 持續輸出（10 行/s/窗）+ focus 切換 15 次 + move 20 次 + 10 s idle 尾段；`xset s off -dpms` | 不讓 screensaver 中途變黑 |
| 9 | expected Gate A traffic | 形狀＝Over a8r8g8b8→x8r8g8b8 無 mask；允許事件 30 種、禁止 6 種（9/12/13/15/16/35）、合計剛好覆蓋 1..36；generation 恆為 1；registry 16 格，滿了走 D0a staging **不算錯** | 只預測「走哪些路」，**不預測數量** |
| 10 | shutdown path | terminal 自行關閉 → `xfce4-session-logout --logout --fast` → K3（X 活、無 client）→ `p_r10_ledger --mode terminate` → K4 | 與 R10 的 clean close 同一條路；絕不用 SIGTERM X |
| 11 | metrics | K0–K4 五個取樣點＋連續 logcat＋每 2 s SF/gpubusy＋每 30 s thermal；衍生指標 20 項定義寫死在 JSON | `upload_bytes` 凍結為 null（B3a 未開，留給 B3-TELEMETRY-VERIFY） |
| 12 | resource proof | K0↔R10 B0、K3↔B1、K4↔B3。**硬性（精確）**：c12=c13、c14=c15、c16=c17、c18/c19/c20=0、c21–c24=0、c27=1、lease 預約=釋放。**軟性**：沿用 R10 凍結 tolerance，超出 = FINDING | R10 已證明只有 counter 是精確的 |
| 13 | crash proof | X pid K0–K3 不變且只因 terminate 結束；Activity pid K0–K4 不變；0 fatal／tombstone／ANR；xfwm4／panel／xfdesktop pid K1=K2；terminal 全部 exit 0 | xfce4-session 會自動重啟崩潰的 client，所以 **pid 變了就是崩潰** |

## 3. 兩個會改變結論的設計決定

### 3.1 compositor 做成兩個變體，不是一個

日常 `:1` 的 XFCE 是 **`use_compositing=false`**（讀 `~/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml`）。
歷史上 B.1 census 與 B.2e 在 `:3` 用的是全新設定，也就是 XFCE 預設 **compositor 開**。

這兩種會送給 Gate A 的流量本質不同：

```
C1 compositor on   xfwm4 把視窗陰影（ARGB32）Over 到 x8r8g8b8 root buffer
                   → 正是 Gate A 那一刀的形狀。B.1 的 1166/1776 Over-none 大半來自這裡。
C0 compositor off  沒有陰影合成；只剩 GTK3／cairo 把 ARGB 圖示畫進 depth-24 視窗
```

只測 C1 會量到「Gate A 被餵飽」的樣子，但 Gate W 要驗的是日常桌面；只測 C0 則失去與
B.1/B.2e 的可比性。兩個都凍結、**永不合併、永不當同一格比較**。

### 3.2 `vblank_mode=off`，不是套件預設的 `auto`

X3 有 GLX。`auto` 會讓 xfwm4 嘗試 GLX 路徑，而 GL 在 PRoot 裡是 client 端 Mesa 的 CPU
renderer，而且會隨呼叫端的 Mesa 環境變數改變。`off` = 純 XRender，可重現。
這是對 C1 唯一有影響的偏離（C0 沒有 compositor，vblank 不起作用）。

### 3.3 其他「讓兩次執行不同」的來源，全部關掉

```
/etc/xdg/autostart 的 21 個項目   全部以 Hidden=true 覆蓋（light-locker、xscreensaver、
                                   nm-applet、pulseaudio… 在 PRoot 裡要嘛失敗要嘛會變黑）
session 內容                       就是系統 Failsafe：xfwm4、xfsettingsd、xfce4-panel、
                                   Thunar 常駐、xfdesktop
panel                              系統 default.xml 去掉 id 7（宣告未定義）、8（pulseaudio，
                                   PRoot 沒有 PulseAudio）、9（power-manager-plugin，未安裝
                                   → 第一次啟動會跳「載入失敗」對話框，那會變成 workload 的一部分）
session 存檔／ssh-agent／gpg-agent  關（gpg-agent 會 daemonize，logout 後殘留）
HOME / XDG_*                       每次全新（/tmp/xfce-x3-run-<id>），不碰 /root 的日常設定
fcitx / IM 變數                    清掉；LANG=C.UTF-8；NO_AT_BRIDGE=1
套件版本                           13 個套件釘版本，不符 → BLOCKED
```

## 4. 判定模型（先於資料凍結）

```
BASELINE_VALID    有效、crash proof 全過、硬性資源檢查全過（軟性只列 FINDING）
BASELINE_DEFECT   crash proof 失敗，或硬性資源檢查失敗 → 產品缺陷證據，進 PGA gap inventory
INVALID           workload 沒照凍結發生 → 無資訊
BLOCKED           XFCE 起來之前就停了 → 不消耗
優先序            crash 永遠不會被降級成 INVALID
分類              全部是 BASELINE（pga_closed=false，計畫書 §11）
```

`GATEA_EVENT` 有全域 seq；seq 不連續 → 事件類指標與 lease 平衡改為 null（不是 0），
但 counter 仍照判——**事件串流不完整不能掩蓋 counter 失衡**（測試釘住）。

## 5. 凍結前抓到的三個工具錯誤（依紀律留痕）

1. **probe v1 的 stdin 吞噬**——見 §1。
2. **judge 與 freeze 對「沒有 close summary」的說法不一致。** freeze 寫 INVALID，judge 卻判
   DEFECT；而 summary 其實 logcat 裡也有一份。改成：先讀檔、再讀 X pid 的 logcat 行；兩處都沒有
   且 logcat 全程活著 → X 沒走到 CloseScreen → crash proof FAIL；logcat 死了 → INVALID。
   freeze 文字同步修正（這發生在任何 XFCE 資料存在之前）。
3. **一個不會失敗的對照組。** `mutation_check.py` 的 mutant 6 把 collector 的 X-pid 過濾整個拿掉，
   `test_x_pid_filter_excludes_stable` 仍然綠——因為測試裡 Stable 的 5 秒行是短格式（與現在 Stable
   的舊 APK 一樣），本來就不匹配完整 regex，過濾根本沒被考到。fixture 補上 Stable 用**完整格式**
   的 5 秒行與 `Probe ENTER`（Stable 換新 APK 就會這樣印），現在 14 個 mutant 全部被殺。

## 6. 驗證狀態

```
test_xfce.py               33 tests OK
mutation_check.py          14/14 killed
verify-xfce-support.py     70 checks PASS；--selftest 8/8 RED
```

## 7. 執行順序

`C1, C0, C1, C0, C1, C0`（每變體 3 次，交錯以分攤 thermal 與背景負載漂移）。
每次：全新 X、全新 Activity（先 force-stop）、全新 HOME/XDG、從 `config/` 複製 overlay。
