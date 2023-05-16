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
        ->Strip(14)
        ->SetIPChecksum
        ->CheckIPHeader
        ->IPChecksumFixer(0)
        ->Unstrip(14)
        ->output
}


/*
clientInputCount, serverInputCount, clientOutputCount, serverOutputCount :: AverageCounter;
arpReqCount, arpReqCount1, arpQueCount, arpQueCount1, ipCount, ipCount1, icmpCount,
icmpCount1, dropCount, dropCount1, dropCount2, dropCount3 :: Counter;*/

fromClient :: FromDevice(lb-eth1, METHOD LINUX, SNIFFER false);
fromServer :: FromDevice(lb-eth2, METHOD LINUX, SNIFFER false);

toServer :: Queue -> ToDevice(lb-eth2, METHOD LINUX);
toClient :: Queue -> ToDevice(lb-eth1, METHOD LINUX);

clientClassifier, serverClassifier :: Classifier(
    12/0806 20/0001, //ARP requrest
    12/0806 20/0002, //ARP respond
    12/0800, //IP
    - ); //others

ipPacketClassifierClient :: IPClassifier(
    dst 100.0.0.45 and icmp, //ICMP
    dst 100.0.0.45 port 80 and tcp, //tcp
    -); //others

ipPacketClassifierServer :: IPClassifier(
    dst 100.0.0.45 and icmp type echo, //ICMP to lb
    src port 80 and tcp, //tcp
    -); //others



arpQuerierClient :: ARPQuerier(100.0.0.45, 1a:a8:60:d2:c3:72);
arpQuerierServer :: ARPQuerier(100.0.0.45, 0a:06:6d:a1:ff:3a);
arpRespondClient :: ARPResponder(100.0.0.45 1a:a8:60:d2:c3:72);
arpRespondServer :: ARPResponder(100.0.0.45 0a:06:6d:a1:ff:3a);

//toClient :: /*FixedForwarder ->*/ toClientDevice;
//toServer :: Queue(1024) -> /*FixedForwarder ->*/ toServerDevice;


ipPacketClient :: GetIPAddress(16) -> CheckIPHeader -> [0]arpQuerierClient -> FixedForwarder -> toClient;
ipPacketServer :: GetIPAddress(16) -> CheckIPHeader -> [0]arpQuerierServer -> FixedForwarder -> toServer;

ipRewrite :: IPRewriter (roundRobin);

roundRobin :: RoundRobinIPMapper(
    100.0.0.45 - 100.0.0.40 - 0 1,
    100.0.0.45 - 100.0.0.41 - 0 1,
    100.0.0.45 - 100.0.0.42 - 0 1);

ipRewrite[0] -> ipPacketServer;
ipRewrite[1] -> ipPacketClient;

//from client
fromClient -> clientClassifier;

clientClassifier[0] -> arpRespondClient -> toClient;
clientClassifier[1] -> [1]arpQuerierClient;
clientClassifier[2] -> Strip(14) -> CheckIPHeader -> ipPacketClassifierClient;
clientClassifier[3] -> Discard;

ipPacketClassifierClient[0] -> ICMPPingResponder -> ipPacketClient;
ipPacketClassifierClient[1] -> [0]ipRewrite;
ipPacketClassifierClient[2] ->  Discard;

//from server
fromServer -> serverClassifier;

serverClassifier[0] -> arpRespondServer -> toServer;
serverClassifier[1] -> [1]arpQuerierServer;
serverClassifier[2] -> Strip(14) -> CheckIPHeader -> ipPacketClassifierServer;
serverClassifier[3] -> Discard;

ipPacketClassifierServer[0] -> ICMPPingResponder -> ipPacketServer;
ipPacketClassifierServer[1] -> [0]ipRewrite;
ipPacketClassifierServer[2] -> Discard;

