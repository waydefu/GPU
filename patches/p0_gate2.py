#!/usr/bin/env python3
"""P0 Gate 2: xterm create → marker → verify → destroy → residue ×N.
Usage: p0_gate2.py :3 [iters]
Never talks to :1.
"""
import os, socket, struct, subprocess, sys, time, signal

disp = sys.argv[1]
iters = int(sys.argv[2]) if len(sys.argv) > 2 else 100
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
        assert len(body) % 4 == 0
        self.s.sendall(struct.pack('<BBH', op, b1, 1 + len(body) // 4) + body)
        return self.seq
    def _read_reply(self, want_seq):
        """Return (kind, payload) where kind is 'reply'|'error'|None. Consume extras."""
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
                        chunk = self.s.recv(need - len(data))
                        if not chunk:
                            break
                        data += chunk
                    if sq == want_seq:
                        return 'reply', (r, data)
                    continue
        except (TimeoutError, socket.timeout):
            return None, None
    def getpixel(self, dr, x, y):
        seq = self.req(73, struct.pack('<IhhhhI', dr, x, y, 1, 1, 0xFFFFFFFF), b1=2)
        kind, payload = self._read_reply(seq)
        if kind != 'reply':
            return 'ERR' if kind == 'error' else None
        r, data = payload
        if len(data) < 4:
            return 'short'
        b, g, rr = data[0], data[1], data[2]
        return f'#{rr:02x}{g:02x}{b:02x}'
    def fill(self, dr, color, x, y, w, h, gcid):
        self.req(56, struct.pack('<III', gcid, 1 << 2, color))
        self.req(70, struct.pack('<II', dr, gcid) + struct.pack('<hhhh', x, y, w, h))
    def create_gc(self, dr):
        gcid = self.xid()
        self.req(55, struct.pack('<III', gcid, dr, 0))
        return gcid
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
        kids = []
        for i in range(n):
            kids.append(struct.unpack('<I', data[i*4:(i+1)*4])[0])
        return kids
    def destroy(self, w):
        self.req(4, struct.pack('<I', w))
    def close(self):
        try:
            self.s.close()
        except Exception:
            pass

def parse(h):
    if not h or not h.startswith('#') or len(h) != 7:
        return None
    return int(h[1:], 16)

def find_xterm_vt(x):
    kids = x.query_tree(x.root)
    for k in kids:
        grand = x.query_tree(k)
        if grand:
            return k, grand[0]
    return None, None

def wait_vt(x, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        frame, vt = find_xterm_vt(x)
        if vt:
            return frame, vt
        time.sleep(0.05)
    return None, None

def wait_gone(x, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        kids = x.query_tree(x.root)
        if not kids:
            return True
        time.sleep(0.05)
    return False

def xserver_alive():
    try:
        s, root, rid = connect()
        s.close()
        return True
    except Exception:
        return False

def spawn_xterm():
    env = os.environ.copy()
    env['DISPLAY'] = disp
    return subprocess.Popen(
        ['xterm', '-geometry', '80x24+0+0'],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True)

def kill_xterm(proc):
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass
    try:
        proc.wait(timeout=2)
    except Exception:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            pass

def main():
    fails = []
    residue_hits = 0
    x = X()
    kids = x.query_tree(x.root)
    if kids:
        print(f'NOTE destroying pre-existing root children n={len(kids)}')
        for k in kids:
            x.destroy(k)
        wait_gone(x)
    x.close()

    for i in range(1, iters + 1):
        if not xserver_alive():
            fails.append((i, 'X server dead'))
            print(f'FATAL iter {i} X dead')
            break
        proc = spawn_xterm()
        x = X()
        frame, vt = wait_vt(x)
        if not vt:
            fails.append((i, 'xterm did not map'))
            kill_xterm(proc)
            x.close()
            print(f'FAIL iter {i} no map')
            continue
        gcid = x.create_gc(vt)
        time.sleep(0.12)
        ok_draw = False
        g = r = p768 = p1069 = None
        for _try in range(8):
            x.fill(vt, 0x00FF00, 20, 20, 40, 40, gcid)
            x.fill(vt, 0xFF0000, 300, 10, 60, 40, gcid)
            x.sync()
            g = parse(x.getpixel(x.root, 21, 21))
            p768 = parse(x.getpixel(x.root, 789, 21))
            r = parse(x.getpixel(x.root, 301, 11))
            p1069 = parse(x.getpixel(x.root, 1069, 11))
            if g == 0x00FF00 and r == 0xFF0000 and p768 == 0 and p1069 == 0:
                ok_draw = True
                break
            time.sleep(0.04)
        if not ok_draw:
            fails.append((i, f'draw GetImage g={g} r={r} 789={p768} 1069={p1069}'))
            print(f'FAIL iter {i} draw g={g} 789={p768} r={r} 1069={p1069}')
        kill_xterm(proc)
        gone = wait_gone(x)
        if not gone:
            fails.append((i, 'xterm still mapped after kill'))
            print(f'FAIL iter {i} not gone')
        # residue: former marker coords must not stay green/red on empty root
        g2 = parse(x.getpixel(x.root, 21, 21))
        r2 = parse(x.getpixel(x.root, 301, 11))
        if g2 == 0x00FF00 or r2 == 0xFF0000:
            residue_hits += 1
            fails.append((i, f'residue g={g2} r={r2}'))
            print(f'FAIL iter {i} residue g={g2} r={r2}')
        x.close()
        if i % 10 == 0:
            alive = xserver_alive()
            print(f'CHECKPOINT {i}/{iters} alive={alive} fails={len(fails)} residue={residue_hits}')
            if not alive:
                fails.append((i, 'X dead at checkpoint'))
                break

    print(f'GATE2_RESULT iters={iters} fails={len(fails)} residue={residue_hits}')
    for i, msg in fails[:20]:
        print(f'  fail[{i}] {msg}')
    if len(fails) > 20:
        print(f'  ... {len(fails)-20} more')
    print('GATE2 ' + ('FAIL' if fails else 'PASS'))
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
