# PGA-GAP-1 — 最小設計（§13.2 第 2 步）

前提：`PGA-GAP-1-RCA.md` 已證明根因（先於本文件）。

## 改什麼

**只改一個函式**：`lorie/src/main/cpp/patches/dix-config.h.in` 的 `p2a2_emit()`。

```c
/* PGA-GAP-1: default OFF. Exact "1" only, read once per translation unit. */
static int p2a2_diag_enabled(void)
{
    static int cached = -1;
    if (cached < 0) {
        const char *e = getenv("TERMUX_X11_P2A_DIAG");
        cached = (e && e[0] == '1' && e[1] == '\0') ? 1 : 0;
    }
    return cached;
}

static void p2a2_emit(const char *msg)
{
    ...
    if (!msg || !p2a2_diag_enabled())
        return;
    ...（原本的 liblog + stderr + snap 追加，一個字元都不改）
}
```

`TERMUX_X11_P2A_DIAG=1` 時行為與 dc94485 完全相同；其他任何值（未設定、`0`、空字串、`true`、
`11`、` 1`）都不輸出。與既有旗標 `TERMUX_X11_GATEA_PROTO` / `TELEMETRY` 同一個「恰為 "1"」慣例。

## 刻意不改的東西

```
p2a3CrashHandler / p2a3WriteLine   崩潰鑑識（Uctx/Upid/Uraw/Ssig）不經過 p2a2_emit，照常寫
                                   stderr 與 snap fd（啟動時開一次，只在崩潰時寫）
xorg_backtrace 的 ErrorFSigSafe    照常；只有重複的 "Sbt" logcat 行跟著 p2a2_emit 關掉
GATEA_EVENT / GATEA_* / R8_OBS     qualification telemetry，各有自己的開關，不動
5 s framecounter log(INFO)         每 5 秒一行，保留（XFCE-FREEZE-V2 改用它當 composite 來源）
"R3 S*" dprintf / buffer.c dprintf 只寫 stderr（4 µs 級，C 變體），未被證明有害 → 不在本缺口內
```

## 為什麼不是其他做法

```
(a) 只拿掉 snap 檔 open/fsync，保留 logcat      仍然每秒數千行進 logd，logd 會掉行
                                              （xfce-c1-03 已實測掉 23 行 GATEA_EVENT），而且
                                              留下的 liblog 成本未量測。不採用。
(b) 編譯期移除（#if 0）                        失去需要時打開診斷的能力；診斷曾經抓到真 bug。不採用。
(c) 刪掉所有呼叫點                            26 處、7 個 xserver 檔，改動面大且與 (b) 同樣失去能力。不採用。
(d) 本設計：執行期旗標、預設關               一個函式、行為在旗標打開時逐字相同。採用。
```

## 驗證（第 3 步，先於 patch）

`tests/pga/test_p2a2_gate.py`：把 `p2a2_emit` 從 `dix-config.h.in` 抽出來，連同 stub
（`__android_log_print`、`open`、`write`、`fsync`、`close` 全部計數）在 host 編譯執行：

```
未設定 / "0" / "" / "true" / "11" / " 1" / "1 "   → 0 次 liblog、0 次 open、0 次 write
"1"                                               → 1 次 liblog、1 次 open、2+2 次 write、1 次 fsync
NULL msg（旗標開）                                → 0 次
紅燈對照：同一套測試對 dc94485 版本的 dix-config.h.in 必須在「未設定 → 0 次」失敗
```

靜態檢查：`p2a2_emit` 在產品樹中只有一個定義；crash handler 不呼叫 `p2a2_emit`。

## 連鎖代價（§13.4）與重驗範圍

新 PRODUCT_SHA → touched-symbol matrix：唯一 touched 符號是 `p2a2_emit`（純 logging，無狀態、
無回傳值）。R7–R10 的 judge 都不讀它的輸出（`tests/` 全樹 grep 已確認，只有 XFCE collector 讀）。
→ R0–R10 CARRY_FORWARD；smoke 沿用 D-12 先例 R8-D + R8-P2（一個 clean close、一個 fatal 路徑）。
XFCE 以 XFCE-FREEZE-V2 在新 artifact 上重跑（V1 的兩個 metric 來源是 stamp，旗標關掉後會是
0 行——**不能讓它被讀成 0**，V2 改用 5 s counter 與 event 串流）。
