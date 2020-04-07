import os
src = input("Give last IP digit of src: ")
dst = input("Give last IP digit of dst: ")
src = '10.0.0.' + str(src)
dst = '10.0.0.' + str(dst)

for i in range (1,21):
    os.system('sudo ovs-ofctl dump-flows {} > flows_{}.txt'.format('s' + str(i), 's' + str(i)))

for i in range(1,21):
    switch = 's' + str(i)
    f = open('flows_{}.txt'.format(switch))
    entries = f.readlines()
    for s in entries:
        if (s.find('nw_src={},'.format(src))!= -1 and s.find('nw_dst={},'.format(dst)) != -1 and s.find('icmp_type=0,') != -1):
            print(switch)
