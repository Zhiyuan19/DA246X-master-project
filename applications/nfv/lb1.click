// Element Definitions

elementclass IPChecksumFixer {
  $print |
  input ->
  SetIPChecksum ->
  class::IPClassifier(tcp, udp, -)
    
  class[0] -> Print(TCP, ACTIVE $print) -> SetTCPChecksum -> output
  class[1] -> Print(UDP, ACTIVE $print) -> SetUDPChecksum -> output
  class[2] -> Print(OTH, ACTIVE $print) -> output
}

elementclass FixedForwarder {
  input ->
  Print(BEFORESTRIP, -1) ->
  Strip(14) ->
  Print(BEFORECHECKSUM, -1) ->
  SetIPChecksum ->
  CheckIPHeader ->
  IPChecksumFixer(0) ->
  Unstrip(14) ->
  output
}

  // Counters

  avgCntToClient, avgCntFromClient, avgCntToServer, avgCntFromServer :: AverageCounter

  cntArpReqSrv, cntArpReqClient, cntArpRspSrv, cntArpRspClient :: Counter
  cntDropFromClientEth, cntDropFromClientIP, cntDropFromSvrEth, cntDropFromSvrIP :: Counter
  cntLbServedFromClient, cntLbServedFromSrv, cntIcmpFromClient, cntIcmpFromServer :: Counter

  // Devices

  fromClient :: FromDevice(lb-eth2, METHOD LINUX, SNIFFER false)
  fromServer :: FromDevice(lb-eth1, METHOD LINUX, SNIFFER false)
  toServerDevice :: ToDevice(lb-eth1, METHOD LINUX)
  toClientDevice :: ToDevice(lb-eth2, METHOD LINUX)

  // Queues

  toServer :: Queue(1024) -> avgCntToServer -> toServerDevice
  toClient :: Queue(1024) -> avgCntToClient -> toClientDevice

  // Classifiers

  clientClassifier, serverClassifier :: Classifier(
						   12/0806 20/0001, // ARP request
						   12/0806 20/0002, // ARP response
						   12/0800,         // IP
						   -                // Others
						   )

  ipPacketClassifierClient :: IPClassifier(
					   dst 100.0.0.45 and icmp,             // ICMP
					   dst 100.0.0.45 port 80 and tcp,      // TCP
					   -                                   // Others
					   )

  ipPacketClassifierServer :: IPClassifier(
					   dst 100.0.0.45 and icmp type echo,   // ICMP to lb
					   src port 80 and tcp,                 // TCP
					   -                                   // Others
					   )

  // ARP Queriers and Responders

  arpQuerierClient :: ARPQuerier(100.0.0.45, lb-eth2)
  arpQuerierServer :: ARPQuerier(100.0.0.45, lb-eth1)
  arpRespondClient :: ARPResponder(100.0.0.45 lb-eth2)
  arpRespondServer :: ARPResponder(100.0.0.45 lb-eth1)

  // IP Packets

  ipPacketClient :: GetIPAddress(16) ->
  Print(TOCLINET_GETIPADDRESS16, -1, ACTIVE 1) ->
  CheckIPHeader ->
  Print(TOCLINENT_CHECKHEADER, -1, ACTIVE 1) ->
  [0]arpQuerierClient ->
  Print(ARPQUERIER, -1, ACTIVE 1) ->
  toClient

  ipPacketServer :: GetIPAddress(16) ->
  Print(TOSERVER_GETIPADDRESS16, -1, ACTIVE 1) ->
  CheckIPHeader ->
  [0]arpQuerierServer ->
  Print(TOSERVER_AFTERARP, -1, ACTIVE 1) ->
  toServer

  // Round Robin IP Mapper and IP Rewriter

  roundRobin :: RoundRobinIPMapper(
				   100.0.0.45 - 100.0.0.40 - 0 1,
				   100.0.0.45 - 100.0.0.41 - 0 1,
				   100.0.0.45 - 100.0.0.42 - 0 1
				   )

  ipRewrite :: IPRewriter(roundRobin)

  ipRewrite[0] -> ipPacketServer
  ipRewrite[1] -> ipPacketClient

  // Packet Routing and Processing

  fromClient ->
  avgCntFromClient ->
  clientClassifier

  clientClassifier[0] ->
  cntArpReqClient ->
  arpRespondClient ->
  toClient                // ARP request

  clientClassifier[1] ->
  cntArpRspClient ->
  [1]arpQuerierClient     // ARP response

  clientClassifier[2] ->
  cntLbServedFromClient ->
  FixedForwarder ->
  Strip(14) ->
  CheckIPHeader ->
  ipPacketClassifierClient    // IP

  clientClassifier[3] ->
  cntDropFromClientEth ->
  Discard                    // Others

  // icmp
  ipPacketClassifierClient[0] ->
  cntIcmpFromClient ->
  Print(CLASSIFIED_CLIENT_PING, -1) ->
  ICMPPingResponder ->
  ipPacketClient

  // permited ip packet, lb apply
  ipPacketClassifierClient[1] ->
  [0]ipRewrite

  ipPacketClassifierClient[2] ->
  cntDropFromClientIP ->
  Discard

  fromServer ->
  avgCntFromServer ->
  serverClassifier

  serverClassifier[0] ->
  cntArpReqSrv ->
  arpRespondServer ->
  toServer                   // ARP request

  serverClassifier[1] ->
  cntArpRspSrv ->
  [1]arpQuerierServer        // ARP response

  serverClassifier[2] ->
  cntLbServedFromSrv ->
  FixedForwarder ->
  Strip(14) ->
  CheckIPHeader ->
  ipPacketClassifierServer   // IP

  serverClassifier[3] ->
  cntDropFromSvrEth ->
  Discard                    // Others

  ipPacketClassifierServer[0] ->
  cntIcmpFromServer ->
  ICMPPingResponder ->
  ipPacketServer

  ipPacketClassifierServer[1] ->
  [0]ipRewrite

  ipPacketClassifierServer[2] ->
  cntDropFromSvrIP ->
  Discard

  // Report

  DriverManager(
		pause,
		print > ../../results/lb1.report "
		=================== LB1 Report ===================
		Input Packet rate (pps): $(add $(avgCntToClient.rate) $(avgCntToServer.rate))
		Output Packet rate (pps): $(add $(avgCntFromClient.rate) $(avgCntFromServer.rate))
        
		Total number of input packets: $(add $(avgCntToClient.count) $(avgCntToServer.count))
		Total number of output packets: $(add $(avgCntFromClient.count) $(avgCntFromServer.count))

		Total number of ARP requests: $(add $(¨cntArpReqClient.count) $(cntArpReqSrv.count))
		Total number of ARP responses: $(add $(cntArpRspClient.count) $(cntArpRspSrv.count))

		Total number of service packets: $(add $(cntLbServedFromSrv.count) $(cntLbServedFromClient.count))
		Total number of ICMP report: $(add $(cntIcmpFromServer.count) $(cntIcmpFromClient.count))
		Total number of dropped packets: $(add $(cntDropFromSvrEth.count) $(cntDropFromSvrIP.count) $(cntDropFromClientEth.count) $(cntDropFromClientIP.count))

		=================================================
		"
		)
