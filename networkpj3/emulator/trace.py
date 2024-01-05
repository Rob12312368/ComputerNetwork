import socket
import struct
import sys
import time
import datetime
import math
import argparse
import random
from collections import deque 

# get parameter
parser = argparse.ArgumentParser()
parser.add_argument('-a') # routetrace port
parser.add_argument('-b') # source hostname

parser.add_argument('-c') # source port
parser.add_argument('-d') # destination hostname
parser.add_argument('-e') # destination port
parser.add_argument('-f') # debug option
args = parser.parse_args()

paradict = {}

try:
    paradict['route_port'] = int(args.a)
    paradict['source_port'] = int(args.c)
    paradict['dest_port'] = int(args.e)
    paradict['debug_opt'] = int(args.f)
except:
    print('Input port or debug option is not an integer!')
    sys.exit(0)

paradict['route_host'] = socket.gethostbyname(socket.gethostname())
paradict['source_host'] = socket.gethostbyname(args.b)
paradict['dest_host'] = socket.gethostbyname(args.d)


trace_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# changed
#trace_sock.setblocking(False) # add non-blocking
trace_sock.setblocking(False) # add non-blocking
trace_sock.bind((paradict['route_host'],paradict['route_port']))

ttl = 0
allowsending = True
lasttime = time.time()
result = ''
while True:
    if allowsending or time.time() - lasttime >= 0.2:
        lasttime = time.time()
        packet = struct.pack('!c4sH4sHI','R'.encode('utf-8'), socket.inet_aton(paradict['route_host']), socket.htons(paradict['route_port']), socket.inet_aton(paradict['dest_host']), socket.htons(paradict['dest_port']), socket.htonl(ttl))
        trace_sock.sendto(packet, (paradict['source_host'], paradict['source_port']))
        if paradict['debug_opt'] == 1 and allowsending:
            print('Just Sent:')
            print('TTL',ttl,'SRC',(paradict['source_host'],paradict['source_port']),'DEST',(paradict['dest_host'],paradict['dest_port']))
    #print('sending to',(paradict['source_host'], paradict['source_port']))
    #print('waiting, just send with ttl = ', ttl)
    try:
        in_packet, in_packet_add = trace_sock.recvfrom(1024)
        _, source_ip, source_port, dest_ip, dest_port, recttl = struct.unpack('!c4sH4sHI',in_packet)
        allowsending = True
        lasttime = time.time()
        ttl += 1
        if paradict['debug_opt'] == 1:
            print('Just Received:')
            print('TTL',socket.ntohl(recttl),'SRC',(socket.inet_ntoa(source_ip),socket.ntohs(source_port)),'DEST',(socket.inet_ntoa(dest_ip),socket.ntohs(dest_port)))
        
        result += f'{ttl-1}, {in_packet_add[0]}, {in_packet_add[1]}\n'
        if in_packet_add == (paradict['dest_host'], paradict['dest_port']):
            #print('done!!!')
            break

        #time.sleep(0.2)
    except socket.error:
        allowsending = False

    #time.sleep(0.2)
print(result)
