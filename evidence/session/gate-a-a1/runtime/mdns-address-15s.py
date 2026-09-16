import ipaddress
import time
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

SERVICE = "_adb-tls-connect._tcp.local."


class Listener(ServiceListener):
    def __init__(self):
        self.found = []
        self.names = []

    def add_service(self, zc, service_type, name):
        info = zc.get_service_info(service_type, name, timeout=3000)
        if info and info.port:
            self.found.append((info.parsed_addresses(), info.port, name, info.server))
            self.names.append(name)

    def update_service(self, zc, service_type, name):
        self.add_service(zc, service_type, name)

    def remove_service(self, zc, service_type, name):
        pass


zc = Zeroconf()
listener = Listener()
ServiceBrowser(zc, SERVICE, listener)
deadline = time.time() + 15
try:
    while time.time() < deadline and not listener.found:
        time.sleep(0.2)
    if listener.found:
        time.sleep(0.5)
finally:
    zc.close()

pairs = []
for addresses, port, name, server in listener.found:
    for address in addresses:
        try:
            if ipaddress.ip_address(address).version == 4:
                pairs.append((address, port, name, server))
        except ValueError:
            pass
print("MDNS_ENDPOINTS")
seen = set()
for address, port, name, server in pairs:
    key = (address, port)
    if key in seen:
        continue
    seen.add(key)
    print(f"address={address} port={port} name={name} server={server}")
if not seen:
    raise SystemExit(1)
