import os
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.clean import cleanup
import time
from topos.fattree import FatTreeTopology

print("Cleaning up..")
cleanup()
topo = FatTreeTopology()
net = Mininet(topo, link=TCLink)
print("Building topology...")
net.start()

print("Running spanning tree protocol...")
for i in range(1, 21):
    os.system('sudo ovs-vsctl set Bridge "%s" stp_enable=true' % ('s'+ str(i)))

time.sleep(20*2)
print("Done!")

CLI(net)
