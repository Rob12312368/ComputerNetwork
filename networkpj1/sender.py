# python3 sender.py -p <port> -g <requester port> -r <rate> -q <seq_no> -l <length>

import socket
import struct
import sys
import time
import datetime
import argparse

def printmessage(type, requet_add, myseqnum, payloadlen, payload):
    if type == 'D':
        print('DATA Packet')
    else:
        print('END Packet')
    curtime = datetime.datetime.now()
    print('{0:<17}{1}'.format('send time:', curtime))
    print('{0:<17}{1}'.format('requester addr:', (requet_add[0] +':'+str(requet_add[1]))))
    print('{0:<17}{1}'.format('sequence:', myseqnum))
    print('{0:<17}{1}'.format('length:', payloadlen))
    print('{0:<17}{1}'.format('payload:', payload))
    print()


# get parameter
parser = argparse.ArgumentParser()
parser.add_argument('-p')
parser.add_argument('-g')
parser.add_argument('-r')
parser.add_argument('-q')
parser.add_argument('-l')
args = parser.parse_args()

paradict = {}
try:
    paradict['receive_port'] = int(args.p)
    paradict['response_port'] = int(args.g)
    paradict['send_rate'] = int(args.r)
    paradict['seq_num'] = int(args.q)
    paradict['packet_len'] = int(args.l)
except:
    print('One of the parameters is not interger!')
    sys.exit(0)
# binding
receive_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receive_sock.bind((socket.gethostbyname(socket.gethostname()),paradict['receive_port']))
#response_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# listen (waiting for the requester)
lastindex = 0
myseqnum = paradict['seq_num']

in_packet, requet_add = receive_sock.recvfrom(1024)
packet_type, _, _ = struct.unpack('!cII',in_packet[:9])
filename = struct.unpack(f'{len(in_packet[9:])}s',in_packet[9:])
if packet_type.decode('utf-8') == 'R':
    with open(filename[0].decode(), 'r') as file:
        data = file.read()
        while lastindex + paradict['packet_len'] <= len(data):
            payload = data[lastindex:lastindex + paradict['packet_len']]
            printmessage('D',requet_add, myseqnum, len(payload), payload[0:4])
            #print(round(time.time() * 1000), requet_add, myseqnum, payload[0:4])
            payload = payload.encode()
            packet = struct.pack(f'!cII{len(payload)}s', 'D'.encode(), socket.htonl(myseqnum), socket.htonl(paradict['packet_len']), payload)
            receive_sock.sendto(packet, requet_add)
            myseqnum += paradict['packet_len']
            lastindex += paradict['packet_len']
            time.sleep(1 / paradict['send_rate'])
        #print(lastindex,len(data))
        if lastindex < len(data):
            payload = data[lastindex:]
            printmessage('D',requet_add, myseqnum, len(payload), payload[0:4])
            payload = payload.encode()
            packet = struct.pack(f'!cII{len(payload)}s', 'D'.encode(), socket.htonl(myseqnum), socket.htonl(len(data[lastindex:])), payload)
            receive_sock.sendto(packet, requet_add)
            myseqnum += len(data[lastindex:])
            time.sleep(1 / paradict['send_rate'])
        packet = struct.pack('!cIIc', 'E'.encode(), socket.htonl(myseqnum), socket.htonl(0), 'E'.encode())
        printmessage('E',requet_add, myseqnum, 0, '')
        receive_sock.sendto(packet, requet_add)
                
                
