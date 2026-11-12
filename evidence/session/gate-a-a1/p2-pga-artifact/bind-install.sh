#!/usr/bin/env bash
# Download a fork CI APK, bind it (sha / size / version / Build ID / signer), derive its install script
# from the previous artifact's, and install it onto com.waydefu.x11gpu ONLY.
#   RUN_INSTALL=YES SERIAL=... bash bind-install.sh <sha7> <full_sha> <ci_run> <prev_sha7> "<change text>"
# Every field of the derived install script is set explicitly and then checked; a global sed once
# corrupted EXPECT_HEAD (artifact-0245ff3), so nothing here relies on substring replacement of shas.
set -euo pipefail
P=/root/projects/GPU加速/evidence/session/gate-a-a1/p2-pga-artifact
N=$1; FULL=$2; RUN=$3; PREV=$4; CHANGE=${5:-}
[ "${#N}" = 7 ] && [ "${#FULL}" = 40 ] && [ "${FULL:0:7}" = "$N" ] || { echo "BAD_ARGS"; exit 2; }
SIGNER=b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1
B=$P/artifact-$N; [ -e "$B/install" ] && { echo "REFUSE $B/install exists"; exit 9; }
mkdir -p "$B/ci-$RUN"; cd "$B/ci-$RUN"
[ -f termux-x11-universal-debug.apk ] || {
  timeout 600 gh run download "$RUN" -R waydefu/termux-x11 -n termux-x11-universal-debug -D dl >/dev/null
  cp dl/termux-x11-universal-debug.apk . && rm -rf dl; }
SHA=$(sha256sum termux-x11-universal-debug.apk | awk '{print $1}')
SZ=$(stat -c%s termux-x11-universal-debug.apk)
VER=$(/usr/bin/aapt dump badging termux-x11-universal-debug.apk | grep -oE "versionName='[^']+'" | cut -d"'" -f2)
unzip -p termux-x11-universal-debug.apk lib/arm64-v8a/libXlorie.so > libXlorie-arm64.so
BID=$(readelf -n libXlorie-arm64.so | awk '/Build ID/{print $3}')
cp termux-x11-universal-debug.apk "/tmp/bind-$N.apk"
SIG=$(/usr/bin/apksigner verify --print-certs "/tmp/bind-$N.apk" 2>/dev/null | awk '/SHA-256 digest/{print $NF; exit}'); rm -f "/tmp/bind-$N.apk"
[ "$SIG" = "$SIGNER" ] || { echo "SIGNER_MISMATCH $SIG"; exit 3; }
[ "$VER" = "1.03.01-$N-${VER##*-}" ] || { echo "VERSION_NOT_FOR_$N $VER"; exit 3; }
PJ=$P/artifact-$PREV/artifact-binding.json
python3 - "$PJ" "$B/artifact-binding.json" "$SHA" "$SZ" "$VER" "$BID" "$FULL" "$RUN" "$PREV" "$CHANGE" <<'EOF'
import json, sys
a = sys.argv; d = json.load(open(a[1]))
parent = {"source_sha": d["source_sha"], "ci_run": d["ci_run"], "apk_sha256": d["apk_sha256"]}
d.update({"source_sha": a[7], "ci_run": int(a[8]), "version_name": a[5], "apk_sha256": a[3], "apk_size": int(a[4]),
          "build_id": a[6], "install_status": "NOT_INSTALLED", "parent": parent, "change": a[10],
          "product_diff": "see git log " + parent["source_sha"][:7] + ".." + a[7][:7]})
d["not_poolable_with"] = [a[9]] + [x for x in d.get("not_poolable_with", []) if x != a[9]]
d.pop("device_verification", None)
json.dump(d, open(a[2], "w"), indent=2)
EOF
PFULL=$(python3 -c "import json;print(json.load(open('$PJ'))['source_sha'])")
OLD=$P/artifact-$PREV/install-$PREV.sh
OSHA=$(awk -F= '/^EXPECT_SHA256=/{print $2}' "$OLD"); ORUN=$(awk -F= '/^EXPECT_CI=/{print $2}' "$OLD")
UP=$(echo "$N" | tr a-z A-Z); OUP=$(echo "$PREV" | tr a-z A-Z)
sed -e "s/^APK=.*/APK=${B//\//\\/}\/ci-$RUN\/termux-x11-universal-debug.apk/" \
    -e "s/^EXPECT_SHA256=.*/EXPECT_SHA256=$SHA/" -e "s/^EXPECT_BUILDID=.*/EXPECT_BUILDID=$BID/" \
    -e "s/^EXPECT_VERSION=.*/EXPECT_VERSION=$VER/" -e "s/^EXPECT_SIZE=.*/EXPECT_SIZE=$SZ/" \
    -e "s/^EXPECT_HEAD=.*/EXPECT_HEAD=$FULL/" -e "s/^EXPECT_PARENT=.*/EXPECT_PARENT=$PFULL/" \
    -e "s/^EXPECT_CI=.*/EXPECT_CI=$RUN/" \
    -e "s/^REMOTE=.*/REMOTE=\/data\/local\/tmp\/gate-a-pga-$N-$RUN.apk/" \
    -e "s/^APK_FOR_SIGNER=.*/APK_FOR_SIGNER=\/tmp\/pga-$N-termux-x11-universal-debug.apk/" \
    -e "s/artifact-$PREV\/install/artifact-$N\/install/g" -e "s/install-$PREV\.sh/install-$N.sh/g" \
    -e "s/pga-$PREV-installed-base/pga-$N-installed-base/g" \
    -e "s/INSTALL_${OUP}_BIND_PASS/INSTALL_${UP}_BIND_PASS/" -e "s/role=$PREV-/role=$N-/" \
    -e "s/APK $PREV (CI $ORUN)/APK $N (CI $RUN)/" \
    "$OLD" > "$B/install-$N.sh"
bash -n "$B/install-$N.sh"
for kv in "EXPECT_SHA256=$SHA" "EXPECT_BUILDID=$BID" "EXPECT_VERSION=$VER" "EXPECT_SIZE=$SZ" "EXPECT_HEAD=$FULL" "EXPECT_PARENT=$PFULL" "EXPECT_CI=$RUN"; do
  grep -qx "$kv" "$B/install-$N.sh" || { echo "DERIVE_CHECK_FAIL $kv"; exit 4; }
done
if grep -q "$OSHA\|$ORUN\|artifact-$PREV/" "$B/install-$N.sh"; then echo "DERIVE_LEFTOVER_FROM_$PREV"; exit 4; fi
echo "BOUND $N sha=$SHA size=$SZ version=$VER build_id=$BID"
[ "${RUN_INSTALL:-}" = YES ] || { echo "NOT_INSTALLED (set RUN_INSTALL=YES)"; exit 0; }
RUN_INSTALL=YES SERIAL="${SERIAL:?}" CELL="$B/install" timeout 400 bash "$B/install-$N.sh" > "$B/install.log" 2>&1
tail -1 "$B/install.log" | grep -qx "INSTALL_${UP}_BIND_PASS" || { echo "INSTALL_FAILED"; tail -3 "$B/install.log"; exit 5; }
python3 - "$B/artifact-binding.json" "$N" "$UP" <<'EOF'
import json, sys
p = sys.argv[1]; d = json.load(open(p)); d["install_status"] = "INSTALLED_AND_VERIFIED_ON_DEVICE"
d["device_verification"] = {"method": f"install-{sys.argv[2]}.sh", "evidence": f"install/ (INSTALL_{sys.argv[3]}_BIND_PASS)"}
json.dump(d, open(p, "w"), indent=2)
EOF
echo "INSTALLED $N"
