#!/data/data/com.termux/files/usr/bin/bash
# deploy-proot-candidate.sh — Safe, verifiable, auto-rolling-back deployment of fast9-combined (patches 01-09 + 09b + 09c).
#
# Defaults to --dry-run (builds in temp staging, verifies strings/SHA256/regression, leaves live out8 untouched).
# Live deployment requires explicit: --apply --confirm-live (and native Termux TracerPid=0 recommended).
set -euo pipefail

MODE="dry-run"
CONFIRM_LIVE=0
ALLOW_NO_REGRESS=0
CLAUDE_SMOKE=0
PREFIX_DIR="/data/data/com.termux/files/usr"
PROOT_ROOT="/data/data/com.termux/files/home/build/proot-fast"
TARGET_OUT="${PROOT_ROOT}/out8"
BASE_ZIP="${PROOT_ROOT}/proot-5.1.107.92.zip"
BACKUP_ROOT="${PROOT_ROOT}/backups"

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/release-files.sh"
REPO_DIR=$(cd -- "${SCRIPT_DIR}/.." && pwd)
PATCH_DIR="${REPO_DIR}/patches"
REGRESS_BIN="${PROOT_REGRESS_BIN:-}"
UBU_ROOTFS="${PREFIX_DIR}/var/lib/proot-distro/containers/ubuntu/rootfs"

usage() {
  cat <<'EOF'
Usage: deploy-proot-candidate.sh [OPTIONS]
  --dry-run              Build and verify candidate in temp staging without touching target-out (default)
  --apply                Actually install candidate into --target-out (requires --confirm-live)
  --confirm-live         Explicit acknowledgement before mutating target-out
  --target-out <dir>     Destination out8 directory (default: ~/build/proot-fast/out8)
  --backup-root <dir>    Backup directory (default: ~/build/proot-fast/backups)
  --base-zip <file>      Clean proot-5.1.107.92.zip tarball
  --regress-bin <file>   Compiled fast9_regress binary for mandatory preflight (or set PROOT_REGRESS_BIN)
  --allow-no-regress     Explicitly allow skipping fast9_regress preflight (not recommended)
  --claude-smoke         Also run isolated claude-desktop non-SIGTRAP smoke during --dry-run (auto-runs post-deploy when installed)
  -h, --help             Show this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) MODE="dry-run"; shift ;;
    --apply) MODE="apply"; shift ;;
    --confirm-live) CONFIRM_LIVE=1; shift ;;
    --target-out) TARGET_OUT="$2"; shift 2 ;;
    --backup-root) BACKUP_ROOT="$2"; shift 2 ;;
    --base-zip) BASE_ZIP="$2"; shift 2 ;;
    --regress-bin) REGRESS_BIN="$2"; shift 2 ;;
    --allow-no-regress) ALLOW_NO_REGRESS=1; shift ;;
    --claude-smoke) CLAUDE_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 64 ;;
  esac
done

if [ "$MODE" = "apply" ] && [ "$CONFIRM_LIVE" -ne 1 ]; then
  echo "REFUSED: --apply requires --confirm-live to prevent accidental live overwrite." >&2
  exit 2
fi

TRACER_PID=$(awk '/^TracerPid:/{print $2}' /proc/self/status 2>/dev/null || echo "")
if [ "${TRACER_PID:-}" != "0" ]; then
  echo "REFUSED: deploy-proot-candidate.sh must run in native Termux (TracerPid=0), got TracerPid=${TRACER_PID:-unknown}" >&2
  exit 2
fi

PATCHES=(
  "01-proot-fast-bwrap-compat.patch"
  "02-proot-fast2-kompat-lean.patch"
  "03-proot-fast5-stat-at-enter.patch"
  "04-proot-fast6-statx-at-enter.patch"
  "05-proot-fast7-peercred.patch"
  "06-proot-fast8-autoshard.patch"
  "07-proot-fast9-ioctl-bpf.patch"
  "08-proot-fast9-geteventmsg.patch"
  "09-proot-fast9-no-close-stop.patch"
  "09b-terra-claude-host-fix.patch"
  "09c-netlink-socket-identity.patch"
)

echo "=== DEPLOY PREFLIGHT mode=$MODE target=$TARGET_OUT ==="
[ -f "$BASE_ZIP" ] || { echo "Missing base zip: $BASE_ZIP" >&2; exit 3; }
[ -d "$TARGET_OUT/bin" ] && [ -x "$TARGET_OUT/bin/proot-fast8" ] || { echo "Invalid target-out: $TARGET_OUT" >&2; exit 3; }
TARGET_OUT=$(cd -- "$TARGET_OUT" && pwd -P)
for p in "${PATCHES[@]}"; do
  [ -f "$PATCH_DIR/$p" ] || { echo "Missing patch: $PATCH_DIR/$p" >&2; exit 3; }
done
if [ "$ALLOW_NO_REGRESS" -ne 1 ]; then
  if [ -z "$REGRESS_BIN" ] || [ ! -x "$REGRESS_BIN" ]; then
    echo "REFUSED: --regress-bin <compiled-fast9_regress> (or PROOT_REGRESS_BIN) is required and must be executable (or pass --allow-no-regress)." >&2
    exit 3
  fi
  if [ ! -d "$UBU_ROOTFS" ]; then
    echo "REFUSED: Ubuntu rootfs missing at $UBU_ROOTFS for mandatory fast9_regress preflight (or pass --allow-no-regress)." >&2
    exit 3
  fi
fi
if [ "$CLAUDE_SMOKE" -eq 1 ] && [ ! -e "$UBU_ROOTFS/usr/bin/claude-desktop" ]; then
  echo "REFUSED: --claude-smoke requested, but $UBU_ROOTFS/usr/bin/claude-desktop is missing." >&2
  exit 3
fi

STAGE_DIR=$(mktemp -d "${PREFIX_DIR}/tmp/fast9-deploy.XXXXXX")
cleanup() {
  rm -rf "$STAGE_DIR"
}
trap cleanup EXIT

echo "1. Extracting clean source and applying patches 01..09 + 09b + 09c (fuzz=0)..."
"$PREFIX_DIR/bin/unzip" -q "$BASE_ZIP" -d "$STAGE_DIR"
SRC_ROOT=$(find "$STAGE_DIR" -maxdepth 2 -type d -name 'proot-*' | head -n 1)
[ -n "$SRC_ROOT" ] && [ -d "$SRC_ROOT/src" ] || { echo "Failed to locate extracted proot source" >&2; exit 4; }

for p in "${PATCHES[@]}"; do
  echo "   applying $p"
  "$PREFIX_DIR/bin/patch" -d "$SRC_ROOT" -p1 --fuzz=0 --batch -s < "$PATCH_DIR/$p"
done

echo "2. Building proot-fast9 (PROOT_UNBUNDLE_LOADER=$TARGET_OUT/libexec)..."
BUILD_HOME="$STAGE_DIR/home"
BUILD_TMP="$STAGE_DIR/tmp"
mkdir -p "$BUILD_HOME" "$BUILD_TMP" "$STAGE_DIR/out/bin" "$STAGE_DIR/out/libexec"
env -i \
  PATH="$PREFIX_DIR/bin:/system/bin:/bin" \
  PREFIX="$PREFIX_DIR" \
  HOME="$BUILD_HOME" \
  TMPDIR="$BUILD_TMP" \
  CPPFLAGS='-DARG_MAX=131072 -DVERSION=\"5.1.107.92-fast9\"' \
  "$PREFIX_DIR/bin/make" -C "$SRC_ROOT/src" clean >/dev/null 2>&1 || true

env -i \
  PATH="$PREFIX_DIR/bin:/system/bin:/bin" \
  PREFIX="$PREFIX_DIR" \
  HOME="$BUILD_HOME" \
  TMPDIR="$BUILD_TMP" \
  CPPFLAGS='-DARG_MAX=131072 -DVERSION=\"5.1.107.92-fast9\"' \
  "$PREFIX_DIR/bin/make" -C "$SRC_ROOT/src" proot \
    SHELL="$PREFIX_DIR/bin/sh" \
    CC="$PREFIX_DIR/bin/clang" \
    OBJCOPY="$PREFIX_DIR/bin/llvm-objcopy" \
    PROOT_WITH_LIBANDROID_SHMEM=true \
    PROOT_UNBUNDLE_LOADER="$TARGET_OUT/libexec" \
    -j2 > "$STAGE_DIR/build.log" 2>&1

install -m 755 "$SRC_ROOT/src/proot" "$STAGE_DIR/out/bin/proot-fast8"
install -m 755 "$SRC_ROOT/src/loader/loader" "$STAGE_DIR/out/libexec/loader"
if [ -f "$SRC_ROOT/src/loader/loader-m32" ]; then
  install -m 755 "$SRC_ROOT/src/loader/loader-m32" "$STAGE_DIR/out/libexec/loader32"
fi

echo "3. Verifying embedded loader path, version string, and SHA256..."
STRINGS_BIN=$("$PREFIX_DIR/bin/strings" "$STAGE_DIR/out/bin/proot-fast8")
printf '%s\n' "$STRINGS_BIN" | grep -qF "${TARGET_OUT}/libexec/loader" || {
  echo "FAIL: embedded loader path does not match ${TARGET_OUT}/libexec/loader" >&2; exit 5;
}
printf '%s\n' "$STRINGS_BIN" | grep -qF "5.1.107.92-fast9" || {
  echo "FAIL: version string 5.1.107.92-fast9 missing" >&2; exit 5;
}
printf '%s\n' "$STRINGS_BIN" | grep -qF "shared-memory-region" || {
  echo "FAIL: shared-memory-region string missing (09b-terra-claude-host-fix.patch not active?)" >&2; exit 5;
}
if printf '%s\n' "$STRINGS_BIN" | grep -qF "PROOT_SYSCALL_STATS"; then
  echo "FAIL: disallowed PROOT_SYSCALL_STATS symbol embedded in candidate binary" >&2; exit 5
fi
case "$TARGET_OUT" in
  *proot-stage5*) ;;
  *)
    if printf '%s\n' "$STRINGS_BIN" | grep -qF "proot-stage5"; then
      echo "FAIL: disallowed stage5 path embedded in candidate binary" >&2; exit 5
    fi
    ;;
esac
(cd "$STAGE_DIR/out" && sha256sum bin/proot-fast8 libexec/loader $([ -f libexec/loader32 ] && echo libexec/loader32) > candidate.sha256)
cat "$STAGE_DIR/out/candidate.sha256"

run_claude_smoke() {
  local proot_bin="$1"
  local loader_bin="$2"
  local cs_rc=0
  local guest_cmd
  local xdisp=$((90 + ($$ % 9)))
  if [ -x "$UBU_ROOTFS/usr/bin/Xvfb" ]; then
    guest_cmd="D=\"/tmp/claude-deploy-smoke.\$\$\"; mkdir -p \"\$D\"; Xvfb :${xdisp} -screen 0 1024x768x24 -nolock >/dev/null 2>&1 & XPID=\$!; sleep 0.5; DISPLAY=:${xdisp} timeout 4 /usr/bin/claude-desktop --no-sandbox --disable-gpu --disable-dev-shm-usage --ozone-platform=x11 --password-store=basic --user-data-dir=\"\$D\" >/dev/null 2>&1; rc=\$?; kill \"\$XPID\" 2>/dev/null || true; wait \"\$XPID\" 2>/dev/null || true; rm -rf \"\$D\"; exit \$rc"
  else
    guest_cmd="D=\"/tmp/claude-deploy-smoke.\$\$\"; mkdir -p \"\$D\"; timeout 4 /usr/bin/claude-desktop --no-sandbox --disable-gpu --disable-dev-shm-usage --headless --user-data-dir=\"\$D\" >/dev/null 2>&1; rc=\$?; rm -rf \"\$D\"; exit \$rc"
  fi
  PROOT_LOADER="$loader_bin" \
    "$proot_bin" -0 -l -r "$UBU_ROOTFS" -w / -b /proc -b /dev \
    /usr/bin/env -i PATH=/usr/bin:/bin HOME=/root F8_NO_SHARD=1 \
    /bin/sh -c "$guest_cmd" || cs_rc=$?
  if [ "$cs_rc" -eq 133 ]; then
    echo "FAIL: claude-desktop smoke hit SIGTRAP (rc=133)" >&2
    return 1
  fi
  if [ "$cs_rc" -ne 124 ] && [ "$cs_rc" -ne 0 ]; then
    echo "FAIL: claude-desktop smoke exited unexpectedly (rc=$cs_rc)" >&2
    return 1
  fi
  echo "   claude-desktop non-SIGTRAP smoke PASS (rc=$cs_rc)"
  return 0
}

echo "4. Pre-flight functional smoke test on staging binary..."
"$STAGE_DIR/out/bin/proot-fast8" --version | grep -q "5.1.107.92-fast9"
if [ -d "$UBU_ROOTFS" ] && [ -n "$REGRESS_BIN" ] && [ -x "$REGRESS_BIN" ]; then
  RDIR=$(dirname "$REGRESS_BIN")
  PROOT_LOADER="$STAGE_DIR/out/libexec/loader" \
    "$STAGE_DIR/out/bin/proot-fast8" -0 -l -r "$UBU_ROOTFS" -w / \
    -b /proc -b /dev -b "$RDIR:/bench" \
    /usr/bin/env -i PATH=/usr/bin:/bin LC_ALL=C "/bench/$(basename "$REGRESS_BIN")" | grep -q "FAST9_REGRESS_OK"
  echo "   fast9_regress PASS on staging binary"
elif [ "$ALLOW_NO_REGRESS" -ne 1 ]; then
  echo "FAIL: fast9_regress preflight did not execute (use --regress-bin or --allow-no-regress)" >&2
  exit 5
else
  echo "   WARN: fast9_regress preflight skipped (--allow-no-regress)"
fi
if [ "$CLAUDE_SMOKE" -eq 1 ]; then
  run_claude_smoke "$STAGE_DIR/out/bin/proot-fast8" "$STAGE_DIR/out/libexec/loader" || exit 5
fi

if [ "$MODE" = "dry-run" ]; then
  echo "DRY_RUN_PASS: candidate built, verified, and smoke-tested without mutating $TARGET_OUT"
  exit 0
fi

# --- LIVE / TARGET APPLY WITH BACKUP & AUTO-ROLLBACK ---
apply_candidate() (
  # Serialize apply and manual rollback for this target. Build/preflight can
  # run concurrently. Every file is staged before changing any target file.
  exec {release_lock}<"$TARGET_OUT"
  flock -x "$release_lock"

  local txn backup recover=""
  local files=(bin/proot-fast8 libexec/loader)
  if [[ -f "$STAGE_DIR/out/libexec/loader32" ]]; then
    files+=(libexec/loader32)
  fi
  files+=(deployed.sha256)
  txn=$(mktemp -d "$TARGET_OUT/.deploy.XXXXXXXX")
  trap 'finish_release_change "$?" "$txn" "$recover" "$TARGET_OUT" "${files[@]}"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM

  mkdir -p -- "$BACKUP_ROOT"
  BACKUP_ROOT=$(cd -- "$BACKUP_ROOT" && pwd -P)
  backup=$(mktemp -d "$BACKUP_ROOT/out8-previous-$(date +%Y%m%d-%H%M%S).XXXXXXXX")
  echo "5. Backing up existing target-out to $backup..."
  snapshot_release "$TARGET_OUT" "$backup"

  cp -- "$STAGE_DIR/out/candidate.sha256" "$STAGE_DIR/out/deployed.sha256"
  prepare_release_files "$STAGE_DIR/out" "$txn/candidate" "${files[@]}"

  echo "6. Replacing target-out binaries..."
  recover="$backup"
  publish_release_files "$txn/candidate" "$TARGET_OUT" "${files[@]}"

  echo "7. Post-deploy integrity & guest smoke verification..."
  (cd "$TARGET_OUT" && sha256sum -c deployed.sha256)
  "$TARGET_OUT/bin/proot-fast8" --version | grep -F "5.1.107.92-fast9" >/dev/null
  if [[ -x "$TARGET_OUT/auto/proot-fast8" ]]; then
    "$TARGET_OUT/auto/proot-fast8" --version | grep -F "5.1.107.92-fast9" >/dev/null
  fi
  if [[ -d "$UBU_ROOTFS" ]]; then
    (
      # Guest processes can outlive the smoke shell. Keep the lock in the caller.
      exec {release_lock}<&-
      local packages
      packages=$("$TARGET_OUT/bin/proot-fast8" -0 -l -r "$UBU_ROOTFS" -w / -b /proc -b /dev /usr/bin/env -i PATH=/usr/bin:/bin LC_ALL=C /bin/bash -o pipefail -c "dpkg-query -W | wc -l")
      [[ "${packages:-0}" -gt 100 ]]
      echo "   guest dpkg-query smoke PASS (packages=$packages)"
      if [[ -e "$UBU_ROOTFS/usr/bin/claude-desktop" || -L "$UBU_ROOTFS/usr/bin/claude-desktop" ]]; then
        run_claude_smoke "$TARGET_OUT/bin/proot-fast8" "$TARGET_OUT/libexec/loader"
      fi
    )
  fi

  if is_fast8 "$backup"; then
    printf '%s\n' "$backup" > "$backup/.latest-fast8"
    mv -fT -- "$backup/.latest-fast8" "$BACKUP_ROOT/LATEST_FAST8_BACKUP"
  fi
  recover=""
  echo "DEPLOY_PASS target=$TARGET_OUT backup=$backup"
)
apply_candidate
