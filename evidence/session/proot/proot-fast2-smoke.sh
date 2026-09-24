#!/bin/bash
# PROOT-FAST v2 functional smoke: identical output expected under stock proot and proot-fast2 (volatile fields removed).
cd /root/build/proot-bench && rm -rf smoke-tmp && mkdir smoke-tmp && cd smoke-tmp
echo "id: $(id)"; echo "uname: $(uname -srm)"; echo "whoami: $(whoami)"
echo data > f; ln f hard; echo "nlink: $(stat -c '%h %U:%G %a' f hard | tr '\n' ' ')"; chmod 640 f; chown root:root f; echo "perm: $(stat -c '%a %U' f)"
ln -s f sym; echo "readlink: $(readlink sym)"; mkdir -p d/e; mv f d/e/g; echo "mv: $(ls d/e)"; rm -rf d hard sym; echo "left: $(ls | wc -l)"
python3 - <<'PY'
import threading, queue, sqlite3, ssl, socket, subprocess, os, time
q = queue.Queue(); lock = threading.Lock(); n = [0]
def w():
    for _ in range(20000):
        with lock: n[0] += 1
ts = [threading.Thread(target=w) for _ in range(8)]; [t.start() for t in ts]; [t.join() for t in ts]
print("threads_locks", n[0])
c = sqlite3.connect(":memory:"); c.execute("create table t(x)"); c.executemany("insert into t values(?)", [(i,) for i in range(1000)]); print("sqlite", c.execute("select sum(x) from t").fetchone()[0])
print("ssl", bool(ssl.create_default_context()))
a, b = socket.socketpair(); a.sendall(b"ping" * 1000); print("socketpair", len(b.recv(8192)))
print("subprocess", subprocess.run(["sh", "-c", "echo $((6*7))"], capture_output=True, text=True).stdout.strip())
r, w_ = os.pipe(); os.write(w_, b"x"); print("pipe", os.read(r, 1))
print("sleep_ok", (lambda t: (time.sleep(0.05), round(time.monotonic() - t, 1))[1])(time.monotonic()) >= 0.0)
PY
node /root/build/proot-bench/smoke-node.js
echo "git: $(git -C /root/projects/GPU加速/src/f8-ahb-exa-async rev-parse --short HEAD)"
echo "dpkg: $(dpkg -s bash | grep -c '^Status: install ok installed')"
echo "apt_policy: $(apt-cache policy bash | grep -c Installed)"
echo "dns: $(getent hosts localhost | awk '{print $1}' | head -1)"
echo "sysvipc: $(python3 -c 'import sysv_ipc' 2>/dev/null && echo mod || ipcs -m >/dev/null 2>&1 && echo ipcs_ok)"
echo SMOKE_DONE
