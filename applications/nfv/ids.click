//ids-eth3<->insp-eth0 (OK OK)    #TO INSP
//ids-eth2<->sw2-eth3 (OK OK)     #TO SWITCH2/OUTSIDE ZONES
//lb1-eth2<->ids-eth1 (OK OK)     #TO WEB SERVERS/LOAD BALANCER

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


fromSWITCH :: FromDevice(ids-eth2, METHOD LINUX, SNIFFER false);
fromSERVER :: FromDevice(ids-eth1, METHOD LINUX, SNIFFER false);
toSWITCH :: Queue -> ToDevice(ids-eth2, METHOD LINUX);
toSERVER :: Queue  -> ToDevice(ids-eth1, METHOD LINUX);
toINSP :: Queue -> ToDevice(ids-eth3, METHOD LINUX);

serverPacketType, clientPacketType :: Classifier(
			
		12/0806,		//ARP
                12/0800,		//IP
                 -
 );


classify_HTTP_others:: IPClassifier(
		
		psh,		//set for HTTP 
		-		//OTHERS, non http 	
		
);


classify_HTTPmethod :: Classifier(
		//66/474554,		// GET
		66/505554,		// PUT
		66/504f5354,		// POST				   
		-			
);
					
					
classify_PUT_keywords :: Classifier(
		0/636174202f6574632f706173737764,		//cat/etc/passwd
		0/636174202f7661722f6c6f672f,    		//cat/var/log
		0/494E53455254,                  		//INSERT
		0/555044415445,                  		//UPDATE
		0/44454C455445,                  		//DELETE
		-
);
                    
                    
search_PUT_keywords :: Search("\r\n\r\n")


//Check Client Packet Type
fromSWITCH -> clientPacketType;
clientPacketType[0] -> FixedForwarder -> toSERVER;      							//ARP
clientPacketType[1] -> Strip(14) -> CheckIPHeader -> /*Print(CLIENT_IP_PACKETS, -1)->*/ classify_HTTP_others;	//ip packets
clientPacketType[2] -> Discard;											//others

//Check HTTP vs NON HTTP
classify_HTTP_others[1] -> Unstrip(14) -> FixedForwarder -> toSERVER;                			        //non-http 
classify_HTTP_others[0] -> Unstrip(14) -> /*Print(TO_HTTP_CLASSIFIER, -1) ->*/ classify_HTTPmethod;		//http

//Check HTTP Method
classify_HTTPmethod[0] -> search_PUT_keywords;			//PUT, so we check keywords
classify_HTTPmethod[1] -> FixedForwarder -> toSERVER;		//POST, pass on to server
classify_HTTPmethod[2] -> FixedForwarder -> toINSP;    		//Others, passed to INSP

//If PUT, search for PUT data
search_PUT_keywords[0] -> /*Print(AFTER_SEARCH, -1) ->*/ classify_PUT_keywords;
search_PUT_keywords[1] -> toINSP;

//If Harmful keywords found, sent to INSP, otherwise send to SERVER
classify_PUT_keywords[0] -> Unstrip(211) -> toINSP;
classify_PUT_keywords[1] -> Unstrip(211) -> toINSP;
classify_PUT_keywords[2] -> Unstrip(211) -> toINSP;
classify_PUT_keywords[3] -> Unstrip(211) -> toINSP;
classify_PUT_keywords[4] -> Unstrip(211) -> toINSP;
classify_PUT_keywords[5] -> /*Print(BEFORE_UNSTRIP, -1) ->*/ Unstrip(211) ->Print(AFTER_UNSTRIP_TO_SERVER, -1) -> FixedForwarder -> toSERVER;


//For the Server Side, check packet type forward accordingly
fromSERVER -> serverPacketType;
serverPacketType[0] -> FixedForwarder -> toSWITCH;
serverPacketType[1] -> FixedForwarder -> toSWITCH;
serverPacketType[2] -> Discard;






