#!/usr/bin/env python3
"""Raw X11: create unmapped window, fill rect in it, GetImage it back.
Discriminates pixmap-mapping bugs from window-positioning bugs.
Usage: xpixmaptest.py :2
Saves /root/projects/GPU加速/evidence/nonlegacy/pixmap-self.png
"""
import socket, struct, sys

disp = sys.argv[1]
num = int(disp.split(':')[1].split('.')[0])
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(f'/tmp/.X11-unix/X{num}')
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
white = struct.unpack('<I', rest[off + 8:off + 12])[0]
black = struct.unpack('<I', rest[off + 12:off + 16])[0]
depth = rest[off + 22]
rid_base = struct.unpack('<I', rest[4:8])[0]
print(f'root=0x{root:x} depth={depth} white=0x{white:x} black=0x{black:x}')
seq = 0
def req(op, body):
    global seq
    seq += 1
    s.sendall(struct.pack('<BBH', op, 0, 1 + len(body) // 4) + body)
    return seq
def readreply():
    r = b''
    while len(r) < 32:
        c = s.recv(32 - len(r))
        if not c:
            break
        r += c
    return r
wid = rid_base | 0x1000
gc = rid_base | 0x1001
W, H = 300, 200
# CreateWindow: depth=CopyFromParent(0), wid, parent=root, x,y,w,h,border=0, class=InputOutput(1), visual=CopyFromParent(0), mask=background-pixel|border-pixel
# CreateWindow: depth,pad,wid,parent,x,y,w,h,border,class,visual,mask,bg,borderpixel
req(1, struct.pack('<BBLLhhHHHHII', depth if depth else 0, 0, wid, root, 10, 10, W, H, 0, 1, 0,
                   (1 << 1) | (1 << 3)) + struct.pack('<II', white, black))
# NOTE: do NOT map the window. CreateGC + fill inside it at (20,30) 100x60 white on white bg? use black fg on white bg
req(55, struct.pack('<III', gc, wid, 0))
req(56, struct.pack('<III', gc, 1 << 2, black))
req(70, struct.pack('<II', wid, gc) + struct.pack('<hhhh', 20, 30, 100, 60))
# GetImage ZPixmap(2) drawable wid x,y=0,0 w,h planeMask=all (format goes in header byte 2)
s.sendall(struct.pack('<BBH', 73, 2, 5) + struct.pack('<IHHHHI', wid, 0, 0, W, H, 0xFFFFFFFF))
# drain errors/replies until GetImage reply (type 1)
from PIL import Image
got = None
s.settimeout(5)
try:
    while True:
        r = readreply()
        if not r:
            break
        if r[0] == 0:
            print(f'XERROR code={r[1]} seq={struct.unpack("<H", r[2:4])[0]} major={r[10]}')
        elif r[0] == 1 and len(r) == 32:
            ln = struct.unpack('<I', r[4:8])[0]
            data = b''
            while len(data) < ln * 4:
                data += s.recv(ln * 4 - len(data))
            print(f'GetImage reply len={ln} data={len(data)}')
            got = (r, data)
            break
        else:
            print('other reply type', r[0], len(r))
except socket.timeout:
    print('timeout waiting GetImage')
if got:
    r, data = got
    dep = r[8]
    print('depth', dep)
    img = Image.frombytes('RGB', (W, H), data, 'raw', 'BGRX')
    img.save('/root/projects/GPU加速/evidence/nonlegacy/pixmap-self.png')
    g = img.convert('L')
    P = g.load()
    xs = [x for x in range(W) if any(P[x, y] < 128 for y in range(H))]
    ys = [y for y in range(H) if any(P[x, y] < 128 for x in range(W))]
    print('dark x-range:', (min(xs), max(xs)) if xs else None, '(expected 20..120)')
    print('dark y-range:', (min(ys), max(ys)) if ys else None, '(expected 30..90)')
