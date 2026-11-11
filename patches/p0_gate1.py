#!/usr/bin/env python3
"""P0 Gate 1: one drawable, one GC, ops isolated by coordinate only.
Usage: p0_gate1.py :3 0xVTCHILD
"""
import socket, struct, sys

disp, DRAW = sys.argv[1], sys.argv[2]
num = int(disp.split(':')[1].split('.')[0])
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    s.connect(f'/tmp/.X11-unix/X{num}')
except FileNotFoundError:
    s.connect('\0/tmp/.X11-unix/X%d' % num)
s.sendall(struct.pack('<BxHHHHH', ord('l'), 11, 0, 0, 0, 0))
hdr = s.recv(8)
ok, rl, major, minor, extra = struct.unpack('<BBHHH', hdr)
assert ok == 1
rest = b''
while len(rest) < extra * 4:
    rest += s.recv(extra * 4 - len(rest))
vlen, maxreq, nroots, nfmts = struct.unpack('<HHBB', rest[16:22])
off = 32 + ((vlen + 3) & ~3) + nfmts * 8
root = struct.unpack('<I', rest[off:off + 4])[0]
rid_base = struct.unpack('<I', rest[4:8])[0]
vendor = rest[32:32 + vlen]
nroots, nfmts  # silence
target = int(DRAW, 16) if DRAW.startswith('0x') else int(DRAW)
RED, WHITE, GREEN = 0xFF0000, 0xFFFFFF, 0x00FF00
seq = 0
NAMES = {}

def req(op, body, b1=0, name='?'):
    global seq
    seq += 1
    NAMES[seq] = name
    assert len(body) % 4 == 0, (name, len(body))
    s.sendall(struct.pack('<BBH', op, b1, 1 + len(body) // 4) + body)
    return seq

def recv32():
    r = b''
    while len(r) < 32:
        c = s.recv(32 - len(r))
        if not c:
            return r
        r += c
    return r

def getpixel(drawable, x, y):
    req(73, struct.pack('<IhhhhI', drawable, x, y, 1, 1, 0xFFFFFFFF), b1=2, name='GetImage')
    while True:
        r = recv32()
        if not r or len(r) < 32:
            return None
        t = r[0]
        if t == 0:
            sq = struct.unpack('<H', r[2:4])[0]
            print(f'XERROR GetImage code={r[1]} seq={sq}({NAMES.get(sq, "?")}) at {x},{y}')
            return 'ERR'
        if t == 1:
            ln = struct.unpack('<I', r[4:8])[0]
            data = bytearray(r[32:])
            need = ln * 4
            while len(data) < need:
                chunk = s.recv(need - len(data))
                if not chunk:
                    break
                data += chunk
            if len(data) < 4:
                return f'short:{len(data)}'
            b, g, rr = data[0], data[1], data[2]
            return f'#{rr:02x}{g:02x}{b:02x}'
        # event: keep waiting for the GetImage reply

def drain_errors(timeout=0.4):
    s.settimeout(timeout)
    errs = []
    try:
        while True:
            r = s.recv(32)
            if not r:
                break
            if r[0] == 0:
                sq = struct.unpack('<H', r[2:4])[0]
                errs.append((r[1], sq, NAMES.get(sq, '?')))
            if len(r) < 32:
                break
    except socket.timeout:
        pass
    s.settimeout(3)
    return errs

gcid = rid_base | 0x100000
fid = rid_base | 0x100001
req(55, struct.pack('<III', gcid, target, 0), name='CreateGC')
# white-clear the op region so leftover Case C red/green cannot fake a PASS
req(56, struct.pack('<III', gcid, 1 << 2, WHITE), name='ChangeGC-white')
req(70, struct.pack('<II', target, gcid) + struct.pack('<hhhh', 280, 0, 200, 240), name='ClearWhite')
req(56, struct.pack('<III', gcid, 1 << 2, RED), name='ChangeGC-red')

# ops at distinct spots, same drawable/GC
req(70, struct.pack('<II', target, gcid) + struct.pack('<hhhh', 300, 10, 60, 40), name='FillRect')
req(69, struct.pack('<IIBBH', target, gcid, 2, 0, 0) + struct.pack('<hhhhhh', 300, 70, 360, 70, 330, 110), b1=0, name='FillPoly')
req(66, struct.pack('<II', target, gcid) + struct.pack('<hhhh', 300, 130, 360, 170), name='Segment')
req(65, struct.pack('<II', target, gcid) + struct.pack('<hhhh', 380, 130, 440, 130), b1=0, name='PolyLine')
px = struct.pack('<I', RED) * (50 * 50)
req(72, struct.pack('<IIHHHHBB', target, gcid, 50, 50, 380, 10, 0, 24) + b'\x00\x00' + px, b1=2, name='PutImage')
fname = b'fixed'
req(45, struct.pack('<IHH', fid, len(fname), 0) + fname + b'\x00\x00\x00', name='OpenFont')
req(56, struct.pack('<III', gcid, 1 << 14, fid), name='ChangeGC-font')
req(76, struct.pack('<IIhh', target, gcid, 300, 200) + b'Hi\x00\x00', b1=2, name='ImageText8')

errs = drain_errors(0.8)
for code, sq, name in errs:
    print(f'XERROR code={code} seq={sq}({name})')

# RENDER QueryExtension + FillRectangles at (380,180) 40x30 if present
# opcode QueryExtension=98
qname = b'RENDER'
req(98, struct.pack('<HH', len(qname), 0) + qname + b'\x00\x00', name='QueryExt-RENDER')
s.settimeout(2)
render_major = None
try:
    while True:
        r = recv32()
        if not r:
            break
        if r[0] == 0:
            sq = struct.unpack('<H', r[2:4])[0]
            print(f'XERROR code={r[1]} seq={sq}({NAMES.get(sq, "?")})')
            errs.append((r[1], sq, NAMES.get(sq, '?')))
        elif r[0] == 1:
            present = r[8]
            maj = r[9]
            if present:
                render_major = maj
            break
except socket.timeout:
    pass

if render_major is not None:
    print(f'RENDER present major_opcode={render_major} (glyph path = CORE ImageText8; no extra RENDER req)')
else:
    print('RENDER extension absent')

s.settimeout(3)
probes = {
    'FillRect': (target, 330, 30, RED),
    'FillPoly': (target, 330, 83, RED),
    'Segment': (target, 330, 150, RED),
    'PolyLine': (target, 410, 130, RED),
    'PutImage': (target, 405, 35, RED),
    'ImageText8-ink': (target, 302, 195, None),  # not white
    'FillRect-control-white': (target, 290, 50, WHITE),
}
# +768 regression on ROOT
reg = {
    '+768-green-slot': (root, 21, 21, None),
    '+768-probe-789': (root, 789, 21, 0x000000),
    '+768-red-slot': (root, 301, 11, RED),  # FillRect window 300,10 + VT origin 1,1
    '+768-probe-1069': (root, 1069, 11, 0x000000),
}

def parse_hex(h):
    if not h or h == 'ERR':
        return None
    return int(h[1:], 16)

fail = 0
print(f'target=0x{target:x} root=0x{root:x}')
for name, (dr, x, y, expect) in probes.items():
    got = getpixel(dr, x, y)
    gh = parse_hex(got)
    if expect is None:
        ok = gh is not None and gh != WHITE
        verdict = 'PASS' if ok else 'FAIL'
        if not ok:
            fail += 1
        print(f'{verdict} {name} ({x},{y}) {got} (expect not-white)')
    else:
        ok = gh == expect
        verdict = 'PASS' if ok else 'FAIL'
        if not ok:
            fail += 1
        print(f'{verdict} {name} ({x},{y}) {got} expect=#{expect:06x}')

print('--- +768 regression (root) ---')
for name, (dr, x, y, expect) in reg.items():
    got = getpixel(dr, x, y)
    gh = parse_hex(got)
    if expect is None:
        print(f'INFO {name} ({x},{y}) {got}')
    else:
        ok = gh == expect
        verdict = 'PASS' if ok else 'FAIL'
        if not ok:
            fail += 1
        print(f'{verdict} {name} ({x},{y}) {got} expect=#{expect:06x}')

if errs:
    fail += 1
    print(f'FAIL request-errors n={len(errs)}')
else:
    print('PASS no XERROR')

print('GATE1_GETIMAGE ' + ('FAIL' if fail else 'PASS'))
sys.exit(1 if fail else 0)
