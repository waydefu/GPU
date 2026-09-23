# GRANT — PGA-GAP-1 修復後的安裝與重驗（新一輪，§19.2 第 11 步）

```
DATE        2026-09-23
SIGNED BY   Claude（依使用者 2026-09-23 授權：HANDOFF-NEXT-SESSION-20260923.md §2
            「安裝 experimental artifact、跑 X3 runtime qualification、直接簽 carry-forward approval」）
PRODUCT     bfb576940ded333f49d29a8910a785f8d680261c   CI 35811368916
APK         ff7b9309c405b07245bc352911867a66e8498464e515e09dbd645b3a1ec18472  15,381,006 B
VERSION     1.03.01-bfb5769-23.09.26   versionCode 15
SIGNER      b6da0148…e5e1（與 b984ded / 7e3a05e / dc94485 相同）
BUILD_ID    890db760a77a7d22945b9640705f70d025b5d518（libXlorie.so arm64）
```

## 授權範圍（僅以下，依序）

```
1. install      p2-pga-artifact/artifact-bfb5769/install-bfb5769.sh → com.waydefu.x11gpu only
2. smoke        R8-D、R8-P2 各一次（touched-semantics audit §4；D-12 先例）
3. XFCE         XFCE-FREEZE-V2（tests/xfce2），順序 C1 C0 C1 C0 C1 C0，每變體 3 次有效
                BLOCKED / X3_STARTUP_CRASH 不消耗；INVALID 消耗且不補跑同一目錄
```

## 不在範圍內

Stable `com.termux.x11` / `:1`、任何 frozen attempt 重跑、dc94485 上的 XFCE 重跑、
放寬任何 V2 判準（包含 10 s 視窗查找上限）。

## 若 smoke 失敗

停止。依 §19 走 RCA，不得進入 XFCE。
