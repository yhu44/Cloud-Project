import os

allPaths = set()

for i in range (1,21):
    os.system('sudo ovs-ofctl dump-flows {} > flows_{}.txt'.format('s' + str(i), 's' + str(i)))

for sr in range(1, 17):
    for ds in range(sr+1, 17):
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
        print(src + " --> " + dst)
        print(switches)
        allPaths.add(switches)

print("Totoal number of unique paths: " + str(len(allPaths)))
os.system('rm flows*')
