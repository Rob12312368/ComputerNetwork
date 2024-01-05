# python3 emulator.py -p <port> -q <queue_size> -f <filename> -l <log>

import socket
import struct
import sys
import time
import datetime
import math
import argparse
import random
from collections import deque 
import copy
'''
ip_port
{'1.0.0.0': '1', '2.0.0.0': '2', '3.0.0.0': '3', '4.0.0.0': '4', '5.0.0.0': '5'}
topo(ip, port)
{
 '1.0.0.0': [('2.0.0.0', '2'), ('3.0.0.0', '3')],
 '2.0.0.0': [('1.0.0.0', '1'), ('3.0.0.0', '3'), ('5.0.0.0', '5')],
 '3.0.0.0': [('1.0.0.0', '1'), ('2.0.0.0', '2'), ('4.0.0.0', '4')], 
 '4.0.0.0': [('3.0.0.0', '3'), ('5.0.0.0', '5')], 
 '5.0.0.0': [('2.0.0.0', '2'), ('4.0.0.0', '4')]
}
forwarding table
{
 'conf': {'1.0.0.0': ['1.0.0.0', 0, '1.0.0.0'], 
 '2.0.0.0': ['2.0.0.0', 1, '2.0.0.0'],
 '3.0.0.0': ['3.0.0.0', 1, '3.0.0.0'], 
 '5.0.0.0': ['5.0.0.0', 2, '2.0.0.0'], 
 '4.0.0.0': ['4.0.0.0', 2, '3.0.0.0']
}, 
 'tent': {}
}
'''



def readtopo(fname):
    topo = {}
    with open(fname, 'r') as f:
        for line in f:
            tmp = line.strip().split(' ')
            #print(tmp)
            tmp = list(map(lambda x:(x.split(',')[0], int(x.split(',')[1])), tmp))
            topo[tmp[0]] = tmp[1:] # topo[tmp[0]] = tmp[1:] to make key with port
    return topo
def buildfwtable(topo, cur_addr):
    # confirmed and tentative
    forward = {'conf':{}, 'tent':{}}
    forward['conf'][cur_addr] = [cur_addr, 0, None] # [dest, cost, nexthop]
    
    # put things into tentative
    for nei_addr in topo[cur_addr]:
        forward['tent'][nei_addr] = [nei_addr, 1, nei_addr]
    #print(forward)
    #print('forward:',forward)
    while len(forward['tent']) > 0:
        nearest = min(forward['tent'].values(), key=lambda x:x[1])
        #print(nearest)
        nei_addr = nearest[0] # the new element added in to confirmed
        forward['conf'][nei_addr] = nearest
        forward['tent'].pop(nei_addr)
        #print(forward)
        # update cost and next hop (there may be a shorter path)
        for i in forward['tent'].values():
            dest,cost,nexthop = i[0], i[1], i[2]
            #print([j[0] for j in topo[nei_ip]])
            if dest in topo[nei_addr]:
                if cost > nearest[1]+1:
                    i[1] = nearest[1] + 1
                    i[2] = nearest[2]

        # add more node into tentative
        for addr in topo[nei_addr]:
            if addr not in forward['conf'].keys() and addr not in forward['tent'].keys():
                forward['tent'][addr] = [addr, nearest[1]+1, forward['conf'][nei_addr][2]]

    # make it the specified format
    return forward['conf']

def fwpacket(tmp, neiandcost, emu_add):

    # forwarding link state message
    nei_ip, nei_port, nei_seq, nei_ttl = tmp
    if nei_ttl > 0:
        packet = struct.pack(f'!c4sHII{len(neiandcost)}s','L'.encode('utf-8'),socket.inet_aton(nei_ip),socket.htons(nei_port),socket.htonl(nei_seq),socket.htonl(nei_ttl-1),neiandcost)
        for nei in topo_copy[emu_add]:
            if nei != (nei_ip, nei_port):
                emulator_sock.sendto(packet, nei)
        

def broadcasthello(in_packet, emu_add, in_packet_add):
    #print('HELLOOOOOOOOOOOOO')
    global cur_link_seq
    global fwtable
    packet_type, source_add, source_port = struct.unpack('!c4sH', in_packet)
    packet_type = packet_type.decode('utf-8')
    source_add = socket.inet_ntoa(source_add)
    source_port = socket.ntohs(source_port)
    latest_timestp[in_packet_add] = time.time()
    # used to be unavailable, need to update to available and broadcast
    if in_packet_add in topo_copy[emu_add] and in_packet_add not in topo[emu_add]:
        #index = topo_unavail[emu_add].index(in_packet_add)
        #topo[emu_add].append(topo_unavail[emu_add].pop(index))
        #index = topo_unavail[in_packet_add].index(emu_add)
        #topo[in_packet_add].append(topo_unavail[in_packet_add].pop(index))
        topo[emu_add].append(in_packet_add)
        if emu_add not in topo[in_packet_add]:
            topo[in_packet_add].append(emu_add)
        fwtable = buildfwtable(topo,emu_add)
        #print(109)
        print_topo_fw()
        # send linkstate message to neighbors
        for nei in topo_copy[emu_add]:
            #packet = struct.pack(f'!cII5s','H'.encode(), 0, 0, 'hello')
            #print('seq_num:', socket.ntohl(seq_num))
            #print('data: ', in_packet[26:])
            #packet = struct.pack(f'!B4sH4sHI',1,socket.inet_aton(emu_ip),socket.htons(paradict['emulator_port']),socket.inet_aton(socket.gethostbyname(nei[0])),socket.htons(int(nei[1])),socket.htonl(len(packet))) + packet      
            #packet = struct.pack('!4sH', 'H',socket.inet_aton(emu_ip),socket,paradict['emulator_port'])
            neiandcost = ''
            for nei in topo[emu_add]:
                neiandcost = neiandcost + f'{nei[0]},{nei[1]},{fwtable[nei][1]} '
            neiandcost = neiandcost.encode('utf-8')
            packet = struct.pack(f'!c4sHII{len(neiandcost)}s','L'.encode('utf-8'), socket.inet_aton(emu_add[0]), socket.htons(paradict['emulator_port']), socket.htonl(cur_link_seq), socket.htonl(10), neiandcost)
            cur_link_seq += 1
            emulator_sock.sendto(packet, nei)

def broadcastlink(in_packet, emu_add, in_packet_add):
    global cur_link_seq
    global fwtable
    nei_type, nei_ip, nei_port, nei_seq, nei_ttl = struct.unpack('!c4sHII',in_packet[:15])
    #tmp = [nei_ip, nei_port, nei_seq, nei_ttl]
    nei_ip = socket.inet_ntoa(nei_ip)
    nei_port = socket.ntohs(nei_port)
    nei_seq = socket.ntohl(nei_seq)
    nei_ttl = socket.ntohl(nei_ttl)
    neighbors = in_packet[15:].decode().strip().split(' ')
    #print(nei_ip, nei_port, nei_seq, nei_ttl, neighbors)
    neighbors = [(i.split(',')[0], int(i.split(',')[1])) for i in neighbors if i]
    # need to change neighbors's format, or it would never be topo[nei_ip]
    # check if it is the latest message
    #print('neighborrrrrr',in_packet_add, neighbors)
    #print('topo', topo)
    #if (nei_ip, nei_port
    if lastest_seq[(nei_ip, nei_port)] < nei_seq:
        lastest_seq[(nei_ip, nei_port)] = nei_seq
        # update topology and forwarding table
        #print(1477)
        print_topo_fw()
        if topo[(nei_ip, nei_port)] != neighbors:
            for addr in topo[(nei_ip, nei_port)]:
                if addr not in neighbors:
                    topo[(nei_ip, nei_port)].remove(addr)
                    if (nei_ip, nei_port) in topo[addr]:
                        topo[addr].remove((nei_ip, nei_port))
            for addr in neighbors:
                if addr not in topo[(nei_ip, nei_port)]:
                    topo[(nei_ip, nei_port)].append(addr)
                    if (nei_ip, nei_port) not in topo[addr]:
                        topo[addr].append((nei_ip, nei_port))
            fwtable = buildfwtable(topo, emu_add)
            #print(147)
            #print(in_packet_add, neighbors)
            #print_topo_fw()
    
    tmp = [nei_ip, nei_port, nei_seq, nei_ttl]
    # wrong, should pass the in_packet along, need to create my own
    fwpacket(tmp, in_packet[15:], emu_add)
def printdict(dic, opt):
    if opt == 'topo':
        for node,neis in dic.items():
            if len(neis) == 0:
                continue
            line = f'{node[0]},{node[1]} '
            for nei in neis:
                line = line + f'{nei[0]},{nei[1]} '
            print(line)
    else:
        for node, data in dic.items():
            if data[2] == None:
                continue
            print(f'{node[0]},{node[1]} {data[2][0]},{data[2][1]}')

def print_topo_fw():
    #return
    print('Topology:')
    #print(topo)
    printdict(topo, 'topo')
    print('------------------------------------')
    print('Forwarding Table:')
    #print(fwtable)
    printdict(fwtable, 'fwtable')

def routetrace(in_packet, emu_add, route_trace_addr):
    packet_type, route_source, route_source_port, route_dest, route_dest_port, ttl = struct.unpack('!c4sH4sHI',in_packet)
    
    tmpttl = socket.ntohl(ttl)
    #print(f'dest ip:{socket.inet_ntoa(route_dest)}, dest port:{socket.ntohs(route_dest_port)}, ttl:{tmpttl}')
    if tmpttl == 0:
        packet = struct.pack('!c4sH4sHI','R'.encode('utf-8'), socket.inet_aton(socket.gethostbyname(socket.gethostname())), socket.htons(paradict['emulator_port']), route_dest, route_dest_port, ttl)
        route_source = socket.inet_ntoa(route_source)
        route_source_port = socket.ntohs(route_source_port)
        #print('ttl0',route_source, route_source_port)
        emulator_sock.sendto(packet, (route_source, route_source_port))
    else:
        tmpttl -= 1
        packet = struct.pack('!c4sH4sHI','R'.encode('utf-8'), route_source, route_source_port, route_dest, route_dest_port,socket.htonl(tmpttl))
        route_dest = socket.inet_ntoa(route_dest)
        route_dest_port = socket.ntohs(route_dest_port)
        #print((route_dest,route_dest_port))
        nexthop = fwtable[(route_dest,route_dest_port)][2]
        #with open('mytext.txt','a') as f:
            #f.write(str(emu_add)+str(nexthop))
        #print('ttl not 0',nexthop)
        emulator_sock.sendto(packet, nexthop)

# routing function
def routing(dest_addr, dest_port, prior, packet, packet_type, source_add, source_port):
    # helloMessage

    if (dest_addr, dest_port) in table:
        if len(queue[prior]) <  paradict['queue_size'] or packet_type == 'E':
            queue[prior].append((table[(dest_addr, dest_port)],packet, packet_type, source_add, source_port))
        else:
            # priority queue is full
            subdict = table[(dest_addr, dest_port)]
            logging(f"priority queue {prior} was full",subdict, prior, len(packet)-26, source_add, source_port)
    else:
        # no forwarding entry found
        logging("no forwarding entry found",subdict, prior, len(packet)-26, source_add, source_port)


# logging function
def logging(message, subdict, prior, payloadlen, source_add, source_port):
    desthost = subdict['destination'][0]
    destport = subdict['destination'][1]
    delay = subdict['delay']
    with open(paradict['log_name'] ,'a') as f:
        line = f'{message} {source_add} {source_port} {desthost} {destport} {delay} {prior} {payloadlen}'
        line = line + '\n'
        f.writelines(line)
    return
# sending function
# queue => [[{'destination':destination, 'nexthop':nexthop, 'delay':delay, 'losprob':losprob}, packet],[],[]]
def sending():
    global expire_time
    global first_visit
    for i, q in queue.items():
        if len(q) > 0:
            # delayq[0]
            if first_visit:
                expire_time = time.time() + q[0][0]['delay']
                first_visit = False
                return
            subdict, packet, packet_type, source_add, source_port= q.popleft()
            #print(subdict, packet, packet_type)
            # packet may be dropped
            myrandom = random.random()
            if packet_type != 'E' and myrandom < subdict['losprob']: # bugs, should be subdict['losprob']/100, leaving it for testing
                # packet drop, keep record
                #print('LOSS!!!')
                #print('Loss: meta:', subdict)
                #print('Loss: data:', packet)
                logging("loss event occurred.",subdict, i, len(packet)-26, source_add, source_port)
            else:
                # send
                #print('SEND!!!')
                #print(subdict['nexthop'])
                emulator_sock.sendto(packet, subdict['nexthop'])
            first_visit = True
            return




# get parameter
parser = argparse.ArgumentParser()
parser.add_argument('-p') # the port or the emulator
#parser.add_argument('-q') # three queue size

parser.add_argument('-f') # forwarding table file name
#parser.add_argument('-l') # log file name
args = parser.parse_args()

paradict = {}
try:
    paradict['emulator_port'] = int(args.p)
    #paradict['queue_size'] = int(args.q)
except:
    print('Input port is not an integer!')
    sys.exit(0)

paradict['table_name'] = args.f
#paradict['log_name'] = args.l

# binding
emulator_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# changed
emulator_sock.setblocking(False) # add non-blocking
emulator_sock.bind((socket.gethostbyname(socket.gethostname()),paradict['emulator_port']))




# read table.txt to know sender
# mumble-03 5000 mumble-05 5000 mumble-05 5000 3000 0
# ()
'''
table = {}
tablefilename = paradict['table_name']
with open(f'{tablefilename}.txt') as file:
    myaddress = socket.gethostbyname(socket.gethostname())
    for line in file:
        tmp = line.rstrip().split()
        #print(tmp[0], tmp[1])
        emulator = (socket.gethostbyname(tmp[0]), int(tmp[1]))
        destination = (socket.gethostbyname(tmp[2]), int(tmp[3]))
        nexthop = (socket.gethostbyname(tmp[4]), int(tmp[5]))
        delay = int(tmp[6]) / 1000
        losprob = int(tmp[7]) / 100
        subdict = {'destination':destination, 'nexthop':nexthop, 'delay':delay, 'losprob':losprob}
        if emulator[0] == myaddress and emulator[1] == paradict['emulator_port']:
            table[destination] = subdict
'''
#for pj3
topo = readtopo(paradict['table_name'])
#print(topo)
topo_copy = copy.deepcopy(topo)
emu_add = (socket.gethostbyname(socket.gethostname()), paradict['emulator_port'])
#print(emu_add)
fwtable = buildfwtable(topo, emu_add)
print_topo_fw()
#sys.exit(0)
topo_unavail = {key:[] for key in topo.keys()}
latest_timestp = {key:0 for key in topo.keys()}
lastest_seq = {key:0 for key in topo.keys() if key != emu_add} # record the lastest seq of a sender
cur_link_seq = 0 # record the current linkstate packet sequence number
def_interval = 0.5
expire_time_hello = time.time() + def_interval # 0.5 second is the defined interval
expire_time_link = time.time() + def_interval

'''
queue = {1:deque([]), 2:deque([]), 3:deque([])}
# delaying time expire
expire_time = time.time()
first_visit = True
logfilename = paradict['log_name'] 
with open(logfilename, 'w') as f:
    pass
'''
while True:
    try:
        # got packet
        in_packet, in_packet_add = emulator_sock.recvfrom(1024)
        #print(in_packet, len(in_packet))    
        # for routetrace packet:
        if in_packet[0] == 82:
            #print('got route trace!!!')
            routetrace(in_packet, emu_add, in_packet_add)
        # for linkstate message
        elif in_packet[0] == 76:
            #packet_type, source_add, source_port = struct.unpack('!s4sH', in_packet)
            broadcastlink(in_packet, emu_add, in_packet_add)
        # for hello message
        elif in_packet[0] == 72:
            broadcasthello(in_packet, emu_add, in_packet_add)
        # for normal data packet
        else:
            prior, source_add, source_port, des_add, des_port, _, packet_type, seq_num, payload_len = struct.unpack('!B4sH4sHIcII', in_packet[:26])
            des_add = socket.inet_ntoa(des_add)
            des_port = socket.ntohs(des_port)
            source_add = socket.inet_ntoa(source_add)
            source_port = socket.ntohs(source_port)
            #routing(des_add, des_port, prior, in_packet, packet_type.decode(), source_add, source_port)
            emulator_sock.sendto(in_packet, fwtable[des_add][2])
        #print(packet_type.decode())
        #if packet_type.decode() == 'E':
            #print('YESSSSSSSSSSSSS')
        
    except socket.error:
        # no packet
        pass

    # send hello message to all neighbors
    if time.time() > expire_time_hello:
        #print('SEND HELLO')
        expire_time_hello = time.time() + 0.25 #used to be def_interval
        for nei in topo_copy[emu_add]: # all neighbors (including avail and unavail)
            packet = struct.pack('!c4sH', 'H'.encode('utf-8'), socket.inet_aton(emu_add[0]),socket.htons(paradict['emulator_port']))
            #print('hello from topo')
            emulator_sock.sendto(packet,nei)
    # check each neighbor
    tmptime = time.time()
    for addr, last in latest_timestp.items():
        if tmptime - last > 3:
            # used to be available, need to update to unavailable and broadcast
            if addr in topo[emu_add]:
                #print(topo[emu_add],addr)
                #print('remove', addr, topo[emu_add])
                topo[emu_add].remove(addr)
                topo[addr].remove(emu_add)
                #index = topo[emu_add].index(addr)
                #topo_unavail[emu_add].append(topo[emu_add].pop(index))
                #index = topo[addr].index(emu_add)
                #topo_unavail[addr].append(topo[addr].pop(index))
                fwtable = buildfwtable(topo, emu_add)
                #print(359)
                print_topo_fw()
                neiandcost = ''
                for nei in topo[emu_add]:
                    neiandcost = neiandcost + f'{nei[0]},{nei[1]},{fwtable[nei][1]} '
                #for nei, cost in fwtable[emu_add]:
                    #neiandcost = neiandcost + f'{nei[0]},{nei[1]},{cost} '
                neiandcost = neiandcost.encode('utf-8')
                #sys.exit(0)
                # send linkstate message to neighbors
                for nei in topo_copy[emu_add]:
                    #packet = struct.pack(f'!cII5s','H'.encode(), 0, 0, 'hello')
                    #print('seq_num:', socket.ntohl(seq_num))
                    #print('data: ', in_packet[26:])
                    #packet = struct.pack(f'!B4sH4sHI',1,socket.inet_aton(emu_ip),socket.htons(paradict['emulator_port']),socket.inet_aton(socket.gethostbyname(nei[0])),socket.htons(int(nei[1])),socket.htonl(len(packet))) + packet      
                    #packet = struct.pack('!4sH', 'H',socket.inet_aton(emu_ip),socket,paradict['emulator_port'])
                    
                    packet = struct.pack(f'!c4sHII{len(neiandcost)}s','L'.encode('utf-8'), socket.inet_aton(emu_add[0]), socket.htons(paradict['emulator_port']), socket.htonl(cur_link_seq), socket.htonl(10), neiandcost)
                    emulator_sock.sendto(packet, nei)
    # send link message to all neighbors
    if time.time() > expire_time_link:
        expire_time_link = time.time() + 0.25
        neiandcost = ''
        #print(fwtable[emu_add])
        for nei in topo[emu_add]:
            neiandcost = neiandcost + f'{nei[0]},{nei[1]},{fwtable[nei][1]} '
        neiandcost = neiandcost.encode('utf-8')
        for nei in topo_copy[emu_add]:
            packet = struct.pack(f'!c4sHII{len(neiandcost)}s','L'.encode('utf-8'), socket.inet_aton(emu_add[0]), socket.htons(paradict['emulator_port']), socket.htonl(cur_link_seq), socket.htonl(10), neiandcost)
            cur_link_seq += 1
            emulator_sock.sendto(packet, nei)
    #if time.time() < expire_time:
        #print('WAITING!!!!!!!!')
        #continue
    #else:
        #sending()

