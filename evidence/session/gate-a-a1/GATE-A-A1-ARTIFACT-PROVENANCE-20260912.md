# Gate A A1 Artifact Provenance — 2026-09-12

CONCLUSION
Artifact verification: PASS, with explicit qualified limitations. Gate A A1 evidence closure: QUALIFIED PASS. This packet is artifact/provenance evidence only; it is not runtime qualification.
Scope: read-only against source, remote, and device. Writes were confined to evidence files under /root/projects/GPU加速/evidence/session/gate-a-a1/, including the two requested deliverables. No source/worktree edit, commit, push, dispatch/rerun, PR, merge, SDK install, ADB/device/package operation, Stable :1 operation, Experimental :3 operation, or HDMI operation was performed. HANDOFF.md was not edited.

SOURCE / CHECKPOINT
repository=waydefu/termux-x11
fork remote=https://github.com/waydefu/termux-x11.git
worktree=/root/projects/GPU加速/src/f8-ahb-gatea-a1
branch=qualification/gatea-a1-microprobe-20260912
base=a6cc7952861b8a63740d42bf78553573cfa0eec0
checkpoint=3db76baa15c0a6c13460349060485d863102dc86
local HEAD=3db76baa15c0a6c13460349060485d863102dc86
parent working tree default status=CLEAN; status with --ignore-submodules=none shows exactly the eight authorized nested dirty submodules below
parent git diff --check=PASS
sha256(git diff BASE..CHECKPOINT --binary)=1bd62b704f8558c485cb5891ad098e8b551c4436ca20437d1a40cbacc4bfeac7
changed parent paths exactly four:
  A lorie/src/main/cpp/lorie/gatea_a1_microprobe.cpp
  A lorie/src/main/cpp/lorie/gatea_a1_microprobe.h
  M lorie/src/main/cpp/lorie/renderer.cpp
  M lorie/src/main/cpp/recipes/xserver.cmake
new-file hashes: gatea_a1_microprobe.cpp=ec7e11ad6f934dff61705debef8d21169cdc43ec349acf3e7c4d7bd08837457b; gatea_a1_microprobe.h=abe6d1c4ce585a00b3c863a5d42c66869f38e5c2dd2e62519232b679415ca4cc

SUBMODULE PATCH-STATE CLOSURE
The live nested audit matched /tmp/gatea-a1-submodule-audit-01.txt. All eight authorized configure-time dirty states have pin=head, exact tracked modified sets, zero diff-check errors, and no untracked/.orig/.rej residue. Parent gitlinks were not changed. Result=ALL_TRACKED_PATCH_STATE; CI_REPRODUCIBLE=YES; residue=NONE.
  lorie/src/main/cpp/libepoxy   pin=head=c84bc9459357a40e46e2fec0408d04fbdde2c973   status_files=1  diff_sha256=7ba07fbb866977622b1f072b805b29dcaacdf208d6eb6d8cc761ea4f61b4c59d
  lorie/src/main/cpp/libx11      pin=head=6c75545a1deb51f5903992c52af6bc35cc9bc103   status_files=4  diff_sha256=c0a31f4e34eaf867412dee1413328e250424b82301fe52bdc416e9361b23b71a
  lorie/src/main/cpp/libxkbfile pin=head=42e5dedd7fd3c7c73f3870a8751893c03c1afc69   status_files=1  diff_sha256=b336a927917dfca924fc48e46c8f18653ea630163de47e0edfddcdb3adabb4cf
  lorie/src/main/cpp/libxtrans   pin=head=cf05ba4a10c90da2c63805a5375e983b174e28b0   status_files=2  diff_sha256=aa3442ab3dc0c871cd410662dfd27ba79192195bbeda4059a02e6042d31062a1
  lorie/src/main/cpp/pixman      pin=head=9cc163c9da0fb4da430641715313d95a6ec466d9   status_files=1  diff_sha256=b6e4fe1d15c1e1155d123dc95435cccd7aa3594bceea69789e8e250634c56904
  lorie/src/main/cpp/xkbcomp     pin=head=2c7789785981ad1fce3858c726615b49293f7de0   status_files=5  diff_sha256=9646b19922e8d4583aee24e264d815e14bbb2b6f1667311a844db09aefe987b6
  lorie/src/main/cpp/xorgproto   pin=head=fcb7e9a1a0b593a44740d83b0babddd331fea830   status_files=1  diff_sha256=178005aabd012a8d80aef25d2a9d68fb52afe230aef724470caca3d08596de0b
  lorie/src/main/cpp/xserver     pin=head=65d790bd208ec380b196eb98f144abb0b32e334d   status_files=23 diff_sha256=d3f6e7a9c33f724a155d9116ca90ae897878491736a464909f4aa787924953bf

LOCAL PACKAGING BOUNDARY
command=ANDROID_HOME=/root/android-sdk ANDROID_SDK_ROOT=/root/android-sdk ./gradlew :lorie-app:assembleStandaloneDebug --console=plain
real_exit_code=1; first_failing_task=:lorie:compileDebugAidl
host uname=aarch64
/root/android-sdk/build-tools/36.0.0/aidl=file reports ELF 64-bit LSB pie executable, x86-64, interpreter /lib64/ld-linux-x86-64.so.2
classification=HOST TOOLING; local APK=NOT PRODUCED
No SDK install, license acceptance, source fix, or workflow change was used. The CI APK below is not a local packaging result.

REMOTE / CI BINDING
Fresh remote branch read: refs/heads/qualification/gatea-a1-microprobe-20260912 -> 3db76baa15c0a6c13460349060485d863102dc86; exact checkpoint required and matched.
Fresh run read: repository=waydefu/termux-x11; run=34688831275; run_number=29; attempt=1; workflow=Build; path=.github/workflows/debug_build.yml; event=workflow_dispatch; status=completed; conclusion=success; head_branch=qualification/gatea-a1-microprobe-20260912; headSha=3db76baa15c0a6c13460349060485d863102dc86; Build job 103540430106=completed/success.
Run URL=https://github.com/waydefu/termux-x11/actions/runs/34688831275
Workflow blob at checkpoint: sha=a13327a01f8200e10a16ffa3c5473394d33edb4e.
Fresh run-scoped artifact API endpoint=gh api repos/waydefu/termux-x11/actions/runs/34688831275/artifacts. Both selected artifact records reported workflow_run id=34688831275, branch=qualification/gatea-a1-microprobe-20260912, head_sha=3db76baa15c0a6c13460349060485d863102dc86.
CI runner/toolchain recorded from the retained run: Ubuntu 24.04.5 / x64; Temurin Java 17.0.20+1; Gradle 9.7.0; AGP 9.3.1; NDK 29.0.14206865; CMake 3.22.1; compileSdk=34; minSdk=24. The workflow build completed 160 actionable tasks and uploaded the exact named artifacts.

ARTIFACT METADATA AND HASHES
Exact selected APK artifact name=termux-x11-universal-debug; id=10296119824; provider size=7337634 bytes; provider digest=sha256:c9cc484b464b6bd5dbecf9c72ba93fc3018431800c19f9f4c34f7fa2ba62416b; expired=false; created/updated=2026-09-12T10:39:40Z; expires=2026-12-11T10:35:03Z.
Exact selected unstripped artifact name=termux-x11-unstripped-libraries-for-ndk-stack; id=10296831247; provider size=28251752 bytes; provider digest=sha256:2f9b49a758220707674d01bacfc1d67503beaad5a6aa28860a4249953596bd22; expired=false; created/updated=2026-09-12T10:39:47Z; expires=2026-12-11T10:35:03Z.
Provider sizes/digests above are for the GitHub artifact archives, not the materialized member files.
Fresh APK=/root/projects/GPU加速/evidence/session/gate-a-a1/artifacts/34688831275/termux-x11-universal-debug.apk; bytes=14957326; SHA256=5a241f1fb726ecd709ecd601d80f607cbe3413a061d9c1cec66fd27009603583.
Fresh unstripped ARM64=/root/projects/GPU加速/evidence/session/gate-a-a1/artifacts/34688831275/01x55434/obj/arm64-v8a/libXlorie.so; bytes=21077008; SHA256=6612aa2ee2888d32a3892cad9edb807e90dd21f524557e7af83188b08252a79f.
Embedded member extracted from the fresh APK=/root/projects/GPU加速/evidence/session/gate-a-a1/apk-verification/libXlorie-embedded.so; bytes=3644024; SHA256=aa39b55588b67da1c50670fae7885c864b667425fb00c9af4c2af20ebe1df40e.
No substitute download was used.

APK IDENTITY / SIGNER
Package analyzer readback: applicationId=com.waydefu.x11gpu; versionCode=15; versionName=1.03.01-3db76ba-12.09.26; expected ABI member lib/arm64-v8a/libXlorie.so=present.
Working Java-based apksigner=/root/android-sdk/build-tools/36.0.0/apksigner, version=0.9. Both literal commands `verify --verbose --print-certs` returned 0 and verified APK Signature Scheme v2.
Fresh Gate A A1 APK signer certificate SHA-256=b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1.
Retained Experimental P2-B.2 APK=/root/projects/GPU加速/evidence/session/p2-b2/termux-x11-universal-debug.apk; SHA256=e47c55164397f356cb4806939e0c9508de3b06fdaa0afde2f793fa6a772a3985; signer certificate SHA-256=b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1.
Certificate comparison=EXACT MATCH. This was an Experimental-only comparison; Stable was not inspected.

ZIP INTEGRITY / ALIGNMENT
Rerun existing verifier=/root/projects/GPU加速/evidence/session/gate-a-a1/verify-apk.py. Its `ZipFile.infolist()` central-directory records are iterated at lines 63-80; every record with compress_type=ZIP_STORED is checked by reading the corresponding 30-byte local header and computing `header_offset + 30 + name_len + extra_len`. The existing checker therefore does cover all STORED entries; a disposable verifier was not needed.
Fresh APK ZIP testzip=PASS (bad_member=null); central records/member_count=493; duplicate names=0; ARM64 member=present.
Structural equivalent check (not formal zipalign execution): stored-entry count=259; local-header data offsets divisible by 4=259/259; failures=0; result=PASS. This is the specified STORED data-offset invariant checked by `zipalign -c -v 4` without `-p/-P`.
formal host zipalign binary: BLOCKED (x86-64 on aarch64). Existing command was `/root/android-sdk/build-tools/36.0.0/zipalign -c -v 4 <fresh APK>`, returncode=127; `file` identified x86-64 and the retained stderr is FileNotFoundError on this aarch64 host. No formal zipalign PASS is claimed.

ELF / BUILD ID / PROBE
Embedded and unstripped `file`/`readelf -h` machine=AArch64. Embedded Build ID=8036f683d110370a7a39dfd719cae9a6ee0adee3; unstripped Build ID=8036f683d110370a7a39dfd719cae9a6ee0adee3; embedded/unstripped Build ID equality=PASS.
Both dynamic dependency reports contain no full libX11. `eglGetNativeClientBufferANDROID` is absent from undefined-symbol census in both. Historical undefined-symbol census is clear in both for xorg_backtrace, ExaDoPrepareAccess, create_bits_picture, fbComposite, pixman_image_composite, and loriePrepareAccess.
GATEA_A1 marker in embedded strings=YES; marker in unstripped strings=YES. `gateaA1MicroprobeRun` in unstripped `nm -a -C`=YES. Embedded dynamic `nm -D -C` export=NO, consistent with hidden visibility. Probe body at checkpoint HEAD via `git show`=YES.

WORKFLOW COVERAGE LIMITS
The exact workflow at checkpoint is the blob above. It uses mutable refs: actions/checkout@v7, gradle/actions/wrapper-validation@v6.3.0, actions/setup-java@v5, actions/cache@v6, actions/upload-artifact@v7, and andelf/nightly-release@main; the run log records resolutions for this run, but the workflow is not SHA-pinned. `runs-on: ubuntu-latest` is also a moving runner label.
No workflow-native event-SHA assertion is present: there is no step comparing `${{ github.sha }}` with `git rev-parse HEAD` and failing on mismatch. The checkout log and fresh external branch/run/artifact read-back all bind this observed run to the exact checkpoint, but that mitigation is not a workflow-native assertion.
No workflow-native submodule pin/status/patch-state assertion is present: the workflow has `submodules: false`, then runs `git submodule update --init --recursive --jobs 8 --depth 1`, without asserting expected gitlink SHAs or tracked patch state. The independent local pin/diff audit above mitigates this record, but is not a workflow-native assertion.
The workflow has no independent APK ZIP/signer/ELF/Build ID/probe verifier; those checks in this packet are post-run independent evidence. These are retained verification-coverage limitations, not silently promoted to PASS.

STABLE / HDMI / RUNTIME BOUNDARY
Stable `com.termux.x11` / `:1`: no operation by this task; retained state=UNTOUCHED. Experimental `:3`: no operation by this task; retained state=UNTOUCHED. HDMI: no operation; retained state=UNTOUCHED.
No ADB, device, package query, installation, launch, process control, or runtime/X11 probe was performed. Runtime qualification=NOT TESTED. EGL/GL, XKB, correctness, stability, stress, lifecycle, display placement, and live-process identity remain NOT TESTED.

RAW EVIDENCE PATHS
/tmp/gatea-a1-build-provenance-02.stdout
/tmp/gatea-a1-submodule-audit-01.txt
/root/projects/GPU加速/evidence/session/gate-a-a1/checkpoint-source-provenance.txt
/root/projects/GPU加速/evidence/session/gate-a-a1/source-input-preflight-20260912.txt
/root/projects/GPU加速/evidence/session/gate-a-a1/source-copy-verification.txt
/root/projects/GPU加速/evidence/session/gate-a-a1/source/
/root/projects/GPU加速/evidence/session/gate-a-a1/local-packaging.log
/root/projects/GPU加速/evidence/session/gate-a-a1/local-packaging-host-tooling.txt
/root/projects/GPU加速/evidence/session/gate-a-a1/ci-run.log
/root/projects/GPU加速/evidence/session/gate-a-a1/ci-run-view.json
/root/projects/GPU加速/evidence/session/gate-a-a1/ci-run-api.json
/root/projects/GPU加速/evidence/session/gate-a-a1/ci-artifacts.json
/root/projects/GPU加速/evidence/session/gate-a-a1/artifact-download-manifest.json
/root/projects/GPU加速/evidence/session/gate-a-a1/workflow-at-head.yml
/root/projects/GPU加速/evidence/session/gate-a-a1/workflow-at-head-api.json
/root/projects/GPU加速/evidence/session/gate-a-a1/verify-apk.py
/root/projects/GPU加速/evidence/session/gate-a-a1/verify-elf.py
/root/projects/GPU加速/evidence/session/gate-a-a1/apk-verification/
/root/projects/GPU加速/evidence/session/gate-a-a1/elf-verification/
/root/projects/GPU加速/evidence/session/gate-a-a1/artifacts/34688831275/
/root/projects/GPU加速/evidence/session/p2-b2/termux-x11-universal-debug.apk

UNKNOWN / RISK / NEXT
UNKNOWN: formal zipalign could not execute on this host; workflow-native event-SHA and submodule assertions are absent; no runtime GATEA_A1 classification exists.
RISK FLAG: do not install or start runtime qualification until Sol reviews this qualified artifact packet and accepts the formal-tooling and workflow-coverage limitations.
NEXT: Sol review before any runtime qualification.
