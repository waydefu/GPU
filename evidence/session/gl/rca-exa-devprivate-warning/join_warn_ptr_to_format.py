#!/usr/bin/env python3
"""Join each 'EXA bug ... devPrivate.ptr was <addr>' line of an x3-launcher.log to the AHB
promotions (R3 S1_AHB ... dst=<addr> ... format=<f>) that mapped the same address.
format 2 = R8G8B8X8 (depth < 32), 5 = B8G8R8A8 (depth 32). 'unmatched' = an address no
promotion in this log mapped (e.g. the root, which is born AHB and never promoted)."""
import collections, re, sys
for path in sys.argv[1:]:
    fmt, warn = {}, collections.Counter()
    for l in open(path, errors="replace"):
        m = re.match(r'R3 S1_AHB .* dst=(0x[0-9a-f]+) w=(\d+) h=(\d+) .* format=(\d+)', l)
        if m:
            fmt.setdefault(m.group(1), set()).add(m.group(4))
        m = re.match(r'EXA bug: pPixmap->devPrivate\.ptr was (0x[0-9a-f]+), but should have been NULL\.$', l.rstrip('\n'))
        if m:
            warn[m.group(1)] += 1
    tot = collections.Counter()
    for a, n in warn.items():
        tot['+'.join(sorted(fmt[a])) if a in fmt else 'unmatched'] += n
    print(f"{path}: total={sum(warn.values())} distinct_ptr={len(warn)} by_format={dict(sorted(tot.items()))}")
