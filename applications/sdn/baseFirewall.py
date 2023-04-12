from pox.core import core

import pox.openflow.libopenflow_01 as of

from pox.lib.addresses import IPAddr

import pox.lib.packet as pkt

from forwarding import l2_learning

log = core.getLogger()


# This is the basic Firewall class which implements all features of your firewall!

# For upcoming packets, you should decide if the packet is allowed to pass according to the firewall rules (which you have provided in networkFirewalls file during initialization.)

# After processing packets you should install the correct OF rule on the device to threat similar packets the same way on dataplane (without forwarding packets to the controller) for a specific period of time.


# rules format:

# [input_HW_port, protocol, src_ip, src_port, dst_ip, dst_port, allow/block]

# Checkout networkFirewalls.py file for detailed structure.


class Firewall (l2_learning.LearningSwitch):

    rules = []

    def __init__(self, connection, name):

        # Initialization of your Firewall. You may want to keep track of the connection, device name and etc.

        super(Firewall, self).__init__(connection, False)

        self.name = name

        self.connection = connection

        ### COMPLETE THIS PART ###

    def subnet_check(self, subnet, ip):

        if (subnet == 'any'):

            return True

        else:

            addr_range, mask = subnet.split('/')

            mask = int(mask)

            check = ip.inNetwork((addr_range, mask))

            return check

    def protocol_check(self, rule, tcp_udp):

        if rule == 'any':

            return True

        if rule != tcp_udp:

            return False

        else:

            return True

    def tcp_port_check(self, rule, our_port):

        if rule == 'any':

            return True

        if rule != our_port:

            return False

        else:

            return True

    # Check if the incoming packet should pass the firewall.

    # It returns a boolean as if the packet is allowed to pass the firewall or not.

    # You should call this function during the _handle_packetIn event to make the right decision for the incoming packet.

    def has_access(self, ip_packet, input_port):

        ### COMPLETE THIS PART ###

        ipp_payload = ip_packet.payload

        tcp_udp = ""

        tcp_src_port = -1

        tcp_dst_port = -1

        # check packet type

        if ip_packet.find('tcp'):

            tcp_udp = 'TCP'

            tcp_src_port = ip_packet.find('tcp').srcport

            tcp_dst_port = ip_packet.find('tcp').dstport

        if ip_packet.find('udp'):

            tcp_udp = 'UDP'

        else:

            tcp_udp = None

        src_addr = ipp_payload.srcip

        dst_addr = ipp_payload.dstip

        for rule in self.rules:

          # fw_hwport = rules[0]

          # protocol = rules[1]

          # source_subnet = rules[2]

          # tcp_source_port = rules[3]

          # destination_subnet = rules[4]

          # tcp_dest_port = rules[5]

          # allow_or_block = rules[6]

            if rule[0] == input_port and self.protocol_check(rule[1], tcp_udp) and self.subnet_check(rule[2], src_addr) and self.tcp_port_check(rule[3], tcp_src_port) and self.subnet_check(rule[4], dst_addr) and self.tcp_port_check(rule[5], tcp_dst_port) and rule[6] == 'allow':

                return True

            elif rule[6] == 'block':

                return False

        return True

    # On receiving a packet from dataplane, your firewall should process incoming event and apply the correct OF rule on the device.

    def install_allow(self, packet, received_port):

        match_obj = of.ofp_match.from_packet(packet, received_port)

        msg = of.ofp_flow_mod()

        msg.match = match_obj

        out_port = -1

        # Only works for our topology, either port 1 or 2

        if received_port == 1:

            out_port = 2

        if received_port == 2:

            out_port = 1

        msg.actions.append(of.ofp_action_output(port=out_port))

        msg.idle_timeout = 10

        msg.hard_timeout = 30

        self.connection.send(msg)

        return

    def install_block(self, packet, received_port):

        match_obj = of.ofp_match.from_packet(packet, received_port)

        msg = of.ofp_flow_mod()

        msg.match = match_obj

        msg.idle_timeout = 10

        msg.hard_timeout = 30

        # msg.actions.append(of.ofp_action_output(port=of.OFPP_NONE)) useless

        self.connection.send(msg)

        return

    def _handle_PacketIn(self, event):

        # check for firstSeenAt

        packet = event.parsed

        mac_addr = packet.src

        dpid = event.connection.dpid

        received_port = event.port

        where = f"switch {dpid} - port {received_port}"

        core.controller.updatefirstSeenAt(mac_addr, where)

        # finished checking for firstSeenAt

        if not packet.parsed:

            print(self.name, ": Incomplete packet received! controller ignores that")

            return

        ### COMPLETE THIS PART ###

        # ofp_msg = event.ofp

        if self.has_access(packet, event.port):

            log.info(f"\n{self.name} : Packet allowed by the Firewall")

            self.install_allow(packet, received_port)

        else:

            log.warning(f"\n{self.name} : Packet blocked by the Firewall!")

            self.install_block(packet, received_port)

            return

        print(packet)

        print("\n")

        super(Firewall, self)._handle_PacketIn(event)

    # You are allowed to add more functions to this file as your need (e.g., a function for installing OF rules)
