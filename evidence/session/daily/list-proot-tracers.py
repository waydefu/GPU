# List proot tracers with tracee counts and parents (setsid -f check, 2026-09-27).
# PRoot's /proc/uptime and /proc/stat btime are faked by proot-distro, so start is
# printed as seconds-since-boot from /proc/<pid>/stat field 22 (real kernel value).
import os, time
HZ = os.sysconf('SC_CLK_TCK')
info = {}
for p in os.listdir('/proc'):
    if not p.isdigit(): continue
    try:
        st = open(f'/proc/{p}/status').read()
        stat = open(f'/proc/{p}/stat').read()
    except Exception:
        continue
    d = {}
    for line in st.splitlines():
        k, _, v = line.partition(':')
        if k in ('Name', 'PPid', 'TracerPid'): d[k] = v.strip()
    rest = stat[stat.rfind(')')+2:].split()
    d['start'] = int(rest[19]) / HZ
    try:
        d['cmd'] = open(f'/proc/{p}/cmdline', 'rb').read().replace(b'\0', b' ').decode(errors='replace').strip()
    except Exception:
        d['cmd'] = '?'
    info[int(p)] = d
tracees = {}
for p, d in info.items():
    t = int(d.get('TracerPid', 0))
    if t: tracees.setdefault(t, []).append(p)
tracers = sorted(p for p, d in info.items() if d.get('Name', '').startswith('proot'))
print(f'procs scanned={len(info)}  proot-named={len(tracers)}')
for p in tracers:
    d = info[p]; pp = int(d['PPid'])
    pd = info.get(pp, {})
    kids = [c for c, e in info.items() if int(e['PPid']) == p]
    tl = tracees.get(p, [])
    print(f"\n[{p}] {d['Name']} start=+{d['start']:.2f}s tracees={len(tl)} ppid={pp}({pd.get('Name','?')})")
    print(f"   cmd: {d['cmd'][:220]}")
    print(f"   parent cmd: {pd.get('cmd','?')[:160]}")
    names = {}
    for t in tl: names[info[t]['Name']] = names.get(info[t]['Name'], 0) + 1
    print(f"   tracee names: {dict(sorted(names.items(), key=lambda x: -x[1])[:8])}")
    nontraced_kids = [c for c in kids if int(info[c].get('TracerPid', 0)) != p]
    if nontraced_kids:
        print(f"   untraced children: {[(c, info[c]['Name'], info[c]['cmd'][:80]) for c in nontraced_kids]}")
