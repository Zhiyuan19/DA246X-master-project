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



