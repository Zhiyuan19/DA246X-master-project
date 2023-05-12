# SDN-NFV
Repository for the KTH course IK2220 - Group 2 

FIXED IN CODE -Manually Delete links before running Mininet:
  sudo mn --link=tc --topo=mytopo
  
TO make http requests:

h1 curl -X POST -d 'Hello' -s 100.0.0.40/post


call this before sending ToDevice in Click:

elementclass IPChecksumFixer{ $print |
        input
        ->SetIPChecksum
        -> class::IPClassifier(tcp, udp, -)
        class[0] -> Print(TCP, ACTIVE $print) -> SetTCPChecksum -> output
        class[1] -> Print(UDP, ACTIVE $print) -> SetUDPChecksum -> output
        class[2] -> Print(OTH, ACTIVE $print) -> output
}

elementclass FixedForwarder{
         input
        ->Strip(14)
        ->SetIPChecksum
        ->CheckIPHeader
        ->IPChecksumFixer(0)
        ->Unstrip(14)
        ->output
}



