// 2 variables to hold ports names
define($PORT1 sw1-eth1, $PORT2 sw1-eth2)

// Script will run as soon as the router starts
// not work with two script
// Script(print "lb1: Load balancer 1 started!"
Script(print "lb1: Click forwarder on $PORT1 $PORT2")

// Group common elements in a single block. $port is a parameter used just to print
elementclass L2Forwarder {$port|
	input
	->cnt::Counter
        ->Print
	->Queue
	->output
}

// From where to pick packets
fd1::FromDevice($PORT1, SNIFFER false, METHOD LINUX, PROMISC true)
fd2::FromDevice($PORT2, SNIFFER false, METHOD LINUX, PROMISC true)

// Where to send packets
td1::ToDevice($PORT1, METHOD LINUX)
td2::ToDevice($PORT2, METHOD LINUX)

// Instantiate 2 forwarders, 1 per directions
fd1->fwd1::L2Forwarder($port1)->td2
fd2->fwd2::L2Forwarder($port2)->td1


// Print something on exit
// DriverManager will listen on router's events
// The pause instruction will wait until the process terminates
// Then the prints will run an Click will exit
DriverManager(
        print "lb1: Router starting",
        pause,
	print "lb1: Packets from ${PORT1}: $(fwd1/cnt.count)",
	print "lb1: Packets from ${PORT2}: $(fwd2/cnt.count)",
)