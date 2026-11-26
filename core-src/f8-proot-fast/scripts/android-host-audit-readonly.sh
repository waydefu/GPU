#!/bin/bash
# android-host-audit-readonly.sh — Read-only Android host telemetry & 3-mode audit on POCO F8 Ultra.
# Never modifies Android settings (no settings put / device_config put) and never touches ADB port 5037.
set -u

LABEL=${1:-current}
ADB_BIN=/data/data/com.termux/files/usr/bin/adb
ADB_PORT_HELPER=/data/data/com.termux/files/usr/bin/f8-adb-port

echo "=== ANDROID_HOST_AUDIT label=$LABEL ts=$(date -Iseconds) ==="
echo "--- 1. MEMORY / SWAP / VMSTAT ---"
grep -E '^(MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapCached|SwapTotal|SwapFree|Active|Inactive):' /proc/meminfo 2>&1 || true
grep -E '^(pswpin|pswpout|pgmajfault|allocstall|compact_stall)' /proc/vmstat 2>&1 || true

echo "--- 2. THERMAL ZONES (READABLE) ---"
tz_count=0
for tz in /sys/class/thermal/thermal_zone*; do
  [ -r "$tz/temp" ] || continue
  tname=$(cat "$tz/type" 2>/dev/null || echo unknown)
  case "$tname" in
    *cpu*|*gpu*|*soc*|*skin*|*battery*|*pm*|*ddr*)
      tval=$(cat "$tz/temp" 2>/dev/null || echo "")
      tag=""
      case "$tname" in
        *hw-trip*) tag=" [HW_TRIP_CONSTANT]" ;;
      esac
      printf "%s (%s): %s%s\n" "$(basename "$tz")" "$tname" "$tval" "$tag"
      tz_count=$((tz_count + 1))
      [ "$tz_count" -ge 35 ] && break
      ;;
  esac
done

echo "--- 3. CPUFREQ / GOVERNOR & GPU ---"
for c in 0 1 2 3 4 5 6 7; do
  f="/sys/devices/system/cpu/cpu${c}/cpufreq"
  [ -d "$f" ] || continue
  printf "cpu%s gov=%s cur=%s max=%s info_max=%s\n" "$c" \
    "$(cat "$f/scaling_governor" 2>/dev/null || echo N/A)" \
    "$(cat "$f/scaling_cur_freq" 2>/dev/null || echo N/A)" \
    "$(cat "$f/scaling_max_freq" 2>/dev/null || echo N/A)" \
    "$(cat "$f/cpuinfo_max_freq" 2>/dev/null || echo N/A)"
done
for gf in gpu_model gpubusy devfreq/cur_freq devfreq/max_freq gpuclk max_gpuclk; do
  [ -r "/sys/class/kgsl/kgsl-3d0/$gf" ] && printf "kgsl.%s=%s\n" "$gf" "$(cat "/sys/class/kgsl/kgsl-3d0/$gf" 2>/dev/null)"
done

echo "--- 4. GPU & BATTERY READABLE NODES ---"
ls -la /dev/kgsl-3d0 /dev/ashmem /dev/dri 2>&1 || true
for f in status capacity temp voltage_now current_now; do
  [ -r "/sys/class/power_supply/battery/$f" ] && printf "battery.%s=%s\n" "$f" "$(cat "/sys/class/power_supply/battery/$f" 2>/dev/null)"
done

echo "--- 5. CURRENT UID TOP-15 PSS/RSS & PHANTOM PROCS COUNT ---"
python3 - <<'PY'
import pathlib, re
rows = []
for p in pathlib.Path("/proc").iterdir():
    if not p.name.isdigit():
        continue
    try:
        comm = (p / "comm").read_text().strip()
        status = (p / "status").read_text()
        tp = int(re.search(r"(?m)^TracerPid:\s+(\d+)", status).group(1))
        sr = (p / "smaps_rollup").read_text()
        pss = int(re.search(r"(?m)^Pss:\s+(\d+)", sr).group(1))
        rss = int(re.search(r"(?m)^Rss:\s+(\d+)", sr).group(1))
        rows.append((pss, rss, int(p.name), tp, comm))
    except Exception:
        continue
rows.sort(reverse=True)
print(f"uid_visible_procs={len(rows)} total_pss_mb={sum(r[0] for r in rows)/1024:.1f} total_rss_mb={sum(r[1] for r in rows)/1024:.1f}")
for pss, rss, pid, tp, comm in rows[:15]:
    print(f"  pid={pid:6d} tracer={tp:6d} pss_mb={pss/1024:7.1f} rss_mb={rss/1024:7.1f} comm={comm}")
PY

echo "--- 6. READ-ONLY ADB (-P 5038) AUDIT ---"
PORT_OUT=$("$ADB_PORT_HELPER" 2>&1 || true)
echo "f8-adb-port: ${PORT_OUT:-EMPTY}"
ADB_STATE=$(HOME=/data/data/com.termux/files/home "$ADB_BIN" -P 5038 get-state 2>&1 || true)
echo "adb -P 5038 get-state: $ADB_STATE"
if [ "$ADB_STATE" = "device" ]; then
  echo "[dumpsys activity settings]"
  HOME=/data/data/com.termux/files/home "$ADB_BIN" -P 5038 shell dumpsys activity settings 2>&1 | grep -E 'max_phantom|monitor_phantom|background|cached' | head -n 20 || true
  echo "[phantom & power flags]"
  for spec in \
    "device_config get activity_manager max_phantom_processes" \
    "settings get global settings_enable_monitor_phantom_procs" \
    "settings get global low_power" \
    "settings get system POWER_PERFORMANCE_MODE_OPEN" \
    "settings get system speed_mode"; do
    printf "%s => %s\n" "$spec" "$(HOME=/data/data/com.termux/files/home "$ADB_BIN" -P 5038 shell $spec 2>&1 | tr '\r\n' ' ')"
  done
  echo "[PSI & ZRAM via ADB]"
  HOME=/data/data/com.termux/files/home "$ADB_BIN" -P 5038 shell "cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io /sys/block/zram0/mm_stat 2>&1" || true
  echo "[dumpsys meminfo com.termux + summary]"
  HOME=/data/data/com.termux/files/home "$ADB_BIN" -P 5038 shell "dumpsys meminfo com.termux | head -n 45" || true
  echo "[dumpsys thermalservice & battery]"
  HOME=/data/data/com.termux/files/home "$ADB_BIN" -P 5038 shell "dumpsys thermalservice | head -n 30; dumpsys battery | head -n 20" || true
else
  echo "ADB_STATUS=OFFLINE_OR_UNAUTHORIZED (read-only audit skipped ADB queries without touching 5037)"
fi
echo "=== END ANDROID_HOST_AUDIT ==="
