#!/usr/bin/python
# -*- coding: utf-8 -*-
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import irange,dumpNodeConnections
from mininet.log import setLogLevel
from mininet.clean import cleanup
from mininet.cli import CLI
from mininet.util import pmonitor
from mininet.node import Node, OVSSwitch, OVSKernelSwitch
import time
import os
import sys
import random
import math

class JellyfishTopology(Topo):

    def __init__(self, linkopts1,linkopts2,linkopts3,p=2, **opts):
        super(JellyfishTopology, self).__init__()
        self.nServers = int((p**2)*(2**(math.log(p,2)-2)))
        self.nSwitches = ((p/2)**2 + p**2)
        print(self.nServers)
        self.nPorts = p
        self.create_topology()

    def create_topology(self):
        servers = []
        for n in range(self.nServers):
            servers.append(self.addHost('h%s' % n))

        switches = []
        openPorts = []
        serverI = 0
        for n in range(self.nSwitches):
            switches.append(self.addSwitch('s%s' % n))
            openPorts.append(self.nPorts)
            if (serverI < self.nServers):
                for i in range(serverI, serverI + self.nPorts/4):
                    self.addLink(switches[n], servers[i])
                    openPorts[n] -= 1
            serverI += self.nPorts/4

        links = set()
        switchesLeft = self.nSwitches
        consecFails = 0
        while switchesLeft > 1 and consecFails < 10:
            s1 = random.randrange(self.nSwitches)
            while openPorts[s1] == 0:
                s1 = random.randrange(self.nSwitches)

            s2 = random.randrange(self.nSwitches)
            while openPorts[s2] == 0 or s1 == s2:
                s2 = random.randrange(self.nSwitches)

            if (s1, s2) in links:
                consecFails += 1
            else:
                consecFails = 0
                links.add((s1, s2))
                links.add((s2, s1))

                openPorts[s1] -= 1
                openPorts[s2] -= 1

                if openPorts[s1] == 0:
                    switchesLeft -= 1

                if openPorts[s2] == 0:
                    switchesLeft -= 1

        if switchesLeft > 0:
            for i in range(self.nSwitches):
                while openPorts[i] > 1:
                    while True:
                        rLink = random.sample(links, 1)
                        if (i, rLink[0]) in links:
                            continue
                        if (i, rLink[1]) in links:
                            continue

                        links.remove(rLink)
                        links.remove(rLink[::-1])

                        links.add((i, rLink[0]))
                        links.add((rLink[0], i))
                        links.add((i, rLink[1]))
                        links.add((rLink[1], i))

                        openPorts[i] -= 2

        for link in links:
            if link[0] < link[1]:
                self.addLink(switches[link[0]], switches[link[1]])

class Pod(object):
    def __init__(self):
        self.layers = [[],[]] #layer 1= agg switches, layer 2 = edge switches


#Creates Fat Tree Topology
#linkopts1 = core and aggregation switches link parameters
#linkopts2 = aggregation and edge switches link parameters
#linkopts3 = edge switches and host link parameters
class FatTreeTopology(Topo):

    def __init__(self,linkopts1,linkopts2,linkopts3,k=2, **opts):

        super(FatTreeTopology, self).__init__(**opts)
        self.k = k
        self.pods = []
        self.cores = []
        self.countHosts = 0
        self.countSwitch = 0
        self.hostForPod = 0
        self.numCores = 0
        self.numSwitchesPerPod = self.k/2

        #Creates Core Switches
        for i in irange(1, self.numSwitchesPerPod**2):
            self.countSwitch += 1
            coreSwitch = self.addSwitch("s%s" % (self.countSwitch),cls=OVSKernelSwitch,failMode='standalone')
            self.cores.append(coreSwitch)
            self.numCores+=1

        #Creates Pods + Hosts
        for i in irange(1,self.k):
            self.pods.append(self.createPod(i,linkopts2,linkopts3))

        #Links Core Switches to Pods
        coreSwitchPos = 0
        for core in self.cores:
            for pod in self.pods:
                if coreSwitchPos < self.numSwitchesPerPod:
                    self.addLink(pod.layers[0][(self.numSwitchesPerPod/2)-1],core,**linkopts1)
                else:
                    self.addLink(pod.layers[0][self.numSwitchesPerPod/2],core,**linkopts1)
            coreSwitchPos += 1

        print("\n---------------------%s-ary fat tree  ---------------" % self.k )
        print("number of pods                            : %s" % self.k)
        print("hosts per pod                             : %s" % self.hostForPod)
        print("number of switch ports in pod             : %s" % self.k)
        print("number of core switches                   : %s" % self.numCores)
        print("total number of hosts                     : %s" % self.countHosts)
        print("-----------------------------------------------------")

    #Function for Creating Pods
    def createPod(self, index,linkopts2,linkopts3):
        pod = Pod()
        self.hostForPod = 0

        for i in irange(1,self.k/2): #for number of switches in pod
           #Add agg switches
           self.countSwitch += 1
           pod.layers[0].append(self.addSwitch("s%s" % (self.countSwitch),cls=OVSKernelSwitch,failMode='standalone'))

           #Add edge switches
           self.countSwitch += 1
           edgeSwitch = self.addSwitch("s%s" % (self.countSwitch),cls=OVSKernelSwitch,failMode='standalone')
           pod.layers[1].append(edgeSwitch)

           #add hosts
           for j in irange(1,self.k/2):
                self.countHosts +=1
                self.addLink(self.addHost("h%s" % (self.countHosts)),edgeSwitch,**linkopts3)
                self.hostForPod += 1

        for i in pod.layers[0]: # Add link btw each agg switch (0) and an edge switch (1)
           for j in pod.layers[1]:
                self.addLink(j,i,**linkopts2)

        return pod

# Creates a Fat Tree Topology
def startFatTreeTopology(k=4,linkopts1 = {'bw':10},linkopts2 = {'bw':10},linkopts3 = {'bw':10}):
    topo = FatTreeTopology(linkopts1,linkopts2,linkopts3,k=k)
    net = Mininet(topo,link=TCLink)
    net.start()
    print("Loading Spanning Tree Protocol...")
    # For each switch, enables stp
    for switch in net.switches:
        os.system('ovs-vsctl set Bridge "%s" stp_enable=true' % switch.name)
    time.sleep(len(net.switches)*2) # Waits until all switches are enabled
  #  CLI(net)
    return net

def startJellyfishTopology(ports=4,linkopts1 = {'bw':10},linkopts2 = {'bw':10}, linkopts3 = {'bw':10}):
    topo = JellyfishTopology(linkopts1,linkopts2,linkopts3, p=ports)
    net = Mininet(topo,link=TCLink)
    net.start()
    print("Loading Spanning Tree Protocol...")
    # For each switch, enables stp

    for switch in net.switches:
        os.system('ovs-vsctl set Bridge "%s" stp_enable=true' % switch.name)
    time.sleep(len(net.switches)*2) # Waits until all switches are enabled
  #  CLI(net)
    return net


# Given a specific parameter, it returns the minimum value between hostSrc and hostDst for that parameter
# eg. Param = "bw"
def getMinParamBetweenHosts(net, hostSrc,hostDst,param):
    minValue = 0
    nameNode1 = hostSrc
    nameNode2 = hostDst

    # Gets the first matched value
    for link in net.links:
        if link.intf1.name.split("-")[0] == hostSrc:
            minValue = link.intf1.params[param]
            break

    # Goes through the tree from the leafs to the root, compares the values,
    # and returns the minimum value for the given parameter
    while(True):
        for link in net.links:

            if(link.intf1.name.split("-")[0] == nameNode1):
                if minValue > link.intf1.params[param]:
                    minValue = link.intf1.params[param]
                nameNode1 = link.intf2.name.split("-")[0]
                break

        for link2 in net.links:
            if(link2.intf1.name.split("-")[0] == nameNode2):
                if minValue > link2.intf1.params[param]:
                    minValue = link2.intf1.params[param]
                nameNode2 = link2.intf2.name.split("-")[0]
                break

        if nameNode1 == nameNode2:
            return minValue

# Given a specific hostSrc and hostDst, it returns the path and the total delay between them
def getPathAndDelayBetweenHosts(net, hostSrc,hostDst):
    result = {'path':"",'sumDelays':0}
    nameNode1 = hostSrc
    nameNode2 = hostDst
    param = 'delay'

    srcToDst = (nameNode1+"-")
    dstToSrc = nameNode2

    # Goes through the tree from the leafs to the root,
    # and returns the path and total delay between hostSrc and hostDst
    while(True):

        for link in net.links:

            if(link.intf1.name.split("-")[0] == nameNode1):
                result['sumDelays'] += int(link.intf1.params[param].split("ms")[0])
                nameNode1 = link.intf2.name.split("-")[0]
                srcToDst += (nameNode1+"-")
                break

        for link2 in net.links:
            if(link2.intf1.name.split("-")[0] == nameNode2):
                result['sumDelays'] +=  int(link.intf1.params[param].split("ms")[0])
                nameNode2 = link2.intf2.name.split("-")[0]
                dstToSrc = (nameNode2+"-"+dstToSrc)
                break

        if nameNode1 == nameNode2:
            srcToDst = srcToDst.replace("-"+nameNode1,'')
            result['path'] = srcToDst + dstToSrc
            result['sumDelays'] = result['sumDelays']*2
            return result

# iPerf Test
def testIperf(net,hostSrc,hostDst):
    nodeHostSrc, nodeHostDst= net.get(hostSrc,hostDst)
    print "\n\n###########################"
    print "######### Result ##########"
    print "###########################\n"
    print("Expected Value = "+str(getMinParamBetweenHosts(net,hostSrc,hostDst,"bw"))+"Mbits/sec\n")
    net.iperf((nodeHostSrc, nodeHostDst))

def explanationIperf(optionMenu):
    print "\n\n###########################"
    print "####### Explanation #######"
    print "###########################\n"
    if optionMenu == 1:
        print "\nThe throughputs given to the links are, as following:"
        print "    1 - Core to Aggregation Switches: 20 Mb/s"
        print "    2 - Aggregation to Edge Switches: 1 Mb/s"
        print "    3 - Edge Switches to Hosts: 10 Mb/s"
    if optionMenu == 2:
        print "\nThe throughputs given to the links are, as following:"
        print "    1 - Core to Aggregation Switches: 10 Mb/s"
        print "    2 - Aggregation to Edge Switches: 10 Mb/s"
        print "    3 - Edge Switches to Hosts: 10 Mb/s"
    print "Baring this values in mind, and since the maximum speed of a connection is limited"
    print "to the maximum speeds of the links it passes through, the expected speed of this"
    print "specific connection can be obtained by looking at all these links, comparing their"
    print "respective connection speeds, and then selecting the minimum value among them.\n"


def explanationPing(net,src,dst,link1,link2,link3):
    pathAndDelay = getPathAndDelayBetweenHosts(net,src,dst)
    print "\n\n###########################"
    print "####### Explanation #######"
    print "###########################\n"
    print "\nAs observed, the value for the first Ping is higher than expected."
    print "This happens because the switch as to first go to the controller in order"
    print "to get the desired route.\n"
    print ("\nDELAYS:\n\tCore <-> Aggregation = %s \n\tAggregation <-> Edge = %s\n\tEdge <-> Host        = %s" % (link1['delay'],link2['delay'],link3['delay']))
    print ("\nThe path between %s and %s is [%s] (round trip)" % (src,dst,pathAndDelay['path']))
    print "Then, and since the delay for each link above, the expected time for"
    print "the Ping command would be around %sms.\n" % pathAndDelay['sumDelays']

def explanationPingLoss():
    print "\n\n###########################"
    print "####### Explanation #######"
    print "###########################\n"
    print "5 packets are sent assuming 10% loss in which one of them.\nSo, 5*10% = 50%, which means that half a packet is loss.\nSince once a packet is corrupted, it is therefore discarted, a whole packet is lost."
    print("Based of following formula: \n\tnumber packets lost / number packets trasmitted\n4we have 1 packet lost / 5 packets trasmitted = 20% packet loss -> minimum expected packet loss value.")
    print "Anything higher than this value, are due to possible network issues."

def testPing(net,node1,node2):
    print "\n\n#############################################"
    print "######## Pinging between %s and %s ##########" % (node1,node2)
    print "#############################################\n"

    popens = {}
    srcH,dstH = net.get(node1, node2)

    numberOfPings = 5

    popens[ dstH ] = srcH.popen("ping -c5 %s" % dstH.IP())
    aux = 1
    for h, line in pmonitor(popens):
        if(h):
            print line,


#Main Function
def run():
    cleanup()
    exit = False
    net = None

    while(not exit):
        #Menu
        print "\n\n######################################"
        print "#### Protocols ####"
        print "######################################\n"
        print "Main Menu:\n"
        print " 1 - Fat Tree Topology"
        print " 2 - Jellyfish Topology"
        print " 3 - Exit Program\n"
        mainOption = input('Please select an option from the menu: ')

        if(mainOption == 3):
             exit = True

        if(mainOption == 1 or mainOption == 2):
            simpleGoBack = False
            fatGoBack = False
            createdTopo = False
            createdTopoPing=False
            createdTopoPingLoss=False
            print "\n\n######################################"
            if (mainOption == 1):
                print "####### Fat Tree Topology #######"
            if (mainOption == 2):
                print "####### Jellyfish Topology #######"
            print "######################################\n"

            inputSimpleFanout = input('Please enter the desired fanout: ')

            while(not simpleGoBack):

                print "\n######################################"
                if(mainOption == 1):
                    print "  Fat Tree Topology with Fanout %s" % inputSimpleFanout
                if(mainOption == 2):
                    print "  JellyfishTopology Topology with Ports %s" % inputSimpleFanout
                print "######################################\n"
                print "Menu:\n"
                print " 1 - Create Topology"
                print " 2 - Run Topology Tests"
                print " 3 - Go Back\n"
                inputSimpleOption = input('Please enter the desired option: ')

                if(inputSimpleOption == 3):
                    cleanup()
                    createdTopo = False
                    simpleGoBack = True

                if(inputSimpleOption == 1):
                    if(createdTopo):
                        print "\nTopology already created!\n"
                    else:
                        if (createdTopoPing or createdTopoPingLoss):
                            cleanup()
                        if(mainOption == 1):
                           net = startFatTreeTopology(inputSimpleFanout)
                           CLI(net)
                        if(mainOption == 2):
                           net = startJellyfishTopology(inputSimpleFanout)
                           CLI(net)
                        createdTopo = True
                if(inputSimpleOption == 2):
                    simpleTestGoBack = False
                    createdTopoPing = False
                    createdTopoPingLoss= False
                    while(not simpleTestGoBack):
                        print "\n###############################################"
                        if(mainOption == 1):
                            print " Tests for Fat Tree Topology with Fanout %s" % inputSimpleFanout
                        if(mainOption == 2):
                            print " Tests for JellyfishTopology Topology with Fanout %s" % inputSimpleFanout
                        print "###############################################\n"
                        print "Menu:\n"
                        print " 1 - iPerf Test"
                        print " 2 - Ping Test"
                        print " 3 - Ping 10% Loss"
                        print " 4 - Go Back\n"
                        inputSimpleTestOption = input('Please enter the desired option: ')

                        if(inputSimpleTestOption == 4):
                            simpleTestGoBack = True

                        if(inputSimpleTestOption == 1):

                            print "\n##############################################"
                            print "############# Running iPerf Test ##############"
                            print "###############################################\n"
                            if (createdTopo == False):
                                if(mainOption == 1):
                                    net = startFatTreeTopology(inputSimpleFanout)
                                if(mainOption == 2):
                                    net = startJellyfishTopology(inputSimpleFanout)
                                createdTopo = True

                            createdTopoPing = False
                            createTopoPingLoss = False

                            node1 = raw_input("\nPlease select a source Host (hX): ")
                            node2 = raw_input("Please select destination Host (hX): ")
                            testIperf(net,node1,node2)
                            explanationIperf(mainOption)

                        if(inputSimpleTestOption == 2):

                            print "\n###############################################"
                            print "############# Running Ping Test ###############"
                            print "###############################################\n"

                            if (createdTopoPing == False):
                                cleanup()
                                linkopts1 = {'delay': "1ms"}
                                linkopts2 = {'delay': "2ms"}
                                linkopts3 = {'delay': "5ms"}

                                if(mainOption == 1):
                                    net = startFatTreeTopology(inputSimpleFanout, linkopts1,linkopts2,linkopts3)
                                if(mainOption == 2):
                                    net = startJellyfishTopology(inputSimpleFanout, linkopts1,linkopts2, linkopts3)
                                createdTopoPing = True
                            createdTopo = False
                            createdTopoPingLoss = False

                            node1 = raw_input("\nPlease select a source Host (hX): ")
                            node2 = raw_input("Please select destination Host (hX): ")
                            testPing(net,node1,node2)
                            explanationPing(net,node1,node2,linkopts1,linkopts2,linkopts3)

                        if(inputSimpleTestOption == 3):
                            print "\n#############################################"
                            print "############# Running Ping Loss Test #########"
                            print "##############################################\n"
                            if (createdTopoPingLoss == False):
                                cleanup()
                                linkopts1 = {'loss':10}
                                linkopts2 = {'loss':10}
                                linkopts3 = {'loss':10}

                                if(mainOption == 1):
                                    net = startFatTreeTopology(inputSimpleFanout,linkopts1,linkopts2,linkopts3)
                                if(mainOption == 2):
                                    net = startJellyfishTopology(inputSimpleFanout,linkopts1,linkopts2, linkopts3)
                                createdTopoPingLoss=True
                            createdTopo = False
                            createdTopoPing = False

                            node1 = raw_input("\nPlease select a source Host (hX): ")
                            node2 = raw_input("Please select destination Host (hX): ")
                            testPing(net,node1,node2)
                            explanationPingLoss()


if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    run()
