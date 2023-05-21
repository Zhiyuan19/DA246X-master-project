//
//CODE for IPChecksumFixer taken FROM COURSE DISCUSSIONS  #https://canvas.kth.se/courses/39067/discussion_topics/302524

elementclass IPChecksumFixer{ $print |
        input
        ->SetIPChecksum
        -> class::IPClassifier(tcp, udp, -)
        class[0] -> Print(TCP, ACTIVE $print) -> SetTCPChecksum -> output
        class[1] -> Print(UDP, ACTIVE $print) -> SetUDPChecksum -> output
        class[2] -> Print(OTH, ACTIVE $print) -> output

}

//Use before passing to ToDevice

elementclass FixedForwarder{ 
         input
        -> Print(BEFORESTRIP, -1) 
        ->Strip(14)
        ->Print(BEFORECHECKSUM, -1)		
        ->SetIPChecksum
        //->Print(AFTERCHECKSUM, -1)
        ->CheckIPHeader
        ->IPChecksumFixer(0)
        ->Unstrip(14)
        ->output

}

define($PORT1 napt-eth1, $PORT2 napt-eth2)
//defination
switchInput, switchOutput, serverInput, serverOutput :: AverageCounter
requestInArp, requestOutArp, responseInArp, responseOutArp, serviseRequest, switchDrop, serverDrop, icmpIn, icmpOut, icmpDropIn1, icmpDropIn2, icmpDropOut1, icmpDropOut2 :: Counter


fromPrz :: FromDevice($PORT2, METHOD LINUX, SNIFFER false);
fromExtern :: FromDevice($PORT1, METHOD LINUX, SNIFFER false);
toPrz :: Queue -> switchOutput -> ToDevice($PORT2);
toExtern :: Queue -> serverOutput -> ToDevice($PORT1);



arpReplyPrz :: ARPResponder(10.0.0.1 10.0.0.0/24 9e-a3-ec-98-af-25);
arpReplyExtern :: ARPResponder(100.0.0.1 100.0.0.0/24 3e-b6-37-4f-63-8e);
arpRequestPrz :: ARPQuerier(10.0.0.1, 9e-a3-ec-98-af-25);	
arpRequestExtern :: ARPQuerier(100.0.0.1, 3e-b6-37-4f-63-8e);



IpNAT :: IPRewriter(pattern 100.0.0.1 20000-65535 - - 0 1);
IcmpNAT :: ICMPPingRewriter(pattern 100.0.0.1 20000-65535 - - 0 1);



packetClassifierPrz, packetClassifierExt :: Classifier(

    12/0806 20/0001, //ARP request
    12/0806 20/0002, //ARP respond
    12/0800, //IP
    - //rest
)


ipClassifierPrz, ipClassifierExt :: IPClassifier(
    tcp,
    icmp type echo,
    icmp type echo-reply,
    -
)


fromPrz -> switchInput -> packetClassifierPrz;

packetClassifierPrz[0] -> requestInArp -> arpReplyPrz -> toPrz;
packetClassifierPrz[1] -> responseInArp -> [1]arpRequestPrz;
packetClassifierPrz[2] -> FixedForwarder -> Strip(14) -> CheckIPHeader -> ipClassifierPrz;
packetClassifierPrz[3] -> switchDrop -> Discard;


ipClassifierPrz[0] -> serviseRequest -> IpNAT[0] -> [0]arpRequestExtern -> toExtern;
ipClassifierPrz[1] -> icmpIn -> IcmpNAT[0] -> [0]arpRequestExtern -> toExtern;
ipClassifierPrz[2] -> icmpDropIn1 -> Discard; 
ipClassifierPrz[3] -> icmpDropIn2 -> Discard;


fromExtern -> serverInput -> packetClassifierExt;

packetClassifierExt[0] -> requestOutArp -> arpReplyExtern -> toExtern;
packetClassifierExt[1] -> responseOutArp -> [1]arpRequestExtern;
packetClassifierExt[2] -> FixedForwarder -> Strip(14) -> CheckIPHeader -> ipClassifierExt;
packetClassifierExt[3] -> serverDrop -> Discard;

ipClassifierExt[0] -> IpNAT[1] -> [0]arpRequestPrz -> toPrz;
ipClassifierExt[2] -> icmpOut -> IcmpNAT[1] -> [0]arpRequestPrz -> toPrz;
ipClassifierExt[3] -> icmpDropOut1  -> Discard;
ipClassifierExt[1] -> icmpDropOut2 -> Discard;

DriverManager(pause , print > /opt/pox/ext/results/napt.report  "
     =================== NAPT Report ===================
        Input Packet rate (pps): $(add $(switchInput.rate) $(serverInput.rate))
        Output Packet rate (pps): $(add $(switchOutput.rate) $(serverOutput.rate))

      Total # of   input packets: $(add $(switchInput.count) $(serverInput.count))
      Total # of  output packets: $(add $(switchOutput.count) $(serverOutput.count))
   
      Total # of   ARP  requests: $(add $(requestInArp.count) $(requestOutArp.count))
      Total # of   ARP responses: $(add $(responseInArp.count) $(responseOutArp.count))

      Total # of service packets: $(add $(serviseRequest.count) ) 
      Total # of    ICMP report:  $(add $(icmpIn.count) $(icmpOut.count))   
      Total # of dropped packets: $(add $(switchDrop.count) $(serverDrop.count) $(icmpDropIn1.count) $(icmpDropIn2.count) $(icmpDropOut1.count) $(icmpDropOut2.count))   
     =================================================



" );
