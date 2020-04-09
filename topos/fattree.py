from mininet.topo import Topo
from mininet.node import OVSKernelSwitch


class Pod(object):
    def __init__(self):
        self.layers = [[],[]]

class FatTreeTopology(Topo):

    def __init__(self,linkopts1={'bw':10},linkopts2={'bw':10},linkopts3={'bw':10},k=4, **opts):
        Topo.__init__( self )
        self.k = k
        self.pods = []
        self.cores = []
        self.countHosts = 0
        self.countSwitch = 0
        self.hostForPod = 0
        self.numCores = 0
        self.numSwitchesPerPod = self.k/2

        #Creates Core Switches
        for i in range(self.numSwitchesPerPod**2):
            self.countSwitch += 1
            coreSwitch = self.addSwitch("s%s" % (self.countSwitch),cls=OVSKernelSwitch,failMode='standalone')
            self.cores.append(coreSwitch)
            self.numCores+=1

        #Creates Pods + Hosts
        for i in range(self.k):
            self.pods.append(self.createPod(i,linkopts2,linkopts3))

        #Links Core Switches to Pods
        coreSwitchPos = 0
        for core in self.cores:
            for pod in self.pods:
                if coreSwitchPos < self.numSwitchesPerPod:
                    self.addLink(pod.layers[0][(self.numSwitchesPerPod/2)-1],core)
                else:
                    self.addLink(pod.layers[0][self.numSwitchesPerPod/2],core)
            coreSwitchPos += 1

    #Function for Creating Pods
    def createPod(self, index,linkopts2,linkopts3):
        pod = Pod()
        self.hostForPod = 0

        for i in range(self.k/2): #for number of switches in pod
           #Add agg switches
           self.countSwitch += 1
           pod.layers[0].append(self.addSwitch("s%s" % (self.countSwitch),cls=OVSKernelSwitch,failMode='standalone'))

           #Add edge switches
           self.countSwitch += 1
           edgeSwitch = self.addSwitch("s%s" % (self.countSwitch),cls=OVSKernelSwitch,failMode='standalone')
           pod.layers[1].append(edgeSwitch)

           #add hosts
           for j in range(self.k/2):
                self.countHosts +=1
                self.addLink(self.addHost("h%s" % (self.countHosts)),edgeSwitch)
                self.hostForPod += 1

        for i in pod.layers[0]: # Add link btw each agg switch (0) and an edge switch (1)
           for j in pod.layers[1]:
                self.addLink(j,i)

        return pod

topos = { 'fattree': ( lambda: FatTreeTopology() ) }
