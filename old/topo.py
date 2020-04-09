############################################
# @dcarou - diogo@dcarou.com
############################################
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
from mininet.node import OVSSwitch, OVSKernelSwitch
import time
import os
import sys
import random

class JellyfishTopology(Topo):

    #Adds one connection to another of the p random core switch
    #The remaing p-1 ports are reserved for edge switches
    def connectCoreSwitches(self, linkopts1):
        for switch in self.coreSwitches:
            while (len(self.countUsedPorts[switch]) == 0):
                randomSwitch = random.choice(self.coreSwitches)
                if (len(self.countUsedPorts[randomSwitch]) == 0 and randomSwitch != switch):
                    self.addLink(switch, randomSwitch,**linkopts1)
                    self.countEdges += 1
                    self.countUsedPorts[switch].append(randomSwitch)
                    self.countUsedPorts[randomSwitch].append(switch)

    #Connects each of the edge switches to a random core swith as long its not occupied
    #Then conneccts the remaining p - 2 ports to random edge switches as long as its not occupied
    #Then connects a host to the remaing port
    def connectEdgeSwitchesToHosts(self, linkopts2, linkopts3):
        for switch in self.edgeSwitches:
            self.countHosts += 1
            host = self.addHost("h%s" % self.countHosts)
            self.countEdges += 1
            self.addLink(host, switch, **linkopts3)
            self.countUsedPorts[switch].append(host)

        for switch in (self.edgeSwitches + self.coreSwitches):
            while (len(self.countUsedPorts[switch]) < self.numPorts):
                randomSwitch = random.choice(self.edgeSwitches + self.coreSwitches)
                if (len(self.countUsedPorts[randomSwitch]) < self.numPorts and randomSwitch != switch and randomSwitch not in self.countUsedPorts[switch]):
                    self.addLink(switch, randomSwitch,**linkopts2)
                    print(switch + "<-->" + randomSwitch)
                    self.countEdges += 1
                    self.countUsedPorts[switch].append(randomSwitch)
                    self.countUsedPorts[randomSwitch].append(switch)


    def __init__(self, linkopts1, linkopts2, linkopts3, p = 2, **opts):
        super(JellyfishTopology, self).__init__(**opts)
        seed = random.randrange(sys.maxsize)
        rng = random.seed(2127772746744491812L)
        self.numPorts = p
        countS = 0
        countH = 0
        self.countEdges = 0
        self.countSwitch = 0
        self.coreSwitches = []
        self.edgeSwitches = []
        self.countUsedPorts = {}
        self.countHosts = 0

        #creates p core switches
        countCores = (self.numPorts/2)**2
        for i in irange(1,countCores):
            self.countSwitch += 1
            coreSwitch = self.addSwitch("s%s" % (self.countSwitch),cls=OVSKernelSwitch,failMode='standalone')
            self.coreSwitches.append(coreSwitch)
            self.countUsedPorts[coreSwitch] = []

        #connects the core switches together
        self.connectCoreSwitches(linkopts1)

        #creates p^2 edge switches to be randomly assigned to core switches
        countEdges = countCores**2
        for i in irange(1,countEdges):
            self.countSwitch += 1
            edgeSwitch = self.addSwitch("s%s" % (self.countSwitch),cls=OVSKernelSwitch,failMode='standalone')
            self.edgeSwitches.append(edgeSwitch)
            self.countUsedPorts[edgeSwitch] = []

        #connects the edge switches to cores and other edge switches
        #connects the hosts to edge switches
        self.connectEdgeSwitchesToHosts(linkopts2, linkopts3)

        print("\n---------------------%s-port Jellyfish  ---------------" % self.numPorts )
        print("number of ports per switch                : %s" % self.numPorts)
        print("total number of switches                  : %s" % self.countSwitch)
        print("  - number of core switches               : %s" % len(self.coreSwitches))
        print("  - number of edge switches               : %s" % len(self.edgeSwitches))
        print("total number of hosts                     : %s" % self.countHosts)
        print("number of links                           : %s" % self.countEdges)
        print("-----------------------------------------------------")


# Creates Simple Tree Topology
class SimpleTreeTopology(Topo):
    def __init__(self,linkopts1,linkopts2,linkopts3,k=2, **opts):

       #linkopts1 = performance parameters for the links between core and aggregation switches
       #linkopts2 = performance parameters for the links between aggregation and edge switches
       #linkopts3 = performance parameters for the links between edge switches and host

        super(SimpleTreeTopology, self).__init__(**opts)
        self.fanout = k
        # Adds Core Switch
        coreSwitch = self.addSwitch("s1")
        countS = 1
        countH = 0
        self.edgeHostConn = 0
        self.numAgg = 0
        self.numEdge = 0
        self.edgeAggConn = 0
        self.aggCoreConn = 0

        #Adds Aggregation Switches and links them to Core Switch
        for i in irange(1,k):
            countS = countS + 1
            aggregationSwitch = self.addSwitch("s%s" % (countS))
            self.numAgg +=1
            self.addLink(aggregationSwitch,coreSwitch,**linkopts1)
            self.aggCoreConn +=1

            #Adds Edge Switches and links them to Aggregation Switches
            for j in irange(1,k):
                countS = countS + 1
                edgeSwitch = self.addSwitch("s%s" % (countS))
                self.numEdge += 1
                self.addLink(edgeSwitch,aggregationSwitch,**linkopts2)
                self.edgeAggConn +=1

                #Adds Hosts and links them to Edge Switches
                for n in irange(1,k):
                    countH = countH + 1
                    host = self.addHost("h%s" % countH)
                    self.addLink(host,edgeSwitch,**linkopts3)
                    self.edgeHostConn += 1

        print("\n---------------------%s-ary simple tree  ---------------" % self.fanout )
        print("edge switch-host connections              : %s" % self.edgeHostConn)
        print("edge switch-aggregation switch connections: %s" % self.edgeAggConn)
        print("aggregation switch-core switch connections: %s" % self.aggCoreConn)
        print("number of edge switches                   : %s" % self.numEdge)
        print("number of aggregation switches            : %s" % self.numAgg)
        print("number of core switches                   : 1")
        print("total number of hosts                     : %s" % countH)
        print("-----------------------------------------------------")

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

# Creates a Simple Tree Topology
def startSimpleTreeTopology(fanout=2,linkopts1 = {'bw':20},linkopts2 = {'bw':1},linkopts3 = {'bw':10}):
    topo = SimpleTreeTopology(linkopts1,linkopts2,linkopts3,k=fanout)
    net = Mininet(topo,link=TCLink)
    net.start()
   # CLI(net)
    return net

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

    # Goes trough the tree from the leafs to the root, compares the values,
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

    # Goes trough the tree from the leafs to the root,
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
        print "#### Protocolos em Redes de Dados ####"
        print "######################################\n"
        print "Main Menu:\n"
        print " 1 - Simple Tree Topology"
        print " 2 - Fat Tree Topology"
        print " 3 - Jellyfish Topology"
        print " 4 - Exit Program\n"
        mainOption = input('Please select an option from the menu: ')

        if(mainOption == 4):
             exit = True

        if(mainOption == 1 or mainOption == 2 or mainOption == 3):
            simpleGoBack = False
            fatGoBack = False
            createdTopo = False
            createdTopoPing=False
            createdTopoPingLoss=False
            print "\n\n######################################"
            if(mainOption == 1 ):
                print "####### Simple Tree Topology #######"
            if (mainOption == 2):
                print "####### Fat Tree Topology #######"
            if (mainOption == 3):
                print "####### Jellyfish Topology #######"
            print "######################################\n"

            inputSimpleFanout = input('Please enter the desired fanout: ')

            while(not simpleGoBack):

                print "\n######################################"
                if(mainOption == 1 ):
                    print "  Simple Tree Topology with Fanout %s" % inputSimpleFanout
                if(mainOption == 2 ):
                    print "  Fat Tree Topology with Fanout %s" % inputSimpleFanout
                if(mainOption == 3 ):
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
                        if(mainOption == 1 ):
                           net = startSimpleTreeTopology(inputSimpleFanout)
                           CLI(net)
                        if(mainOption == 2 ):
                           net = startFatTreeTopology(inputSimpleFanout)
                           CLI(net)
                        if(mainOption == 3 ):
                           net = startJellyfishTopology(inputSimpleFanout)
                           CLI(net)
                        createdTopo = True
                if(inputSimpleOption == 2):
                    simpleTestGoBack = False
                    createdTopoPing = False
                    createdTopoPingLoss= False
                    while(not simpleTestGoBack):
                        print "\n###############################################"
                        if(mainOption == 1 ):
                            print " Tests for Simple Tree Topology with Fanout %s" % inputSimpleFanout
                        if(mainOption == 2 ):
                            print " Tests for Fat Tree Topology with Fanout %s" % inputSimpleFanout
                        if(mainOption == 3 ):
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
                                if(mainOption == 1 ):
                                    net = startSimpleTreeTopology(inputSimpleFanout)
                                if(mainOption == 2 ):
                                    net = startFatTreeTopology(inputSimpleFanout)
                                if(mainOption == 3 ):
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

                                if(mainOption == 1 ):
                                    net = startSimpleTreeTopology(inputSimpleFanout, linkopts1,linkopts2,linkopts3)
                                if(mainOption == 2 ):
                                    net = startFatTreeTopology(inputSimpleFanout, linkopts1,linkopts2,linkopts3)
                                if(mainOption == 3 ):
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

                                if(mainOption == 1 ):
                                    net = startSimpleTreeTopology(inputSimpleFanout,linkopts1,linkopts2,linkopts3)
                                if(mainOption == 2 ):
                                    net = startFatTreeTopology(inputSimpleFanout,linkopts1,linkopts2,linkopts3)
                                if(mainOption == 3 ):
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
