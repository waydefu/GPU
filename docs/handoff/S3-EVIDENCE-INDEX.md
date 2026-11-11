# S3 Evidence Index (clean-link checkpoint recorded; retain all evidence until runtime qualification completes)

| Path | Purpose | Authority | Keep/Delete |
|---|---|---|---|
| `/tmp/s3-q1-artifact-34396950445/` | E1b APK, embedded native, hashes, badging and ELF audit | GitHub run 34396950445 / artifact 10122068244 (SUCCESS) | KEEP |
| `/tmp/s3-e1b-arm64-native.log` | E1b ARM64 canonical native build | `BUILD SUCCESSFUL` | KEEP |
| `/tmp/s3-e1b-runtime-summary-20260910.txt` | E1b runtime qualification summary and observability limitation | current E1b runtime authority | KEEP |
| `/tmp/s3-e1b-r3-oracle.out`, `/tmp/s3-e1b-x100.out`, `/tmp/s3-e1b-mixed100.out` | fresh R3 exact and stress results | current correctness/stress evidence | KEEP |
| `/tmp/s3-e1b-xkbcomp-xkb.txt`, `/tmp/s3-e1b-xev-keyboard.log` | fresh XKB compile and modifier keyboard evidence | current XKB evidence | KEEP |
| `/tmp/s3-q1-artifact-34383008399/` | previous S3-Q1 APK/native artifact, hashes, badging and ELF audit | GitHub run 34383008399 / artifact 10116787938 (historical) | KEEP |
| `/tmp/s3-device-preflight-20260910.log` | Termux-native helper loader failure and invalid PRoot probe evidence | historical preflight boundary | KEEP |
| `/tmp/s3-runtime-display-preflight-20260910.txt` | built-in target selection, invalid HDMI-target attempts, and valid displayId=0 attempt | current display/runtime boundary | KEEP |
| `/tmp/s3-activity-displays-after-display0-20260910.txt` | proof Experimental Activity foreground/current focus on displayId=0 | valid internal-display target proof | KEEP |
| `/tmp/s3-crash-symbolization-20260910.txt` | exact APK Build ID, stripped disassembly, PLT/GOT `x17` chain and source call-site forensic report | current native crash forensics | KEEP |
| `/tmp/s3-runtime-logcat-all-20260910-display0.txt` | fresh logcat for valid internal-display launch crash | current runtime crash evidence | KEEP |
| `/tmp/s3-runtime-logcat-all-20260910.txt` | full fresh logcat captured after launch crash | current runtime crash evidence | KEEP |
| `/tmp/s3-runtime-crash-logcat-20260910.txt` | crash-buffer capture without clearing | crash evidence; current tombstone absent | KEEP |
| `/tmp/ci-r3-libs` (28 MB) | R3 CI artifacts: 4-ABI unstripped `libXlorie.so` + APKs | CI run 34168546084 (SUCCESS) | KEEP |
| `/tmp/b3a-fresh-arm64` | pristine-configure manual build dir (526/536 + link-19) | forensic build, verdict C | KEEP |
| `/tmp/b3a-fresh-configure.log` | fresh configure log | provenance | KEEP |
| `/tmp/b3a-fresh-build.log`, `build2.log` | manual fresh build logs (shmem stop → link-19) | provenance | KEEP |
| `/tmp/b3a-pristine-r3` | detached pristine worktree @9822435, pins verified | attribution baseline | KEEP |
| `/tmp/b3a-pristine-gradle*.log` | pristine canonical runs (env fail → setgid → quad → … → link-19) | provenance | KEEP |
| `/tmp/b3a-link.log` | dirty-tree canonical link full error list (19) | link-19 authority | KEEP |
| `/tmp/b3a-dry*.txt`, `/tmp/b3a-pris-dry*.txt` | patch idempotency dry-runs (scmd invariant proof) | patch hygiene proof | KEEP |
| `/tmp/b3a-oldcxx-prov/` | old-`.cxx` provenance (CMakeCache, build.ninja, compile_commands.json, shmem.o SHA256) | stale-state forensics | KEEP |
| `/tmp/b3a-gradle-native.log` | dirty-tree canonical Gradle log (≈ line 1341 = final link) | link-19 authority | KEEP |
| `/tmp/s3-canonical-gradle.log` | S3-X1 canonical Gradle-native arm64 build | clean-link authority | KEEP |
| canonical `libXlorie.so` | `.cxx/Debug/01x55434` arm64 artifact; SHA256 recorded in S3 gate | ELF authority | KEEP |
| `evidence/session/s3/GATE-S3-LINK.md` | S3-E1/X1 patch, build, link, symbol and ELF gate | current S3 link authority | KEEP |
| `evidence/session/s3/GATE-S3-RUNTIME.md` | E1b behavioral qualification, evidence limitation and runtime verdict | current S3 runtime authority | KEEP |
| `evidence/session/s3/provenance-runtime.txt` | E1b candidate/device/runtime provenance | runtime provenance | KEEP |
| `evidence/session/s3/results-runtime.json` | machine-readable E1b artifact and behavioral runtime result | runtime result | KEEP |
| `evidence/session/p2-b3a/` | GATE-P2-B.3a.md; U3/U4 lifecycle, cold-N5, artifact `10160961032` provenance, matching ARM64 unstripped library, and C2 batch16 exact-sequence raw evidence | gate authority: exact batch16 protocol qualified; architecture verdict remains INCONCLUSIVE | KEEP |
| `evidence/session/p2-b2/` | R3 PASS oracle + stress + bounded XFCE | correctness authority | KEEP |
| `evidence/session/p2-b1/`, `p2-a4/`, `exa/`, `present/`, `fence/`, `baseline/` | closed-gate evidence | historical authority | KEEP |
