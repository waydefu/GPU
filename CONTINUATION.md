# 接續手冊 — 2026-09-17

本檔告訴下一手 **怎麼把專案接起來**。它 **不授權** 跑 R7-05。
沒有新的顯式授權：只准讀、重判已有證據、核對裝置／產地，不准開新 cell。

工作站權威根：`/root/projects/GPU加速`。本倉庫腳本預設寫死這個路徑，以便在 F8 上直接接續。

---

## 0. 30 秒核對

在 F8 工作站：

```bash
test -f /root/projects/GPU加速/HANDOFF.md
git -C /root/projects/GPU加速/src/f8-ahb-gatea-case-loop rev-parse HEAD
# 期待：fdfb1ce44b429897eda17c43bf33fbd37afe67f3

python3 /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py \
  fbo-incomplete \
  /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-04-requalification-01/logcat-follow.txt \
  --ring /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-04-requalification-01/gatea-ring.txt \
  --summary /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-04-requalification-01/gatea-summary.txt \
  --x-alive 0 --exit-signal 0
# 期待：R7_PASS fbo-incomplete

python3 /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r7-design/judge-r7.py \
  fbo-incomplete \
  /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-7549e36/r7-qualification-01/r7-04/logcat-follow.txt \
  --ring /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-7549e36/r7-qualification-01/r7-04/gatea-ring.txt \
  --summary /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-7549e36/r7-qualification-01/r7-04/gatea-summary.txt \
  --x-alive 0 --exit-signal 0
# 期待：R7_FAIL halt_mismatch what=x-direct-not-success reason=4
```

本倉庫內相對路徑等價（clone 之後）：

```bash
python3 evidence/session/gate-a-a1/p2-r7-design/judge-r7.py \
  fbo-incomplete \
  evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-04-requalification-01/logcat-follow.txt \
  --ring evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-04-requalification-01/gatea-ring.txt \
  --summary evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-04-requalification-01/gatea-summary.txt \
  --x-alive 0 --exit-signal 0
```

`handoff-kit/rejudge-r7-04.sh` 一次跑兩格。

---

## 1. 空機／新 Cursor 最小落地

1. Clone 本倉庫到工作站權威路徑（若該路徑已存在，**不要**用 clone 覆蓋；只把本快照當 GitHub 紀錄）：

   ```bash
   git clone -b docs/fdfb1ce-r7-04-handoff-20260917 \
     https://github.com/waydefu/GPU.git /root/projects/GPU加速
   ```

2. 依 `WORKTREE-MAP.md` clone `waydefu/termux-x11` 到 `src/f8-ahb-gatea-case-loop`，checkout **`fdfb1ce`**。凍結 R6 worktree 只要讀，不要改。

3. 讀 `ADB-CONNECT.md`。isolated lane **5038**，`HOME=/data/data/com.termux/files/home`，**不准碰 5037**。serial 用 `handoff-kit/mdns-address-15s.py` live-fetch `_adb-tls-connect._tcp.local.`。

4. 只核對 experimental 已是 `1.03.01-fdfb1ce-16.09.26`。已安裝就 **不要重裝**。APK 本體不在本倉庫；需要時從
   [CI 35103216566](https://github.com/waydefu/termux-x11/actions/runs/35103216566) 下載，SHA256 必須是
   `5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c`。

5. 確認沒有活著的 experimental X3（cmdline 必須是 `termux-x11gpu com.waydefu.x11gpu :3` 才准殺）。Stable `:1` 不准殺。

---

## 2. 重判與 host 驗證（不需要授權）

```bash
# 凍結 judge 單元測試（GPU 副本的 HERE 已改成相對路徑）
python3 evidence/session/gate-a-a1/p2-r7-design/test-judge-r7.py
# 期待：16/16 PASS

# 分類器 host test（需要 case-loop worktree）
cc -O0 -o /tmp/test_gatea_direct_done_class \
  src/f8-ahb-gatea-case-loop/scripts/test_gatea_direct_done_class.c
/tmp/test_gatea_direct_done_class
# 期待：GATEA_DIRECT_DONE_CLASS=PASS

python3 src/f8-ahb-gatea-case-loop/scripts/verify_r7_fatal_propagation.py \
  src/f8-ahb-gatea-case-loop
# 期待：R7_FATAL_PROPAGATION=PASS
```

本倉庫 `core-src/` 也有 classifier 與摘錄，可在沒有完整 worktree 時閱讀；靜態 verifier 仍以 worktree 為準。

---

## 3. 另開授權後：R7-05 怎麼跑（現在不要執行）

**本 PR / 本檔不是授權。** 下列是凍結合約的精確接法，給下一張授權票直接貼。

### 環境（必須寫進 X `/proc/<pid>/environ`，不能只看 shell）

```text
TERMUX_X11_GATEA_PROTO=1
TERMUX_X11_GATEA_TELEMETRY=1
TERMUX_X11_GATEA_TEST_FAULT=post-draw-gl
TERMUX_X11_GATEA_TEST_ARM=1
```

不准帶：R6 OOM、Present requeue、其他 R7 selector、`TERMUX_X11_GATEA_A1`。

### 證據目錄

```text
/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce/r7-05
```

若該目錄已有 `primary-verdict.txt` / `fixture.out` / `logcat-follow.txt`：**STOP，INVALID，不准 retry。**
不准寫進 `runtime-7549e36/r7-qualification-01/`。不准 overlay `r7-04-requalification-01`。

### 命令（授權後才跑；恰好一次；不准 retry）

```bash
SERIAL="$(python3 /root/projects/GPU加速/evidence/session/gate-a-a1/runtime/mdns-address-15s.py)"
# 再 adb connect + devices -l；identity myron；Awake；keyguard false

CELL_ID=r7-05 FAULT=post-draw-gl FIXTURE=direct WAIT_S=12 \
ROOT=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/runtime-fdfb1ce \
SERIAL="$SERIAL" \
bash /root/projects/GPU加速/evidence/session/gate-a-a1/p2-r3-xpump-runtime/run-r7-one-cell-fdfb1ce.sh
```

Runner 會：核對 installed version `1.03.01-fdfb1ce-16.09.26`、新鮮 X3、arm 後觸發一次 `p_r3_single_direct`、跑凍結 `judge-r7.py post-draw-gl`、清 X3。

### 凍結 judge 期待（R7-05 ≠ R7-04）

| 項目 | R7-04（已 PASS） | R7-05（下一格） |
|---|---|---|
| selector | `fbo-incomplete` | `post-draw-gl` |
| 構造鏈 | PUBLISH → LOOKUP_OK | PUBLISH → DRAW |
| 最後 halt | `r-gatea-DIRECT_LOOKUP_FAIL` reason=2 | `x-direct-not-success` reason=2 |
| 語意 | renderer FATAL；preserve publishedFatal | FAILED_QUIESCED；**需要** X-side `x-direct-not-success` |
| event 35 | 恰好 1 | 恰好 1 |
| 成功路徑 | 全 0 | 全 0 |
| timeout reason=4 | 禁止 | 禁止（R7-05 是 DRAW=2，不是 TIMEOUT=4） |

GetImage FAIL 在注入 fatal 後預期，不自動算資格失敗。X `_exit(127)` 預期。不要因為 X 死了就判 FAIL。

Fail-fast：R7-05 FAIL → 清 X3 → **STOP**，其餘格 NOT RUN。不准改 judge 去救。

---

## 4. 禁止清單（抄進下一張授權票）

- 不准重跑 `runtime-fdfb1ce/r7-04-requalification-01`
- 不准重跑 / overlay `runtime-7549e36/r7-qualification-01`
- 不准重跑 B-2、repair-validation、任何 stall-obs、`0d72332` / `a7528bd` oracle
- 不准安裝 `327b028`
- 不准從 R7-05 自動續跑 R7-01+（除非授權寫明整段 R7）
- 不准改 timeout / source / judge / 契約
- 不准碰 Stable / HDMI
- 不准 `logcat -c`、不准 `pkill -f f8-x11gpu`

---

## 5. APK 若遺失

1. 打開 [CI 35103216566](https://github.com/waydefu/termux-x11/actions/runs/35103216566)
2. 下載 **同一 run** 的 APK + unstripped
3. SHA256 必須等於 `5313fc9a7e3e87907fd42ece330124362ab7284d41fbf6e4b492eb12ffd4915c`
4. 只准裝 `com.waydefu.x11gpu`。`install-fdfb1ce.sh` 需 `RUN_INSTALL=YES` 且 CELL=`.../runtime-fdfb1ce/r0`（該 r0 已有安裝紀錄：不要重跑安裝格；若必須重裝，開新 r0 目錄，不要 overlay）

---

## 6. 技能

工作樹視窗不會自動看到專案 skills。讀：

- `/root/projects/GPU加速/.cursor/skills/gate-a-r6-runtime-qualification/SKILL.md`（ADB / 安裝紀律；不要拿來開 R7 格除非授權）
- 本倉庫 `skills/` 副本
- portable：`skills/portable/` 與 `~/.agents/skills/`（evidence-first-gate-test-design、verification-integrity、safe-git-ci-discipline）
