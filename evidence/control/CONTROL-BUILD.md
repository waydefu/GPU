# Control build 記錄（Phase 1A）

> 歷史建置紀錄（01:29 CST）。本檔的 PID、時間與安裝狀態只屬該次 control build；Experimental／Stable 現況見 `HANDOFF.md`。此 APK **未**裝進 Stable。
> 上游 SHA 與 PR 狀態已於 2026-09-08 15:33 CST 重新查驗，對齊結果見 `TEST-MATRIX.md`。

- upstream HEAD（live `git ls-remote`，2026-09-07）：`9df8b767645aa0d0a2f2576767449df55b41962f`
- PR #1095：OPEN＋MERGEABLE，head `8862681a2396b8494a687af1d2d690d491138e09`（未合併，本輪不用）
- PR #1114：OPEN＋MERGEABLE，head `c48e84e63b156be4412004935b6417cbbfebdfe8`（未合併，本輪不用）
- fork：`waydefu/termux-x11`（2026-09-07 新建，parent `termux/termux-x11`）
- `f8-control`：`9df8b76` ＋ 1 個空 commit `11b82d9`（`chore: trigger workflow indexing on fork`，
  純為讓新 fork 的 Actions 索引 workflow；`git diff 9df8b76..11b82d9` 無程式碼差異）
- fork `master`：同 `11b82d9`（push 觸發索引用；Stable 手機端完全未動）
- 本機 `src/upstream`：clone 完成，`git status --short` 乾淨，16 個 submodule 如下

```
6a8690fc8d26c815e798c588f796eabe9d684cf0 lorie/src/main/cpp/bzip2 (bzip2-1.0.8)
c84bc9459357a40e46e2fec0408d04fbdde2c973 lorie/src/main/cpp/libepoxy (1.5.10)
780d1f6f192a331de7b298a96e23ebc44d2a884b lorie/src/main/cpp/libfontenc (libfontenc-1.1.9)
5ca4ca92f629d9d83e83544b9239abaaacf0a527 lorie/src/main/cpp/libtirpc (libtirpc-1-2-7-rc4)
6c75545a1deb51f5903992c52af6bc35cc9bc103 lorie/src/main/cpp/libx11 (libX11-1.8.13)
a9c65683e68b3a4349afee5d7673b393fb924d2e lorie/src/main/cpp/libxau (libXau-1.0.12)
dd8631c61465cc0de5e476c7a98e56528d62b163 lorie/src/main/cpp/libxcvt (libxcvt-0.1.3)
1192d3bc407348ff316bd3bffc791b3ac73f591b lorie/src/main/cpp/libxdmcp (libXdmcp-1.1.5)
88b9df882c0ea91d7bb468aa4792ef1b6f13aa9d lorie/src/main/cpp/libxfont (libXfont2-2.0.8)
42e5dedd7fd3c7c73f3870a8751893c03c1afc69 lorie/src/main/cpp/libxkbfile (libxkbfile-1.2.0)
89f064748554e11832a3ec783945e1f4c7fe846e lorie/src/main/cpp/libxshmfence (libxshmfence-1.3.3)
cf05ba4a10c90da2c63805a5375e983b174e28b0 lorie/src/main/cpp/libxtrans (xtrans-1.6.0)
9cc163c9da0fb4da430641715313d95a6ec466d9 lorie/src/main/cpp/pixman (pixman-0.46.4)
2c7789785981ad1fce3858c726615b49293f7de0 lorie/src/main/cpp/xkbcomp (xkbcomp-1.5.0)
fcb7e9a1a0b593a44740d83b0babddd331fea830 lorie/src/main/cpp/xorgproto (xorgproto-2025.1-9-gfcb7e9a)
65d790bd208ec380b196eb98f144abb0b32e334d lorie/src/main/cpp/xserver (xorg-server-21.1.24)
```

## 官方 build 環境（`.github/workflows/debug_build.yml`）

- runner：`ubuntu-latest`
- Java：Temurin 17（`actions/setup-java@v6`）
- submodules：`git submodule update --init --recursive --jobs 8 --depth 1`
- build：`./gradlew assembleDebug`
- Gradle wrapper：9.7.1（`gradle-wrapper.properties`）
- AGP：9.3.1（root `build.gradle`）
- NDK：`29.0.14206865`（`lorie/version.gradle`，`termuxX11NdkVersion`）
- compileSdk 34 / targetSdk 34 / minSdk 24
- 產物：`lorie-app/build/outputs/apk/standalone/debug/termux-x11-universal-debug.apk`
  ＋ sharedUid APK ＋ companion deb/pkg ＋ unstripped native libs

## CI run（control APK）

- workflow：Build（`debug_build.yml`），`workflow_dispatch`，ref `f8-control`
- run id：`34048065064`，headSha `11b82d96f07b69df1f6dca5f6be926524920bc43`
- 狀態：見下方 APK 段（成功後補 SHA256）

## APK（✅ 2026-09-07 01:29 CST，run completed/success）

- 路徑：`evidence/control/termux-x11-universal-debug.apk`（14,596,802 bytes，zip 完整性 OK）
- SHA256：`aad3d433f47cf7757d959166ce187b8b679e989289049b73f09a732889ea98e9`
- sharedUid：`evidence/control/termux-x11-universal-sharedUid-debug.apk`（zip OK）
- SHA256：`42fb92cd47aca7c82bb8b94df5c960c38187f8036d0a9dfe9e09a527b4c6cdf3`
- 下載：`gh run download 34048065064 --repo waydefu/termux-x11 -n termux-x11-universal-debug`
- 未安裝到手機，Stable 原封不動（收尾再驗：`:1 -legacy-drawing` PID 10718 存活，裸 glxinfo 仍 llvmpipe）

## Stable 不動聲明

- 手機 Stable `termux-x11 :1 -legacy-drawing`（PID 10718）全程未重啟
- 未安裝／未覆蓋任何 APK；`f8desk`、`f8desk-external` 僅讀取＋sha256 凍結
- 未改全域 GPU env；`f8-gpu` 包裝器未動
