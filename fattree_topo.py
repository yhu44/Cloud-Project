#!/usr/bin/python
# -*- coding: utf-8 -*-
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import irange
from mininet.node import OVSKernelSwitch
import time
import os
import sys
import math

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
    return net
