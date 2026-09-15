# B3a U4-C2 artifact provenance — artifact 10160961032

日期：2026-09-11（Asia/Taipei）  
狀態：artifact-side **PASS**；C2 等待 installed APK fresh readback。

## Artifact binding

```text
repository: waydefu/termux-x11
artifact ID: 10160961032
artifact name: termux-x11-unstripped-libraries-for-ndk-stack
workflow run: 34498279213
workflow: Build / debug_build.yml
head branch: qualification/s3-runtime-20260909
head SHA: 1954f82cda9b548ab88f420e428f7296a2d3c72c
artifact bytes: 28124818
GitHub digest: sha256:7edf7776eba65bbf9cbdf1ffabbd2e9c5e79ebf65e6a41c35f9ef9df8e721da5
created: 2026-09-10T15:56:18Z
expires: 2026-12-09T15:50:37Z
run conclusion: success
```

Raw provenance files:

- `artifact-10160961032.api.json`
- `run-34498279213.json`
- `run-34498279213-artifacts.api.json`
- `debug_build.yml.1954f82`

## ZIP proof

```text
local ZIP: artifact-10160961032.zip
ZIP bytes: 28124818
ZIP SHA256: 7edf7776eba65bbf9cbdf1ffabbd2e9c5e79ebf65e6a41c35f9ef9df8e721da5
ZIP digest comparison: PASS
entries: 40
duplicate names: 0
ZipFile.testzip(): None
```

## ARM64 unstripped extraction

```text
member: 01x55434/obj/arm64-v8a/libXlorie.so
output: libXlorie-arm64-v8a-unstripped.so
uncompressed bytes: 20981104
SHA256: 2d555d13b97b1554cc37574f2e0541d0afd1a98b361c7b572c7d9c9739fb9ba6
ELF: ELF64 LSB shared object, ARM aarch64
stripping: not stripped
DWARF: .debug_loc/.debug_abbrev/.debug_info/.debug_ranges/.debug_str/.debug_line/.debug_aranges present
ELF Build ID: b15d75a5a3d4217eb736208f18d5a1aa84280bf9
expected Build ID: b15d75a5a3d4217eb736208f18d5a1aa84280bf9
Build ID comparison: PASS
```

## Installed APK comparison

```text
serial: 10.56.180.219:39035
model/codename: 25102PCBEG / myron
package: com.waydefu.x11gpu
package path: /data/app/~~sq1GIvXb2CltEkye8jmvcg==/com.waydefu.x11gpu-uW05Pf569Dzy4Cj_3iBH7g==/base.apk
versionCode: 15
versionName: 1.03.01-1954f82-09.09.26
installed APK SHA256: 5cc87f4121bfe52e7504348e36c36421b28355549b3b26fe031f175a234c1dce
APK ZIP integrity: testzip=None, entries=493, duplicates=0
embedded member: lib/arm64-v8a/libXlorie.so
embedded library SHA256: da79b03df087435813ff494b62eebc792d4df074a8b520c3006f7288b06903fd
embedded ELF: AArch64 DYN, stripped
embedded Build ID: b15d75a5a3d4217eb736208f18d5a1aa84280bf9
unstripped library SHA256: 2d555d13b97b1554cc37574f2e0541d0afd1a98b361c7b572c7d9c9739fb9ba6
unstripped Build ID: b15d75a5a3d4217eb736208f18d5a1aa84280bf9
Build ID comparison: PASS
```

The stripped embedded library and unstripped symbol library necessarily have
不同 SHA256；the authoritative binding is the identical ELF Build ID. The
unstripped file is retained at `libXlorie-arm64-v8a-unstripped.so` and contains
DWARF `.debug_*` sections.

## C2 prerequisite verdict

```text
artifact 10160961032: PASS
ZIP SHA256/digest: PASS
ARM64 unstripped extraction: PASS
unstripped Build ID == expected embedded Build ID: PASS
installed APK embedded Build ID == expected: PASS
C2 prerequisite: PASS
```

依批准，下一步直接開始三次完整 `CPU-A → R3-A → CPU-B → R3-B`。
