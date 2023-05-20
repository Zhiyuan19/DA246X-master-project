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

avgCntToClient, avgCntFromClient, avgCntToServer, avgCntFromServer :: AverageCounter

cntArpReqSrv, ¨cntArpReqClient, cntArpRspSrv, cntArpRspClient :: Counter
cntDropFromClientEth, cntDropFromClientIP, cntDropFromSvrEth, cntDropFromSvrIP,  :: Counter
cntLbServedFromClient, cntLbServedFromSrv, cntIcmpFromClient, cntIcmpFromServer :: Counter

fromClient :: FromDevice(lb-eth2, METHOD LINUX, SNIFFER false);
fromServer :: FromDevice(lb-eth1, METHOD LINUX, SNIFFER false);
toServerDevice :: ToDevice(lb-eth1, METHOD LINUX);
toClientDevice :: ToDevice(lb-eth2, METHOD LINUX);

toServer :: Queue(1024) -> avgCntToServer -> toServerDevice;
toClient :: Queue(1024) -> avgCntToClient -> toClientDevice;

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

ipPacketClient :: GetIPAddress(16) -> Print(TOCLINET_GETIPADDRESS16, -1, ACTIVE 1) -> CheckIPHeader -> Print(TOCLINENT_CHECKHEADER, -1, ACTIVE 1) -> [0]arpQuerierClient -> Print(ARPQUERIER, -1, ACTIVE 1) -> toClient;
ipPacketServer :: GetIPAddress(16) -> Print(TOSERVER_GETIPADDRESS16, -1, ACTIVE 1) -> CheckIPHeader -> [0]arpQuerierServer -> Print(TOSERVER_AFTERARP, -1, ACTIVE 1) -> toServer;

roundRobin :: RoundRobinIPMapper(
    100.0.0.45 - 100.0.0.40 - 0 1,
    100.0.0.45 - 100.0.0.41 - 0 1,
    100.0.0.45 - 100.0.0.42 - 0 1);

ipRewrite :: IPRewriter (roundRobin);

ipRewrite[0] -> ipPacketServer;
ipRewrite[1] -> ipPacketClient;

//from client
fromClient -> avgCntFromClient -> /*Print(FROMCLIENT, -1) ->*/ clientClassifier;

clientClassifier[0] -> ¨cntArpReqClient -> /*Print(CLIENT_PING, -1) ->*/ arpRespondClient -> toClient;				//arp request
clientClassifier[1] -> cntArpRspClient -> [1]arpQuerierClient;									//arp response
clientClassifier[2] -> cntLbServedFromClient -> FixedForwarder -> Strip(14) -> CheckIPHeader -> ipPacketClassifierClient;		//ip	
clientClassifier[3] -> cntDropFromClientEth -> Discard;											//others

ipPacketClassifierClient[0] -> cntIcmpFromClient -> Print(CLASSIFIED_CLIENT_PING, -1) -> ICMPPingResponder -> /*Print(PINGRESPONSE, -1)->*/ ipPacketClient;
ipPacketClassifierClient[1] -> [0]ipRewrite;
ipPacketClassifierClient[2] -> cntDropFromClientIP -> Discard;

//from server
fromServer -> avgCntFromServer -> serverClassifier;

serverClassifier[0] -> cntArpReqSrv -> arpRespondServer -> toServer;
serverClassifier[1] -> cntArpRspSrv -> [1]arpQuerierServer;
serverClassifier[2] -> cntLbServedFromSrv -> FixedForwarder -> Strip(14) -> CheckIPHeader -> ipPacketClassifierServer;
serverClassifier[3] -> cntDropFromSvrEth -> Discard;

ipPacketClassifierServer[0] -> cntIcmpFromServer -> ICMPPingResponder -> ipPacketServer;
ipPacketClassifierServer[1] -> [0]ipRewrite;
ipPacketClassifierServer[2] -> cntDropFromSvrIP -> Discard;

DriverManager(wait , print > ../../results/lb1.report  "
     =================== LB1 Report ===================
        Input Packet rate (pps): $(add $(avgCntToClient.rate) $(avgCntToServer.rate))
        Output Packet rate (pps): $(add $(avgCntFromClient.rate) $(avgCntFromServer.rate))
        
      Total # of   input packets: $(add $(avgCntToClient.count) $(avgCntToServer.count))
      Total # of  output packets: $(add $(avgCntFromClient.count) $(avgCntFromServer.count))

      Total # of   ARP  requests: $(add $(¨cntArpReqClient.count) $(cntArpReqSrv.count))
      Total # of   ARP responses: $(add $(cntArpRspClient.count) $(cntArpRspSrv.count))

      Total # of service packets: $(add $(cntLbServedFromSrv.count) $(cntLbServedFromClient.count))
      Total # of    ICMP report:  $(add $(cntIcmpFromServer.count) $(cntIcmpFromClient.count))
      Total # of dropped packets: $(add $(cntDropFromSvrEth.count) $(cntDropFromSvrIP.count) $(cntDropFromClientEth.count) $(cntDropFromClientIP.count))  

     =================================================

   " , stop);

