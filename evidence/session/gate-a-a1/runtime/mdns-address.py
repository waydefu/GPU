import ipaddress
import time
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

SERVICE = "_adb-tls-connect._tcp.local."


class Listener(ServiceListener):
    def __init__(self):
        self.found = []

    def add_service(self, zc, service_type, name):
        info = zc.get_service_info(service_type, name, timeout=2000)
        if info and info.port:
            self.found.append((info.parsed_addresses(), info.port))

    def update_service(self, zc, service_type, name):
        self.add_service(zc, service_type, name)

    def remove_service(self, zc, service_type, name):
        pass


zc = Zeroconf()
listener = Listener()
ServiceBrowser(zc, SERVICE, listener)
deadline = time.time() + 6
try:
    while time.time() < deadline and not listener.found:
        time.sleep(0.2)
finally:
    zc.close()

pairs = set()
for addresses, port in listener.found:
    for address in addresses:
        try:
            if ipaddress.ip_address(address).version == 4:
                pairs.add((address, port))
        except ValueError:
            pass
print("MDNS_ENDPOINTS")
for address, port in sorted(pairs):
    print(f"address={address} port={port}")
if not pairs:
    raise SystemExit(1)
