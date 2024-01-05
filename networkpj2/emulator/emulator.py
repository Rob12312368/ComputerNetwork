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


# routing function
def routing(dest_addr, dest_port, prior, packet, packet_type, source_add, source_port):
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
parser.add_argument('-q') # three queue size

parser.add_argument('-f') # forwarding table file name
parser.add_argument('-l') # log file name
args = parser.parse_args()

paradict = {}
try:
    paradict['emulator_port'] = int(args.p)
    paradict['queue_size'] = int(args.q)
except:
    print('Input port is not an integer!')
    sys.exit(0)

paradict['table_name'] = args.f
paradict['log_name'] = args.l

# binding
emulator_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# changed
emulator_sock.setblocking(False) # add non-blocking
emulator_sock.bind((socket.gethostbyname(socket.gethostname()),paradict['emulator_port']))




# read table.txt to know sender
# mumble-03 5000 mumble-05 5000 mumble-05 5000 3000 0
# ()
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

queue = {1:deque([]), 2:deque([]), 3:deque([])}
# delaying time expire
expire_time = time.time()
first_visit = True
logfilename = paradict['log_name'] 
with open(logfilename, 'w') as f:
    pass

        
while True:
    try:
        # got packet
        in_packet, in_packet_add = emulator_sock.recvfrom(1024)
        #print(in_packet, len(in_packet))
        prior, source_add, source_port, des_add, des_port, _, packet_type, seq_num, payload_len = struct.unpack('!B4sH4sHIcII', in_packet[:26])
        des_add = socket.inet_ntoa(des_add)
        des_port = socket.ntohs(des_port)
        source_add = socket.inet_ntoa(source_add)
        source_port = socket.ntohs(source_port)
        #print(packet_type.decode())
        #if packet_type.decode() == 'E':
            #print('YESSSSSSSSSSSSS')
        routing(des_add, des_port, prior, in_packet, packet_type.decode(), source_add, source_port)

    except socket.error:
        # no packet
        pass
    if time.time() < expire_time:
        #print('WAITING!!!!!!!!')
        continue
    else:
        sending()

