import socket
import struct
import sys
import time
import datetime
import math
import argparse


def printmessage(type, requet_add, myseqnum, payloadlen, payload):
    if type == 'D':
        print('DATA Packet')
    else:
        print('END Packet')
    curtime = datetime.datetime.now()
    print('{0:<17}{1}'.format('recv time:', curtime))
    print('{0:<17}{1}'.format('sender addr:', (requet_add[0] +':'+str(requet_add[1]))))
    print('{0:<17}{1}'.format('sequence:', myseqnum))
    print('{0:<17}{1}'.format('length:', payloadlen))
    if type == 'D':
        print('{0:<17}{1}'.format('payload:', payload))
    else:
        print('{0:<17}{1}'.format('payload:', 0))
    print()

def printsum(requet_add, total_data, total_byte, average, duration):
    print('Summary')
    print('{0:<25}{1}'.format('sender addr:', (requet_add[0] +':'+str(requet_add[1]))))
    print('{0:<25}{1}'.format('Total Data packets:', total_data))
    print('{0:<25}{1}'.format('Total Data bytes:', total_byte))
    print('{0:<25}{1}'.format('Average packets/second:', average))
    print('{0:<25}{1} {2}'.format('Duration of the test:', duration, 'ms'))
    print()
# get parameter
parser = argparse.ArgumentParser()
parser.add_argument('-p')
parser.add_argument('-o')
args = parser.parse_args()

paradict = {}
try:
    paradict['requester_port'] = int(args.p)
except:
    print('Input port is not an integer!')
    sys.exit(0)
paradict['file_opt'] = args.o.encode()

# binding
requester_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
requester_sock.bind((socket.gethostbyname(socket.gethostname()),paradict['requester_port']))

# read tracker.txt to know sender
store = {}
with open('tracker.txt') as file:
    for line in file:
        tmp = line.rstrip().split()
        if tmp[0] in store:
            store[tmp[0]].append(tmp[1:])
        else:
            store[tmp[0]] = [tmp[1:]]
for i,v in store.items():
    store[i] = sorted(store[i], key = lambda x:x[0])
# send request packet
#{'file1.txt': [['1', 'mumble-03', '6000'], ['2', 'mumble-01', '5000'], ['3', 'mumble-01', '7000']], 'file2.txt': [['1', 'mumble-02', '5000']]}
tmplen = len(paradict['file_opt'])
packet = struct.pack(f'!cII{tmplen}s','R'.encode(), 0, 0, paradict['file_opt'])
for name,info in store.items():
    buffer = ''
    for i in info:
        total_data = 0
        total_byte = 0
        requester_sock.sendto(packet,(socket.gethostbyname(i[1]),int(i[2])))
        #requester_sock.sendto(packet,(socket.gethostname(),i[2]))
        while True:
            in_packet, requet_add = requester_sock.recvfrom(1024)
            if total_byte == 0:
                start_time = time.time()
            packet_type, seq_num, payload_len = struct.unpack('!cII', in_packet[:9])
            payload = in_packet[9:].decode()
            total_byte += socket.ntohl(payload_len)
            if packet_type.decode() == 'D':
                total_data += 1
                buffer = buffer + payload
                printmessage('D',requet_add, socket.ntohl(seq_num), socket.ntohl(payload_len), payload[0:4])
                #print(round(time.time() * 1000), requet_add, socket.ntohl(seq_num), socket.ntohl(payload_len), payload[0:4])
                
            elif packet_type.decode() == 'E':
                end_time = time.time()
                #total_data += 1
                printmessage('E',requet_add, socket.ntohl(seq_num), socket.ntohl(payload_len), payload[0:4])
                printsum(requet_add, total_data, total_byte, math.ceil(total_data / (end_time-start_time)), (end_time-start_time)*1000)
                #print(round(time.time() * 1000), requet_add, i[2], total_data, total_byte, socket.ntohl(seq_num), socket.ntohl(payload_len), payload, total_data / (end_time-start_time), end_time-start_time)
                break
    with open(name, 'w') as f:
        f.write(buffer)            

