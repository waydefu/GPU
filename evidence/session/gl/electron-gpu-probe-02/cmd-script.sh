#!/usr/bin/env bash
# ELECTRON-GPU-PROBE-01 (exploration, not a qualification cell): does Cursor's (Chrome 144) GPU process
# pick up /opt/mesa-kgsl (Turnip KGSL + Zink) on the experimental X (:3)?
#   run by evidence/session/gl/run-gl-bench.sh KIND=cmd (DISPLAY=:3), arg 1 = cell evidence dir
# Variants (fresh throw-away --user-data-dir each, never the user's /root/.cursor-data):
#   v0-control  --disable-gpu (today's daily flags)            -> must report software / GPU disabled
#   v1-angle-gl ANGLE on EGL (-> glvnd -> Zink on Turnip)
#   v2-angle-vk ANGLE on Vulkan (-> Turnip directly)
#   v3-shim-nomesa GPU enabled with Ubuntu's own Mesa (expected: llvmpipe, i.e. GPU process alive but CPU driver)
# v1-v3 run with LD_PRELOAD=libdiag.so: hides libpci (its default error handler exit(1)s when /proc/bus/pci
# is missing - the cause of every GPU-process death in probe-01) and logs a backtrace on exit()/_exit()
# in the gpu-process. Probe-01 (without the shim) is kept as it is.
# Per variant: wait 30 s, read SystemInfo.getInfo over the DevTools protocol (Chromium's own report),
# sample the GPU process CPU over 20 s of idle, then end the variant's process group (exact pgid).
set -uo pipefail
OUT=${1:?evidence dir}
BIN=/usr/share/cursor/cursor
PROF=/root/build/electron-probe
SHIM=/root/build/electron-probe/nopci/libdiag.so
MESA_ENV=(VK_ICD_FILENAMES=/opt/mesa-kgsl/share/vulkan/icd.d/freedreno_icd.aarch64.json
  "VK_LOADER_LAYERS_DISABLE=*" LD_LIBRARY_PATH=/opt/mesa-kgsl/lib
  __EGL_VENDOR_LIBRARY_FILENAMES=/opt/mesa-kgsl/share/glvnd/egl_vendor.d/50_mesa.json
  __GLX_VENDOR_LIBRARY_NAME=mesa MESA_LOADER_DRIVER_OVERRIDE=zink GALLIUM_DRIVER=zink)
COMMON=(--no-sandbox --disable-gpu-sandbox --disable-dev-shm-usage --ozone-platform=x11
  --disable-updates --skip-welcome --disable-workspace-trust --new-window)

cdp_info() {   # port outfile
  node - "$1" "$2" <<'JS'
const [port, out] = process.argv.slice(2);
const fs = require('fs');
(async () => {
  const v = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
  const ws = new WebSocket(v.webSocketDebuggerUrl);
  const res = await new Promise((ok, bad) => {
    const t = setTimeout(() => bad(new Error('timeout')), 15000);
    ws.onopen = () => ws.send(JSON.stringify({ id: 1, method: 'SystemInfo.getInfo' }));
    ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id === 1) { clearTimeout(t); ok(d); } };
    ws.onerror = (e) => bad(e);
  });
  ws.close();
  fs.writeFileSync(out, JSON.stringify(res, null, 1));
  const g = (res.result || {}).gpu || {};
  const aux = g.auxAttributes || {};
  console.log(JSON.stringify({ browser: v.Browser, devices: (g.devices || []).map(d => d.deviceString || d.vendorString),
    glRenderer: aux.glRenderer, glVendor: aux.glVendor, glImplementationParts: aux.glImplementationParts,
    displayType: aux.displayType, featureStatus: g.featureStatus }));
})().catch(e => { console.log(JSON.stringify({ error: String(e) })); process.exit(0); });
JS
}
gpu_pid() {   # pgid -> pid of the --type=gpu-process in that group
  local p
  for p in /proc/[0-9]*; do
    [ "$(awk '{print $5}' "$p/stat" 2>/dev/null)" = "$1" ] || continue
    tr '\0' ' ' < "$p/cmdline" 2>/dev/null | grep -q -- '--type=gpu-process' && { echo "${p##*/}"; return; }
  done
}
ticks() { awk '{print $14+$15}' "/proc/$1/stat" 2>/dev/null || echo null; }

run_variant() {   # name port use_mesa(0/1) use_shim(0/1) flags...
  local name=$1 port=$2 mesa=$3 shim=$4; shift 4
  local dir=$PROF/$name; rm -rf "$dir"; mkdir -p "$dir"
  local envs=(); [ "$mesa" = 1 ] && envs=("${MESA_ENV[@]}"); [ "$shim" = 1 ] && envs+=("LD_PRELOAD=$SHIM")
  setsid env "${envs[@]}" "$BIN" "${COMMON[@]}" --user-data-dir="$dir" --remote-debugging-port="$port" \
    --enable-logging=stderr "$@" > "$OUT/$name.stderr" 2>&1 < /dev/null &
  local pg=$!
  echo "VARIANT $name pgid=$pg flags=$*"
  sleep 30
  echo "INFO $name $(cdp_info "$port" "$OUT/$name.gpuinfo.json")"
  local gp; gp=$(gpu_pid "$pg")
  if [ -n "$gp" ]; then
    tr '\0' '\n' < "/proc/$gp/cmdline" > "$OUT/$name.gpu-process-cmdline.txt"
    local t0 t1; t0=$(ticks "$gp"); sleep 20; t1=$(ticks "$gp")
    echo "IDLE $name gpu_pid=$gp gpu_cpu_s_20s=$(awk -v a="$t0" -v b="$t1" 'BEGIN{if(a=="null"||b=="null")print "null"; else printf "%.2f",(b-a)/100}')"
  else
    echo "IDLE $name gpu_pid=none gpu_cpu_s_20s=null"
  fi
  # CONSTRUCTION: end exactly the process group this script started
  echo "end_variant $name pgid=$pg" >> "$OUT/electron-probe-kills.txt"
  kill -TERM -- "-$pg" 2>/dev/null || true
  for _ in $(seq 1 20); do kill -0 -- "-$pg" 2>/dev/null || break; sleep 0.5; done
  kill -KILL -- "-$pg" 2>/dev/null || true
  sleep 3
  # verify: nothing may survive with this variant's throw-away profile (2026-09-24: debug runs outside this
  # script leaked 4 Cursor groups / 5.3 GB because $! was not the real pgid and nothing checked)
  local q c left=0
  for q in /proc/[0-9]*; do
    [ "${q##*/}" = "$$" ] && continue
    c=$(tr '\0' ' ' < "$q/cmdline" 2>/dev/null) || continue
    case "$c" in "$BIN "*"--user-data-dir=$dir "*|"$BIN "*"--user-data-dir=$dir") kill -KILL "${q##*/}" 2>/dev/null && left=$((left + 1))
      echo "survivor_killed $name pid=${q##*/}" >> "$OUT/electron-probe-kills.txt";; esac
  done
  echo "END $name survivors_killed=$left"
}

run_variant v0-control 9230 0 0 --disable-gpu
run_variant v1-angle-gl 9231 1 1 --ignore-gpu-blocklist --use-gl=angle --use-angle=gl-egl
run_variant v2-angle-vk 9232 1 1 --ignore-gpu-blocklist --use-gl=angle --use-angle=vulkan \
  --enable-features=Vulkan,VulkanFromANGLE,DefaultANGLEVulkan
run_variant v3-shim-nomesa 9233 0 1 --ignore-gpu-blocklist
echo ELECTRON_GPU_PROBE_DONE
