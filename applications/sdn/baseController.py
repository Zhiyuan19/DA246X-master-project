from pox.core import core

import pox.openflow.libopenflow_01 as of

from pox.lib.addresses import IPAddr

from pox.lib.util import dpid_to_str

import pox.lib.packet as pkt

import networkFirewalls

import webserver

import subprocess

import shlex

import datetime

import click_wrapper

from l2_learning import LearningSwitch

import signal

log = core.getLogger()


class controller (object):

    # Here you should save a reference to each element:

    devices = dict()

    # Here you should save a reference to the place you saw the first time a specific source mac

    firstSeenAt = dict()

    def __init__(self):
        
        #signal.signal(signal.SIGINT, click_wrapper.handle_kill)
        
        webserver.webserver(self)

        core.openflow.addListeners(self)

        self.click_pids = {} 
    

    #Taken from Click Tutorial Video
    def ids_launch_click(self, dpid):
        cmd = "sudo click /opt/pox/ext/ids.click &"
        print("Started Click")
        p = subprocess.Popen(cmd, shell=True)
        log.info("Launched click with PID:" +str(p.pid)+"\n")
       
    def napt_launch_click(self, dpid):
        cmd = "sudo click /opt/pox/ext/napt.click &"
        print("Started Click napt")
        p = subprocess.Popen(cmd, shell=True)
        log.info("Launched click with PID:" +str(p.pid)+"\n")
    
    def launch_click(self, dpid):
        cmd = "sudo click /opt/pox/ext/lb1.click &"
        print("Started Click")
        p = subprocess.Popen(cmd, shell=True)
        log.info("Launched click with PID:" +str(p.pid)+"\n")
    
        
    def _handle_ConnectionUp(self, event):
        """

        This function is called everytime a new device starts in the network.

        You need to determine what is the new device and run the correct application based on that.



        Note that for normal switches you should use l2_learning module that already is available in pox as an external module.

        """

        # In phase 2, you will need to run your network functions on the controller. Here is just an example how you can do it (Please ignore this for phase 1):
        #click = click_wrapper.start_click("../nfv/forwarder.click", "", "/tmp/forwarder.stdout", "/tmp/forwarder.stderr")
        # For the webserver part, you might need a record of switches that are already connected to the controller.
        # Please keep them in "devices".
        # For instance: self.devices[len(self.devices)] = fw

        dpid = event.dpid

        if dpid == 1 or dpid == 2 or dpid == 3 or dpid == 4 :

            l2_instance = LearningSwitch(event.connection, False)

            self.devices[len(self.devices)] = l2_instance

            # print(l2_instance.macToPort)

        if dpid == 5:

            fw1 = networkFirewalls.FW1(event.connection)

            self.devices[len(self.devices)] = fw1

        if dpid == 6:

            fw2 = networkFirewalls.FW2(event.connection)

            self.devices[len(self.devices)] = fw2
        
        if dpid == 8:
            log.info("\nStarting a Click process for IDS Switch %d" % event.dpid)
        #    p = click_wrapper.start_click("/opt/pox/ext/ids.click", -1, "/opt/pox/ext/ids_tmp/ids.out", "/opt/pox/ext/ids_tmp/ids.err" )
            self.ids_launch_click(event.dpid)
            #log.info("Launched click with PID:" +str(p.pid)+"\n")
          
        if dpid == 7:
            log.info("Starting click process for LB Switch = %d" % dpid)
            #p = click_wrapper.start_click("/opt/pox/ext/lb1.click", "", "/opt/pox/ext/ids_tmp/lb1.out", "/opt/pox/ext/ids_tmp/lb1.err")
            self.launch_click(dpid)
#           ib1 = self.launch_click
# lb1 does not exist
#            self.devices[len(self.devices)] = lb1

        if dpid == 9:
            log.info("\nStarting a Click process for NAPT Switch %d" % event.dpid)
        #   p = click_wrapper.start_click("/opt/pox/ext/napt.click", -1, "/opt/pox/ext/ids_tmp/napt.out", "/opt/pox/ext/ids_tmp/napt.err" )
            self.napt_launch_click(event.dpid)


        return

    # This should be called by each element in your application when a new source MAC is seen

    def updatefirstSeenAt(self, mac, where):
        """

        This function updates your first seen dictionary with the given input.

        It should be called by each element in your application when a new source MAC is seen

        """

        # TODO: More logic needed here!

        if mac in self.firstSeenAt:

            return

        else:

            self.firstSeenAt[mac] = (
                where, datetime.datetime.now().isoformat())

            # print(where)

        return

    def flush(self):
        """

        This will be called by the webserver and act as a 'soft restart'. It should:

        1) ask the switches to flush the rules (look for 'how to delete openflow rules'

        2) clear the mac learning table in each l2_learning switch (Python side) 

        3) clear the firstSeenAt dictionary: it's like starting from an empty state

        """

        for key, value in self.devices.items():

            value.macToPort = {}

        self.firstSeenAt.clear()

        for connection in core.openflow._connections.values():

            connection.send(of.ofp_flow_mod(command=of.OFPFC_DELETE))

        return


def launch(configuration=""):
    core.registerNew(controller)
