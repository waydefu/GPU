# B3a U4-C2 provenance prerequisite — BLOCKED at artifact retrieval authorization

> **Superseded 2026-09-11** by `B3A-U4-C2-ARTIFACT-PROVENANCE-20260911.md` and
> `B3A-T2-U4-C2-20260911.md`. The exact artifact was later downloaded and its
> Build ID matched; this file remains historical evidence of the earlier block.

日期：2026-09-10（Asia/Taipei）  
狀態：**BLOCKED — no C2 runtime action started**。

## Required binding

C2 batch16 exact-sequence reproduction requires an unstripped ARM64 `libXlorie.so`
with Build ID exactly matching the installed APK embedded library. The installed artifact
is:

```text
source commit: 1954f82cda9b548ab88f420e428f7296a2d3c72c
APK SHA256: 5cc87f4121bfe52e7504348e36c36421b28355549b3b26fe031f175a234c1dce
embedded lib SHA256: da79b03df087435813ff494b62eebc792d4df074a8b520c3006f7288b06903fd
embedded Build ID: b15d75a5a3d4217eb736208f18d5a1aa84280bf9
```

The original S3-Q1 artifact `10125997237` was re-read: its `libXlorie.so` has exactly
that hash and Build ID, but is `stripped` and has no `.debug_*` section. It is an exact
control-flow artifact, not an exact DWARF symbol file.

The historical local unstripped control candidate has a different Build ID
`0c8dfb30410ea08f59180ec9bb8b66991117a014`; it is excluded from C2.

## Exact CI provenance run

The existing `debug_build.yml` uploads `termux-x11-unstripped-libraries-for-ndk-stack`.
No exact-commit run existed, so the unchanged existing workflow was dispatched at remote
branch `qualification/s3-runtime-20260909`; `git ls-remote` confirmed that branch points
exactly to `1954f82…`.

Readback of new run:

```text
run: 34498279213
workflow: Build / debug_build.yml
head branch: qualification/s3-runtime-20260909
head SHA: 1954f82cda9b548ab88f420e428f7296a2d3c72c
conclusion: success
unstripped artifact: 10160961032
name: termux-x11-unstripped-libraries-for-ndk-stack
artifact digest: sha256:7edf7776eba65bbf9cbdf1ffabbd2e9c5e79ebf65e6a41c35f9ef9df8e721da5
expires: 2026-12-09T15:50:37Z
```

## Blocker

Downloading the exact CI unstripped artifact was submitted once and was explicitly blocked
by the execution layer because user consent was not obtained. The artifact was **not**
downloaded; therefore its ARM64 Build ID and its companion debug APK hash have not been
verified against the installed S3-Q1 APK.

A local provenance build was intentionally not used as a substitute: the nominal local
`/root/android-sdk/cmake/3.22.1/bin/cmake` resolves to `/usr/bin/cmake` and reports
`3.28.3`, whereas the S3-Q1 CI requires CMake `3.22.1`. That mixed toolchain cannot prove
an exact matching Build ID.

## Verdict

```text
C2 artifact provenance: BLOCKED_AT_ARTIFACT_RETRIEVAL_AUTHORIZATION
matching unstripped Build ID: NOT VERIFIED
C2 exact sequence: NOT STARTED
batch16 performance completion: NOT STARTED
batch16 original crash classification: observed / non-reproduced (unchanged)
Stable: UNTOUCHED
```

No APK install, Activity start, X3 launch, logcat, oracle, or batch16 client was run in
this C2 provenance step. C2 may begin only after the already-created artifact `10160961032`
is downloaded and its arm64 unstripped `libXlorie.so` is verified to have Build ID
`b15d75a5a3d4217eb736208f18d5a1aa84280bf9`.
