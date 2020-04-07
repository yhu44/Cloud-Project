import os
import time

for i in range(1, 21):
    os.system('sudo ovs-vsctl set Bridge "%s" stp_enable=true' % ('s'+ str(i)))
time.sleep(20*2)
print("Done!")
