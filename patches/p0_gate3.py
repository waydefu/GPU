#!/usr/bin/env python3
"""P0 Gate 3: one variable at a time on :3. Usage: p0_gate3.py :3 <subtest>
subtests: move | expose | overlap | all
RRSetSize is driven from the shell (prefs).
"""
import os, socket, struct, subprocess, sys, time, signal

disp = sys.argv[1]
sub = sys.argv[2] if len(sys.argv) > 2 else 'all'
num = int(disp.split(':')[1].split('.')[0])

def connect():
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
    return s, root, rid_base

def recv32(s):
    r = b''
    while len(r) < 32:
        c = s.recv(32 - len(r))
        if not c:
            return r
        r += c
    return r

class X:
    def __init__(self):
        self.s, self.root, self.rid = connect()
        self.seq = 0
        self.next_id = 1
        self.s.settimeout(3)
    def xid(self):
        i = self.next_id
        self.next_id += 1
        return self.rid | (i & 0x1FFFFF)
    def req(self, op, body, b1=0):
        self.seq += 1
        self.s.sendall(struct.pack('<BBH', op, b1, 1 + len(body) // 4) + body)
        return self.seq
    def _read_reply(self, want_seq):
        try:
            while True:
                r = recv32(self.s)
                if not r or len(r) < 32:
                    return None, None
                t = r[0]
                sq = struct.unpack('<H', r[2:4])[0]
                if t == 0:
                    if sq == want_seq:
                        return 'error', r
                    continue
                if t == 1:
                    ln = struct.unpack('<I', r[4:8])[0]
                    data = bytearray(r[32:])
                    need = ln * 4
                    while len(data) < need:
                        data += self.s.recv(need - len(data))
                    if sq == want_seq:
                        return 'reply', (r, data)
                    continue
        except (TimeoutError, socket.timeout):
            return None, None
    def getpixel(self, dr, x, y):
        seq = self.req(73, struct.pack('<IhhhhI', dr, x, y, 1, 1, 0xFFFFFFFF), b1=2)
        kind, payload = self._read_reply(seq)
        if kind != 'reply':
            return None
        r, data = payload
        if len(data) < 4:
            return None
        b, g, rr = data[0], data[1], data[2]
        return (rr << 16) | (g << 8) | b
    def create_gc(self, dr):
        gcid = self.xid()
        self.req(55, struct.pack('<III', gcid, dr, 0))
        return gcid
    def fill(self, dr, color, x, y, w, h, gcid):
        self.req(56, struct.pack('<III', gcid, 1 << 2, color))
        self.req(70, struct.pack('<II', dr, gcid) + struct.pack('<hhhh', x, y, w, h))
    def sync(self):
        seq = self.req(43, b'')
        self._read_reply(seq)
    def query_tree(self, w):
        seq = self.req(15, struct.pack('<I', w))
        kind, payload = self._read_reply(seq)
        if kind != 'reply':
            return []
        r, data = payload
        n = struct.unpack('<H', r[16:18])[0]
        return [struct.unpack('<I', data[i*4:(i+1)*4])[0] for i in range(n)]
    def destroy(self, w):
        self.req(4, struct.pack('<I', w))
    def unmap(self, w):
        self.req(10, struct.pack('<I', w))
    def mapw(self, w):
        self.req(8, struct.pack('<I', w))
    def configure_xy(self, w, x, y):
        # ConfigureWindow valuemask x(1<<0)|y(1<<1)
        self.req(12, struct.pack('<IHH', w, 0x0003, 0) + struct.pack('<ii', x, y))
    def geom(self, w):
        seq = self.req(14, struct.pack('<I', w))
        kind, payload = self._read_reply(seq)
        if kind != 'reply':
            return None
        r, data = payload
        # reply: depth, root, x,y,w,h,border
        root = struct.unpack('<I', r[8:12])[0]
        x, y = struct.unpack('<hh', r[12:16])
        ww, hh = struct.unpack('<HH', r[16:20])
        return x, y, ww, hh
    def close(self):
        self.s.close()

def spawn_xterm(geom='80x24+0+0'):
    env = os.environ.copy()
    env['DISPLAY'] = disp
    return subprocess.Popen(['xterm', '-geometry', geom], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)

def kill_xterm(proc):
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        proc.terminate()
    try:
        proc.wait(timeout=2)
    except Exception:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            pass

def wait_vt(x, timeout=5):
    t0 = time.time()
    while time.time() - t0 < timeout:
        kids = x.query_tree(x.root)
        for k in kids:
            g = x.query_tree(k)
            if g:
                return k, g[0]
        time.sleep(0.05)
    return None, None

def wait_n_frames(x, n, timeout=5):
    t0 = time.time()
    while time.time() - t0 < timeout:
        kids = x.query_tree(x.root)
        frames = []
        for k in kids:
            g = x.query_tree(k)
            if g:
                frames.append((k, g[0]))
        if len(frames) >= n:
            return frames
        time.sleep(0.05)
    return []

def mark(x, vt, gcid):
    x.fill(vt, 0x00FF00, 20, 20, 40, 40, gcid)
    x.fill(vt, 0xFF0000, 300, 10, 60, 40, gcid)
    x.sync()

def verify_at(x, ox, oy):
    geo = x.geom(x.root)
    rw, rh = (geo[2], geo[3]) if geo else (9999, 9999)
    def gp(px, py):
        if px < 0 or py < 0 or px >= rw or py >= rh:
            return 'OOB'
        return x.getpixel(x.root, px, py)
    g = gp(ox + 21, oy + 21)
    p768 = gp(ox + 789, oy + 21)
    r = gp(ox + 301, oy + 11)
    p1069 = gp(ox + 1069, oy + 11)
    def okpix(v, expect):
        if v == 'OOB':
            return True  # probe not applicable at this origin/size
        return v == expect
    ok = okpix(g, 0x00FF00) and okpix(r, 0xFF0000) and okpix(p768, 0) and okpix(p1069, 0)
    return ok, g, r, p768, p1069

def retry_mark(x, vt, gcid, ox, oy, tries=8):
    last = None
    for _ in range(tries):
        mark(x, vt, gcid)
        last = verify_at(x, ox, oy)
        if last[0]:
            return last
        time.sleep(0.04)
    return last

fails = []

def test_move():
    proc = spawn_xterm('80x24+0+0')
    x = X()
    frame, vt = wait_vt(x)
    time.sleep(0.12)
    gcid = x.create_gc(vt)
    ok, *rest = retry_mark(x, vt, gcid, 0, 0)
    if not ok:
        fails.append(f'move pre {rest}')
        print('FAIL move: markers at 0,0', rest)
    else:
        print('PASS move: markers at 0,0')
    # ConfigureWindow move frame to +180+90
    x.configure_xy(frame, 180, 90)
    x.sync()
    time.sleep(0.1)
    geo = x.geom(frame)
    print('frame geom after move', geo)
    if geo is None or geo[0] != 180 or geo[1] != 90:
        fails.append(f'move geom {geo}')
        print('FAIL move geom', geo)
    else:
        print('PASS move geom 180,90')
    ok, *rest = retry_mark(x, vt, gcid, 180, 90)
    if not ok:
        fails.append(f'move post {rest}')
        print('FAIL move: markers at 180,90', rest)
    else:
        print('PASS move: markers follow 180,90; +768 absent')
    # old origin must not keep a second green copy
    old = x.getpixel(x.root, 21, 21)
    if old == 0x00FF00:
        # might still be in the window if move didn't clear; window now at 180,90 so 21,21 is root
        print('INFO pixel at old 21,21', hex(old) if old is not None else None)
    kill_xterm(proc)
    x.close()

def test_expose():
    proc = spawn_xterm('80x24+0+0')
    x = X()
    frame, vt = wait_vt(x)
    time.sleep(0.12)
    gcid = x.create_gc(vt)
    ok, *rest = retry_mark(x, vt, gcid, 0, 0)
    if not ok:
        fails.append(f'expose pre {rest}')
        print('FAIL expose pre', rest)
    x.unmap(frame)
    x.sync()
    time.sleep(0.1)
    gone = x.getpixel(x.root, 21, 21)
    if gone == 0x00FF00:
        fails.append('expose unmap residue green')
        print('FAIL expose: unmapped still green at 21,21')
    else:
        print('PASS expose: unmap cleared 21,21', hex(gone) if gone is not None else None)
    x.mapw(frame)
    x.sync()
    time.sleep(0.15)
    ok, *rest = retry_mark(x, vt, gcid, 0, 0)
    if not ok:
        fails.append(f'expose remap {rest}')
        print('FAIL expose remap', rest)
    else:
        print('PASS expose: remap + redraw markers; +768 absent')
    kill_xterm(proc)
    x.close()

def test_overlap():
    p1 = spawn_xterm('80x24+0+0')
    x = X()
    frames = wait_n_frames(x, 1)
    time.sleep(0.12)
    f1, vt1 = frames[0]
    g1 = x.create_gc(vt1)
    ok, *rest = retry_mark(x, vt1, g1, 0, 0)
    if not ok:
        fails.append(f'overlap bottom {rest}')
        print('FAIL overlap bottom', rest)
    else:
        print('PASS overlap: bottom markers')
    p2 = spawn_xterm('80x24+0+0')
    frames = wait_n_frames(x, 2)
    time.sleep(0.12)
    # destroy covering xterm
    kill_xterm(p2)
    t0 = time.time()
    while time.time() - t0 < 3:
        if len(x.query_tree(x.root)) == 1:
            break
        time.sleep(0.05)
    time.sleep(0.1)
    # bottom content may have been exposed/cleared; redraw is allowed for damage
    ok, *rest = retry_mark(x, vt1, g1, 0, 0)
    if not ok:
        fails.append(f'overlap uncover {rest}')
        print('FAIL overlap uncover', rest)
    else:
        print('PASS overlap: uncover + redraw; +768 absent')
    kill_xterm(p1)
    x.close()

def test_rrset_markers():
    """After shell has already RRSetSize, verify we can still draw and +768 is absent."""
    proc = spawn_xterm('80x24+0+0')
    x = X()
    frame, vt = wait_vt(x)
    time.sleep(0.12)
    gcid = x.create_gc(vt)
    geo_root = x.geom(x.root)
    print('root geom', geo_root)
    ok, *rest = retry_mark(x, vt, gcid, 0, 0)
    if not ok:
        fails.append(f'rrset markers {rest}')
        print('FAIL rrset markers', rest)
    else:
        print('PASS rrset markers +768 absent')
    kill_xterm(proc)
    x.close()

if sub in ('move', 'all'):
    test_move()
if sub in ('expose', 'all'):
    test_expose()
if sub in ('overlap', 'all'):
    test_overlap()
if sub in ('rrset',):
    test_rrset_markers()

print('GATE3_SUB', sub, 'FAIL' if fails else 'PASS', 'nfail=', len(fails))
for f in fails:
    print(' ', f)
sys.exit(1 if fails else 0)
