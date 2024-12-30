from containernet.net import Containernet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from containernet.cli import CLI
from containernet.link import TCLink
from mininet.log import info, setLogLevel
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os
import time
import random
#from gym_idsgame.envs.snort_reader import snort_alert_reader
#from gym_idsgame.envs.variables import variable
class Mytopo:
    def __init__(self):
        self.net = Containernet(controller=None, switch=OVSKernelSwitch)
        #self.net = Containernet(controller=Controller, switch=OVSKernelSwitch)
        
        # Add hosts
        h1 = self.net.addDocker('h1', ip='10.0.0.20/24', defaultRoute='via 10.0.0.22', dimage= "mcnamee/huntkit:attack", volumes=["/home/videoserver/Desktop/DA246X-master-project/topology/attacks:/home/attacks"])
        dns = self.net.addDocker('dns', ip='10.0.0.21/24', dimage="containernet:dns", defaultRoute='via 10.0.0.254')
        corpdns = self.net.addDocker('corpdns', ip='10.0.0.23/24', dimage="containernet:corpdns", defaultRoute='via 10.0.0.22')
        Mahost = self.net.addDocker('Mahost', ip='10.0.0.50/24', dimage="containernet:intranetserver")
        h3 = self.net.addDocker('h3', ip='10.0.1.2/24', dimage="containernet:intranetserver", defaultRoute='via 10.0.1.1')
        #h4 = self.net.addDocker('h4', ip='10.0.1.3/24', dimage="containernet:intranetserver", defaultRoute='via 10.0.1.1')
        #ws1 = self.net.addDocker('ws1', ip='100.0.0.40/24', dimage="containernet:videoserver", ports=[8001,8081,8082],devices=["/dev/video0","/dev/snd"], defaultRoute='via 100.0.0.254')
        ws1 = self.net.addDocker('ws1', ip='100.0.0.40/24', dimage="containernet:videoserver", ports=[8001,8081,8082], defaultRoute='via 100.0.0.1')
        #fw = self.net.addHost('fw', ip='10.0.0.22/24')
        fw = self.net.addDocker('fw', ip='10.0.0.22/24',dimage="containernet:firewall")
        IDS = self.net.addDocker('IDS', ip='10.0.0.30/24',dimage="containernet:firewall", volumes=["/etc/snort:/etc/snort", "/var/log/snort:/var/log/snort", "/usr/local/lib/snort_dynamicrules:/usr/local/lib/snort_dynamicrules"])
        
        # Add switch
        s1 = self.net.addSwitch('s1', dpid="1")
        s2 = self.net.addSwitch('s2', dpid="2")
        s3 = self.net.addSwitch('s3', dpid="3")
    
        # Add links
        self.net.addLink(fw, s1)  # Interface for Pbz
        self.net.addLink(fw, s3)  # Interface for DMZ
        self.net.addLink(fw, s2)  # Interface for prz network
        self.net.addLink(h1, s1)
        self.net.addLink(dns, s1)
        self.net.addLink(h3, s2)
        #self.net.addLink(h4, s2)
        self.net.addLink(ws1, s3)
        self.net.addLink(IDS, s1)
        self.net.addLink(IDS, s3)
        self.net.addLink(IDS, s2)
        self.net.addLink(Mahost, s1)
        self.net.addLink(Mahost, s3)
        self.net.addLink(Mahost, s2)
        self.net.addLink(corpdns, s1)
    
        # Add controller
        self.net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633 )
    
        self.net.start()
    
        IDS.cmd("ifconfig IDS-eth0 10.0.0.30 netmask 255.255.255.0")
        IDS.cmd("ifconfig IDS-eth1 100.0.0.30 netmask 255.255.255.0")
        IDS.cmd("ifconfig IDS-eth2 10.0.1.4 netmask 255.255.255.0")
        Mahost.cmd("ifconfig Mahost-eth0 10.0.0.50 netmask 255.255.255.0")
        Mahost.cmd("ifconfig Mahost-eth1 100.0.0.50 netmask 255.255.255.0")
        Mahost.cmd("ifconfig Mahost-eth2 10.0.1.5 netmask 255.255.255.0")
        fw.cmd("ifconfig fw-eth0 10.0.0.22 netmask 255.255.255.0")
        fw.cmd("ifconfig fw-eth1 100.0.0.1 netmask 255.255.255.0")
        fw.cmd("ifconfig fw-eth2 10.0.1.1 netmask 255.255.255.0")
        fw.cmd('sysctl -w net.ipv4.ip_forward=1')
        fw.cmd('ip route add default via 100.0.0.254')
                
        # Configure routing and Internet access
        self.net.get("dns").cmd("ip route add 10.0.1.0/24 via 10.0.0.22")
        self.net.get("dns").cmd("ip route add 100.0.0.0/24 via 10.0.0.22")
        self.net.get("h1").cmd("ip route add 10.0.1.0/24 via 10.0.0.22")
        self.net.get("h1").cmd("ip route add 100.0.0.0/24 via 10.0.0.22")
        #s1.cmd('ifconfig s1 10.0.0.254/24')
    
        self.net.get("ws1").cmd("ip route add 10.0.1.0/24 via 100.0.0.1")
        self.net.get("ws1").cmd("ip route add 10.0.0.0/24 via 100.0.0.1")
        s3.cmd('ifconfig s3 100.0.0.254/24')
        #os.system('sudo ip route add 10.0.0.0/24 via 100.0.0.1')
        
        #h1.cmd('echo "nameserver 8.8.8.8" > /tmp/resolv.conf')
        #dns.cmd('echo "nameserver 8.8.8.8" > /tmp/resolv.conf')
    
        #h1.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
        #dns.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
    
        #dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
        #dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
          
        h1.cmd('echo "nameserver 10.0.0.21" > /etc/resolv.conf')
        dns.cmd('echo "nameserver 10.0.0.21" > /etc/resolv.conf')
        ws1.cmd('echo "nameserver 10.0.0.23" > /etc/resolv.conf')
                
        s1.cmd("sudo ovs-vsctl -- set Bridge s1 mirrors=@m \
-- --id=@s1-eth1 get Port s1-eth1 \
-- --id=@s1-eth5 get Port s1-eth5 \
-- --id=@s1-eth4 get Port s1-eth4 \
-- --id=@m create Mirror name=s1-mirror select-dst-port=@s1-eth1,@s1-eth5 select-src-port=@s1-eth1,@s1-eth5 output-port=@s1-eth4")
        s3.cmd("sudo ovs-vsctl -- set Bridge s3 mirrors=@m \
-- --id=@s3-eth1 get Port s3-eth1 \
-- --id=@s3-eth3 get Port s3-eth3 \
-- --id=@m create Mirror name=s3-mirror select-dst-port=@s3-eth1 select-src-port=@s3-eth1 output-port=@s3-eth3")
        s2.cmd("sudo ovs-vsctl -- set Bridge s2 mirrors=@m \
-- --id=@s2-eth1 get Port s2-eth1 \
-- --id=@s2-eth4 get Port s2-eth4 \
-- --id=@m create Mirror name=s2-mirror select-dst-port=@s2-eth1 select-src-port=@s2-eth1 output-port=@s2-eth4")
        #print("\nTesting bandwidth between h1 and ws1...")
        #h1, ws1 = self.net.get('h1', 'ws1')
        #result = ws1.cmd('iperf -s &')  
        #print(h1.cmd('iperf -c', ws1.IP()))  
    
        #h1.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
        #dns.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
        #dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')
    
    def restartservice(self):
        print("Info: Restarting services")
        new_password = "password123"
        nodes = [
            (self.net.get('ws1'), [f"echo -e '{new_password}\\n{new_password}' | passwd user", 
                'service ssh restart',
                'python3 -m http.server 80 &',
                'python3 -m http.server 8001 &'
            ]),
            (self.net.get('h3'), [f"echo -e '{new_password}\\n{new_password}' | passwd user",
                'service ssh restart',
                'python3 -m http.server 80 &'
            ]),
            (self.net.get('fw'), [f"echo -e '{new_password}\\n{new_password}' | passwd user", 'service ssh restart']),
            (self.net.get('Mahost'), [f"echo -e '{new_password}\\n{new_password}' | passwd user", 'service ssh restart']),
            (self.net.get('dns'), ['service bind9 restart']),
            (self.net.get('corpdns'), ['service bind9 restart'])
        ]
        def execute_commands(node):
            node_name = node[0].name  # Get the node name for logging
            try:
                for command in node[1]:
                    #print(f"Info: Executing '{command}' on {node_name}")
                    node[0].cmd(command)
                print(f"Info: All commands executed on {node_name}")
            except Exception as e:
                print(f"Error: Failed to execute commands on {node_name}: {e}")
        
        with ThreadPoolExecutor() as executor:
            executor.map(execute_commands, nodes)
        print("Info: All services restarted!")
        
        
    def start_webcamservice(self):
        ws1 = self.net.get('ws1')
        ws1.cmd('cd /home/linux-webcam-server/ && ./start_http_server &')
        
    def mockscan(self, node_id:int):
        h1 = self.net.get('h1')
        if node_id == 0:
            ws1 = self.net.get('ws1')
            target_ip = ws1.IP()
        if node_id == 1:
            h3 = self.net.get('h3')
            target_ip = h3.IP()
        if node_id == 2:
            fw = self.net.get('fw')
            target_ip = fw.IP()
        if node_id == 4:
            dns = self.net.get('dns')
            target_ip = dns.IP()
        if node_id == 5:
            corpdns = self.net.get('corpdns')
            target_ip = corpdns.IP()
        if node_id == 3:
            Mahost = self.net.get('Mahost')
            target_ip = Mahost.IP()
        print(f"Info: Attacker is taking the action for nmap scanning on target {target_ip}")
        ping_result = h1.cmd(f'ping -c 3 {target_ip} -w 1')
        #print(ping_result)
        if "100% packet loss" in ping_result:
            h1.cmd(f"timeout 0.1 hping3 -S -p 1-1000 --flood {target_ip}")
            print(f"Info: reconnaissance completed on {target_ip}")
            return False, False
        else:
            h1.cmd(f"timeout 0.1 hping3 -S -p 1-1000 --flood {target_ip}")
            print(f"Info: reconnaissance completed on {target_ip}")
            if target_ip == "100.0.0.40":
                return True, True
            else:
                return True, False
            
        
    def reconnaissance(self, node_id: int):
        h1 = self.net.get('h1')
        if node_id == 0:
            ws1 = self.net.get('ws1')
            target_ip = ws1.IP()
        if node_id == 1:
            h3 = self.net.get('h3')
            target_ip = h3.IP()
        if node_id == 2:
            fw = self.net.get('fw')
            target_ip = fw.IP()
        if node_id == 4:
            dns = self.net.get('dns')
            target_ip = dns.IP()
        if node_id == 5:
            corpdns = self.net.get('corpdns')
            target_ip = corpdns.IP()
        if node_id == 3:
            Mahost = self.net.get('Mahost')
            target_ip = Mahost.IP()
        print(f"Info: Attacker is taking the action for nmap scanning on target {target_ip}")
        h1.cmd(f"/home/attacks/t1595_scan.sh {target_ip}")
        output_file_path = f"/home/attacks/t1595_scan_results_{target_ip}.txt"
        result = h1.cmd(f"cat {output_file_path}")
        if not result.strip():
            print(f"Error: No content found in {output_file_path}")
            return False, False
        print("output is")
        print(result)
        print(f"Info: reconnaissance completed on {target_ip}")
        if "Skipping host" in result and "host timeout" in result:
            #print(f"Info: Nmap scan on {target_ip} timed out.")
            return False, False
        if "ssh" in result:
            if "8001" in result:
                #print("output is")
                #print(result)
                #print("Info: scan completed. Open ports/services detected.")
                return True, True
            else:
                return True, False
        
    def sshbruteforce(self, node_id: int):
        h1 = self.net.get('h1')
        if node_id == 0:
            target = self.net.get('ws1')
        if node_id == 1:
            target = self.net.get('h3')
        if node_id == 2:
            target = self.net.get('fw')
        if node_id == 4:
            target = self.net.get('dns')
        if node_id == 5:
            target = self.net.get('corpdns')
        if node_id == 3:
            target = self.net.get('Mahost')
        target_ip = target.IP()
        print(f"Info: Attacker is taking the action for brute force attack on target {target_ip}")
        #test1 = h1.cmd(f"ping {target_ip} -c 3")
        #print(test1)
        #test2 = h1.cmd(f"nc -zv {target_ip} 22")
        #print(test2)
        status = target.cmd('service ssh status')
        if "sshd is running" in status:
            print(f"ssh service is running on {target_ip}")
        #print(status)
        result = h1.cmd(f"/home/attacks/t1190ssh.sh {target_ip}")
        #print("ssh bruteforce result is", result)
        if "[+] Exploit successful" in result:
            print(f"Info: brute force attack succeed on {target_ip}!")
            return True
        else:
            print("Info: brute force attack failed!")
            return False
            
    def root(self, node_id: int):
        h1 = self.net.get('h1')
        if node_id == 0:
            ws1 = self.net.get('ws1')
            target_ip = ws1.IP()
        if node_id == 1:
            h3 = self.net.get('h3')
            target_ip = h3.IP()
        if node_id == 2:
            fw = self.net.get('fw')
            target_ip = fw.IP()
        if node_id == 4:
            dns = self.net.get('dns')
            target_ip = dns.IP()
        if node_id == 5:
            corpdns = self.net.get('corpdns')
            target_ip = corpdns.IP()
        if node_id == 3:
            Mahost = self.net.get('Mahost')
            target_ip = Mahost.IP()
        print(f"Info: Attacker is taking the action for privilege escalation on target {target_ip}")
        #test1 = h1.cmd(f"ping {target_ip} -c 3")
        #print(test1)
        #test2 = h1.cmd(f"nc -zv {target_ip} 22")
        #print(test2)
        result = h1.cmd(f"/home/attacks/t1078_root.sh {target_ip}")
        #print("Privilege escalation script result:", result)       
        if "[+] Privilege escalation successful" in result:
            print(f"Info: Privilege escalation succeed {target_ip}!")
            return True
        else:
            print("Info: Privilege escalation failed!")
            return False
            
    def persistence(self, node_id: int):
        h1 = self.net.get('h1')
        if node_id == 0:
            ws1 = self.net.get('ws1')
            target_ip = ws1.IP()
        if node_id == 1:
            h3 = self.net.get('h3')
            target_ip = h3.IP()
        if node_id == 2:
            fw = self.net.get('fw')
            target_ip = fw.IP()
        if node_id == 4:
            dns = self.net.get('dns')
            target_ip = dns.IP()
        if node_id == 5:
            corpdns = self.net.get('corpdns')
            target_ip = corpdns.IP()
        if node_id == 3:
            Mahost = self.net.get('Mahost')
            target_ip = Mahost.IP()
        print(f"Info: Attacker is taking the action for persistence attacks on target {target_ip}")
        #test1 = h1.cmd(f"ping {target_ip} -c 3")
        #print(test1)
        #test2 = h1.cmd(f"nc -zv {target_ip} 22")
        #print(test2)
        result = h1.cmd(f"/home/attacks/t1098_persistence.sh {target_ip}")
        #print("persistence result:", result)  
        if "Done. Verify user privileges on the target server" in result:
            print(f"Info: Persistence attacks succeed on {target_ip}!")
            return True
        else:
            print("Info: Persistence attacks failed!")
            return False
            
    def DDoS(self, node_id: int):
        h1 = self.net.get('h1')
        if node_id == 0:
            ws1 = self.net.get('ws1')
            target_ip = ws1.IP()
            target_port = 8001
        if node_id == 1:
            h3 = self.net.get('h3')
            target_ip = h3.IP()
            target_port = 80
        if node_id == 2:
            fw = self.net.get('fw')
            target_ip = fw.IP()
            print(f"Info: Attacker is taking the action for DDoS attacks on target {target_ip}")
            print(f"Info: DDoS attacks are not available!")
            return False
        if node_id == 4:
            dns = self.net.get('dns')
            target_ip = dns.IP()
            target_port = 53
        if node_id == 5:
            corpdns = self.net.get('corpdns')
            target_ip = corpdns.IP()
            target_port = 53
        if node_id == 3:
            Mahost = self.net.get('Mahost')
            target_ip = Mahost.IP()
            print(f"Info: Attacker is taking the action for DDoS attacks on target {target_ip}")
            print(f"Info: DDoS attacks are not available!")
            return False
        #result1 = h1.cmd(f"ping -c 4 {target_ip}")
        #print("Ping result:", result1)
        print(f"Info: Attacker is taking the action for DDoS attacks on target {target_ip}")
        result = h1.cmd(f"/home/attacks/t1498_impact.sh {target_ip} {target_port}")
        #print("DDoS result:", result) 
        if "Attacks completed." in result:
            print(f"Info: DDoS attacks succeed on {target_ip}!")
            return True
        else:
            print(f"Info: DDoS attacks failed!")
            return False
            
            
    def attack_modidyfirewall(self, node_id:int):
        print("Info: Attacker is taking the action for removing all firewall restrictions between h1 subnet and ws1")
        fw = self.net.get('fw')
        Mahost = self.net.get('Mahost')
        if node_id == 2:
            target_ip = fw.IP()
        elif node_id == 3:
            target_ip = Mahost.IP()
        h1 = self.net.get('h1')
        result = h1.cmd(f"/home/attacks/identify.sh {target_ip}")  
        #result = h1.cmd(f"ping -c 3 {target_ip}") 
        #print(result)   
        if "Root access has been confirmed" in result:
            if target_ip == Mahost.IP():
                Mahost.cmd("nc -zv 100.0.0.1 22")
            if fw.cmd('which iptables'):
                # Flush specific rules that restrict traffic between h1 subnet and ws1
                fw.cmd('iptables -F')
                fw.cmd('iptables -X')
                fw.cmd('iptables -P FORWARD ACCEPT')
                print("Info: All traffic restrictions have been removed")
                return True
            else:
                print("iptables not found on fw host")
                return False
        else:
            print("Info: Attacker has lost the access to the fw node")
            return False

        
    
    def default_firewall(self):
        """
         configure and start default firewall
        """
        ws1 = self.net.get('ws1')
        for intf in ws1.intfList():
            ws1.cmd(f'ip link set {intf} up')
        fw = self.net.get('fw')
        # Check if iptables is available and add firewall rules
        print("Info: Defender is starting regular firewall")
        if fw.cmd('which iptables'):
            # Flush existing rules
            fw.cmd('iptables -F')
            fw.cmd('iptables -t nat -F')
            fw.cmd('iptables -t mangle -F')
            fw.cmd('iptables -X')

            # Default policies to drop all traffic
            fw.cmd('iptables -P FORWARD ACCEPT')

            # Allow all traffic on the loopback interface
            #fw.cmd('iptables -A INPUT -i lo -j ACCEPT')
            #fw.cmd('iptables -A OUTPUT -o lo -j ACCEPT')

            # Allow traffic from internal to DMZ port 80
            fw.cmd('iptables -A FORWARD -s 10.0.0.0/24 -d 100.0.0.0/24 -p tcp --dport 80 -j ACCEPT')
            fw.cmd('iptables -A FORWARD -d 10.0.0.0/24 -s 100.0.0.0/24 -p tcp --sport 80 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            # Allow all traffic from DMZ to h1 subnet
            fw.cmd('iptables -A FORWARD -s 100.0.0.0/24 -d 10.0.0.0/24 -j ACCEPT')
            fw.cmd('iptables -A FORWARD -s 10.0.0.0/24 -d 100.0.0.0/24 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            # Block all other traffic from h1 subnet to DMZ
            fw.cmd('iptables -A FORWARD -s 10.0.0.0/24 -d 100.0.0.0/24 -j REJECT')
            # accept all the traffic from Prz to pbz
            fw.cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth0 -j ACCEPT')
            fw.cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth2 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            # block traffic from pbz to prz
            fw.cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth2 -j REJECT')
            # from DMZ to pbz
            #fw.cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth0 -j ACCEPT')
            #fw.cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth1 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            #from pbz to DMZ
            #fw.cmd('iptables -A FORWARD -i fw-eth0 -o fw-eth1 -j ACCEPT')
            #fw.cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            #from prz to dmz
            fw.cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth1 -j ACCEPT')
            fw.cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth2 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            #from dmz to prz
            fw.cmd('iptables -A FORWARD -i fw-eth1 -o fw-eth2 -j ACCEPT')
            fw.cmd('iptables -A FORWARD -i fw-eth2 -o fw-eth1 -m state --state ESTABLISHED,RELATED -j ACCEPT')
            print("Info: Default firewall has been configured!")

        else:
            print("iptables not found on fw host")

    def IDS(self):
        #start snort
        print("Info: Defender is starting the IDS monitor---")
        IDS = self.net.get('IDS')
        commands = [
            'snort -D -i IDS-eth0 -c /etc/snort/snort.conf -A fast',
            'snort -D -i IDS-eth2 -c /etc/snort/snorteth0.conf -A fast',
            'snort -D -i IDS-eth1 -c /etc/snort/snorteth1.conf -A fast'
        ]
        for command in commands:
            IDS.cmd(command)
        result = IDS.cmd("ps aux | grep snort")
        #print(result)
        print("Info: IDS monitor start completed")
    
    def pause_services(self, node_id:int):
        # stop ssh sevices
        # D3-PS
        if node_id == 0:
            defender = self.net.get('ws1')
        if node_id == 1:
            defender = self.net.get('h3')
        if node_id == 2:
            defender = self.net.get('fw')
        if node_id == 3:
            defender = self.net.get('Mahost')
        if node_id == 4:
            defender = self.net.get('dns')
        if node_id == 5:
            defender = self.net.get('corpdns')
        target_ip = defender.IP()
        for intf in defender.intfList():
            defender.cmd(f'ip link set {intf} up')
        #command = "netstat -tulnp | awk '/:8001|:8081|:8082/ {print $7}' | cut -d'/' -f1 | xargs -r kill"
        #result = defender.cmd(command)
        #if result:
            #print("sevices on port 8001,8081 and 8082 have been stopped。")
        #else:
            #print("services not found")

        # stop ssh sevice
        print(f"Info: Defender is taking the action for pausing ssh service on {defender.IP()}")
        ssh_result = defender.cmd('service ssh stop')
        if "Stopping" in ssh_result:
            print(f"Info: SSH service on {defender.IP()} has been stopped.")
            return True
        else:
            print(f"Info: Failed to stop SSH service on {defender.IP()} or service not found.")
            return False



    def block_traffic(self, node_id:int):
        """
         configure new firewall rules for blocking attacker traffic
         D3-ITF
        """
        if node_id == 0:
            defender = self.net.get('ws1')
            target_ip = defender.IP()
        if node_id == 1:
            defender = self.net.get('h3')
            target_ip = defender.IP()
        if node_id == 2:
            defender = self.net.get('fw')
            target_ip = defender.IP()
        if node_id == 3:
            defender = self.net.get('Mahost')
            target_ip = '100.0.0.40'
        fw = self.net.get('fw')
        h1 = self.net.get('h1')
        #for intf in defender.intfList():
            #defender.cmd(f'ip link set {intf} up')
        #ws1 = self.net.get('ws1')
        ping_result = h1.cmd(f'ping -c 1 {target_ip} -w 1')
        #print(ping_result)

        if "100% packet loss" in ping_result:
            print(f"Info: Defender considers taking the action for blocking untrusted traffic. But target {target_ip} is not reachable. No firewall rules needed.")
            return True
        else:
            print(f"Info: Defender is taking the action of configuring new firewall rules for blocking traffic when target {target_ip} is reachable.")
            if node_id == 2:
                # Block all incoming traffic from h1 to fw
                fw.cmd('iptables -A INPUT -s 10.0.0.20 -j REJECT')
                # Block all outgoing traffic from fw to h1
                fw.cmd('iptables -A OUTPUT -d 10.0.0.20 -j REJECT')
                print("Info: Verifying iptables rules:")
                result1 = fw.cmd('iptables -L INPUT -n -v')
                result2 = fw.cmd('iptables -L OUTPUT -n -v')
                print(result1)
                print(result2)
                if "REJECT" in result1 and "REJECT" in result2:
                    print("Info: Blocked successfully")
                    return True
                else:
                    print("Info: Block failed")        
                    return False
            else:
                command_1 = f"iptables -I FORWARD -s {h1.IP()} -d {target_ip} -j REJECT"
                command_2 = f"iptables -I FORWARD -s {target_ip} -d {h1.IP()} -j REJECT"

                result_1 = fw.cmd(command_1)
                result_2 = fw.cmd(command_2)

                print("Info: Verifying iptables rules:")
                result3 = fw.cmd(f"iptables -L FORWARD -n -v | grep {h1.IP()} | grep {target_ip}")
                print(result3)

                if "REJECT" in result3:
                #result4 = h1.cmd(f'ping -c 4 {target_ip}')
                #print(result4)
                    print("Info: Blocked successfully")
                    return True
                else:
                    print("Info: Block failed")
                    return False
                    

                    
    def remove_rules(self):
        fw = self.net.get('fw')
        local_rules_path = "/etc/snort/rules/local.rules"
        target_sid = 1000003

        try:
            # Read the existing rules from the file
            existing_rules = fw.cmd(f"cat {local_rules_path}")
        
            if not existing_rules.strip():
                print(f"Info: No rules found in {local_rules_path}. Nothing to delete.")
                return True

            # Filter rules: keep only those with SID <= target_sid
            filtered_rules = []
            for rule in existing_rules.splitlines():
                if "sid:" in rule:
                    sid = int(rule.split("sid:")[1].split(";")[0])
                    if sid <= target_sid:
                        filtered_rules.append(rule)
                else:
                    filtered_rules.append(rule)  # Include comments or non-SID lines

        # Write the filtered rules back to the file
            fw.cmd(f"echo '' > {local_rules_path}")  # Clear the file first
            for rule in filtered_rules:
                escaped_rule = rule.replace('"', '\\"')  # Escape double quotes
                fw.cmd(f"echo \"{escaped_rule}\" >> {local_rules_path}")

            print(f"Info: All rules with SID greater than {target_sid} have been removed.")
            return True
        except Exception as e:
            print(f"Error: Failed to remove rules after SID {target_sid}. {str(e)}")
            return False
            
    def addsnortrules(self, node_id:int):
        print("Info: Defender is taking the action for adding new snort rules")
        fw = self.net.get('fw')
        local_rules_path = "/etc/snort/rules/local.rules"
        if node_id == 0:
            target_subnet = "100.0.0.0/24"
        if node_id == 1:
            target_subnet = "10.0.1.0/24"
        if node_id == 2:
            target_subnet = "10.0.0.0/24"
        existing_rules = fw.cmd(f"grep '{target_subnet}.*22' {local_rules_path}")
        if existing_rules.strip():
            print(f"Info: Rules for {target_subnet} already exist in {local_rules_path}. No changes made.")
            return False
        else:
            last_sid_output = fw.cmd(f"grep -oP 'sid:\\d+' {local_rules_path} | tail -1")
            if last_sid_output.strip():
                last_sid = int(last_sid_output.split(":")[1])
                print(f"Info: Last existing SID found: {last_sid}")
            else:
                print("Info: No existing SID found. Starting from default SID: 1000000")
                return False
            sid = last_sid+1
            rule1 = f'alert tcp any any -> {target_subnet} 22 (msg:"SSH incoming"; flow:stateless; flags:S+; classtype:suspicious-login; priority:3; sid:{sid}; rev:1;)'
            sid = sid +1
            rule2 = f'alert tcp any any -> {target_subnet} 22 (msg:"Potential SSH Brute Force Attack"; flow:to_server; flags:S; threshold:type threshold, track by_src, count 3, seconds 60; classtype:attempted-dos; priority:2; sid:{sid}; rev:1; resp:rst_all;)'
            sid = sid +1
            rule3 = f'alert tcp any any -> {target_subnet} any (msg:"Nmap SYN Scan Detected"; flags:S; threshold:type both, track by_src, count 10, seconds 10; classtype:attempted-recon; priority:4; sid:{sid}; rev:1;)'
            sid = sid +1
            rule4 = f'alert tcp any any -> {target_subnet} [22,80,8001,8081,8082] (msg:"DDoS SYN Flood Attack Detected on Ports 22, 80, 8001, 8081, 8082"; flags:S; threshold:type threshold, track by_dst, count 1000, seconds 1; classtype:attempted-dos; priority:1; sid:{sid}; rev:1;)'
            try:
                # Kill any running Snort processes
                #result = fw.cmd("ps aux | grep snort")
                #print(result)
                fw.cmd("pid=$(ps aux | grep snort | grep -v grep | awk '{print $2}'); kill -9 $pid")  
                escaped_rule1 = rule1.replace('"', '\\"')
                escaped_rule2 = rule2.replace('"', '\\"')
                escaped_rule3 = rule3.replace('"', '\\"')
                escaped_rule4 = rule4.replace('"', '\\"')
                fw.cmd(f"echo \"{escaped_rule1}\" >> {local_rules_path}")
                fw.cmd(f"echo \"{escaped_rule2}\" >> {local_rules_path}")
                fw.cmd(f"echo \"{escaped_rule3}\" >> {local_rules_path}")
                fw.cmd(f"echo \"{escaped_rule4}\" >> {local_rules_path}")
                print("Info: Adding new snort rules succeeded!")
                print("Info: Restarting Snort service...")
                #result1 = fw.cmd('ps aux | grep snort')
                #print(result1)
       
                # Restart Snort with default configuration
                fw.cmd('snort -D -i fw-eth0 -c /etc/snort/snort.conf -A fast')
                fw.cmd('snort -D -i fw-eth2 -c /etc/snort/snorteth0.conf -A fast')
                fw.cmd('snort -D -i fw-eth1 -c /etc/snort/snorteth1.conf -A fast')
                print("Info: Snort restarted successfully.")
                #result2 = fw.cmd("ps aux | grep snort")
                #print(result2)
                return True
            except Exception as e:
                print(f"Error: Failed to restart Snort. {str(e)}")
                return False
                
           
    def restart_alllinks(self):
        print("Info: Restarting all network interfaces---")

        host_names = ['Mahost', 'h3']

        for host_name in host_names:
            host = self.net.get(host_name)
            host.cmd('iptables -F')
            host.cmd('iptables -P INPUT ACCEPT')
            host.cmd('iptables -P OUTPUT ACCEPT')
            host.cmd('iptables -P FORWARD ACCEPT')
            print(f"Info: {host_name} has been unblocked and is now active.")
        print("Info: All network interfaces have been restarted") 
        
    def restartssh(self):
        host_names = ['Mahost', 'h3', 'fw', 'ws1']
        new_password = "password123"
        for host_name in host_names:
            host = self.net.get(host_name)
            host.cmd(f"echo -e '{new_password}\\n{new_password}' | passwd user")
            host.cmd('service ssh restart')
            status = host.cmd('service ssh status')
            if "sshd is running" in status:
                print(f"ssh service is running on {host_name}")
            
    
    def isolate_node(self, node_id:int):
        #isolate the compromised node
        #D3-NI
        if node_id == 0:
            defender = self.net.get('ws1')
            target_ip = defender.IP()
        if node_id == 1:
            defender = self.net.get('h3')
            target_ip = defender.IP()
        if node_id == 2:
            defender = self.net.get('fw')
            target_ip = defender.IP()
        if node_id == 3:
            defender = self.net.get('Mahost')
            target_ip = defender.IP()
        print(f"Info:defender is taking the action for isolating the compromised node {target_ip}")
        if node_id == 0 or node_id == 2:
            print(f"Info:The compromised node {target_ip} has been isolated")
            return True
        else:
            defender.cmd('iptables -F')
            defender.cmd('iptables -P INPUT DROP')
            defender.cmd('iptables -P OUTPUT DROP')
            defender.cmd('iptables -P FORWARD DROP')
            print(f"Info:The compromised node {target_ip} has been isolated")
            return True
        #for intf in defender.intfList():
            #defender.cmd(f'ip link set {intf} down')
            #return True
            #result = h1.cmd(f"ping -c 4 {target_ip}")
            #print(result)
    

    def reset_services(self, node_id:int):
        """
        reset passwords and ssh credentials, restart ssh service
        D3-CRO
        """
        if node_id == 0:
            defender = self.net.get('ws1')
            target_ip = defender.IP()
        if node_id == 1:
            defender = self.net.get('h3')
            target_ip = defender.IP()
            defender.cmd('iptables -F')
            defender.cmd('iptables -P INPUT ACCEPT')
            defender.cmd('iptables -P OUTPUT ACCEPT')
            defender.cmd('iptables -P FORWARD ACCEPT')
        if node_id == 2:
            defender = self.net.get('fw')
            target_ip = defender.IP()
        if node_id == 3:
            defender = self.net.get('Mahost')
            target_ip = defender.IP()
            defender.cmd('iptables -F')
            defender.cmd('iptables -P INPUT ACCEPT')
            defender.cmd('iptables -P OUTPUT ACCEPT')
            defender.cmd('iptables -P FORWARD ACCEPT')
        #reset password
        print(f"Info: Defender is taking the action for resetting ssh service on {target_ip}")
        password_list = ["new_passwordkth123", "password123"]
        password_weights = [0.6, 0.4]
        new_password = random.choices(password_list, weights=password_weights, k=1)[0]
        print("Info: new password is", new_password)
        password_reset_command = f"echo -e '{new_password}\\n{new_password}' | passwd user"
        result = defender.cmd(password_reset_command)
        #print("Password reset result:", result)

        # reset ssh key
        print("Info: Resetting ssh keys")
        defender.cmd('rm -f /home/user/shared/id_rsa /home/user/shared/id_rsa.pub')
        reset_key_command = "sudo -u user ssh-keygen -t rsa -b 2048 -f /home/user/shared/id_rsa -N ''"
        result = defender.cmd(reset_key_command)
        #print("SSH key generation result:", result)
        defender.cmd("chmod 644 /home/user/shared/id_rsa")
        defender.cmd("cat /home/user/shared/id_rsa.pub > /home/user/shared/authorized_keys")
        defender.cmd("chmod 644 /home/user/shared/authorized_keys")
        defender.cmd("cat /home/user/shared/id_rsa.pub > /root/.ssh/authorized_keys")
        defender.cmd("chmod 600 /root/.ssh/authorized_keys")

        # restart ssh service
        ssh_restart_command = "service ssh restart"
        ssh_restart_result = defender.cmd(ssh_restart_command)
        #print(ssh_restart_result)
        print("Info: ssh service reset completed")
        return True

        #print("Verifying SSH key configuration...")
        #verify_ssh_key_command = "ls -l /home/user/shared/id_rsa /home/user/shared/id_rsa.pub /home/user/shared/authorized_keys"
        #ssh_key_verification = ws1.cmd(verify_ssh_key_command)
        #print("SSH key verification result:")
        #print(ssh_key_verification)
     
            

if __name__ == '__main__':
    setLogLevel('info')
    #os.system('sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1')
    #os.system('sudo iptables -t nat -A POSTROUTING -o enp0s3 -j MASQUERADE > /dev/null 2>&1')
    #os.system('ip route > /dev/null 2>&1')
    #os.system('sudo iptables -A FORWARD -i s1 -j ACCEPT > /dev/null 2>&1')
    #os.system('sudo iptables -A FORWARD -o s1 -j ACCEPT > /dev/null 2>&1')
    #os.system('sudo iptables -A FORWARD -i s3 -j ACCEPT > /dev/null 2>&1')
    #os.system('sudo iptables -A FORWARD -o s3 -j ACCEPT > /dev/null 2>&1')
    # start the containernet network
    topo = Mytopo()
    #topo.start_webcamservice()
    #topo.default_firewall()
    topo.IDS()
    topo.restartservice()
    #topo.addsnortrules(0)
    #topo.addsnortrules(0)
    #topo.addsnortrules(1)
    #topo.addsnortrules(2)
    #topo.remove_rules()
    
    ######testing for reconnaissance attack:
    #output = topo.reconnaissance(0)
    #print("reconnaisance is :")
    #print(output)
    #output = topo.reconnaissance(1)
    #print("reconnaisance is :")
    #print(output)
    #output = topo.reconnaissance(2)
    #print("reconnaisance is :")
    #print(output)
    #output4 = topo.DDoS(0)
    #print("Testing:DDoS result boolean flag is", output4)
    #output = topo.mockscan(0)
    #print("Testing: reconnaisance is :", output)
    #time.sleep(2)
    #output = topo.mockscan(1)
    #time.sleep(2)
    #print("Testing: reconnaisance is :", output)
    output = topo.mockscan(2)
    time.sleep(1)
    #print("Testing: reconnaisance is :", output)
    #print(output)
    ######
    #output1 = topo.sshbruteforce(0)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    #output1 = topo.sshbruteforce(1)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    #output1 = topo.sshbruteforce(2)
    #time.sleep(5)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    #output1 = topo.sshbruteforce(1)
    #time.sleep(2)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    output1 = topo.sshbruteforce(2)
    topo.reset_services(2)
    time.sleep(5)
    output1 = topo.sshbruteforce(2)
    topo.restartssh()
    output1 = topo.sshbruteforce(2)
    topo.pause_services(2)
    topo.reset_services(2)
    topo.reset_services(2)
    output1 = topo.sshbruteforce(2)
    topo.restartssh()
    output1 = topo.sshbruteforce(2)
    
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    #output1 = topo.sshbruteforce(3)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    
    #output2 = topo.root(2)
    #time.sleep(2)
    #print("Testing:ssh root result boolean flag is", output2)
    #output2 = topo.root(3)
    #print("Testing:ssh root result boolean flag is", output2)
    ######
    #output3 = topo.persistence(0)
    #print("Testing:persistence result boolean flag is", output3)
    #output3 = topo.persistence(1)
    #print("Testing:persistence result boolean flag is", output3)
    #output3 = topo.persistence(2)
    #print("Testing:persistence result boolean flag is", output3)
    #output3 = topo.persistence(2)
    #print("Testing:persistence result boolean flag is", output3)
    #topo.attack_modidyfirewall()
    ######
    #output = topo.reconnaissance(0)
    #print("reconnaisance is :")
    #print(output)
    #output4 = topo.DDoS(0)
    #print("Testing:DDoS result boolean flag is", output4)
    #output4 = topo.DDoS(1)
    #print("Testing:DDoS result boolean flag is", output4)
    #output4 = topo.DDoS(2)
    #print("Testing:DDoS result boolean flag is", output4)
    #output4 = topo.DDoS(3)
    #print("Testing:DDoS result boolean flag is", output4)
    #topo.pause_services(1)
    #topo.pause_services(2)
    #topo.block_traffic(0)
    #topo.block_traffic(1)
    #topo.block_traffic(2)
    #topo.block_traffic(0)
    #output1 = topo.sshbruteforce(2)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    #output2 = topo.root(2)
    #print("Testing:ssh root result boolean flag is", output2)
    #output3 = topo.persistence(2)
    #print("Testing:persistence result boolean flag is", output3)
    #topo.attack_modidyfirewall(3)
    #time.sleep(2)
    #output5 = topo.mockscan(0)
    #time.sleep(2)
    #print("Testing: reconnaisance is :", output5)
    #output1 = topo.sshbruteforce(0)
    #time.sleep(2)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    #output2 = topo.root(0)
    #time.sleep(2)
    #print("Testing:ssh root result boolean flag is", output2)
    #output3 = topo.persistence(0)
    #time.sleep(2)
    #print("Testing:persistence result boolean flag is", output3)
    #topo.pause_services(3)
    #topo.pause_services(2)
    #topo.block_traffic(3)
    #output1 = topo.sshbruteforce(2)
    #output1 = topo.sshbruteforce(3)
    #output1 = topo.sshbruteforce(0)
    #topo.isolate_node(3)
    #topo.isolate_node(1)
    #topo.block_traffic(0)
    #output1 = topo.sshbruteforce(1)
    #output1 = topo.sshbruteforce(2)
    #output1 = topo.sshbruteforce(3)
    output4 = topo.DDoS(0)
    print("Testing:DDoS result boolean flag is", output4)
    #while True:
    #topo.reset_services(3)
    #time.sleep(5)
    #output3 = topo.persistence(3)
    #print("Testing:persistence result boolean flag is", output3)
    #time.sleep(2)
    #output2 = topo.root(3)
    #print("Testing:ssh root result boolean flag is", output2)
    #time.sleep(2)
    #output3 = topo.persistence(3)
    #print("Testing:persistence result boolean flag is", output3)
    #topo.restart_alllinks()
    #time.sleep(2)
    #output1 = topo.sshbruteforce(3)
    #time.sleep(2)
    #output1 = topo.sshbruteforce(1)
    #output3 = topo.persistence(3)
    #print("Testing:persistence result boolean flag is", output3)
    #time.sleep(2)
    #output2 = topo.root(3)
    #print("Testing:ssh root result boolean flag is", output2)
    #time.sleep(2)
    #output3 = topo.persistence(3)
    #print("Testing:persistence result boolean flag is", output3)
    
    #output2 = topo.root()
    #print("Testing:ssh root result boolean flag is", output2)
    #output3 = topo.persistence()
    #print("Testing:persistence result boolean flag is", output3)
    ##testing isolation function:
    #topo.isolate_node(2)
    topo.restartssh()
    time.sleep(2)
    output4 = topo.DDoS(0)
    
    print("Testing:DDoS result boolean flag is", output4)
    CLI(topo.net)
    topo.net.stop()
    
    #os.system('sudo echo "nameserver 8.8.8.8" > /etc/resolv.conf')
