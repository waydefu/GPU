# Stage 7.5 resource audit — source baseline b649b5de

This is a source accounting, not a device measurement or an acceptance receipt. Baseline default parameters: 32 daemon clients, 16 global native workers, 8 local workers per relay (configurable to 16). Number of independently launched relays is unbounded. PSS acceptance remains 256 MiB, 64 threads, 192 FD; no source-level arithmetic below establishes any of these limits. The plan's A/R/J and device high waters are pending.

| Component / lifetime | Baseline allocation or count ceiling and worst-case accounting | Unbounded or not established |
|---|---|---|
| Selective relay input | frame 4 MiB; incomplete stdin buffer checked at 8 MiB after 64 KiB read; replay copy 4 MiB; to-daemon queue checked at 8 MiB after processing a read | Multiple frames and parsed request objects can coexist transiently; pending native IDs were unbounded, as was completed local response deque. Python container overhead and overshoot need measurement. |
| Selective relay output | incomplete native frame 16 MiB plus 64 KiB read; stdout stops reads at 8 MiB and aborts above 24 MiB + 64 KiB | local workers serialize outside queue lock; up to 8 active plus accumulated completed responses. Response copies and parsed JSON objects add to these thresholds. |
| Raw relay | 8 MiB per direction + 4 MiB replay; read sizes bounded by remaining space, thus nominal 20 MiB per relay | kernel socket/pipe buffers, object overhead and auto-reconnect/replay transient copies. Raw traffic bypasses selective pending limits. |
| Local fallback | input up to 8 MiB + read chunk; output hard 16 MiB; 8 default workers, maximum 16 | each worker builds and serializes result before output check; stdin JSON objects and worker working sets coexist. |
| Daemon session | 4 MiB input plus up to 64 KiB received before check, 16 MiB output hard; 32 default sessions give nominal 640 MiB for these two buffers alone | serialization occurs before output capacity check; parser objects, transient frames and kernel buffers not included. |
| Daemon global work | default 16 admitted workers across all sessions; max-clients counted before session thread start, plus one accepted FD during admission | user-configurable limits; worker result/JSON copies and cleanup threads overlap. No global byte reservation. |
| Tree / text results | up to 50,000 tree entries and 5,000 search matches retained prior to 1 MiB final text trimming; search reads 2 MiB/file and text/splitlines create copies | directory fanout from os.walk/sorted and path sizes; retained Python objects and first full json.dumps cannot be bounded from the output cap. |
| JSON summary | JSON 16 MiB raw plus decoded string and parsed object; JSONL total 32 MiB with 1 MiB line | Python object expansion depends on input, allocator and implementation; no safe PSS bound follows from byte cap. |
| Git / regex child, per admitted work | stdout 2 MiB + stderr 256 KiB before copies; temporary stdin, wake pipe, optional pidfd, two output pipes | child address space, its threads, subprocess internals and short-lived descendants are not hard bounded; byte caps govern captured output only. |
| Threads, baseline | daemon main + ≤32 sessions + ≤16 workers = 49; per selective relay main + ≤8 local workers = 9; fallback adds output thread = 10; Git/regex child task count extra | 8 selective relays give 49 + 8×9 = 121 before child tasks, helper/control processes and teardown overlap. Not a global 64 cap. |
| FDs, baseline | per selective relay: stdio 3 + socket 1 + two pipes 4 + selector FD where applicable; daemon session: accepted socket 1 + wake pipe 2; each child work adds temp input, pipes, wake pipe and optional pidfd | daemon listener/control/log, inherited descriptors, transient accept, files, child FDs and platform selector/pidfd vary. Total cannot be inferred as ≤192. FD entries count separately per PID. |
| Admission / cleanup | daemon sessions and workers are separately count-limited; local fallback still runs after daemon failure | no launcher-wide quota, no byte reservations spanning parsing, worker generation, output and cleanup; cancellation / exit can overlap resource release. |

Changes accompanying this audit add a **cooperative opt-in two-relay lease**, shared across raw, selective, fallback and retry paths, and cap selective pending native IDs at 16 and canonical IDs at 1024 UTF-8 bytes. Cancellation removes tracking before execution necessarily stops, so this is not a hard bound on outstanding execution; the daemon worker count remains its execution limit. Busy requests return -32000. This is a count bound, not a byte or PSS budget. Existing standalone deployments remain unlimited in relay count unless every launcher sets the same `F8_HYBRID2_BUDGET_DIR`. Provision a private owner-only persistent directory (mode 0700), shared by the *same actual lock filesystem* across participants; never delete/replace slot files while any participant may be running. On Linux flock releases on process exit, but PRoot/native shared locking must be tested on the actual filesystem. A different directory, uncooperative direct daemon client, another daemon, or a bypassing relay is outside the quota. The directory and slot files are trusted administrator-controlled state, not a security boundary against same-UID processes.

For an isolated candidate use a common directory and explicit `--max-local-inflight 1`; independently start daemon with `--max-clients 2 --max-inflight 2`. This setup has at most two cooperative relay processes, two admitted daemon sessions and two daemon workers, but it does **not** constrain JSON expansion, OS PSS, external subprocess tasks/FD, serialization copies, local output accumulation or direct clients. It is not approved for scaling or production use. Verify lease contention and crash reclamation across actual native/PRoot processes before reliance. No device tests were performed in this change.

Next: implement byte reservations held through output drain and cleanup, bounded incremental result generation/serialization, and admission encompassing daemon and every eligible client/child. Verify error paths and exact output semantics before obtaining representative single-client peak data, A/R/J, and independent 1/2-client validation; then evaluate larger levels. Until then Stage 7.5 global hard budget and soak remain BLOCKED / UNVERIFIED.

Example, after provisioning the **same** private directory in both namespaces and starting the isolated daemon (replace both paths and map with verified equivalents):

```sh
install -d -m 700 /path/to/private-budget
python3 -B scripts/f8_hybrid2_daemon.py --socket /path/to/run/hybrid.sock \
  --home /path/to/clean-home --tmp /path/to/clean-tmp \
  --map /guest/fixture=/host/fixture --max-clients 2 --max-inflight 2
# In each authorized relay launcher, export this exact shared directory:
export F8_HYBRID2_BUDGET_DIR=/path/to/private-budget
python3 -B scripts/f8_hybrid2_relay.py --socket /path/to/run/hybrid.sock \
  --map /guest/fixture=/guest/fixture --max-local-inflight 1 --no-fallback
```

For fallback testing omit `--no-fallback`; the lease is held before connection attempts and through fallback/early-EOF retry. Disable automatic startup or ensure an independently controlled daemon uses the specified limits: relay `--auto-start` does not forward these daemon limits. The lock FD adds one FD to each leased relay. This example does not establish Git trust; use the existing trusted-roots policy and independently validated fixture. Slots remain fixed at two because no reservation arithmetic supports increasing them.
