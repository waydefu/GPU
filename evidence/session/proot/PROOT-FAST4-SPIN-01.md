# PROOT-FAST4-SPIN-01 — 「追蹤器忙等」假設被推翻（2026-09-25）

## 假設
微基準顯示每個 ptrace stop 約 30 µs、與處理內容無關（futex no-op 1 停 31 µs、fcntl 2 停 63 µs、fstat 2 停 67 µs）。
推測主因是追蹤器在閒置核心上睡著、被喚醒的延遲；若追蹤器在阻塞前先 `waitpid(WNOHANG)` 忙等，連續攔截（git 的 stat 風暴）應變快。

## 實作
v4 = v2 ＋ `src/tracee/event.c` 在阻塞 waitpid 前忙等 `PROOT_SPIN_US` 微秒（預設 0＝原行為；shadow pipes 期間不忙等）。
`~/build/proot-fast/proot-5.1.107.92-v4`、`build4.sh`、`out4/bin/proot-fast4`（sha256 前綴 `4647b1b9`）。

## 量測 `proot-fast4-spin-01.txt`（`statmix.sh`＋`statmix-run.sh`，PRoot 外經 run-as，交錯兩次）
| 版本 | git_status×10 ms | find×10 ms | stat_storm×3 ms | fstat µs | open+close µs | 總 CPU s |
|---|---|---|---|---|---|---|
| v2 | 1110／1108 | 192／170 | 1942／1934 | 63.4／68.0 | 83.8／77.3 | 5.0／4.8 |
| v4 spin 0（對照，須等於 v2） | 1209／1156 | 173／187 | 2018／1902 | 66.2／60.7 | 89.3／78.1 | 5.2／4.9 |
| v4 spin 20 | 1253／1335 | 184／200 | 2476／2417 | 65.4／60.0 | 121.6／119.2 | 7.0／6.9 |
| v4 spin 50 | 1261／1234 | 237／229 | 2215／2190 | 68.1／61.2 | 102.7／99.3 | 7.3／7.1 |
| v4 spin 100 | 1213／1234 | 219／226 | 2110／2103 | 65.7／62.6 | 97.1／93.5 | 7.1／7.1 |
| v4 spin 200 | 1201／1214 | 221／228 | 2080／2126 | 71.2／69.0 | 88.8／96.8 | 7.0／7.4 |

## 結論
**假設被推翻**：忙等下 fstat 單次成本不變，整體更慢且總 CPU +40–50%。每次 stop 的 ~30 µs 不是追蹤器喚醒延遲。v4 不部署。
下一步候選：以 strace 等工具看追蹤器每個 stop 自己發出的 syscall 數與成本（PTRACE_GETREGSET／process_vm_readv／/proc 讀取等），
或量 tracee 端喚醒；尚未進行。
