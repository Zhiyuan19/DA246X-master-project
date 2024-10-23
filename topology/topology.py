from containernet.net import Containernet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from containernet.cli import CLI
from containernet.link import TCLink
from mininet.log import info, setLogLevel
import subprocess
import os

class Mytopo:
    def __init__(self):
        self.net = Containernet(controller=None, switch=OVSKernelSwitch)
        
        # Add hosts
        h1 = self.net.addHost('h1', ip='10.0.0.20/24', defaultRoute='via 10.0.0.22')
        dns = self.net.addDocker('dns', ip='10.0.0.21/24', dimage="containernet:dns", defaultRoute='via 10.0.0.254')
        h3 = self.net.addHost('h3', ip='10.0.1.2/24', defaultRoute='via 10.0.1.1')
        h4 = self.net.addHost('h4', ip='10.0.1.3/24', defaultRoute='via 10.0.1.1')
        ws1 = self.net.addDocker('ws1', ip='100.0.0.40/24', dimage="containernet:videoserver", ports=[8001,8081,8082],devices=["/dev/video0","/dev/snd"], defaultRoute='via 100.0.0.254')
        fw = self.net.addHost('fw', ip='10.0.1.1/24')
        
        # Add switch
        s1 = self.net.addSwitch('s1', dpid="1")
        s2 = self.net.addSwitch('s2', dpid="2")
        s3 = self.net.addSwitch('s3', dpid="3")
    
        # Add links
        self.net.addLink(fw, s2)  # Interface for Prz
        self.net.addLink(fw, s3)  # Interface for DMZ
        self.net.addLink(fw, s1)  # Interface for pbz network
        self.net.addLink(h1, s1)
        self.net.addLink(dns, s1)
        self.net.addLink(h3, s2)
        self.net.addLink(h4, s2)
        self.net.addLink(ws1, s3)
    
        # Add controller
        self.net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633 )
    
        self.net.start()
    
        self.net.get("fw").cmd("ifconfig fw-eth0 10.0.1.1 netmask 255.255.255.0")
        self.net.get("fw").cmd("ifconfig fw-eth1 100.0.0.1 netmask 255.255.255.0")
        self.net.get("fw").cmd("ifconfig fw-eth2 10.0.0.22 netmask 255.255.255.0")
        self.net.get("fw").cmd('sysctl -w net.ipv4.ip_forward=1')
        fw.cmd('ip route add default via 100.0.0.254')
    
        # Check if iptables is available and add firewall rules
        if self.net.get("fw").cmd('which iptables'):
            # Flush existing rules
            self.net.get("fw").cmd('iptables -F')
            self.net.get("fw").cmd('iptables -t nat -F')
            self.net.get("fw").cmd('iptables -t mangle -F')
            self.net.get("fw").cmd('iptables -X')

            # Default policies to drop all traffic
            self.net.get("fw").cmd('iptables -P FORWARD DROP')

            # Allow all traffic on the loopback interface
            #self.net.get("fw").cmd('iptables -A INPUT -i lo -j ACCEPT')
            #self.net.get("fw").cmd('iptables -A OUTPUT -o lo -j ACCEPT')

            # Allow traffic from internal to DMZ
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth2 -j ACCEPT')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth0 -j DROP')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth2 -j ACCEPT')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth1 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth1 -j ACCEPT')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth2 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth1 -j ACCEPT')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth0 -j ACCEPT')
            self.net.get("fw").cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth1 -m state --state ESTABLISHED,RELATED -j ACCEPT')

        else:
            print("iptables not found on fw host")
            
        # Configure routing and Internet access
        self.net.get("dns").cmd("ip route add 10.0.1.0/24 via 10.0.0.22")
        self.net.get("dns").cmd("ip route add 100.0.0.0/24 via 10.0.0.22")
        self.net.get("h1").cmd("ip route add 10.0.1.0/24 via 10.0.0.22")
        self.net.get("h1").cmd("ip route add 100.0.0.0/24 via 10.0.0.22")
        #s1.cmd('ifconfig s1 10.0.0.254/24')
    
        self.net.get("ws1").cmd("ip route add 10.0.1.0/24 via 100.0.0.1")
        self.net.get("ws1").cmd("ip route add 10.0.0.0/24 via 100.0.0.1")
        s3.cmd('ifconfig s3 100.0.0.254/24')
        os.system('sudo ip route add 10.0.0.0/24 via 100.0.0.1')
        
        h1.cmd('echo "nameserver 8.8.8.8" > /tmp/resolv.conf')
        dns.cmd('echo "nameserver 8.8.8.8" > /tmp/resolv.conf')
    
        h1.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
        dns.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
    
        dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
        dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')

        dns.cmd('service bind9 restart')    
        
        h1.cmd('echo "nameserver 10.0.0.21" > /etc/resolv.conf')
        dns.cmd('echo "nameserver 10.0.0.21" > /etc/resolv.conf')
    
        #configure snort
        fw.cmd('snort -T -c /etc/snort/snort.conf -i fw-eth2')
        fw.cmd('snort -D -i fw-eth2 -c /etc/snort/snort.conf -A fast')
        fw.cmd('snort -D -i fw-eth0 -c /etc/snort/snorteth0.conf -A fast')
        fw.cmd('snort -D -i fw-eth1 -c /etc/snort/snorteth1.conf -A fast')
    
        #print("\nTesting bandwidth between h1 and ws1...")
        #h1, ws1 = self.net.get('h1', 'ws1')
        #result = ws1.cmd('iperf -s &')  
        #print(h1.cmd('iperf -c', ws1.IP()))  
    
        #h1.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
        #dns.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
        #dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
        

if __name__ == '__main__':
    setLogLevel('info')
    os.system('sudo sysctl -w net.ipv4.ip_forward=1')
    os.system('sudo iptables -t nat -A POSTROUTING -o enp0s3 -j MASQUERADE')
    os.system('ip route')
    os.system('sudo iptables -A FORWARD -i s1 -j ACCEPT')
    os.system('sudo iptables -A FORWARD -o s1 -j ACCEPT')
    os.system('sudo iptables -A FORWARD -i s3 -j ACCEPT')
    os.system('sudo iptables -A FORWARD -o s3 -j ACCEPT')
    
    topo = Mytopo()
    #print("Testing connectivity in my network")
    #topo.net.pingAll()
    CLI(topo.net)
    topo.net.stop()
    os.system('sudo echo "nameserver 8.8.8.8" > /etc/resolv.conf')
