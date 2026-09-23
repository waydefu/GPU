# V2-XFCE-BASELINE-RUN — round 1 on dc94485（非 PASS 報告，§19.3 格式）

```
PACKET_ID          V2-XFCE-BASELINE-RUN  (XFCE-FREEZE-V1, fork dfb82e6)
GRANT_REFERENCE    使用者 2026-09-23 授權（HANDOFF-NEXT-SESSION-20260923.md §2），由我簽
CLASSIFIER         xfce-c1-03 = BASELINE_DEFECT（凍結 judge 原樣輸出）
決策樹命中         Q6 → VALID_FAIL
失敗的 predicate   「XFCE workload 能照凍結時間表執行」
                   crash-proof terminals_exit_0：5 次 close 的 rc 全為 None（10 s 內未結束）
                   validity：choreo_every_step_ok / choreo_no_step_late / logout_clean
                   hard resource：全過
根因               PGA-GAP-1（已證明，見 planning-v2/pga/PGA-GAP-1-RCA.md）
ATTEMPT_CONSUMED   xfce-c1-03 : true
                   xfce-c1-01 : false（BLOCKED，runner bug：外接螢幕檢查把 "0\nx" 當成非 0）
                   xfce-c1-02 : false（X3_STARTUP_CRASH，XFCE 未啟動；VM-JIT 類，R-31）
EVIDENCE_PATH      p2-xfce-runtime/runtime-dc94485/xfce-c1-0{1,2,3}/ 各自 sha256sums.txt
STABLE             :1 pid 20881 before/after 相同（stable-before/after.json）
X3 residue         after: /tmp/.X11-unix 只剩 X1（c1-03 x11-unix-after.txt）
凍結狀態           已 freeze
下一步             PGA-GAP-1 修復 packet（§13.2 八步），新 artifact 後以 XFCE-FREEZE-V2 重跑
需要新 grant       yes（修復與驗證跨輪，§19.2 鐵則）
```

## 三個目錄各自發生了什麼

### xfce-c1-01 — BLOCKED（runner bug，不消耗）

外接螢幕檢查 `ADB shell "dumpsys display | grep -c 'type EXTERNAL'" | tr -d '\r' || echo x`：
遠端 `grep -c` 沒匹配時印 `0` 並回 exit 1，adb 把 exit code 帶回來，pipefail 觸發本地的
`|| echo x`，結果是 `"0\nx"`。runner 修正為遠端 `|| true`，並在 runner 內留註解。

### xfce-c1-02 — X3_STARTUP_CRASH（不消耗，但是證據）

X3 pid 23886 在啟動 1.6 s 後 SIGSEGV，XFCE 還沒有任何 process。簽名與
`mem:global/art-jit-crash-triage` 逐項吻合（PC 0x4800229c 在 dalvik-jit-code-cache、x0=0x61、
Uraw 含 `undleMonitorStub`）。分類 `OBSERVED / VM-JIT-CLASS / ROOT CAUSE NOT PROVEN`，不是
Gate A 缺陷。當時 runner 誤標為 `x_root_size`（空值），已改：Activity 起來後先確認 X 還活著，
死了以 exit 4 `X3_STARTUP_CRASH` 結束，並且每輪都保存 launcher log 中屬於本輪的片段。
launcher log 歷史：34 次 X 啟動中 1 次在啟動時崩潰。登記為 R-31。

### xfce-c1-03 — BASELINE_DEFECT（消耗）

依 triage 協議做了一次同變體重跑。X 正常起來，XFCE 11.85 s ready，root 1200×2191 正確。
choreography 第 0 步就失敗：T1 的視窗 12.9 s 才映射（上限 10 s）。之後所有依賴視窗的步驟
失敗、terminal 收不到 close flag（X 不讀它們的 pty，`printf` 被塞住），logout 後 5 個
terminal 相關 process 殘留到 X 被 terminate。**Gate A 完全乾淨**：560 對資源平衡、registry
與 lease 歸零、c27=1、零 fatal。

量測到的（僅供紀錄，這一輪不是有效 baseline）：

```
composite (probe)       1011      exa_comp_check T/F   234 / 1371
Gate A direct (c0)        15      D0a staged (FDCLONE)   58
EXA copy offload     746/746      present offload   746/747
SF frames                469      present lag p50/p95/p99  25.3 / 31.5 / 32.3 ms  jank 0
SF refresh period  16.67 ms  ← probe 時是 8.33 ms：MIUI 動態切換 60/120 Hz，列為共變數
X CPU (K1→K2)        77.3 s      Activity CPU 2.2 s
GATEA_EVENT        157,676 / nextSequence 157,699 → 23 行被 logcat 丟掉 → events_incomplete
```

## judge 的一個說法要講清楚（不重判）

凍結 judge 把這一輪歸在 crash-proof 失敗（`terminals_exit_0`）。實際機制不是崩潰，是 X 飽和
讓 client 餓死——terminal 並沒有非 0 exit，而是根本沒 exit（rc=None）。verdict 類別
`BASELINE_DEFECT`（產品缺陷證據）在實質上正確；依紀律 frozen attempt 不重判，只在此記錄機制。
XFCE-FREEZE-V2 會把「沒有 exit」與「exit 非 0」分成兩個檢查，讓下一次的標籤更精確。

## 本輪禁止事項（§19.3）

不延長 10 s 視窗查找上限、不放寬 choreography 判準、不在 dc94485 上重跑 C1/C0。
C0 在 dc94485 上沒有跑：缺陷已由 C1 證明，而 C0 同樣以 glyph（fallback）為主，跑了只會再消耗一次。
