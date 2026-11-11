#!/usr/bin/env python3
"""Op matrix on ONE drawable with ONE GC: fillrect, fillpoly, segment, putimage, text.
Usage: xopmatrix.py <display> <drawable>   (e.g. xopmatrix.py :3 0x20000c)
All ops solid RED (00ff0000? no: ff0000) at distinct spots. Prints XERRORs if any.
"""
import socket, struct, sys

disp, DRAW = sys.argv[1], sys.argv[2]
num = int(disp.split(':')[1].split('.')[0])
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    s.connect(f'/tmp/.X11-unix/X{num}')
except FileNotFoundError:
    s.connect('\0/tmp/.X11-unix/X%d' % num)  # abstract socket fallback
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
target = int(DRAW, 16) if DRAW.startswith('0x') else int(DRAW)
RED = 0xFF0000
seq = 0
NAMES = {}
def req(op, body, b1=0, name='?'):
    global seq
    seq += 1
    NAMES[seq] = name
    s.sendall(struct.pack('<BBH', op, b1, 1 + len(body) // 4) + body)
    return seq
gcid = rid_base | 0x100000
fid = rid_base | 0x100001
req(55, struct.pack('<III', gcid, target, 0), name='CreateGC')
req(56, struct.pack('<III', gcid, 1 << 2, RED), name='ChangeGC-fg')
# 1. PolyFillRectangle (70) at (300,10) 60x40
req(70, struct.pack('<II', target, gcid) + struct.pack('<hhhh', 300, 10, 60, 40), name='FillRect')
# 2. FillPoly (69) triangle (300,70)(360,70)(330,110)
# xFillPolyReq: drawable, gc, then shape/coordMode/pad (NOT points immediately).
# shape: Complex=0 Nonconvex=1 Convex=2; coordMode Origin=0. Header byte1 is pad.
req(69, struct.pack('<IIBBH', target, gcid, 2, 0, 0) + struct.pack('<hhhhhh', 300, 70, 360, 70, 330, 110), b1=0, name='FillPoly')
# 3. PolySegment (66) (300,130)-(360,170)
req(66, struct.pack('<II', target, gcid) + struct.pack('<hhhh', 300, 130, 360, 170), name='Segment')
# 3b. PolyLine (65) header byte1 = coordMode Origin; (380,130)-(440,130)
req(65, struct.pack('<II', target, gcid) + struct.pack('<hhhh', 380, 130, 440, 130), b1=0, name='PolyLine')
# 4. PutImage (72) ZPixmap 50x50 at (380,10), depth 24, solid red
px = struct.pack('<I', RED) * (50 * 50)
req(72, struct.pack('<IIHHHHBB', target, gcid, 50, 50, 380, 10, 0, 24) + b'\x00\x00' + px, b1=2, name='PutImage')
# 5. OpenFont 'fixed' + text 'Hi' at (300,200)
fname = b'fixed'
req(45, struct.pack('<IHH', fid, len(fname), 0) + fname + b'\x00\x00\x00', name='OpenFont')
req(56, struct.pack('<III', gcid, 1 << 14, fid), name='ChangeGC-font')
# ImageText8: n in header byte1, then drawable/gc/x/y + STRING8 + pad
req(76, struct.pack('<IIhh', target, gcid, 300, 200) + b'Hi\x00\x00', b1=2, name='ImageText8')
s.settimeout(3)
errs = 0
try:
    while True:
        r = s.recv(32)
        if not r:
            break
        if r[0] == 0:
            sq = struct.unpack('<H', r[2:4])[0]
            print(f'XERROR code={r[1]} seq={sq}({NAMES.get(sq, "?")}) major={r[10]}')
            errs += 1
        if len(r) < 32:
            break
except socket.timeout:
    pass
print(('FAILED' if errs else 'OK') + ' op matrix done')
