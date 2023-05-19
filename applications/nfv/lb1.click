//smh
//lb-eth2<->ids-eth1 (OK OK) FROM 		CLIENTS  lb-eth2
//sw4-eth1<->lb-eth1 (OK OK) TO 		SERVERS  lb-eth1

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

switchInput, switchOutput, serverInput, serverOutput :: AverageCounter
requestServerArp, requestClientArp, responseServerArp, responseClientArp, clientDrop, serverDrop, serverDrop1, clientDrop1, serviceClient, serviceServer, icmpClient, icmpServer :: Counter

fromClient :: FromDevice(lb-eth2, METHOD LINUX, SNIFFER false);
fromServer :: FromDevice(lb-eth1, METHOD LINUX, SNIFFER false);
toServerDevice :: ToDevice(lb-eth1, METHOD LINUX);
toClientDevice :: ToDevice(lb-eth2, METHOD LINUX);

toServer :: Queue(1024) -> serverInput -> toServerDevice;
toClient :: Queue(1024) -> switchInput -> toClientDevice;

clientClassifier, serverClassifier :: Classifier(
    12/0806 20/0001, //ARP request
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


arpQuerierClient :: ARPQuerier(100.0.0.45, lb-eth2);
arpQuerierServer :: ARPQuerier(100.0.0.45, lb-eth1);
arpRespondClient :: ARPResponder(100.0.0.45 lb-eth2);
arpRespondServer :: ARPResponder(100.0.0.45 lb-eth1);

ipPacketClient :: GetIPAddress(16) -> /*Print(GETIPADDRESS16, -1)->*/ CheckIPHeader -> /*Print(CHECKHEADER, -1) ->*/ [0]arpQuerierClient -> /*Print(ARPQUERIER, -1) ->*/ toClient;
ipPacketServer :: GetIPAddress(16) -> CheckIPHeader -> [0]arpQuerierServer -> toServer;

ipRewrite :: IPRewriter (roundRobin);

roundRobin :: RoundRobinIPMapper(
    100.0.0.45 - 100.0.0.40 - 0 1,
    100.0.0.45 - 100.0.0.41 - 0 1,
    100.0.0.45 - 100.0.0.42 - 0 1);

ipRewrite[0] -> ipPacketServer;
ipRewrite[1] -> ipPacketClient;

//from client
fromClient -> switchOutput -> /*Print(FROMCLIENT, -1) ->*/ clientClassifier;

clientClassifier[0] -> requestClientArp -> /*Print(CLIENT_PING, -1) ->*/ arpRespondClient -> toClient;				//arp request
clientClassifier[1] -> responseClientArp -> [1]arpQuerierClient;									//arp response
clientClassifier[2] -> serviceClient -> FixedForwarder -> Strip(14) -> CheckIPHeader -> ipPacketClassifierClient;		//ip	
clientClassifier[3] -> clientDrop -> Discard;											//others

ipPacketClassifierClient[0] -> icmpClient -> Print(CLASSIFIED_CLIENT_PING, -1) -> ICMPPingResponder -> /*Print(PINGRESPONSE, -1)->*/ ipPacketClient;
ipPacketClassifierClient[1] -> [0]ipRewrite;
ipPacketClassifierClient[2] -> clientDrop1 -> Discard;

//from server
fromServer -> serverOutput -> serverClassifier;

serverClassifier[0] -> requestServerArp -> arpRespondServer -> toServer;
serverClassifier[1] -> responseServerArp -> [1]arpQuerierServer;
serverClassifier[2] -> serviceServer -> FixedForwarder -> Strip(14) -> CheckIPHeader -> ipPacketClassifierServer;
serverClassifier[3] -> serverDrop -> Discard;

ipPacketClassifierServer[0] -> icmpServer -> ICMPPingResponder -> ipPacketServer;
ipPacketClassifierServer[1] -> [0]ipRewrite;
ipPacketClassifierServer[2] -> serverDrop1 -> Discard;

DriverManager(wait , print > ../../results/lb1.report  "
     =================== LB1 Report ===================
        Input Packet rate (pps): $(add $(switchInput.rate) $(serverInput.rate))
        Output Packet rate (pps): $(add $(switchOutput.rate) $(serverOutput.rate))
        
      Total # of   input packets: $(add $(switchInput.count) $(serverInput.count))
      Total # of  output packets: $(add $(switchOutput.count) $(serverOutput.count))

      Total # of   ARP  requests: $(add $(requestClientArp.rate) $(requestServerArp.rate))
      Total # of   ARP responses: $(add $(responseClientArp.rate) $(responseServerArp.rate))

      Total # of service packets: $(add $(serviceServer.rate) $(serviceClient.rate))
      Total # of    ICMP report:  $(add $(icmpServer.rate) $(icmpClient.rate))
      Total # of dropped packets: $(add $(serverDrop.rate) $(serverDrop1.rate) $(clientDrop.rate) $(clientDrop1.rate))  



     =================================================

   " , stop);

