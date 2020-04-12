from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import irange
from mininet.node import OVSKernelSwitch
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
        self.nPorts = p
        self.create_topology()

    def create_topology(self):
        servers = []
        for n in range(self.nServers):
            servers.append(self.addHost('h%s' % str(n+1)))

        switches = []
        openPorts = []
        serverI = 0
        for n in range(self.nSwitches):
            switches.append(self.addSwitch('s%s' % str(n+1)))
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
                        if (i, rLink[0][0]) in links:
                            continue
                        if (i, rLink[0][1]) in links:
                            continue

                        links.remove(rLink[0])
                        links.remove(rLink[0][::-1])

                        links.add((i, rLink[0][0]))
                        links.add((rLink[0][0], i))
                        links.add((i, rLink[0][1]))
                        links.add((rLink[0][1], i))

                        openPorts[i] -= 2

        for link in links:
            if link[0] < link[1]:
                self.addLink(switches[link[0]], switches[link[1]])

def startJellyfishTopology(ports=4,linkopts1 = {'bw':10},linkopts2 = {'bw':10}, linkopts3 = {'bw':10}):
    topo = JellyfishTopology(linkopts1,linkopts2,linkopts3, p=ports)
    net = Mininet(topo,link=TCLink)
    net.start()
    print("Loading Spanning Tree Protocol...")
    # For each switch, enables stp
    for switch in net.switches:
        os.system('ovs-vsctl set Bridge "%s" stp_enable=true' % switch.name)
    time.sleep(len(net.switches)*2) # Waits until all switches are enabled
    return net


topos = { 'jellyfish': ( lambda: JellyfishTopology() ) }
