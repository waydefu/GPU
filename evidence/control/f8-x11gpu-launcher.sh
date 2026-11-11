#!/data/data/com.termux/files/usr/bin/bash
# f8-x11gpu: side-by-side experimental launcher (Phase 1B-2+).
# Stable `termux-x11` / loader.apk untouched. New paths only.
if [ ! -e /system/bin/getprop ] || [ ! -e /system/bin/app_process ]; then
  echo "Headless system detected. Termux:X11 requires standard Android to work,"
  echo "and depends on APKs and system properties."
  exit 1
fi
if [ "$(getprop ro.build.version.sdk)" -lt "24" ]; then
  echo "Termux:X11 requires at least Android 7 or newer."
  exit 1
fi
[ -z "${LD_LIBRARY_PATH+x}" ] || export XSTARTUP_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"
[ -z "${LD_PRELOAD+x}" ] || export XSTARTUP_LD_PRELOAD="$LD_PRELOAD"
[ -z "${CLASSPATH+x}" ] || export XSTARTUP_CLASSPATH="$CLASSPATH"
export CLASSPATH=/data/data/com.termux/files/usr/libexec/x11gpu/loader.apk
unset LD_LIBRARY_PATH LD_PRELOAD
[ -n "$(trap -p USR1)" ] && export TERMUX_X11_NOTIFY_PARENT=1
exec /system/bin/app_process -Xnoimage-dex2oat / --nice-name="termux-x11gpu com.waydefu.x11gpu $*" com.termux.x11.Loader "$@"
