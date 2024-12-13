from containernet.net import Containernet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from containernet.cli import CLI
from containernet.link import TCLink
from mininet.log import info, setLogLevel
import subprocess
import os
import time
class Mytopo:
    def __init__(self):
        self.net = Containernet(controller=None, switch=OVSKernelSwitch)
        
        # Add hosts
        h1 = self.net.addDocker('h1', ip='10.0.0.20/24', defaultRoute='via 10.0.0.22', dimage= "mcnamee/huntkit:attack", volumes=["/home/videoserver/Desktop/DA246X-master-project/topology/attacks:/home/attacks"])
        dns = self.net.addDocker('dns', ip='10.0.0.21/24', dimage="containernet:dns", defaultRoute='via 10.0.0.254')
        h3 = self.net.addDocker('h3', ip='10.0.1.2/24', dimage="containernet:intranetserver", defaultRoute='via 10.0.1.1')
        h4 = self.net.addDocker('h4', ip='10.0.1.3/24', dimage="containernet:intranetserver", defaultRoute='via 10.0.1.1')
        ws1 = self.net.addDocker('ws1', ip='100.0.0.40/24', dimage="containernet:videoserver", ports=[8001,8081,8082],devices=["/dev/video0","/dev/snd"], defaultRoute='via 100.0.0.254')
        #fw = self.net.addHost('fw', ip='10.0.1.1/24')
        fw = self.net.addDocker('fw', ip='10.0.0.22/24',dimage="containernet:firewall", volumes=["/etc/snort:/etc/snort", "/var/log/snort:/var/log/snort", "/usr/local/lib/snort_dynamicrules:/usr/local/lib/snort_dynamicrules"])
        
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
        self.net.addLink(h4, s2)
        self.net.addLink(ws1, s3)
    
        # Add controller
        self.net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633 )
    
        self.net.start()
    
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
        
        ws1.cmd('service ssh restart')
        h3.cmd('service ssh restart')
        h4.cmd('service ssh restart')
        fw.cmd('service ssh restart')
        ws1.cmd("python3 -m http.server 80 &")
        h3.cmd("python3 -m http.server 80 &")

        #print("\nTesting bandwidth between h1 and ws1...")
        #h1, ws1 = self.net.get('h1', 'ws1')
        #result = ws1.cmd('iperf -s &')  
        #print(h1.cmd('iperf -c', ws1.IP()))  
    
        #h1.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
        #dns.cmd('ln -sf /tmp/resolv.conf /etc/resolv.conf')
        #dns.cmd('echo "nameserver 8.8.8.8" > /etc/resolv.conf')


    def handle_exit(self, sig, frame):
        print("\nProgram interrupted! Stopping all containers...")
        os.system('docker stop mn.dns mn.ws1 mn.h1')
        os.system('docker rm mn.dns mn.ws1 mn.h1')
        os.system('sudo mn -c')
        sys.exit(1)

    def register_exit_handler(self):
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        
        
    def start_webcamservice(self):
        ws1 = self.net.get('ws1')
        ws1.cmd('cd /home/linux-webcam-server/ && ./start_http_server &')
        
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
        if node_id == 3:
            dns = self.net.get('dns')
            target_ip = dns.IP()
        print(f"Info: Attacker is taking the action for nmap scanning on target {target_ip}")
        h1.cmd(f"/home/attacks/t1595_scan.sh {target_ip}")
        output_file_path = f"/home/attacks/t1595_scan_results_{target_ip}.txt"
        result = h1.cmd(f"cat {output_file_path}")
        if not result.strip():
            print(f"Error: No content found in {output_file_path}")
            return False
        print("output is")
        print(result)
        print("Info: scan completed")
        if "Skipping host" in result and "host timeout" in result:
            #print(f"Info: Nmap scan on {target_ip} timed out.")
            return False
        if "open" in result:
            #print("output is")
            #print(result)
            #print("Info: scan completed. Open ports/services detected.")
            return True
        
    def sshbruteforce(self, node_id: int):
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
        if node_id == 3:
            dns = self.net.get('dns')
            target_ip = dns.IP()
        print(f"Info: Attacker is taking the action for brute force attack on target {target_ip}")
        result = h1.cmd(f"/home/attacks/t1190ssh.sh {target_ip}")
        print("ssh bruteforce result is", result)
        if "[+] Exploit successful" in result:
            print("Info: brute force attack succeed!")
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
        if node_id == 3:
            dns = self.net.get('dns')
            target_ip = dns.IP()
        print(f"Info: Attacker is taking the action for privilege escalation on target {target_ip}")
        result = h1.cmd(f"/home/attacks/t1078_root.sh {target_ip}")
        print("Privilege escalation script result:", result)       
        if "[+] Privilege escalation successful" in result:
            print("Info: Privilege escalation succeed!")
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
        if node_id == 3:
            dns = self.net.get('dns')
            target_ip = dns.IP()
        print(f"Info: Attacker is taking the action for persistence attacks on target {target_ip}")
        result = h1.cmd(f"/home/attacks/t1098_persistence.sh {target_ip}")
        print("persistence result:", result)  
        if "Done. Verify user privileges on the target server" in result:
            print("Info: Persistence attacks succeed!")
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
            print(f"Info: Attacker is taking the action for DDoS attacks on target {target_ip}")
            print(f"Info: DDoS attacks are not available!")
            return False
        if node_id == 2:
            fw = self.net.get('fw')
            target_ip = fw.IP()
            print(f"Info: Attacker is taking the action for DDoS attacks on target {target_ip}")
            print(f"Info: DDoS attacks are not available!")
            return False
        if node_id == 3:
            dns = self.net.get('dns')
            target_ip = dns.IP()
            target_port = 53
        #result1 = h1.cmd(f"ping -c 4 {target_ip}")
        #print("Ping result:", result1)
        print(f"Info: Attacker is taking the action for DDoS attacks on target {target_ip}")
        result = h1.cmd(f"/home/attacks/t1498_impact.sh {target_ip} {target_port}")
        print("DDoS result:", result) 
        if "Attacks completed." in result:
            print(f"Info: DDoS attacks succeed!")
            return True
        else:
            print(f"Info: DDoS attacks failed!")
            return False
            
            
    def attack_modidyfirewall(self):
        print("Info: Attacker is taking the action for removing all firewall restrictions between h1 subnet and ws1")
        fw = self.net.get('fw')
        target_ip = fw.IP()
        h1 = self.net.get('h1')
        result = h1.cmd(f"/home/attacks/identify.sh {target_ip}")      
        if "Root access has been confirmed" in result:
            if fw.cmd('which iptables'):
                # Flush specific rules that restrict traffic between h1 subnet and ws1
                fw.cmd('iptables -D FORWARD -s 10.0.0.0/24 -d 100.0.0.0/24 -j REJECT')
                fw.cmd('iptables -D FORWARD -s 10.0.0.0/24 -d 100.0.0.0/24 -p tcp --dport 80 -j ACCEPT')
                fw.cmd('iptables -D FORWARD -d 10.0.0.0/24 -s 100.0.0.0/24 -p tcp --sport 80 -m state --state ESTABLISHED,RELATED -j ACCEPT')

                # Allow all traffic between h1 subnet and ws1
                fw.cmd('iptables -I FORWARD -s 10.0.0.0/24 -d 100.0.0.0/24 -j ACCEPT')
                fw.cmd('iptables -I FORWARD -d 10.0.0.0/24 -s 100.0.0.0/24 -j ACCEPT')

                print("Info: All traffic restrictions between h1 subnet and ws1 have been removed")
                return True
            else:
                print("iptables not found on fw host")
                return False
        else:
            print("Info: Attacker has lost the access to the fw node")
            return False

        
    
    def default_firewall_and_IDS(self):
        """
         configure and start default firewall and IDS
         D3-NTA
        """
        ws1 = self.net.get('ws1')
        for intf in ws1.intfList():
            ws1.cmd(f'ip link set {intf} up')
        fw = self.net.get('fw')
        # Check if iptables is available and add firewall rules
        print("Info: Defender is starting regular firewall and IDS monitor")
        if fw.cmd('which iptables'):
            # Flush existing rules
            fw.cmd('iptables -F')
            fw.cmd('iptables -t nat -F')
            fw.cmd('iptables -t mangle -F')
            fw.cmd('iptables -X')

            # Default policies to drop all traffic
            fw.cmd('iptables -P FORWARD DROP')

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

        else:
            print("iptables not found on fw host")
        #configure snort
        fw.cmd('snort -T -c /etc/snort/snort.conf -i fw-eth0')
        fw.cmd('snort -D -i fw-eth0 -c /etc/snort/snort.conf -A fast')
        fw.cmd('snort -D -i fw-eth2 -c /etc/snort/snorteth0.conf -A fast')
        fw.cmd('snort -D -i fw-eth1 -c /etc/snort/snorteth1.conf -A fast')
        print("Info: start completed")
          
    def pause_services(self, node_id:int):
        # stop sevices
        # D3-PS
        if node_id == 0:
            defender = self.net.get('ws1')
            target_ip = defender.IP()
        if node_id == 1:
            defender = self.net.get('h3')
            target_ip = defender.IP()
        if node_id == 2:
            defender = self.net.get('fw')
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
        print("Info: Defender is taking the action for pausing ssh service")
        if str(defender) == 'ws1':
        # Stop SSH service for ws1
            ssh_result = defender.cmd('service ssh stop')
            if "Stopping" in ssh_result:
                print("Info: SSH service on ws1 has been stopped.")
            else:
                print("Info: Failed to stop SSH service on ws1 or service not running.")
        else:
            print(f"Info: No SSH service running on {str(defender)}. Nothing to stop.")


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
        fw = self.net.get('fw')
        h1 = self.net.get('h1')
        for intf in defender.intfList():
            defender.cmd(f'ip link set {intf} up')
        #ws1 = self.net.get('ws1')
        ping_result = h1.cmd(f'ping -c 4 {target_ip}')
        #print(ping_result)

        if "100% packet loss" in ping_result:
            print(f"Info: Defender considers taking the action for blocking untrusted traffic. But target {target_ip} is not reachable. No firewall rules needed.")
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
                else:
                    print("Info: Block failed")        
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
                else:
                    print("Info: Block failed")

    def addsnortrules(self):
        fw = self.net.get('fw')
        try:
            print("Info: Restarting Snort service...")
            # Kill any running Snort processes
            #result = fw.cmd("ps aux | grep snort")
            #print(result)
            fw.cmd("pid=$(ps aux | grep snort | grep -v grep | awk '{print $2}'); kill -9 $pid")  
            time.sleep(3)
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
            
    """
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
        h1 = self.net.get('h1')
        if str(defender) == 'fw':
            print("Info: defender considers isolating the firewall node, but no neccessary")
        else:
            result = h1.cmd(f"ping -c 4 {target_ip}")
            #print(result)
            if "100% packet loss" in result:
                print(f"Info:defender considers isolating ths node {target_ip}, but the node is already unreachable")
            else:
                print(f"Info:defender is taking the action for isolating the compromised node {target_ip}")
                for intf in defender.intfList():
                    defender.cmd(f'ip link set {intf} down')
                print("Info:The compromised node has been isolated")
                #result = h1.cmd(f"ping -c 4 {target_ip}")
                #print(result)
    """

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
        if node_id == 2:
            defender = self.net.get('fw')
            target_ip = defender.IP()
        if str(defender) == 'ws1':
            # reset password
            print("Info: Defender is taking the action for resetting ssh service")
            new_password = "new_passwordkth123"
            password_reset_command = f"echo -e '{new_password}\\n{new_password}' | passwd user"
            result = defender.cmd(password_reset_command)
            #print("Password reset result:", result)

            # reset ssh key
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
            print(ssh_restart_result)
            print("Info: ssh service reset completed")
        else:
            print("Info: Defender considers taking the action for resetting ssh service, but not ssh service found")
        #print("Verifying SSH key configuration...")
        #verify_ssh_key_command = "ls -l /home/user/shared/id_rsa /home/user/shared/id_rsa.pub /home/user/shared/authorized_keys"
        #ssh_key_verification = ws1.cmd(verify_ssh_key_command)
        #print("SSH key verification result:")
        #print(ssh_key_verification)
     
            

if __name__ == '__main__':
    setLogLevel('info')
    os.system('sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1')
    os.system('sudo iptables -t nat -A POSTROUTING -o enp0s3 -j MASQUERADE > /dev/null 2>&1')
    os.system('ip route')
    os.system('sudo iptables -A FORWARD -i s1 -j ACCEPT > /dev/null 2>&1')
    os.system('sudo iptables -A FORWARD -o s1 -j ACCEPT > /dev/null 2>&1')
    os.system('sudo iptables -A FORWARD -i s3 -j ACCEPT > /dev/null 2>&1')
    os.system('sudo iptables -A FORWARD -o s3 -j ACCEPT > /dev/null 2>&1')
    # start the containernet network
    topo = Mytopo()
    topo.start_webcamservice()
    time.sleep(3)
    topo.default_firewall_and_IDS()
    #topo.addsnortrules()
    
    ######testing for reconnaissance attack:
    output = topo.reconnaissance(0)
    print("reconnaisance is :")
    print(output)
    output = topo.reconnaissance(1)
    print("reconnaisance is :")
    print(output)
    output = topo.reconnaissance(2)
    print("reconnaisance is :")
    print(output)
    #output4 = topo.DDoS(0)
    #print("Testing:DDoS result boolean flag is", output4)
    output = topo.reconnaissance(3)
    print("reconnaisance is :")
    print(output)
    ######
    #output1 = topo.sshbruteforce(0)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    #output1 = topo.sshbruteforce(1)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    #output1 = topo.sshbruteforce(2)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    #output1 = topo.sshbruteforce(3)
    #print("Testing:ssh bruteforce result boolean flag is", output1)
    ######
    #output2 = topo.root(0)
    #print("Testing:ssh root result boolean flag is", output2)
    #output2 = topo.root(1)
    #print("Testing:ssh root result boolean flag is", output2)
    #output2 = topo.root(2)
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
    #output3 = topo.persistence(3)
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
    #topo.pause_services(0)
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
    #topo.attack_modidyfirewall()
    #output4 = topo.DDoS(0)
    #print("Testing:DDoS result boolean flag is", output4)
    #output4 = topo.persistence()
    #topo.reset_services(0)
    #topo.reset_services(1)
    #topo.reset_services(2)
    #output2 = topo.root()
    #print("Testing:ssh root result boolean flag is", output2)
    #output3 = topo.persistence()
    #print("Testing:persistence result boolean flag is", output3)
    ##testing isolation function:
    #topo.isolate_node(2)
    CLI(topo.net)
    topo.net.stop()
    
    os.system('sudo echo "nameserver 8.8.8.8" > /etc/resolv.conf')
