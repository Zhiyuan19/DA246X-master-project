#from mininet.net import Mininet
from containernet.net import Containernet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
#from mininet.cli import CLI
from containernet.cli import CLI
from containernet.link import TCLink
#from mininet.log import setLogLevel
from mininet.log import info, setLogLevel
import subprocess
import os

def simpleTopo():
    net = Containernet(controller=None, switch=OVSKernelSwitch)
    
    # Add hosts
    h1 = net.addHost('h1', ip='10.0.0.20/24', defaultRoute='via 10.0.0.254')
    dns = net.addDocker('dns', ip='10.0.0.21/24', dimage="ubuntu:trusty", defaultRoute='via 10.0.0.254')
    h3 = net.addHost('h3', ip='10.0.1.2/24', defaultRoute='via 10.0.1.1')
    h4 = net.addHost('h4', ip='10.0.1.3/24', defaultRoute='via 10.0.1.1')
    ws1 = net.addHost('ws1', ip='100.0.0.40/24', defaultRoute='via 100.0.0.254')
    fw = net.addHost('fw', ip='10.0.1.1/24')
    # Add switch
    s1 = net.addSwitch('s1', dpid="1")
    s2 = net.addSwitch('s2', dpid="2")
    s3 = net.addSwitch('s3', dpid="3")
    
    # Add links
    net.addLink(fw, s2)  # Interface for Prz
    net.addLink(fw, s3)  # Interface for DMZ
    net.addLink(fw, s1)  # Interface for pbz network
    net.addLink(h1, s1)
    net.addLink(dns, s1)
    net.addLink(h3, s2)
    net.addLink(h4, s2)
    net.addLink(ws1, s3)
    
    # Add controller
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633 )
    
    net.start()
    
    net.get("fw").cmd("ifconfig fw-eth0 10.0.1.1 netmask 255.255.255.0")
    net.get("fw").cmd("ifconfig fw-eth1 100.0.0.1 netmask 255.255.255.0")
    net.get("fw").cmd("ifconfig fw-eth2 10.0.0.22 netmask 255.255.255.0")
    net.get("fw").cmd('sysctl -w net.ipv4.ip_forward=1')
    
    # Check if iptables is available and add firewall rules
    if net.get("fw").cmd('which iptables'):
        # Flush existing rules
        net.get("fw").cmd('iptables -F')
        net.get("fw").cmd('iptables -t nat -F')
        net.get("fw").cmd('iptables -t mangle -F')
        net.get("fw").cmd('iptables -X')

        # Default policies to drop all traffic
        net.get("fw").cmd('iptables -P FORWARD DROP')

        # Allow all traffic on the loopback interface
        #net.get("fw").cmd('iptables -A INPUT -i lo -j ACCEPT')
        #net.get("fw").cmd('iptables -A OUTPUT -o lo -j ACCEPT')

        # Allow traffic from internal to DMZ
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth2 -j ACCEPT')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth0 -j DROP')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth2 -j ACCEPT')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth1 -m state --state ESTABLISHED,RELATED -j ACCEPT')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth1 -j ACCEPT')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth2 -m state --state ESTABLISHED,RELATED -j ACCEPT')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth1 -j ACCEPT')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth0 -j ACCEPT')
        net.get("fw").cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth1 -m state --state ESTABLISHED,RELATED -j ACCEPT')

    else:
        print("iptables not found on fw host")
    # Configure routing and Internet access
    net.get("dns").cmd("ip route add 10.0.1.0/24 via 10.0.0.22")
    net.get("dns").cmd("ip route add 100.0.0.0/24 via 10.0.0.22")
    net.get("h1").cmd("ip route add 10.0.1.0/24 via 10.0.0.22")
    net.get("h1").cmd("ip route add 100.0.0.0/24 via 10.0.0.22")
    s1.cmd('ifconfig s1 10.0.0.254/24')
    
    net.get("ws1").cmd("ip route add 10.0.1.0/24 via 100.0.0.1")
    net.get("ws1").cmd("ip route add 10.0.0.0/24 via 100.0.0.1")
    s3.cmd('ifconfig s3 100.0.0.254/24')
    
        
    h1.cmd('echo "nameserver 8.8.8.8" > /tmp/resolv.conf')
    dns.cmd('echo "nameserver 8.8.8.8" > /tmp/resolv.conf')
    
    h1.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
    dns.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
    
    dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
    dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
    #install DNS
    dns.cmd('apt-get update')
    dns.cmd('echo "Y" |apt install bind9 bind9utils bind9-doc')
    dns.cmd('echo "Y" |apt install dnsutils')
    #configure DNS
    
    os.system('docker cp /home/ik2220/Desktop/project/topology/named.conf.options mn.dns:/etc/bind/')
    os.system('docker cp /home/ik2220/Desktop/project/topology/named.conf.local mn.dns:/etc/bind/')
    os.system('docker cp /home/ik2220/Desktop/project/topology/db.demo.com mn.dns:/etc/bind/')
    os.system('docker cp /home/ik2220/Desktop/project/topology/db.0.0.10 mn.dns:/etc/bind/')

    dns.cmd('service bind9 restart')
    
    
    h1.cmd('echo "nameserver 10.0.0.21" > /etc/resolv.conf')
    dns.cmd('echo "nameserver 10.0.0.21" > /etc/resolv.conf')
    
    #configure snort
    fw.cmd('snort -T -c /etc/snort/snort.conf -i fw-eth2')
    fw.cmd('snort -D -i fw-eth2 -c /etc/snort/snort.conf -A fast')
    fw.cmd('snort -D -i fw-eth0 -c /etc/snort/snorteth0.conf -A fast')
    fw.cmd('snort -D -i fw-eth1 -c /etc/snort/snorteth1.conf -A fast')
    
    print("Testing connectivity in my network")
    net.pingAll()
    print("\nTesting bandwidth between h1 and ws1...")
    h1, ws1 = net.get('h1', 'ws1')
    result = ws1.cmd('iperf -s &')  
    print(h1.cmd('iperf -c', ws1.IP()))  
    
    #h1.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
    #dns.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
    CLI(net)
    #dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    os.system('sudo sysctl -w net.ipv4.ip_forward=1')
    os.system('sudo iptables -t nat -A POSTROUTING -o enp0s8 -j MASQUERADE')
    os.system('ip route')
    os.system('sudo iptables -A FORWARD -i s1 -j ACCEPT')
    os.system('sudo iptables -A FORWARD -o s1 -j ACCEPT')
    os.system('sudo iptables -A FORWARD -i s3 -j ACCEPT')
    os.system('sudo iptables -A FORWARD -o s3 -j ACCEPT')
    
    simpleTopo()
    os.system('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
