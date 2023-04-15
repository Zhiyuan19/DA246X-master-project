

from mininet.topo import Topo

from mininet.net import Mininet

from mininet.node import Switch

from mininet.cli import CLI

from mininet.node import RemoteController

from mininet.node import OVSSwitch

from topology import *

import testing


topos = {'mytopo': (lambda: MyTopo())}


def run_tests(net):

    # You can automate some tests here

    # TODO: How to get the hosts from the net??

    hosts = net.hosts

    for host in hosts:

        if host.IP() == '100.0.0.10':

            a = host

        elif host.IP() == '100.0.0.11':

            b = host

    print("a =", a.name, a.IP())

    print("b =", b.name, b.IP())

    # Launch some tests

    testing.ping(a, b, True)

    # testing.curl(h1, h2, expected=False)


if __name__ == "__main__":

    # Create topology

    topo = MyTopo()

    ctrl = RemoteController("c0", ip="127.0.0.1", port=6633)

    # Create the network

    net = Mininet(topo=topo,

                  switch=OVSSwitch,

                  controller=ctrl,

                  autoSetMacs=True,

                  autoStaticArp=True,

                  build=True,

                  cleanup=True)

    # Start the network

    net.start()

    startup_services(net)

    run_tests(net)

    # Start the CLI

    CLI(net)

    # You may need some commands before stopping the network! If you don't, leave it empty

    ### COMPLETE THIS PART ###

    net.stop()
