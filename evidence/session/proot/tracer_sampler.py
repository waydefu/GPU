# PRoot tracer queue sampler — runs OUTSIDE PRoot (adb run-as com.termux, Termux python) so it is not traced
# itself. Every ~20 ms: state of the tracer (R = busy) and every thread in state 't' (stopped, waiting for the
# tracer) with the syscall it is stopped in. Read-only.  usage: python tracer_sampler.py <tracer_pid> <seconds> <out.json>
import os, sys, time, json, collections
T, DUR, OUT = sys.argv[1], float(sys.argv[2]), sys.argv[3]
NAMES = {56: 'openat', 79: 'newfstatat', 291: 'statx', 48: 'faccessat', 439: 'faccessat2', 78: 'readlinkat', 221: 'execve',
         17: 'getcwd', 49: 'chdir', 35: 'unlinkat', 34: 'mkdirat', 38: 'renameat', 276: 'renameat2', 29: 'ioctl', 63: 'read',
         64: 'write', 98: 'futex', 73: 'ppoll', 22: 'epoll_pwait', 57: 'close', 260: 'wait4', 220: 'clone', 435: 'clone3',
         203: 'connect', 200: 'bind', 160: 'uname', 117: 'ptrace', 167: 'prctl', 129: 'kill', 131: 'tgkill', 43: 'statfs',
         44: 'fstatfs', 5: 'setxattr', 8: 'getxattr', 88: 'utimensat', 52: 'fchownat', 53: 'fchmodat', 36: 'symlinkat',
         37: 'linkat', 61: 'getdents64', 80: 'fstat', 25: 'fcntl', 280: 'bpf', 157: 'setsid', 94: 'exit_group', 93: 'exit',
         242: 'accept4', 204: 'getsockname', 205: 'getpeername', 212: 'recvmsg', 211: 'sendmsg', 62: 'lseek', 67: 'pread64'}
names = {}
def pname(pid):
    if pid not in names:
        try: c = open(f'/proc/{pid}/cmdline', 'rb').read().split(b'\0')[0].decode(errors='replace')
        except Exception: c = '?'
        c = c.split('/')[-1] or '?'
        names[pid] = c[:40]
    return names[pid]
def tstate(path):
    s = open(path).read(); return s[s.rfind(')') + 2]
per = collections.Counter(); per_sys = collections.Counter(); qlen = collections.Counter()
samples = busy = 0; t0 = time.time(); pids = [p for p in os.listdir('/proc') if p.isdigit()]; last_scan = t0
while time.time() - t0 < DUR:
    if time.time() - last_scan > 2:
        pids = [p for p in os.listdir('/proc') if p.isdigit()]; last_scan = time.time()
    try:
        if tstate(f'/proc/{T}/stat') == 'R': busy += 1
    except Exception: break
    q = 0
    for p in pids:
        try: tids = os.listdir(f'/proc/{p}/task')
        except Exception: continue
        for t in tids:
            try:
                if tstate(f'/proc/{p}/task/{t}/stat') != 't': continue
                nr = int(open(f'/proc/{p}/task/{t}/syscall').read().split()[0])
            except Exception: continue
            q += 1; key = pname(p); sc = NAMES.get(nr, f'nr{nr}')
            per[key] += 1; per_sys[(key, sc)] += 1
    qlen[q] += 1; samples += 1
    time.sleep(0.02)
dt = time.time() - t0
json.dump({'tracer': T, 'seconds': dt, 'samples': samples, 'tracer_busy_frac': busy / max(samples, 1),
           'queue_len_hist': dict(qlen), 'waiting_by_process': per.most_common(30),
           'waiting_by_process_syscall': [[k[0], k[1], v] for k, v in per_sys.most_common(40)]}, open(OUT, 'w'), indent=1)
print(f'samples={samples} dt={dt:.1f}s tracer_busy={busy / max(samples, 1):.2f}')
