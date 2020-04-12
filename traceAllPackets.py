import os

allPaths = set()
numSwitchHits = {}

numSwitches = 20
numHosts = 16

for i in range (1,numSwitches+1):
    os.system('sudo ovs-ofctl dump-flows {} > flows_{}.txt'.format('s' + str(i), 's' + str(i)))

for sr in range(1, numHosts+1):
    for ds in range(1, numHosts+1):
        if (sr == ds):
            continue
        switches = ''
        src = '10.0.0.' + str(sr)
        dst = '10.0.0.' + str(ds)
        for i in range(1,21):
            switch = 's' + str(i)
            f = open('flows_{}.txt'.format(switch))
            entries = f.readlines()
            for s in entries:
                if (s.find('nw_src={},'.format(src))!= -1 and s.find('nw_dst={},'.format(dst)) != -1 and s.find('icmp_type=0,') != -1):
                    switches += " " + switch

                    if switch not in numSwitchHits:
                        numSwitchHits[switch] = 1
                    else:
                        numSwitchHits[switch] += 1

        print(src + " --> " + dst)
        print(switches)
        allPaths.add(switches)

print("Totoal number of unique paths: " + str(len(allPaths)))
print(numSwitchHits)
#os.system('rm flows*')
