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
parser.add_argument('-p') # the port requester waits on
parser.add_argument('-o') # name of the file being requested

parser.add_argument('-f') # emulator name
parser.add_argument('-e') # emulator port
parser.add_argument('-w') # request window size
args = parser.parse_args()

paradict = {}
try:
    paradict['requester_port'] = int(args.p)
    paradict['emulator_port'] = int(args.e)
    paradict['req_wind_size'] = int(args.w)
except:
    print('Input port is not an integer!')
    sys.exit(0)
paradict['file_opt'] = args.o.encode()
paradict['emulator_name'] = args.f

# binding
requester_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# changed
requester_sock.setblocking(False) # add non-blocking
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
rpacket = struct.pack(f'!cII{tmplen}s','R'.encode(), 0, socket.htonl(paradict['req_wind_size']), paradict['file_opt'])
buffer = {}
for name,info in store.items():
    for i in info:
        total_data = 0
        total_byte = 0
        # changed
        source_addr = socket.gethostbyname(socket.gethostname())
        #source_len = len(source_addr)
        dest_addr = socket.gethostbyname(i[1])
        #dest_len = len(dest_addr)
        packet = struct.pack(f'!B4sH4sHI',1, socket.inet_aton(source_addr),socket.htons(paradict['requester_port']),socket.inet_aton(dest_addr),socket.htons(int(i[2])),socket.htonl(len(rpacket))) + rpacket
        #print(paradict['emulator_name'])
        requester_sock.sendto(packet,(socket.gethostbyname(paradict['emulator_name']),paradict['emulator_port']))
        #requester_sock.sendto(packet,(socket.gethostname(),i[2]))
        while True:
            try:
                in_packet, requet_add = requester_sock.recvfrom(1024)
                _, _, _, des_add, des_port, _, packet_type, seq_num, payload_len = struct.unpack('!B4sH4sHIcII', in_packet[:26])
                packet = struct.pack(f'!cII{tmplen}s','A'.encode(), seq_num, 0, paradict['file_opt'])
                #print('seq_num:', socket.ntohl(seq_num))
                #print('data: ', in_packet[26:])
                packet = struct.pack(f'!B4sH4sHI',1,socket.inet_aton(socket.gethostbyname(socket.gethostname())),socket.htons(paradict['requester_port']),socket.inet_aton(socket.gethostbyname(i[1])),socket.htons(int(i[2])),socket.htonl(len(packet))) + packet
                requester_sock.sendto(packet,(socket.gethostbyname(paradict['emulator_name'] ),paradict['emulator_port']))
            except socket.error:
                #print("G",end=None)
                continue
            if total_byte == 0:
                start_time = time.time()
            # changed
            #print(in_packet)
            #_, _, _, des_add, des_port, _, packet_type, seq_num, payload_len = struct.unpack('!B4sH4sHIcII', in_packet[:26])
            des_add = socket.inet_ntoa(des_add)
            des_port = socket.ntohs(des_port)
            if des_add != socket.gethostbyname(socket.gethostname()) or des_port != paradict['requester_port']:
                continue
            
            payload = in_packet[26:].decode()
            total_byte += socket.ntohl(payload_len)
            #print(packet_type.decode())
            if packet_type.decode() == 'D':
                total_data += 1
                buffer[socket.ntohl(seq_num)] = payload
                #printmessage('D',requet_add, socket.ntohl(seq_num), socket.ntohl(payload_len), payload[0:4])
                #print(round(time.time() * 1000), requet_add, socket.ntohl(seq_num), socket.ntohl(payload_len), payload[0:4])
                
            elif packet_type.decode() == 'E':
                end_time = time.time()
                #total_data += 1
                #printmessage('E',requet_add, socket.ntohl(seq_num), socket.ntohl(payload_len), payload[0:4])
                printsum((socket.gethostbyname(i[1]), i[2]), total_data, total_byte, math.ceil(total_data / (end_time-start_time)), (end_time-start_time)*1000)
                #print(round(time.time() * 1000), requet_add, i[2], total_data, total_byte, socket.ntohl(seq_num), socket.ntohl(payload_len), payload, total_data / (end_time-start_time), end_time-start_time)
                break
            
            # changed
            #packet = struct.pack(f'!cII{tmplen}s','A'.encode(), seq_num, 0, paradict['file_opt'])
            #packet = struct.pack(f'!B4sH4sHI',1,socket.inet_aton(socket.gethostbyname(socket.gethostname())),socket.htons(paradict['requester_port']),socket.inet_aton(socket.gethostbyname(i[1])),socket.htons(int(i[2])),socket.htonl(len(packet))) + packet
            #print(packet)
            #requester_sock.sendto(packet,(socket.gethostbyname(paradict['emulator_name'] ),paradict['emulator_port']))


    # sort buffer dict
    buffer = dict(sorted(buffer.items())) 
    result = ''
    for content in buffer.values():
        result = result + content
    #print(buffer)
    with open(name, 'w') as f:
        f.write(result)            

