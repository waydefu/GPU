#!/usr/bin/env python3
"""Minimal raw X11 client: fill a rect on ANY drawable at exact coords.
Usage: xfillrect.py <display> <drawable> <colorhex> <x> <y> <w> <h>
  drawable: root or 0x... window id (e.g. 0x511, 0x20000c)
  colorhex: e.g. ffffff, ff0000, 00ff00
"""
import socket, struct, sys, os

disp, DRAW, COLOR, X, Y, W, H = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7])
num = int(disp.split(':')[1].split('.')[0])
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    s.connect(f'/tmp/.X11-unix/X{num}')
except FileNotFoundError:
    s.connect('\0/tmp/.X11-unix/X%d' % num)  # abstract socket fallback
# setup: little-endian, X11.0, no auth
s.sendall(struct.pack('<BxHHHHH', ord('l'), 11, 0, 0, 0, 0))
hdr = s.recv(8)
assert len(hdr) == 8, hdr
ok, reason_len, major, minor, extra = struct.unpack('<BBHHH', hdr)
assert ok == 1, f'setup failed status={ok}'
rest = b''
need = extra * 4
while len(rest) < need:
    rest += s.recv(need - len(rest))
# parse setup fixed part
(rls, rid_base, rid_mask, motion_len, vlen, max_req, nroots,
 nformats, img_bo, bmp_bo, bmp_scan, bmp_pad, min_kc, max_kc) = struct.unpack('<IIIIHHBBBBBBBBxxxx', rest[:32])
# root = first screen: skip vendor string (padded) + format list (8B each)
off = 32 + ((vlen + 3) & ~3) + nformats * 8
root = struct.unpack('<I', rest[off:off+4])[0]
white = struct.unpack('<I', rest[off+8:off+12])[0]
target = int(DRAW, 16) if DRAW.startswith('0x') else (root if DRAW == 'root' else int(DRAW))
fg = int(COLOR, 16)
print(f'root=0x{root:x} white=0x{white:x} idbase=0x{rid_base:x}')
seq = 0
def req(opcode, body):
    global seq
    seq += 1
    s.sendall(struct.pack('<BBH', opcode, 0, 1 + len(body) // 4) + body)
    return seq
gcid = rid_base | 0x100000  # stay clear of other clients' low ids
# CreateGC empty (valuemask=0), then set foreground
req(55, struct.pack('<III', gcid, target, 0))
# ChangeGC foreground=fg
req(56, struct.pack('<III', gcid, (1 << 2), fg))
# PolyFillRectangle target gc x,y,w,h
req(70, struct.pack('<II', target, gcid) + struct.pack('<hhhh', X, Y, W, H))
import select
s.settimeout(2)
errs = 0
try:
    while True:
        r = s.recv(32)
        if not r:
            break
        if r[0] == 0:
            print(f'XERROR code={r[1]} seq={struct.unpack("<H", r[2:4])[0]} value=0x{struct.unpack("<I", r[4:8])[0]:x} major={r[10]} minor={struct.unpack("<H", r[8:10])[0]}')
            errs += 1
        if len(r) < 32:
            break
except socket.timeout:
    pass
print(('FAILED' if errs else 'OK') + f' filled root rect ({X},{Y}) {W}x{H} white')
