//counter
fromPrzCt, toPrzCt, fromDmzCt, toDmzCt :: AverageCounter;
arpRespondIntCt, arpRespondExtCt, arpQueryIntCt, arpQueryExtCt, icmpExtCt, icmpIntCt, tcpIntCt, dropIntCt, dropExtCt, icmpEchoDropIntCt, icmpEchoDropExtCt, icmpReplyDropIntCt, icmpReplyDropExtCt :: Counter;

//
define($PORT1 napt-eth1, $PORT2 napt-eth2)

//defination

fromInt :: FromDevice($PORT2, METHOD LINUX, SNIFFER false);
fromExt :: FromDevice($PORT1, METHOD LINUX, SNIFFER false);
toInt :: Queue -> toPrzCt -> ToDevice($PORT2);
toExt :: Queue -> toDmzCt -> ToDevice($PORT1);

arpReplyIntern :: ARPResponder(10.0.0.1 10.0.0.0/24 9e-a3-ec-98-af-25);
arpReplyExtern :: ARPResponder(100.0.0.1 100.0.0.0/24 3e-b6-37-4f-63-8e);

arpRequestIntern :: ARPQuerier(10.0.0.1, 9e-a3-ec-98-af-25);	
arpRequestExtern :: ARPQuerier(100.0.0.1, 3e-b6-37-4f-63-8e);



IpNAT :: IPRewriter(pattern 100.0.0.1 20000-65535 - - 0 1);
IcmpNAT :: ICMPPingRewriter(pattern 100.0.0.1 20000-65535 - - 0 1);


packetClassifierInt, packetClassifierExt :: Classifier(

    12/0806 20/0001, //ARP request

    12/0806 20/0002, //ARP respond

    12/0800, //IP

    - //rest

)



ipClassifierInt, ipClassifierExt :: IPClassifier(

    tcp,

    icmp type echo,

    icmp type echo-reply,

    -

)



fromInt -> fromPrzCt -> packetClassifierInt;

packetClassifierInt[0] -> arpQueryIntCt -> arpReplyIntern -> toInt;

packetClassifierInt[1] -> arpRespondIntCt  -> [1]arpRequestIntern;

packetClassifierInt[2] -> Strip(14) -> CheckIPHeader -> ipClassifierInt;

packetClassifierInt[3] -> dropIntCt  -> Discard;





ipClassifierInt[0] -> tcpIntCt -> IpNAT[0] -> [0]arpRequestExtern -> toExt;

ipClassifierInt[1] -> icmpIntCt -> IcmpNAT[0] -> [0]arpRequestExtern -> toExt;

ipClassifierInt[2] -> icmpEchoDropIntCt -> Discard;

ipClassifierInt[3] -> icmpReplyDropIntCt -> Discard;



fromExt -> fromDmzCt -> packetClassifierExt;

packetClassifierExt[0] -> arpQueryExtCt -> arpReplyExtern -> toExt;

packetClassifierExt[1] -> arpRespondExtCt -> [1]arpRequestExtern;

packetClassifierExt[2] -> Strip(14) -> CheckIPHeader -> ipClassifierExt;

packetClassifierExt[3] -> dropExtCt -> Discard;



ipClassifierExt[0] -> IpNAT[1] -> [0]arpRequestIntern -> toInt;

ipClassifierExt[1] -> icmpEchoDropExtCt -> Discard;

ipClassifierExt[2] -> icmpExtCt -> IcmpNAT[1] -> [0]arpRequestIntern -> toInt;

ipClassifierExt[3] -> icmpReplyDropExtCt  -> Discard;









