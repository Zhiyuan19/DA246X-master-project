//counters
fromPrz, toPrz, fromDmz, toDmz :: AverageCounter;
arpRespondInt, arpRespondExt, arpQueryInt, arpQueryExt, icmpExt, icmpInt, tcpInt, dropInt, dropExt, icmpEchoDropInt, icmpEchoDropExt, icmpReplyDropInt, icmpReplyDropExt :: Counter;
// 2 variables to hold ports names
define($PORT1 napt-eth1, $PORT2 napt-eth2)

//from where to receive packets
FromInternal :: FromDevice($PORT2, METHOD LINUX, SNIFFER false);
FromExternal :: FromDevice($PORT1, METHOD LINUX, SNIFFER false);

//where to send packets
ToInternal :: ToDevice($PORT2)
ToExternal :: ToDevice($PORT1)

//ARP
ArpReplyInternal :: ARPResponder(10.0.0.1 $PORT2);
ArpReplyExternal :: ARPResponder(100.0.0.1 $PORT1);

ArpRequestInternal :: ARPQuerier(10.0.0.1, $PORT2);
ArpRequestExternal :: ARPQuerier(100.0.0.1, $PORT1);

IpNAT :: IPRewriter(pattern 100.0.0.1 20000-65535 - - 0 1);
IcmpNAT :: ICMPPingRewriter(pattern 100.0.0.1 20000-65535 - - 0 1);

PacketClassifierInternal, PacketClassifierExternal :: Classifier(
    12/0806 20/0001, //ARP request
    12/0806 20/0002, //ARP respond
    12/0800, //IP
    - //rest
)

IpClassifierInternal, IpClassifierExternal :: IPClassifier(
    tcp,
    icmp type echo,
    icmp type echo-reply,
    -
)

FromInternal -> fromPrz -> PacketClassifierInternal;
PacketClassifierInternal[0] -> arpQueryInt -> ArpReplyInternal -> Tointern :: Queue -> toPrz -> ToInternal;
PacketClassifierInternal[1] -> arpRespondInt -> [1]ArpRequestInternal;
PacketClassifierInternal[2] -> Strip(14) -> CheckIPHeader -> IpClassifierInternal;
PacketClassifierInternal[3] -> dropInt -> Discard;


IpClassifierInternal[0] -> tcpInt -> IpNAT[0] -> [0]ArpRequestExternal -> toExtern :: Queue -> toDmz ->ToExternal;
IpClassifierInternal[1] -> icmpInt -> IcmpNAT[0] -> [0]ArpRequestExternal-> toExtern :: Queue -> toDmz -> ToExternal;
IpClassifierInternal[2] -> icmpEchoDropInt -> Discard;
IpClassifierInternal[3] -> icmpReplyDropInt -> Discard;

FromExternal -> fromDmz -> PacketClassifierExternal;
PacketClassifierExternal[0] -> arpQueryExt -> ArpReplyExternal -> toExtern :: Queue -> toDmz ->ToExternal;
PacketClassifierExternal[1] -> arpRespondExt -> [1]ArpRequestExternal;
PacketClassifierExternal[2] -> Strip(14) -> CheckIPHeader -> IpClassifierExternal
PacketClassifierExternal[3] -> dropExt -> Discard;

IpClassifierExternal[0] -> IpNAT[1] -> [0]ArpRequestInternal -> Tointern :: Queue -> toPrz -> ToInternal;
IpClassifierExternal[1] -> icmpEchoDropExt -> Discard;
IpClassifierExternal[2] -> icmpExt -> IcmpNAT[1] -> [0]ArpRequestInternal -> Tointern :: Queue -> toPrz -> ToInternal;
IpClassifierExternal[3] -> icmpReplyDropExt -> Discard;




DriverManager(wait, print > ../../results/napt.report "
        ===================== NAPT Report ====================
        Input Packet Rate (pps): $(add $(fromPrz.rate) $(fromDmz.rate))
        Output Packet Rate(pps): $(add $(toPrz.rate) $(toDmz.rate))

        Total # of input packets: $(add $(fromPrz.count) $(fromDmz.count))
        Total # of output packets: $(add $(toPrz.count) $(toDmz.count))

        Total # of ARP request packets: $(add $(arpQueryInt.count) $(arpQueryExt.count))
        Total # of ARP reply packets: $(add $(arpRespondInt.count) $(arpRespondExt.count))

        Total # of service requests packets: $(add $(tcpInt.count))
        Total # of ICMP packets: $(add $(icmpInt.count) $(icmpExt.count))
        Total # of dropped packets: $(add $(dropInt.count) $(dropExt.count) $(icmpEchoDropInt.count) $(icmpEchoDropExt.count) $(icmpReplyDropInt.count) $(icmpReplyDropExt.count))
        ======================================================",
        stop);

