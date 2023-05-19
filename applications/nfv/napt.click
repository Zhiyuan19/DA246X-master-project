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



fromInt :: FromDevice($PORT2, METHOD LINUX, SNIFFER false);

fromOut :: FromDevice($PORT1, METHOD LINUX, SNIFFER false);

toInt :: Queue -> switchOutput -> ToDevice($PORT2);

toOut :: Queue -> serverOutput -> ToDevice($PORT1);



arpReplyIntern :: ARPResponder(10.0.0.1 10.0.0.0/24 9e-a3-ec-98-af-25);

arpReplyOutern :: ARPResponder(100.0.0.1 100.0.0.0/24 3e-b6-37-4f-63-8e);

arpRequestIntern :: ARPQuerier(10.0.0.1, 9e-a3-ec-98-af-25);	

arpRequestOutern :: ARPQuerier(100.0.0.1, 3e-b6-37-4f-63-8e);



IpNAT :: IPRewriter(pattern 100.0.0.1 20000-65535 - - 0 1);

IcmpNAT :: ICMPPingRewriter(pattern 100.0.0.1 20000-65535 - - 0 1);



packetClassifierInt, packetClassifierOut :: Classifier(

    12/0806 20/0001, //ARP request

    12/0806 20/0002, //ARP respond

    12/0800, //IP
    
    - //rest
)


ipClassifierInt, ipClassifierOut :: IPClassifier(

    tcp,

    icmp type echo,

    icmp type echo-reply,

    -

)


fromInt -> switchInput -> packetClassifierInt;



packetClassifierInt[0] -> requestInArp -> arpReplyIntern -> toInt;

packetClassifierInt[1] -> responseInArp -> [1]arpRequestIntern;

packetClassifierInt[2] -> FixedForwarder -> Strip(14) -> CheckIPHeader -> ipClassifierInt;

packetClassifierInt[3] -> switchDrop -> Discard;



ipClassifierInt[0] -> serviseRequest -> IpNAT[0] -> [0]arpRequestOutern -> toOut;

ipClassifierInt[1] -> icmpIn -> IcmpNAT[0] -> [0]arpRequestOutern -> toOut;

ipClassifierInt[2] -> icmpDropIn1 -> Discard; 

ipClassifierInt[3] -> icmpDropIn2 -> Discard;



fromOut -> serverInput -> packetClassifierOut;

packetClassifierOut[0] -> requestOutArp -> arpReplyOutern -> toOut;

packetClassifierOut[1] -> responseOutArp -> [1]arpRequestOutern;

packetClassifierOut[2] -> FixedForwarder -> Strip(14) -> CheckIPHeader -> ipClassifierOut;

packetClassifierOut[3] -> serverDrop -> Discard;



ipClassifierOut[0] -> IpNAT[1] -> [0]arpRequestIntern -> toInt;

ipClassifierOut[2] -> icmpOut -> IcmpNAT[1] -> [0]arpRequestIntern -> toInt;

ipClassifierOut[3] -> icmpDropOut1  -> Discard;

ipClassifierOut[1] -> icmpDropOut2 -> Discard;



DriverManager(wait , print > ../../results/napt.report  "
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

" , stop);

