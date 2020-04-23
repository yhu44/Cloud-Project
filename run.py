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
from topos.fattree import startFatTreeTopology, FatTreeTopology
from topos.jellyfish import startJellyfishTopology, JellyfishTopology

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

def testRandomIperf(net, option, testOption, fanout):
    print("starting random iperf test")
    port_min = 1025
    port_max = 65536

    hosts = net.hosts

    for host in range(len(hosts) / 2):
        port = str(random.randint(port_min, port_max))
        endpts = random.sample(hosts, 2)
        src = net.get(str(endpts[0]))
        dst = net.get(str(endpts[1]))

	#set up server
        topo = "fattree"
        test = None
        if option == 2:
            topo = "jellyfish"
        
        if testOption == 1:
            test = "randIperf/" 
        if testOption == 2:
            test = "randIperfDelLinks/"

        server_cmd = "iperf -s -p "
        server_cmd += port
        server_cmd += " -i 1"
        server_cmd += " > " + topo +"-logs/" + test +"fanout-" + str(fanout) + "/flow%003d" % host + ".txt 2>&1"
        server_cmd += " & "

        client_cmd = "iperf -c "
        client_cmd += dst.IP() + " "
        client_cmd += " -p " + port
        client_cmd += " -t " + str(60)
        client_cmd += " & "

	#sleep as flows are generated


	#send cmd
        dst.cmdPrint(server_cmd)
        src.cmdPrint(client_cmd)

    time.sleep(60)
    #kill iperf in all hosts
    for host in net.hosts:
        host.cmdPrint('killall -9 iperf')

#delete links for testing fault resiliency
def delLinks(net):
    print("deleting links")
    numDelLinks = 2
    links = net.links
    allSwitches = None
    finDelLinks = []
    while(True):
        delLinks = random.sample(links, numDelLinks)
        for link in delLinks:
            src = str(link.intf1)
            dst = str(link.intf2)
            print(src[0])
            print(dst[0]) 
            if(src[0] != 's' or dst[0] != 's'):
                allSwitches = False
                break
            else:
                allSwitches = True 
        if(allSwitches):
            for link in delLinks:
                finDelLinks.append(str(link)) 
                net.delLink(link)
            break
    return finDelLinks

#add deleted links back into the topology
def addLinks(net, delLinks):
    print("Adding back deleted links")
    for link in delLinks:
        linkStrSplit = link.split("-")
        nodeStr1 = linkStrSplit[0]
        nodeStr2 = linkStrSplit[2]
        nodeStr2 = nodeStr2[1:]
        print(nodeStr1, nodeStr2) 
        node1 = net.get(nodeStr1)
        node2 = net.get(nodeStr2)
        net.addLink(node1, node2)
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


def printAllPaths(net, option, fanout):
    net.pingAll()
    time.sleep(2)
    allPaths = set()
    numSwitchHits = {}
    for switch in net.switches:
        os.system('sudo ovs-ofctl dump-flows {} > flows_{}.txt'.format(switch, switch))

    for sr in range(1, len(net.hosts)):
        for ds in range(1, len(net.hosts)):
            if (sr == ds):
                continue
            switches = ''
            src = '10.0.0.' + str(sr)
            dst = '10.0.0.' + str(ds)
            for i in range(1, len(net.switches)+1):
                f = open('flows_{}.txt'.format('s' + str(i)))
                entries = f.readlines()
                switch = 's' + str(i)
                for e in entries:
                    if (e.find('nw_src={},'.format(src)) != -1 and e.find('nw_dst={},'.format(dst)) != -1 and e.find('icmp_type=0') != -1):
                        switches += "s" + str(i) + " "
                        if switch not in numSwitchHits:
                            numSwitchHits[switch] = 1
                        else:
                            numSwitchHits[switch] += 1
            print(src + "-->" + dst)
            print(switches)
            allPaths.add(switches)
    f_name = ""
    if option == 1:
        f_name += 'fattree-logs/'
    else:
        f_name += 'jellyfish-logs/'
    f_name += 'pathDiversity/'
    f_name += 'fanout-{}.txt'.format(fanout)
    
    f = open(f_name, "w")
    while len(numSwitchHits) > 0:
        m = -1
        maxSwitch = ''
        for switch in numSwitchHits:
            if numSwitchHits[switch] > m:
                m = numSwitchHits[switch]
                maxSwitch = switch
        f.write(maxSwitch + " " + str(m) + '\n')
        del numSwitchHits[maxSwitch]
    
    f.close()
    print("Total number of unique paths: " + str(len(allPaths)))
    print(numSwitchHits)
    os.system('rm flows*')



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
                        print " 2 - iPerf Test w/ deleted Links"
                        print " 3 - Print all paths"
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

                            #node1 = raw_input("\nPlease select a source Host (hX): ")
                            #node2 = raw_input("Please select destination Host (hX): ")
                            testRandomIperf(net, mainOption, inputSimpleTestOption, inputSimpleFanout)
                            explanationIperf(mainOption)

                        if(inputSimpleTestOption == 2):

                            print "\n##############################################"
                            print "############# Running iPerf Test with deleted Links##############"
                            print "###############################################\n"
                            if (createdTopo == False):
                                if(mainOption == 1):
                                    net = startFatTreeTopology(inputSimpleFanout)
                                if(mainOption == 2):
                                    net = startJellyfishTopology(inputSimpleFanout)
                                createdTopo = True

                            createdTopoPing = False
                            createTopoPingLoss = False

                            #node1 = raw_input("\nPlease select a source Host (hX): ")
                            #node2 = raw_input("Please select destination Host (hX): ")
                            deletedLinks = delLinks(net)
                            testRandomIperf(net, mainOption, inputSimpleTestOption, inputSimpleFanout)
                            addLinks(net, deletedLinks)
                            explanationIperf(mainOption)
                        #PRINT ALL PATHS
                        if(inputSimpleTestOption == 3):
                            if (createdTopo == False):
                                cleanup()
                                if(mainOption == 1):
                                    net = startFatTreeTopology(inputSimpleFanout)
                                if(mainOption == 2):
                                    net = startJellyfishTopology(inputSimpleFanout)
                                createdTopo = True
                            printAllPaths(net, mainOption, inputSimpleFanout)


if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    run()
