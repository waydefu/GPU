import socket, struct, sys
CNXN, STLS, AUTH = 0x4e584e43, 0x534c5453, 0x48545541
def is_adbd(port, host="127.0.0.1", timeout=1.0):
    payload = b"host::\x00"
    pkt = struct.pack("<6I", CNXN, 0x01000001, 256 * 1024, len(payload), 0, CNXN ^ 0xffffffff) + payload
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout); s.sendall(pkt)
            hdr = b""
            while len(hdr) < 24:
                chunk = s.recv(24 - len(hdr))
                if not chunk: break
                hdr += chunk
    except OSError as e:
        return f"no ({e.__class__.__name__})"
    if len(hdr) < 24: return f"no (got {len(hdr)} bytes)"
    cmd, _, _, _, _, magic = struct.unpack("<6I", hdr)
    ok = cmd in (CNXN, STLS, AUTH) and magic == cmd ^ 0xffffffff
    return f"{'YES' if ok else 'no'} (cmd=0x{cmd:08x})"
for p in sys.argv[1:]:
    print(p, is_adbd(int(p)))
