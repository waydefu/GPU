#!/bin/bash
# proot-fast v3 check: interface enumeration (getifaddrs / Node / iproute2), then the v2 fast paths must stay fast.
python3 -c "import ifaddr; print('ifaddr', sorted(a.name for a in ifaddr.get_adapters()))" 2>&1 | tail -1
node -e "try{console.log('node_ifaces', Object.keys(require('os').networkInterfaces()).sort().join(','))}catch(e){console.log('node_THROW', e.message)}"
ip -brief addr 2>&1 | awk '{print "ip", $1, $3}' | head -4
/root/build/proot-bench/sysbench2 | grep -E 'vdso|futex|epoll|send\+recv'
