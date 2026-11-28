# Stage 7.6 — acceptance freeze (2026-11-28)

Frozen before any Stage 7.6 device data. Extends the [F13 freeze](F8-HYBRID2-F13-L2S-FREEZE-20261128.md) (its rule and U1–U4/D1–D3 stay as written) and reuses the [7.5 tiered freeze](F8-HYBRID2-STAGE75-TIERED-FREEZE-20261128.md) gates G1–G5 and ceilings (256 MiB PSS, 64 threads, 192 FDs) unchanged. The deployed 4-way pilot, Stable `:1` and Fast9+09c are not touched; every run uses its own run directory, socket and budget directory.

## Scope of the candidate

| # | Change |
|---|---|
| F13 | Native `git_ro` accepts PRoot link2symlink object files only in the exact two-hop shape (F13 freeze). |
| F14 | Path resolution in the policy (`resolve_path`) and link tests in tool walks (`is_link`) detect links with `readlink()`. Under PRoot (proot-fast9), `lstat()` of a link whose target name starts with `.l2s.` fails with `EPERM` or reports the target, so `os.path.realpath`/`islink` treated escaping links as contained (found during F13 work: all four tools read outside the mapped root). |
| A1 | Governed `--auto-start`: the TermuxService bootstrap exports `F8_HYBRID2_BUDGET_DIR` (validated, must be initialised); the relay no longer refuses `--auto-start` in budget mode. |
| A2 | `append_rotating`: one bounded generation, flock + inode re-check; used for the daemon audit log (already rotated at 5 MiB, now multi-process safe) and the relay route log (previously unbounded); direct-start `daemon.out` rotates at 1 MiB. |

Mid-session daemon loss keeps the 7.4 fail-closed behaviour (relay exits; outstanding native calls are never replayed). Recovery is at the next relay start (A1). This is documented, not gated.

## Gates (device, isolated)

| Gate | PASS condition |
|---|---|
| S1 PRoot-made repos, parity | Isolated native daemon with the default `/root/projects` map and the same trusted-root list as the pilot: for every trusted non-worktree repo that has l2s objects, the five F13 D1 commands match `F8_NO_HYBRID=1` byte for byte (`stdout`, `stderr`, `returncode`). A fixture repo created by PRoot git inside the run directory (≥1 l2s object, checked before use) also passes. Worktree checkouts are expected `git-worktree-not-supported` on both routes (unchanged). |
| S2 should-be-red, native | In the fixture: (a) object → link into a PRoot hard link of a non-git file; (b) forged two-hop chain in a non-l2s directory; (c) l2s chain whose final is a directory. Each refused `symlink-escape`; the secret marker appears in no output. |
| S3 should-be-red, PRoot route (F14) | `F8_NO_HYBRID=1` relay: `.l2s.`-named file link and dir chain pointing outside the map, through all four tools: each refused (`symlink-escape` or `l2s-path`), marker absent. Control: the same inputs on the 7.5 candidate scripts leak the marker (expected red). |
| S4 race | 300 native `git_ro cat-file -p <oid>` calls while another process keeps swapping that object between the genuine l2s link and a link to an outside plaintext secret file: zero responses contain the marker; daemon alive; every response is either the correct object, a policy refusal, or a git error. Counts of each are recorded. A second, informational race swaps to an outside **valid** git object and records how often its content is returned (residual check-then-use window shared with all pre-7.6 symlink checks). |
| S5 malicious objects | l2s-shaped object with corrupt zlib, and a 64 MiB zero-blob bomb: `git_ro` returns an error or a bounded/truncated result within the configured output limit and timeout; daemon alive; group peak PSS (daemon + relays + children) ≤ 256 MiB. |
| S6 fallback & auto-start | (a) Governed relay with `--auto-start` and no daemon: daemon is launched through TermuxService, its environment contains the run's `F8_HYBRID2_BUDGET_DIR`, it holds the daemon lease, `max_clients` equals the mode. (b) After the daemon is stopped by `ctl stop`, the next relay start relaunches it. (c) With `disabled.flag`, results come from PRoot and match native output. |
| S7 performance (informational) | Native vs `F8_NO_HYBRID=1` `git_ro` latency p50/p95 (n=20) for `log -n 20 --stat` and `cat-file -p` on two real repos, and policy scan time on the largest object store. Not a gate. |
| M matrix | Modes 2, 4, 6 rerun with `stage75_matrix.py` on the 7.6 candidate; the fixture repo is now created by PRoot git (l2s objects present). Verdict rules G1–G5 unchanged. Mode 8 is not rerun: its HOLD is from the theoretical sum (G3), which these changes do not lower. |
| R regression | Full suite on PRoot and Termux native; GitHub CI on the final head (judged separately). |
| Red lines | Stable `X1` inode, Fast9+09c `deployed.sha256`, pilot `tools/hybrid2/DEPLOYED.sha256`, pilot daemon pid, and `~/.claude.json` unchanged from start to end. |

F13 is GO only if S1, S2, S4 and S5 pass and the matrix keeps its verdicts. Otherwise `git_ro` stays on the PRoot route in the pilot.
