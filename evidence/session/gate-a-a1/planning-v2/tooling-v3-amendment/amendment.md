# TOOLING AUTHORITY AMENDMENT — runner v2 -> v3 (F1)

DATE      2026-09-21
REASON    F1 (see ../c1-preflight-20260921/preflight-verdict.md): v2 wrote
          EXPECT_APK_SHA256 / EXPECT_BUILD_ID / EXPECT_SIGNER into
          artifact-binding.json but never compared them to the device.
SCOPE     Runner only. Judge, spec, orchestration, collector, obs-stream and the
          ten-cell set are UNCHANGED and keep their pinned hashes.
APPEND-ONLY  v2 and v1 are untouched and remain byte-identical to their pinned
          hashes; v3 is a new file, exactly as v2 was added beside v1.

## New authority
```
RUNNER (current)      p2-r8-runtime/run-r8-one-cell-b984ded-v3.sh
                      16808107886123e8b7b3de4e1654df227185ff2f838d258e350d62caecc164ce
MANIFEST (current)    p2-r8-runtime/runtime-b984ded/r8-runtime-tooling-manifest-v3.json
RUNNER (superseded)   run-r8-one-cell-b984ded-v2.sh
                      53e0c6b8ac613eab7dcce970438e7adc071bddcde4d7e1e202763bfe62de44e5
                      SUPERSEDED, not FORBIDDEN - it is correct, merely weaker on
                      artifact verification. v1 remains FORBIDDEN (frozen judge).
```

## Delta
1. Before any device mutation, read the installed APK back and compare:
   `pm path com.waydefu.x11gpu` -> `sha256sum <path>` vs EXPECT_APK_SHA256.
   Mismatch -> `refuse "apk_sha256_mismatch got=<...>"` -> exit 3 R8_BLOCKED,
   **attempt NOT consumed**. Placed inside the preflight region, after the
   versionName gate and before `am force-stop`.
2. `artifact-binding.json` gains a `provenance` block stating how each field was
   established: apk_sha256 MEASURED, signer DERIVED (byte-identical APK implies the
   embedded certificate), build_id NON-DISCRIMINATING, source_sha BOUND.
3. VALIDATE_ONLY marker renamed V2 -> V3 so a dry run cannot misreport which runner
   produced it. No functional consumer of that string exists.
4. MANIFEST path -> manifest-v3.json, which records `previous_runner_*` for lineage.

## Why build_id is NOT compared
`3658dd1f8047bfbb9d4671b269305313adaf1aa7` is the ELF build-id of the native
library and is **identical across product fb4f017 and b984ded** (see
p2-r8-design/GATE-A-P2-R8-INSTALL-BIND-PASS-{FB4F017,B984DED}-20260918.md). It
cannot establish artifact identity, so comparing it would add ceremony, not proof.
apk_sha256 is the discriminating check and is now enforced.

## Verification performed before use
```
bash -n                                    PASS
manifest self-consistency (3 runner hashes) PASS
VALIDATE_ONLY dry run                      R8_LIVE_RUNNER_B984DED_V3_VALIDATE_ONLY R8-C1, exit 0
bad cell rejection                         R8_BLOCKED bad_cell c1, exit 3
F1 block positive path (live device)       VERIFY_OK apk_sha256=0d06de68...d398d3, rc=0
F1 block negative path (forced mismatch)   R8_BLOCKED apk_sha256_mismatch, rc=3
attempt-09 directory after all of the above ABSENT - nothing consumed
```
