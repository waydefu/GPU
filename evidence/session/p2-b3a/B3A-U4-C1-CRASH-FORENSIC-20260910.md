# B3a U4-C1 Crash Forensic — launch-only controlled attempts

日期：2026-09-10（Asia/Taipei）  
範圍：Experimental `com.waydefu.x11gpu` / `DISPLAY=:3`；無 benchmark workload、無 source mutation。  
ADB endpoint：`192.168.1.101:45279`；device：`25102PCBEG / myron`。

## Artifact provenance

- Package：`com.waydefu.x11gpu`
- versionCode：`15`
- versionName：`1.03.01-1954f82-09.09.26`
- Installed APK：`/data/app/~~sq1GIvXb2CltEkye8jmvcg==/com.waydefu.x11gpu-uW05Pf569Dzy4Cj_3iBH7g==/base.apk`
- APK SHA256：`5cc87f4121bfe52e7504348e36c36421b28355549b3b26fe031f175a234c1dce`
- Embedded `lib/arm64-v8a/libXlorie.so` SHA256：`da79b03df087435813ff494b62eebc792d4df074a8b520c3006f7288b06903fd`
- Embedded library Build ID：`b15d75a5a3d4217eb736208f18d5a1aa84280bf9`
- Local unstripped candidate：`evidence/control/termux-x11-unstripped-libraries-for-ndk-stack/01x55434/obj/arm64-v8a/libXlorie.so`
- Local candidate SHA256：`b42429fe53494bd86cd0a56932e21e5666b84b8c568853a273bf0b6a1feccffc`
- Local candidate Build ID：`0c8dfb30410ea08f59180ec9bb8b66991117a014`
- Build ID match：`NO`。未找到與本次 APK embedded library 相符的 unstripped DWARF；不得作 exact source-line symbolization。

## Preflight and target

- Fresh endpoint：收到 `192.168.1.101:45279` 後，`adb connect` 回傳 `already connected`；
  `adb devices -l` 顯示唯一目標為 `device`、`product:myron_global model:25102PCBEG device:myron`。
- `NO_X3_RESIDUE` confirmed before launch。
- Activity 明確以 `--display 0` 啟動；回讀 `display=0`、`state=RESUMED`、
  `reportedDrawn=true`、`mVisible=true`，SurfaceView 存在。
- APK path、版本與 hash 均由實際安裝 package readback 綁定；未安裝任何 APK。

## Launch-only attempts

每次只執行 `/data/data/com.termux/files/usr/bin/f8-x11gpu :3`，不發 oracle、cell、X workload 或 batch request。

| attempt | X PID | startup evidence | result | teardown |
|---|---:|---|---|---|
| #1 | 27838 | EGL 1.5；`InstallProbe installed=0`；17:12:48 | survived launch-only | `NO_X3_RESIDUE` |
| #2 | 32307 | EGL 1.5；`InstallProbe installed=0`；17:15:28 | survived launch-only | `NO_X3_RESIDUE` |
| #3 | 6585 | EGL 1.5；`InstallProbe installed=0`；17:17:16 | survived launch-only | `NO_X3_RESIDUE` |

- 三個 PID 的 exact cmdline 都是 `termux-x11gpu com.waydefu.x11gpu :3`。
- `u4-c1-main-system.log` 搜尋三個 PID 的 `Fatal signal`、`SIGSEGV`、`SIGABRT`、
  `crash_dump`、`tombstone`：`0 matches`。
- 未觀察到 process death；三次都是 controlled survival，不是 crash reproduction。

## Forensic observability

- `/proc/<PID>/maps`：三次均 `Permission denied`；輸出檔只有對應的 permission-denied 行，
  沒有 mapping，不能從 live maps 導出 load bias。
- `debuggerd -b 27838`：`debuggerd: root is required`，exit=1。依規則未對同一方法重試。
- 已保存完整 crash stream 與 crash-buffer dump；兩者 hash 相同。
- Crash buffer 內只有較早的 09-08／09-09 歷史項目，沒有 C1 三個 PID 或本輪啟動項目。
  因為本輪沒有 crash，沒有新的 tombstone 可供 `ndk-stack` 使用。

## Verdict

```text
U4-C1 launch-only: NON-REPRODUCED — 0/3 reproduced after historical crash 1/1
C1 crash root cause: UNKNOWN / NOT ATTRIBUTED
Exact DWARF symbolization: NOT AVAILABLE (Build ID mismatch)
Live maps: NOT OBSERVED (permission denied)
debuggerd: NOT OBSERVED (root required)
Batch16 R3-B: remains NOT TESTED
B3a: remains BLOCKED at crash-forensic gate / no authorization to resume
Gate A/D/H: HOLD
Stable: UNTOUCHED
```

`NON-REPRODUCED` 不等於證明原始 crash 不存在；它只表示本次三次受控、無 workload 啟動未重現。不得以此恢復 batch16 或繼續 U4，除非另有明確決策。

## Evidence files

本目錄保存：APK、embedded library、三次 launcher log、三份 maps permission result、
crash stream、crash-buffer dump、main/system log。Preflight blocker 另見
`B3A-U4-C1-PREFLIGHT-20260910.md`。
